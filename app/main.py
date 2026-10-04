import csv
import io
import secrets
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .clinic import CLINIC
from .config import get_settings
from .database import Base, engine, get_db
from .models import Appointment
from .photo_quality import check_photo
from .scheduling import TEHRAN, available_slots, is_bookable_date, now_tehran
from .security import decrypt_text, encrypt_text, searchable_hash
from .validators import (
    clean_name,
    is_valid_mobile,
    is_valid_name,
    is_valid_national_id,
    normalize_national_id,
    normalize_phone,
)

ROOT = Path(__file__).resolve().parent.parent
STORAGE = ROOT / "storage" / "photos"
settings = get_settings()

app = FastAPI(title="سامانه نوبت‌دهی طب کار کوثر", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")
security = HTTPBasic()


@app.on_event("startup")
def startup() -> None:
    if settings.is_production:
        weak = (
            settings.admin_password == "change-this-before-production"
            or settings.app_secret == "development-only-secret"
            or not settings.encryption_key
        )
        if weak:
            raise RuntimeError("Production secrets must be configured before startup")
    STORAGE.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    username_ok = secrets.compare_digest(credentials.username, settings.admin_username)
    password_ok = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور نادرست است.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def appointment_view(item: Appointment) -> dict:
    national_id = decrypt_text(item.national_id_encrypted)
    phone = decrypt_text(item.phone_encrypted)
    return {
        "id": item.id,
        "tracking_code": item.tracking_code,
        "name": f"{item.first_name} {item.last_name}",
        "national_id": national_id,
        "masked_national_id": f"******{national_id[-4:]}",
        "phone": phone,
        "masked_phone": f"{phone[:4]}***{phone[-4:]}",
        "date": item.appointment_date.isoformat(),
        "time": item.appointment_time.strftime("%H:%M"),
        "status": item.status,
        "photo_quality_status": item.photo_quality_status,
        "exported": item.exported,
        "created_at": item.created_at.isoformat(),
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"clinic": CLINIC})


@app.get("/health")
def health():
    return {"ok": True, "service": "kosar-appointment", "version": app.version}


@app.get("/api/dates")
def list_dates(db: Session = Depends(get_db)):
    today = now_tehran().date()
    dates = []
    for offset in range(31):
        day = today + timedelta(days=offset)
        if is_bookable_date(day, db, today=today):
            slots = available_slots(day, db, today=today)
            if slots:
                dates.append({"date": day.isoformat(), "available_count": len(slots)})
    return dates


@app.get("/api/slots")
def list_slots(day: date, db: Session = Depends(get_db)):
    return {
        "date": day.isoformat(),
        "slots": [slot.strftime("%H:%M") for slot in available_slots(day, db)],
    }


@app.post("/api/appointments", status_code=201)
async def create_appointment(
    national_id: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    appointment_date: date = Form(...),
    appointment_time: time = Form(...),
    consent: bool = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    national_id = normalize_national_id(national_id)
    phone = normalize_phone(phone)
    first_name = clean_name(first_name)
    last_name = clean_name(last_name)

    errors = []
    if not consent:
        errors.append("پذیرش قوانین حریم خصوصی الزامی است.")
    if not is_valid_national_id(national_id):
        errors.append("کد ملی معتبر نیست.")
    if not is_valid_name(first_name) or not is_valid_name(last_name):
        errors.append("نام یا نام خانوادگی معتبر نیست.")
    if not is_valid_mobile(phone):
        errors.append("شماره همراه معتبر نیست.")
    if errors:
        raise HTTPException(422, detail=errors)

    selected_time = appointment_time.replace(second=0, microsecond=0)
    if selected_time not in available_slots(appointment_date, db):
        raise HTTPException(409, detail="این نوبت دیگر در دسترس نیست؛ ساعت دیگری انتخاب کنید.")

    national_hash = searchable_hash(national_id)
    active = db.scalar(
        select(Appointment).where(
            Appointment.national_id_hash == national_hash,
            Appointment.status.in_(["confirmed", "attended"]),
        )
    )
    if active:
        raise HTTPException(409, detail="برای این کد ملی یک نوبت فعال وجود دارد.")

    photo_bytes = await photo.read()
    photo_result = check_photo(photo_bytes)
    if not photo_result.accepted:
        raise HTTPException(422, detail=photo_result.reason)

    suffix = Path(photo.filename or "photo.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    photo_path = STORAGE / filename
    photo_path.write_bytes(photo_bytes)

    tracking = f"KOS-{appointment_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    item = Appointment(
        tracking_code=tracking,
        national_id_hash=national_hash,
        national_id_encrypted=encrypt_text(national_id),
        first_name=first_name,
        last_name=last_name,
        phone_encrypted=encrypt_text(phone),
        appointment_date=appointment_date,
        appointment_time=selected_time,
        photo_path=str(photo_path.relative_to(ROOT)),
        consented_at=datetime.now(timezone.utc),
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        photo_path.unlink(missing_ok=True)
        raise HTTPException(409, detail="این ساعت هم‌اکنون رزرو شد؛ ساعت دیگری انتخاب کنید.")
    db.refresh(item)
    return {
        "message": "نوبت با موفقیت ثبت شد.",
        "appointment": appointment_view(item),
        "clinic": CLINIC,
    }


@app.post("/api/appointments/cancel")
def cancel_appointment(
    tracking_code: str = Form(...),
    national_id: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized = normalize_national_id(national_id)
    item = db.scalar(
        select(Appointment).where(
            Appointment.tracking_code == tracking_code.strip().upper(),
            Appointment.national_id_hash == searchable_hash(normalized),
            Appointment.status == "confirmed",
        )
    )
    if not item:
        raise HTTPException(404, detail="نوبت فعالی با این مشخصات پیدا نشد.")
    starts_at = datetime.combine(item.appointment_date, item.appointment_time, tzinfo=TEHRAN)
    if starts_at - now_tehran() < timedelta(hours=24):
        raise HTTPException(409, detail="لغو اینترنتی کمتر از ۲۴ ساعت مانده به نوبت امکان‌پذیر نیست.")
    item.status = "cancelled"
    item.active_slot_key = None
    db.commit()
    return {"message": "نوبت شما لغو شد و ظرفیت آن آزاد گردید."}


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items = db.scalars(
        select(Appointment).order_by(Appointment.appointment_date, Appointment.appointment_time)
    ).all()
    return templates.TemplateResponse(
        request,
        "admin.html",
        {"clinic": CLINIC, "appointments": [appointment_view(item) for item in items]},
    )


@app.get("/admin/export.csv")
def export_csv(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    items = db.scalars(
        select(Appointment).order_by(Appointment.appointment_date, Appointment.appointment_time)
    ).all()
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow(["کد رهگیری", "نام", "کد ملی", "شماره همراه", "تاریخ", "ساعت", "وضعیت"])
    for item in items:
        view = appointment_view(item)
        writer.writerow(
            [view["tracking_code"], view["name"], view["national_id"], view["phone"], view["date"], view["time"], view["status"]]
        )
    data = io.BytesIO(output.getvalue().encode("utf-8"))
    return StreamingResponse(
        data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=kosar-appointments.csv"},
    )
