"""The sidebar shared by every page: who you are, how deep to analyse, engine status."""
from __future__ import annotations

import streamlit as st

from core import chesscom
from core.engine import find_stockfish
from .state import DEPTHS


@st.cache_data(ttl=300, show_spinner=False)
def _fetch(username: str, limit: int) -> list:
    """chess.com answers are kept for five minutes, so pressing the button twice doesn't hit their API twice."""
    return chesscom.recent_games(username, limit=limit)


def _load_games():
    ss = st.session_state
    ss.error = None
    try:
        with st.spinner("Fetching your games from chess.com…"):
            ss.games = _fetch((ss.user_input or "").strip().lower(), ss.get("n_games", 20))
        ss.username = ss.user_input.strip().lower()
    except chesscom.ChessComError as e:
        ss.games, ss.error = None, str(e)


def render() -> bool:
    """Draws the sidebar; returns True when a Stockfish binary is available."""
    ss = st.session_state
    with st.sidebar:
        st.markdown("<div class='brand'><div class='logo'>♟️</div><div><b>Chess Coach</b><small>Free game review · Stockfish</small></div></div>",
                    unsafe_allow_html=True)
        st.text_input("chess.com username", key="user_input", placeholder="e.g. hikaru")
        st.button("Load my games", on_click=_load_games, type="primary", width="stretch", disabled=not (ss.get("user_input") or "").strip())
        st.slider("How many recent games", 5, 40, 20, 5, key="n_games")
        st.divider()
        st.radio("Analysis depth", list(DEPTHS), index=1, key="depth_name",
                 help="Deeper = more accurate and slower. Standard takes roughly 5-30 seconds per game.")
        sf = find_stockfish()
        st.caption("🟢 Stockfish ready" if sf else "⚠️ Stockfish isn't installed here")
        st.caption("Reviews are saved, so opening a game twice is instant.")
    return bool(sf)
