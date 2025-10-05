import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(page_title="Calendar+Tasks", page_icon="📅", layout="wide")

if "theme_inited" not in st.session_state:
    html(
        """
        <script>
        try {
          const k = "streamlitTheme";
          if (window.localStorage.getItem(k)) {
            window.localStorage.removeItem(k);
          }
        } catch (e) {}
        </script>
        """,
        height=0,
    )
    st.session_state["theme_inited"] = True

from msal_auth import maybe_exchange_code_silently
maybe_exchange_code_silently()   

st.title("Plans are worthless, but planning is everything.")

from db import init_db
init_db()
