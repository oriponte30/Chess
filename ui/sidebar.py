"""The sidebar shared by every page: who you are, how deep to analyse, engine status."""
from __future__ import annotations

import html

import streamlit as st

from core import background, chesscom
from core.engine import find_stockfish
from . import remember
from .state import DEPTHS, depth as current_depth


@st.cache_data(ttl=300, show_spinner=False)
def _fetch(username: str, limit: int) -> list:
    """chess.com answers are kept for five minutes, so pressing the button twice doesn't hit their API twice."""
    return chesscom.recent_games(username, limit=limit)


def load_games():
    """Fetches the typed user's recent games and starts reading them in the background."""
    ss = st.session_state
    ss.error = None
    try:
        with st.spinner("Fetching your games from chess.com…"):
            ss.games = _fetch((ss.user_input or "").strip().lower(), ss.get("n_games", 20))
        ss.username = ss.user_input.strip().lower()
        if ss.get("bg_on", True):
            background.start(ss.username, ss.games, current_depth())
    except chesscom.ChessComError as e:
        ss.games, ss.error = None, str(e)


def forget_me():
    """'Not you?': drop the remembered user from this visit and from the browser."""
    ss = st.session_state
    background.stop(ss.get("username", ""))
    ss.update(games=None, username="", user_input="", remembered=False, rev=None, rev_id=None, forget_now=True)


def boot() -> None:
    """Once per visit: if the browser sent a 'remember me' cookie, fill in the sidebar and load the games before anything is drawn."""
    ss = st.session_state
    if ss.get("_boot"):
        return
    ss["_boot"] = True
    prefs = remember.read()
    if not prefs.get("u"):
        return
    ss.user_input, ss.remembered = prefs["u"], True
    if "d" in prefs:
        ss.depth_name = list(DEPTHS)[prefs["d"]]
    if "n" in prefs:
        ss.n_games = prefs["n"]
    load_games()


def _progress_line(user: str) -> str:
    job = background.status(user) if user else None
    if job is None or not job.total:
        return ""
    if job.running:
        return f"🔎 Reading your games… {job.done} of {job.total}"
    return f"✅ All {job.total} games read" if not job.failed else f"✅ {job.total - job.failed} of {job.total} games read"


def render() -> bool:
    """Draws the sidebar; returns True when a Stockfish binary is available."""
    ss = st.session_state
    with st.sidebar:
        st.markdown("<div class='brand'><div class='logo'>♟️</div><div><b>Chess Coach</b><small>Free game review · Stockfish</small></div></div>",
                    unsafe_allow_html=True)
        if ss.get("remembered"):
            who = ss.get("username") or ss.get("user_input") or ""
            st.markdown(f"<div class='welcome'>👋 Welcome back, <b>{html.escape(str(who))}</b></div>", unsafe_allow_html=True)
            st.button("Not you? Forget me", key="forget_btn", on_click=forget_me, width="stretch")
        st.text_input("chess.com username", key="user_input", placeholder="e.g. hikaru")
        st.button("Load my games", on_click=load_games, type="primary", width="stretch", disabled=not (ss.get("user_input") or "").strip())
        st.slider("How many recent games", 5, 40, step=5, key="n_games", help="Insights covers all of them. The coach reads them in the background.")
        line = _progress_line(ss.get("username", ""))
        if line:
            st.caption(line)
        st.checkbox("Remember me on this device", key="remember_me", help="Keeps your username in a cookie, so your games load by themselves next time.")
        st.toggle("Read my games in the background", key="bg_on", help="The engine analyses your recent games while you browse, so Insights is ready before you open a game.")
        st.divider()
        st.radio("Analysis depth", list(DEPTHS), key="depth_name",
                 help="Deeper = more accurate and slower. Standard takes roughly 5-30 seconds per game.")
        sf = find_stockfish()
        st.caption("🟢 Stockfish ready" if sf else "⚠️ Stockfish isn't installed here")
        st.caption("Reviews are saved, so opening a game twice is instant.")
    # the browser cookie follows the checkbox
    if ss.pop("forget_now", False) or not ss.get("remember_me", True):
        remember.sync(forget=True)
    elif ss.get("username"):
        remember.sync(ss.username, ss.get("depth_name", "⚖️ Standard"), ss.get("n_games", 20))
    return bool(sf)
