# ==========================================================
# pages/40_delete_photos.py
# ==========================================================
import io
from pathlib import Path
from typing import List, Tuple
from PIL import Image, UnidentifiedImageError
import streamlit as st

# Load from db.py (assumes provided definitions)
from db import SessionLocal, Person, Photo, DATA_DIR

st.set_page_config(page_title="Delete Photos", page_icon="🗑", layout="wide")

# ========== Utilities ==========

def resolve_path(rel_or_abs: str) -> Path:
    """Resolve Photo.file_path (relative/absolute) to an absolute path. Assumes relative to data/ by default."""
    p = Path(rel_or_abs)
    return p if p.is_absolute() else (DATA_DIR / p)

def open_image_safe(path: Path) -> Image.Image | None:
    """Safely open an image. Return None if corrupted/unreadable."""
    if not path.exists() or not path.is_file():
        return None
    try:
        with path.open("rb") as f:
            img = Image.open(io.BytesIO(f.read()))
            img.load()  # finalize Pillow's lazy loading
        return img
    except (UnidentifiedImageError, OSError):
        return None

def list_person_options(session) -> List[Tuple[str, int]]:
    """Return (label, person.id) tuples for selectbox options."""
    people = (
        session.query(Person)
        .order_by(Person.name.asc(), Person.id.asc())
        .all()
    )
    return [(f"{p.name} (id={p.id})", p.id) for p in people]

def fetch_photos(
    session,
    person_id: int | None,
    q: str,
    order_key: str,
    ascending: bool,
    offset: int,
    limit: int,
) -> Tuple[List[Photo], int]:
    """Fetch Photo records with search/sort/pagination. Returns (rows, total_count)."""
    query = session.query(Photo)
    if person_id is not None:
        query = query.filter(Photo.person_id == person_id)
    if q:
        # Partial match on caption and filename
        like = f"%{q}%"
        query = query.filter(
            (Photo.caption.ilike(like)) | (Photo.file_path.ilike(like))
        )

    # Sorting
    order_col = {
        "created_at": Photo.created_at,
        "id": Photo.id,
        "file_path": Photo.file_path,
    }.get(order_key, Photo.created_at)
    if ascending:
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())

    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    return rows, total

def delete_photos_by_ids(session, photo_ids: List[int]) -> Tuple[int, int, List[str]]:
    """Delete given Photo.id records from DB and filesystem. Returns (ok_count, error_count, messages)."""
    ok = 0
    ng = 0
    msgs: List[str] = []
    for pid in photo_ids:
        photo = session.query(Photo).get(pid)
        if not photo:
            ng += 1
            msgs.append(f"id={pid}: record not found")
            continue
        abs_path = resolve_path(photo.file_path)
        # Delete file first (skip if missing)
        try:
            if abs_path.exists():
                abs_path.unlink()
        except Exception as e:
            # Even if file deletion fails, delete DB record; record message.
            msgs.append(f"id={pid}: file deletion failed ({abs_path}): {e}")

        try:
            session.delete(photo)
            ok += 1
        except Exception as e:
            ng += 1
            msgs.append(f"id={pid}: DB deletion failed: {e}")

    # Commit as a batch
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        # On error here, which records committed is DB-dependent; notify user.
        msgs.append(f"Commit failed: {e}")
    return ok, ng, msgs

# ========== Sidebar (Search Criteria) ==========

st.title("🗑 Delete Photos")

with st.sidebar:
    st.header("Search Criteria")

    with SessionLocal() as session:
        person_opts = list_person_options(session)

    target_person = st.selectbox(
        "Filter by person (optional)", ["All"] + [lbl for (lbl, _) in person_opts], index=0
    )
    person_id = None
    if target_person != "All":
        # Map label → id
        idx = [lbl for (lbl, _) in person_opts].index(target_person)
        person_id = person_opts[idx][1]

    q = st.text_input("Keyword (partial match in caption/filename)", "")

    order_key = st.selectbox("Sort by", ["created_at", "id", "file_path"], index=0)
    ascending = st.toggle("Ascending", value=False)

    page_size = st.number_input("Page size", min_value=6, max_value=120, value=24, step=6)
    page_num = st.number_input("Page number (starts at 1)", min_value=1, value=1, step=1)
    offset = (page_num - 1) * page_size

# ========== Search & Display ==========

with SessionLocal() as session:
    photos, total = fetch_photos(
        session=session,
        person_id=person_id,
        q=q,
        order_key=order_key,
        ascending=ascending,
        offset=offset,
        limit=page_size,
    )

    st.caption(f"Matches: {total} (showing: {len(photos)})")

    # Keep selection state
    if "delete_selection" not in st.session_state:
        st.session_state.delete_selection = set()

    # Grid
    cols_per_row = 4
    rows = (len(photos) + cols_per_row - 1) // cols_per_row
    selected_ids_in_page: List[int] = []

    for r in range(rows):
        cols = st.columns(cols_per_row)
        for c in range(cols_per_row):
            i = r * cols_per_row + c
            if i >= len(photos):
                continue
            ph = photos[i]
            box = cols[c].container(border=True)
            abs_path = resolve_path(ph.file_path)
            img = open_image_safe(abs_path)
            if img is not None:
                box.image(img, use_column_width=True)
            else:
                box.info("Unable to display image")

            box.write(f"id: {ph.id}")
            box.write(f"file: {ph.file_path}")
            if ph.caption:
                box.write(f"cap: {ph.caption}")
            if ph.created_at:
                box.caption(f"created: {ph.created_at}")

            # Delete single item
            del_one = box.button("Delete this photo", key=f"del_one_{ph.id}")
            sel = box.checkbox("Add to bulk delete", key=f"sel_{ph.id}", value=False)
            if sel:
                selected_ids_in_page.append(ph.id)
            if del_one:
                ok, ng, msgs = delete_photos_by_ids(session, [ph.id])
                if ok:
                    st.success(f"Deleted id={ph.id} (DB and file).")
                if ng:
                    st.error(f"An issue occurred while deleting id={ph.id}.")
                for m in msgs:
                    st.caption(m)
                # App will auto-rerun after button press; no explicit rerun needed

    # Bulk delete (selection in this page + optional manual IDs)
    st.divider()
    st.subheader("Bulk Delete")

    manual_ids = st.text_input("Additional Photo IDs (comma-separated, optional)", "")
    extra_ids = []
    if manual_ids.strip():
        try:
            extra_ids = [int(s.strip()) for s in manual_ids.split(",") if s.strip()]
        except ValueError:
            st.error("Invalid Photo ID format (integers, comma-separated).")

    merged_ids = sorted(set(selected_ids_in_page + extra_ids))

    st.write(f"Candidates: {merged_ids if merged_ids else '(none)'}")

    colA, colB = st.columns([1, 2])
    with colA:
        confirm = st.checkbox("Confirm deletion (irreversible)", value=False)
    with colB:
        if st.button("Delete selected photos", type="primary", disabled=not (confirm and merged_ids)):
            if not merged_ids:
                st.warning("No deletion targets selected.")
            else:
                ok, ng, msgs = delete_photos_by_ids(session, merged_ids)
                if ok:
                    st.success(f"Deleted {ok} item(s).")
                if ng:
                    st.error(f"Issues occurred for {ng} item(s).")
                for m in msgs:
                    st.caption(m)
                # The list will refresh due to auto-rerun

# ========== Operational Notes ==========
st.info(
    "Note: Deletions cannot be undone. Photo.file_path is assumed to be a path relative to data/. "
    "If an image is corrupted, it may not preview but can still be deleted."
)
