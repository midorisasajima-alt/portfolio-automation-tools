import os
import streamlit as st
import msal

TENANT = st.secrets.get("AZURE_TENANT_ID", os.environ.get("AZURE_TENANT_ID", "common"))
AUTHORITY = f"https://login.microsoftonline.com/{TENANT}"
CLIENT_ID = st.secrets.get("AZURE_CLIENT_ID", os.environ.get("AZURE_CLIENT_ID", ""))
CLIENT_SECRET = st.secrets.get("AZURE_CLIENT_SECRET", os.environ.get("AZURE_CLIENT_SECRET", ""))
REDIRECT_URI = st.secrets.get("REDIRECT_URI", os.environ.get("REDIRECT_URI", "http://localhost:8501/"))
SCOPES = ["User.Read", "Calendars.ReadWrite"]

def _app():
    return msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET or None
    )

def get_access_token():
    import streamlit as st
    import msal

    if "token" in st.session_state and st.session_state["token"].get("access_token"):
        return st.session_state["token"]["access_token"]

    # --- クエリ取得（新旧API両対応）---
    code = None
    try:
        qp = st.query_params            # 新
        code = qp.get("code")
        if isinstance(code, list):
            code = code[0]
    except Exception:
        qp = st.experimental_get_query_params()  # 旧
        code = qp.get("code", [None])[0] if qp else None

    cca = _app()
    if not code:
        auth_url = cca.get_authorization_request_url(
            scopes=["User.Read", "Calendars.ReadWrite"],
            redirect_uri=REDIRECT_URI,
            prompt="select_account"
        )
        st.link_button("Sign in with Microsoft", auth_url)
        st.stop()

    result = cca.acquire_token_by_authorization_code(
        code=code,
        scopes=["User.Read", "Calendars.ReadWrite"],
        redirect_uri=REDIRECT_URI
    )
    if "access_token" not in result:
        st.error(f"Auth error: {result.get('error_description') or result}")
        st.stop()

    st.session_state["token"] = result

    # --- URL から ?code を消してリロード ---
    try:
        st.query_params.clear()                 # 新
    except Exception:
        st.experimental_set_query_params()      # 旧（空にする）
    st.rerun()

# msal_auth.py に追記
def maybe_exchange_code_silently():
    # 既にトークンがあれば何もしない
    if "token" in st.session_state and st.session_state["token"].get("access_token"):
        return

    # クエリから code を拾う（新旧API両対応）
    try:
        qp = st.query_params
        code = qp.get("code")
        if isinstance(code, list):
            code = code[0]
    except Exception:
        qp = st.experimental_get_query_params()
        code = (qp.get("code", [None]) or [None])[0]

    if not code:
        return  # 何もせず帰る（プロンプトは出さない）

    cca = _app()
    result = cca.acquire_token_by_authorization_code(
        code=code,
        scopes=["User.Read", "Calendars.ReadWrite"],
        redirect_uri=REDIRECT_URI
    )
    if "access_token" not in result:
        st.error(f"Auth error: {result.get('error_description') or result}")
        st.stop()

    st.session_state["token"] = result

    # URL から ?code を除去してリロード（多重交換防止）
    try:
        st.query_params.clear()
    except Exception:
        st.experimental_set_query_params()
    st.rerun()
