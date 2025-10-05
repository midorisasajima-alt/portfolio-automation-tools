# pages/40_写真削除.py
import io
from pathlib import Path
from typing import List, Tuple
from PIL import Image, UnidentifiedImageError
import streamlit as st

# db.py から読み込み（提示の定義を前提）
from db import SessionLocal, Person, Photo, DATA_DIR

st.set_page_config(page_title="写真削除", page_icon="🗑", layout="wide")

# ========== ユーティリティ ==========

def resolve_path(rel_or_abs: str) -> Path:
    """Photo.file_path（相対/絶対）を絶対パスに解決。原則 data/ 相対を想定。"""
    p = Path(rel_or_abs)
    return p if p.is_absolute() else (DATA_DIR / p)

def open_image_safe(path: Path) -> Image.Image | None:
    """画像を安全に開く。壊れている場合はNone。"""
    if not path.exists() or not path.is_file():
        return None
    try:
        with path.open("rb") as f:
            img = Image.open(io.BytesIO(f.read()))
            img.load()  # Pillowの遅延読みを確定
        return img
    except (UnidentifiedImageError, OSError):
        return None

def list_person_options(session) -> List[Tuple[str, int]]:
    """セレクトボックス用に (表示名, person.id) を返す。"""
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
    """検索・並べ替え・ページング付きでPhotoを取得。総件数も返す。"""
    query = session.query(Photo)
    if person_id is not None:
        query = query.filter(Photo.person_id == person_id)
    if q:
        # captionの部分一致 + ファイル名の部分一致
        like = f"%{q}%"
        query = query.filter(
            (Photo.caption.ilike(like)) | (Photo.file_path.ilike(like))
        )

    # 並べ替え
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
    """与えられたPhoto.idをDBおよびファイルから削除。戻り値: (成功件数, 失敗件数, メッセージ)"""
    ok = 0
    ng = 0
    msgs: List[str] = []
    for pid in photo_ids:
        photo = session.query(Photo).get(pid)
        if not photo:
            ng += 1
            msgs.append(f"id={pid}: レコードが見つかりません")
            continue
        abs_path = resolve_path(photo.file_path)
        # 先にファイル削除（存在しない場合はスキップ）
        try:
            if abs_path.exists():
                abs_path.unlink()
        except Exception as e:
            # ファイル削除に失敗してもDB側は削除し、メッセージに記録
            msgs.append(f"id={pid}: ファイル削除失敗 ({abs_path}): {e}")

        try:
            session.delete(photo)
            ok += 1
        except Exception as e:
            ng += 1
            msgs.append(f"id={pid}: DB削除失敗: {e}")

    # まとめてコミット
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        # ここでエラーの場合、どのレコードまで反映されたかはDB依存。利用者に注意喚起。
        msgs.append(f"コミット失敗: {e}")
    return ok, ng, msgs

# ========== サイドバー（検索条件） ==========

st.title("🗑 写真削除")

with st.sidebar:
    st.header("検索条件")

    with SessionLocal() as session:
        person_opts = list_person_options(session)

    target_person = st.selectbox(
        "人物で絞り込み（任意）", ["すべて"] + [lbl for (lbl, _) in person_opts], index=0
    )
    person_id = None
    if target_person != "すべて":
        # ラベル→id変換
        idx = [lbl for (lbl, _) in person_opts].index(target_person)
        person_id = person_opts[idx][1]

    q = st.text_input("キーワード（キャプション／ファイル名 部分一致）", "")

    order_key = st.selectbox("並べ替え項目", ["created_at", "id", "file_path"], index=0)
    ascending = st.toggle("昇順", value=False)

    page_size = st.number_input("ページサイズ", min_value=6, max_value=120, value=24, step=6)
    page_num = st.number_input("ページ番号（1開始）", min_value=1, value=1, step=1)
    offset = (page_num - 1) * page_size

# ========== 検索・表示 ==========

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

    st.caption(f"該当: {total} 件（表示: {len(photos)} 件）")

    # 選択状態保持用
    if "delete_selection" not in st.session_state:
        st.session_state.delete_selection = set()

    # グリッド表示
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
                box.info("画像を表示できません")

            box.write(f"id: {ph.id}")
            box.write(f"file: {ph.file_path}")
            if ph.caption:
                box.write(f"cap: {ph.caption}")
            if ph.created_at:
                box.caption(f"created: {ph.created_at}")

            # 単体削除ボタン
            del_one = box.button(f"この写真を削除", key=f"del_one_{ph.id}")
            sel = box.checkbox("一括削除に追加", key=f"sel_{ph.id}", value=False)
            if sel:
                selected_ids_in_page.append(ph.id)
            if del_one:
                ok, ng, msgs = delete_photos_by_ids(session, [ph.id])
                if ok:
                    st.success(f"id={ph.id} を削除しました（DBとファイル）。")
                if ng:
                    st.error(f"id={ph.id} の削除で問題が発生しました。")
                for m in msgs:
                    st.caption(m)
                # ボタン押下後は自動的に再実行されるため、明示rerun不要

    # 一括削除（ページ内選択＋任意のID手入力も可能）
    st.divider()
    st.subheader("一括削除")

    manual_ids = st.text_input("追加のPhoto ID（半角カンマ区切り、任意）", "")
    extra_ids = []
    if manual_ids.strip():
        try:
            extra_ids = [int(s.strip()) for s in manual_ids.split(",") if s.strip()]
        except ValueError:
            st.error("Photo ID の形式が不正です（整数、カンマ区切り）。")

    merged_ids = sorted(set(selected_ids_in_page + extra_ids))

    st.write(f"削除候補: {merged_ids if merged_ids else '（なし）'}")

    colA, colB = st.columns([1, 2])
    with colA:
        confirm = st.checkbox("削除を確認（取り消し不可）", value=False)
    with colB:
        if st.button("選択した写真を一括削除", type="primary", disabled=not (confirm and merged_ids)):
            if not merged_ids:
                st.warning("削除対象が選択されていません。")
            else:
                ok, ng, msgs = delete_photos_by_ids(session, merged_ids)
                if ok:
                    st.success(f"{ok} 件を削除しました。")
                if ng:
                    st.error(f"{ng} 件で問題が発生しました。")
                for m in msgs:
                    st.caption(m)
                # 自動再実行により一覧は更新されます

# ========== 操作上の注意 ==========
st.info(
    "注意: 削除は取り消せません。Photo.file_path は data/ 以下の相対パスを前提にしています。"
    " 画像が壊れている場合はプレビューできませんが、削除は可能です。"
)
