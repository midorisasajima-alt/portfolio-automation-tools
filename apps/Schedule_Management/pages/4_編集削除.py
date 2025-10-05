import streamlit as st
from db import get_candidate, update_candidate, delete_candidate

st.title("4) 候補 編集・削除")

# ── IDを取得（セッション → クエリの順でフォールバック） ──
def _get_cid() -> int | None:
    cid = st.session_state.get("edit_id")
    if cid is not None:
        try:
            return int(cid)
        except Exception:
            return None
    # クエリ文字列（新API→旧API）
    try:
        v = st.query_params.get("id")
        if isinstance(v, list):
            v = v[0]
    except Exception:
        qp = st.experimental_get_query_params()
        v = (qp.get("id", [None]) or [None])[0]
    try:
        return int(v) if v is not None else None
    except Exception:
        return None

cid = _get_cid()
if cid is None:
    st.warning("候補IDがありません。2) 候補ページから遷移してください。")
    st.stop()

# ── レコード取得 ──
c = get_candidate(cid)
if not c:
    st.error(f"候補が見つかりません（id={cid}）。")
    st.stop()

# ── 編集フォーム ──
with st.form("cand_edit"):
    title = st.text_input("タイトル", c.get("title", ""))
    date_s = st.text_input("日付 (YYYY-MM-DD)", c.get("date", ""))
    start = st.text_input("開始時間 (HH:MM)", c.get("start_time", ""))
    end   = st.text_input("終了時間 (HH:MM)", c.get("end_time", ""))
    info  = st.text_input("情報（リンク）", c.get("info_url", ""))

    col1, col2 = st.columns(2)
    saved   = col1.form_submit_button("保存")
    removed = col2.form_submit_button("削除")

if saved:
    update_candidate(cid, date_s, title, start, end, info)
    st.success("保存しました。")

if removed:
    delete_candidate(cid)
    st.success("削除しました。")
    # セッションに残っている参照をクリア（戻り動線用）
    st.session_state.pop("edit_id", None)
