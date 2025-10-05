import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from db import SessionLocal, Person, Photo, PHOTOS_DIR

def get_session() -> Session:
    return SessionLocal()

def upsert_person(sess: Session, **kwargs) -> Person:
    pid = kwargs.pop("id", None)
    if pid:
        p = sess.get(Person, pid)
        if not p:
            raise ValueError("person not found")
        for k, v in kwargs.items():
            setattr(p, k, v)
    else:
        p = Person(**kwargs)
        sess.add(p)
    sess.commit()
    sess.refresh(p)
    return p

def delete_person(sess: Session, person_id: int) -> None:
    p = sess.get(Person, person_id)
    if p:
        sess.delete(p)
        sess.commit()

def search_persons(sess: Session, name_q: str = "", country_q: str = "") -> List[Person]:
    q = sess.query(Person)
    if name_q:
        like = f"%{name_q.strip()}%"
        q = q.filter(Person.name.like(like))
    if country_q:
        likec = f"%{country_q.strip()}%"
        q = q.filter(Person.country.like(likec))
    return q.order_by(Person.name.asc()).limit(200).all()

def save_photo_bytes(person_id: int, filename: str, data: bytes) -> Path:
    person_dir = PHOTOS_DIR / str(person_id)
    person_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(filename).stem
    ext = Path(filename).suffix.lower() or ".bin"
    unique = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    out = person_dir / f"{stem}-{unique}{ext}"
    out.write_bytes(data)
    return out

def add_photo(sess: Session, person_id: int, file_path: Path, caption: Optional[str]) -> Photo:
    rel_path = file_path.as_posix()
    rel_path = str(Path("data") / Path(rel_path).relative_to(Path("data")))
    ph = Photo(person_id=person_id, file_path=rel_path, caption=caption or "")
    sess.add(ph)
    sess.commit()
    sess.refresh(ph)
    return ph
