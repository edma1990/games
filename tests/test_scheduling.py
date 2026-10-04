from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.scheduling import all_slots, available_slots


def test_regular_day_slots_start_and_end():
    # Saturday
    slots = all_slots(date(2026, 10, 3))
    assert len(slots) == 20
    assert slots[0] == time(7, 20)
    assert slots[-1] == time(13, 40)


def test_thursday_has_17_slots():
    slots = all_slots(date(2026, 10, 8))
    assert len(slots) == 17
    assert slots[-1] == time(12, 40)


def test_friday_is_closed():
    assert all_slots(date(2026, 10, 9)) == []


def test_available_slots_for_open_day():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        assert len(available_slots(date(2026, 10, 3), db, today=date(2026, 10, 3))) == 20
