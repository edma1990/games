from datetime import date, datetime, time, timezone

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, LargeBinary, String, Time, text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Appointment(Base):
    __tablename__ = "appointments"


    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tracking_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    bale_chat_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    national_id_hash: Mapped[str] = mapped_column(String(64), index=True)
    national_id_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(150))
    phone_encrypted: Mapped[bytes] = mapped_column(LargeBinary)
    appointment_date: Mapped[date] = mapped_column(Date, index=True)
    appointment_time: Mapped[time] = mapped_column(Time)
    # MySQL has no partial unique indexes. This nullable key is unique only while
    # an appointment is active; cancellation clears it and releases the slot.
    active_slot_key: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    photo_path: Mapped[str] = mapped_column(String(500))
    photo_quality_status: Mapped[str] = mapped_column(String(30), default="basic_approved")
    status: Mapped[str] = mapped_column(String(30), default="confirmed", index=True)
    consent_version: Mapped[str] = mapped_column(String(20), default="1.0")
    consented_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    exported: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    holiday_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), default="تعطیل")
