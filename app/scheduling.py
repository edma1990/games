from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Appointment, Holiday

TEHRAN = ZoneInfo("Asia/Tehran")
FIRST_SLOT = time(7, 20)
# Python weekdays: Monday=0 ... Thursday=3, Friday=4, Saturday=5, Sunday=6
CLOSED_WEEKDAY = 4


def now_tehran() -> datetime:
    return datetime.now(TEHRAN)


def closing_time(day: date) -> time | None:
    if day.weekday() == CLOSED_WEEKDAY:
        return None
    if day.weekday() == 3:  # Thursday
        return time(13, 0)
    return time(14, 0)


def is_bookable_date(day: date, db: Session, today: date | None = None) -> bool:
    today = today or now_tehran().date()
    if day < today or day > today + timedelta(days=30) or closing_time(day) is None:
        return False
    return db.scalar(select(Holiday.id).where(Holiday.holiday_date == day)) is None


def all_slots(day: date) -> list[time]:
    closing = closing_time(day)
    if closing is None:
        return []
    current = datetime.combine(day, FIRST_SLOT)
    end = datetime.combine(day, closing)
    result: list[time] = []
    while current < end:
        result.append(current.time())
        current += timedelta(minutes=20)
    return result


def available_slots(day: date, db: Session, today: date | None = None) -> list[time]:
    explicit_today = today is not None
    effective_today = today or now_tehran().date()
    if not is_bookable_date(day, db, today=effective_today):
        return []
    booked = set(
        db.scalars(
            select(Appointment.appointment_time).where(
                Appointment.appointment_date == day,
                Appointment.status.in_(["confirmed", "attended"]),
            )
        ).all()
    )
    return [slot for slot in all_slots(day) if slot not in booked]
