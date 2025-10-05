# =============================
# pages/9_課題編集削除.py
# -----------------------------
import streamlit as st
import datetime as dt
from pathlib import Path
from db import get_task, update_task, delete_task, insert_task_proof

st.title("9) 課題 編集・削除・完了")

# --- rerun 互換関数 ---
def _rerun():
    fn = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
    if fn:
        fn()

# --- id の受け取り：URLクエリ or session_state の両対応 ---
task_id = None

# 1) URL クエリ（対応バージョンのみ）
qid = None
if hasattr(st, "query_params"):
    q = st.query_params.get("id")
    # st.query_params.get は値 or [値] の場合があるので正規化
    if isinstance(q, list):
        q = q[0] if q else None
    qid = q

# 2) session_state フォールバック
if qid is None:
    qid = st.session_state.get("edit_task_id")

# 数値化
if qid is not None:
    try:
        task_id = int(qid)
    except Exception:
        task_id = None

if task_id is None:
    st.info("課題IDが指定されていません。7) 課題一覧 から遷移してください。")
    st.stop()

t = get_task(task_id)
if not t:
    st.error("課題が見つかりません。")
    st.stop()

# 進捗の安全化
prog_init = t.get("progress", 0.0) or 0.0
try:
    prog_init_pct = int(round(float(prog_init) * 100))
except Exception:
    prog_init_pct = 0

# --- 編集・削除フォーム ---
with st.form("task_edit"):
    title = st.text_input("タイトル", t["title"])
    d = st.text_input("締め切り日 (YYYY-MM-DD)", t["due_date"])
    tm = st.text_input("締め切り時間 (HH:MM)", t["due_time"])
    hrs = st.number_input("かかる時間（h）", min_value=0.0, step=0.5, value=float(t["required_hours"]))
    info = st.text_input("情報（リンク）", t.get("info_url", ""))
    prog = st.slider("達成率", 0, 100, prog_init_pct)

    col1, col2, col3 = st.columns(3)
    with col1:
        saved = st.form_submit_button("保存")
    with col2:
        removed = st.form_submit_button("削除")
    with col3:
        done = st.form_submit_button("完了（証拠アップロード）")

if saved:
    update_task(task_id, title, d, tm, float(hrs), info, prog / 100.0)
    st.success("保存しました。")
    _rerun()

if removed:
    delete_task(task_id)
    st.success("削除しました。")
    _rerun()

# --- 完了アップロードモード ---
if done:
    st.session_state["proof_mode"] = True
    # 編集フォームの値も最新で完了時点に合わせたい場合はここで一旦保存してもよい
    # update_task(task_id, title, d, tm, float(hrs), info, prog / 100.0)
    _rerun()

if st.session_state.get("proof_mode"):
    st.subheader("完了の証拠アップロード")
    with st.form("proof_form"):
        up = st.file_uploader("完了の証拠（スクショ等）", type=["png", "jpg", "jpeg", "pdf"])
        c1, c2 = st.columns(2)
        with c1:
            confirm = st.form_submit_button("アップロードして完了にする")
        with c2:
            cancel = st.form_submit_button("キャンセル")

    if confirm:
        if up is None:
            st.warning("先にファイルを選択してください。")
        else:
            up_dir = Path("uploads")
            up_dir.mkdir(parents=True, exist_ok=True)
            # 簡易なファイル名安全化
            safe_name = f"task_{task_id}_{Path(up.name).name}"
            save_to = up_dir / safe_name
            with open(save_to, "wb") as f:
                f.write(up.getbuffer())

            insert_task_proof(task_id, str(save_to), dt.datetime.utcnow().isoformat())
            # 進捗を 100% に更新
            update_task(task_id, title, d, tm, float(hrs), info, 1.0)
            st.success("完了として登録しました。")
            # モード解除
            st.session_state.pop("proof_mode", None)
            _rerun()

    if cancel:
        st.session_state.pop("proof_mode", None)
        _rerun()
