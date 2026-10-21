"""Which colour scheme is Streamlit showing right now? The CSS adapts to it, so the app is readable on the light theme (the default when
no .streamlit/config.toml is present) and on the dark one."""
from __future__ import annotations

import streamlit as st

from .styles import TOKENS, css


def mode() -> str:
    try:
        t = st.context.theme.type
    except Exception:                                   # noqa: BLE001  (older Streamlit, or no theme info)
        t = None
    return t if t in TOKENS else "dark"


def inject() -> str:
    """Writes the stylesheet for the active theme and returns the mode ('dark' / 'light')."""
    m = mode()
    st.markdown(css(m), unsafe_allow_html=True)
    return m


def tokens() -> dict:
    return TOKENS[mode()]
