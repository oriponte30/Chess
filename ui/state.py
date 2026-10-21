"""Shared session state and settings. Every page reads the same values from here, so a new page needs no plumbing of its own."""
from __future__ import annotations

import streamlit as st

DEPTHS = {"⚡ Quick": 12, "⚖️ Standard": 14, "🔬 Deep": 18}
DEFAULTS = {"games": None, "username": "", "rev": None, "rev_id": None, "ply": 0, "error": None}


def init_state() -> None:
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


def depth() -> int:
    """The analysis depth picked in the sidebar."""
    return DEPTHS.get(st.session_state.get("depth_name", "⚖️ Standard"), 14)


def username() -> str:
    """The chess.com user whose games are loaded ('' when none)."""
    return st.session_state.get("username", "")
