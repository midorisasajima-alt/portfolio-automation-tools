# pages/20_候補一覧.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db import get_conn, delete_candidate, get_candidate
from msal_auth import get_access_token
from graph_client import create_event_from_candidate

st.set_page_config(page_title="候補一覧", layout="wide")
st.title("候補一覧")

# --- CSS（先頭で一度だけ追加） ---
st.markdown(
    """
<style>
a.btn-jump {
  display:inline-block; padding:6px 10px; border:1px solid #3b82f6;
  border-radius:6px; text-decoration:none;
  font-size:0.9rem;
}
a.btn-jump:hover { background:#eef5ff; }
</style>
""",
    unsafe_allow_html=True,
)

# --- 内部ページ遷移リンク（?page=...&date=...） ---
from urllib.parse import urlencode

PAGE_NAME = "1_予定"  # 実際のファイル名（例: pages/1_予定.py）の表示名に合わせる
def _mk_jump(datestr: str) -> str:
    qs = urlencode({"page": PAGE_NAME, "date": datestr})
    href = f"?{qs}"  # 先頭にスラッシュを付けない（デプロイのサブパスでも安全）
    return f'<a href="{href}" class="btn-jump" target="_self">予定へ</a>'

# --- 1) フィルタUI ---
today = date.today()
col = st.columns([2, 2, 2, 2, 2])
with col[0]:
    dfrom = st.date_input("開始日", today)
with col[1]:
    dto = st.date_input("終了日", today + timedelta(days=14))
with col[2]:
    q = st.text_input("キーワード", "")
with col[3]:
    sort_key = st.selectbox("並び替えキー", ["date", "start_time", "title"])
with col[4]:
    asc = st.toggle("昇順", value=True)

if dfrom > dto:
    st.error("開始日が終了日を超えています。")
    st.stop()

# --- 2) データ取得（db.pyを変更せず、ページ側から直接SELECT） ---
params = [dfrom.isoformat(), dto.isoformat()]
where = ["date BETWEEN ? AND ?"]
if q.strip():
    where.append("(title LIKE ? OR IFNULL(info_url,'') LIKE ?)")
    like = f"%{q.strip()}%"
    params.extend([like, like])

order = f"ORDER BY {sort_key} {'ASC' if asc else 'DESC'}, id ASC"
sql = f"""
SELECT id, date, title, start_time, end_time, info_url
FROM candidate
WHERE {' AND '.join(where)}
{order}
"""

with get_conn() as conn:
    cur = conn.cursor()
    rows = [dict(r) for r in cur.execute(sql, params).fetchall()]

# --- 3) DataFrame 整形（1回だけ描画） ---
def _mk_link(u: str | None) -> str:
    if not u:
        return ""
    safe = u.replace('"', "%22")
    return f'<a href="{safe}" target="_blank">link</a>'

df = pd.DataFrame(rows)
if df.empty:
    st.info("該当する候補はありません。")
else:
    df["time_span"] = df["start_time"].astype(str) + "–" + df["end_time"].astype(str)
    df["link"] = df["info_url"].apply(_mk_link)

    df_view = df[["id", "date", "time_span", "title", "link"]].rename(
        columns={
            "id": "ID",
            "date": "日付",
            "time_span": "時間",
            "title": "タイトル",
            "link": "情報",
        }
    )
    st.caption(f"件数: {len(df_view)}")

    # 最右列「操作」＝予定ページへジャンプ
    df_view["操作"] = df["date"].apply(_mk_jump)
    df_view = df_view[["ID", "日付", "時間", "タイトル", "情報", "操作"]]

    st.write(df_view.to_html(escape=False, index=False), unsafe_allow_html=True)

# --- 4) 行アクション（単発） ---
st.subheader("行アクション")
aid = st.number_input("対象IDを入力", min_value=0, step=1, value=0)
c1, c2 = st.columns([1, 1])

with c1:
    if st.button("Outlookに追加", use_container_width=True, disabled=(aid <= 0)):
        cand = get_candidate(aid)
        if not cand:
            st.error("対象IDが見つかりません。")
        else:
            try:
                token = get_access_token()
                res = create_event_from_candidate(
                    token,
                    cand["date"],
                    cand["title"],
                    cand["start_time"],
                    cand["end_time"],
                )
                if res:
                    st.success(
                        f"作成完了: {res.get('subject')}（{cand['date']} {cand['start_time']}–{cand['end_time']}）"
                    )
                    st.toast("Outlook作成に成功", icon="✅")
            except Exception as e:
                st.error(f"作成中にエラー: {e}")

with c2:
    if st.button(
        "ゴミ箱へ移動（削除）",
        type="secondary",
        use_container_width=True,
        disabled=(aid <= 0),
    ):
        cnt = delete_candidate(aid)
        if cnt == 1:
            st.success(f"ID {aid} をゴミ箱へ移動しました。")
            st.toast("削除（ゴミ箱）完了", icon="🗑️")
            st.rerun()
        else:
            st.warning("対象IDが見つかりませんでした。")

# --- 5) 複数選択 → 一括操作（任意） ---
st.subheader("一括操作（任意）")
ids_str = st.text_input("カンマ区切りのID（例: 12,13,20）", "")
b1, b2 = st.columns([1, 1])

def _parse_ids(s: str) -> list[int]:
    if not s.strip():
        return []
    out = []
    for t in s.split(","):
        t = t.strip()
        if t.isdigit():
            out.append(int(t))
    return out

with b1:
    if st.button("一括でOutlook作成", disabled=(not ids_str.strip())):
        token = get_access_token()
        ok, ng = 0, 0
        for cid in _parse_ids(ids_str):
            cand = get_candidate(cid)
            if not cand:
                ng += 1
                continue
            try:
                res = create_event_from_candidate(
                    token,
                    cand["date"],
                    cand["title"],
                    cand["start_time"],
                    cand["end_time"],
                )
                ok += 1 if res else 0
            except Exception:
                ng += 1
        st.info(f"作成 成功:{ok} 失敗:{ng}")

with b2:
    if st.button("一括でゴミ箱へ移動", type="secondary", disabled=(not ids_str.strip())):
        ok, ng = 0, 0
        ids = _parse_ids(ids_str)
        for cid in ids:
            ok += delete_candidate(cid)
        ng = len(ids) - ok
        st.info(f"削除 成功:{ok} 失敗:{ng}")
        st.rerun()
