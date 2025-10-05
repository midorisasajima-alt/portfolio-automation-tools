from pathlib import Path
from datetime import datetime
from sqlalchemy import (create_engine, Column, Integer, String, Text, Date, DateTime, ForeignKey, Index)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATA_DIR = Path("data")
PHOTOS_DIR = DATA_DIR / "photos"
DATA_DIR.mkdir(exist_ok=True, parents=True)
PHOTOS_DIR.mkdir(exist_ok=True, parents=True)

engine = create_engine("sqlite:///data/contacts.sqlite3", future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    instagram = Column(String(200))
    whatsapp = Column(String(200))
    linkedin = Column(String(300))
    country = Column(String(120), index=True)
    region = Column(String(200))
    work_history = Column(Text)
    birthday = Column(Date)
    residence = Column(String(300))
    notes = Column(Text)
    photo_album = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    photos = relationship("Photo", back_populates="person", cascade="all, delete-orphan")

Index("idx_persons_name_country", Person.name, Person.country)

class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), index=True, nullable=False)
    file_path = Column(String(500), nullable=False)  # relative path under data/
    caption = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="photos")

def init_db():
    Base.metadata.create_all(bind=engine)

# =============================
# db.py（追加・分割版）
# =============================
from pathlib import Path
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Date, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# 既存と同一の設定を前提
DATA_DIR = Path("data")
PHOTOS_DIR = DATA_DIR / "photos"
DATA_DIR.mkdir(exist_ok=True, parents=True)
PHOTOS_DIR.mkdir(exist_ok=True, parents=True)

engine = create_engine("sqlite:///data/contacts.sqlite3", future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    instagram = Column(String(200))
    whatsapp = Column(String(200))
    linkedin = Column(String(300))
    country = Column(String(120), index=True)
    region = Column(String(200))
    work_history = Column(Text)
    birthday = Column(Date)
    residence = Column(String(300))
    notes = Column(Text)
    photo_album = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    photos = relationship("Photo", back_populates="person", cascade="all, delete-orphan")

Index("idx_persons_name_country", Person.name, Person.country)

class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.id", ondelete="CASCADE"), index=True, nullable=False)
    file_path = Column(String(500), nullable=False)
    caption = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    person = relationship("Person", back_populates="photos")


def init_db():
    Base.metadata.create_all(bind=engine)

# ---- 誕生日ユーティリティ ----

def _is_leap_year(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def _birthday_matches_on(bday: date | None, on_date: date, celebrate_feb29_on_feb28: bool = True) -> bool:
    if bday is None:
        return False
    if bday.month == 2 and bday.day == 29 and not _is_leap_year(on_date.year):
        return celebrate_feb29_on_feb28 and (on_date.month == 2 and on_date.day == 28)
    return bday.month == on_date.month and bday.day == on_date.day


def _calc_age_on(bday: date, on_date: date) -> int:
    years = on_date.year - bday.year
    has_had_birthday = (on_date.month, on_date.day) >= (bday.month, bday.day)
    return years if has_had_birthday else years - 1


# ---- 公開関数（ページから呼び出し） ----

def list_birthdays_on(session, on_date: date, celebrate_feb29_on_feb28: bool = True) -> List[Dict]:
    rows: List[Dict] = []
    people = session.query(Person).filter(Person.birthday.isnot(None)).all()
    for p in people:
        if _birthday_matches_on(p.birthday, on_date, celebrate_feb29_on_feb28):
            rows.append({
                "id": p.id,
                "name": p.name,
                "age": _calc_age_on(p.birthday, on_date),
                "birthday": p.birthday.isoformat(),
            })
    rows.sort(key=lambda x: (x["name"], x["id"]))
    return rows


def list_birthdays_today_and_tomorrow(tz: str = "Europe/London") -> Dict[str, List[Dict]]:
    zone = ZoneInfo(tz)
    today = datetime.now(zone).date()
    tomorrow = today + timedelta(days=1)
    with SessionLocal() as session:
        return {
            "today": list_birthdays_on(session, today),
            "tomorrow": list_birthdays_on(session, tomorrow),
        }



