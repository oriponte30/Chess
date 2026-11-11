"""Shared session state and settings. Every page reads the same values from here, so a new page needs no plumbing of its own."""
from __future__ import annotations

import streamlit as st

DEPTHS = {"⚡ Quick": 12, "⚖️ Standard": 14, "🔬 Deep": 18}
DEFAULTS = {"games": None, "username": "", "rev": None, "rev_id": None, "ply": 0, "error": None,
            "depth_name": "⚖️ Standard", "n_games": 20, "remember_me": True, "bg_on": True, "remembered": False}


def init_state() -> None:
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


def depth() -> int:
    """The analysis depth picked in the sidebar."""
    return DEPTHS.get(st.session_state.get("depth_name", "⚖️ Standard"), 14)


def username() -> str:
    """The chess.com user whose games are loaded ('' when none)."""
    return st.session_state.get("username", "")


def game_ids() -> set | None:
    """The ids of the games currently loaded from chess.com (None when no games are loaded): the window the Insights page looks at."""
    games = st.session_state.get("games")
    return {g.game_id for g in games} if games else None
