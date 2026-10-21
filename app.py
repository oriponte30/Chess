"""Chess Coach: a free game reviewer for chess.com games, powered by Stockfish.

This file is only the shell: page setup, the shared sidebar and the navigation. Each feature is a page in app_pages/ and is registered
in ui/features.py."""
from __future__ import annotations

import streamlit as st

from core import service
from ui import sidebar
from ui.features import FEATURES
from ui.state import init_state
from ui import theme

st.set_page_config(page_title="Chess Coach", page_icon="♟️", layout="wide")
theme.inject()
init_state()
if not st.session_state.get("_warm"):                  # launch Stockfish in the background while the page loads
    st.session_state["_warm"] = True
    service.warm_up()
st.session_state["engine_ok"] = sidebar.render()

pages = [st.Page(f.path, title=f.title, icon=f.icon, url_path=f.url, default=f.default) for f in FEATURES]
st.navigation(pages, position="top").run()
