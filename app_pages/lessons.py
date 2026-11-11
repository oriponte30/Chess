"""Lessons: a gallery of opening lessons. A lesson opens as a browser-side player (ui/assets/lesson.js) with the whole variation tree
inside it, so every step is instant; Stockfish's lines come from the server only when asked for."""
from __future__ import annotations

import streamlit as st

from core import lesson_export, library
from ui import live, views

ss = st.session_state
if "lesson_slug" not in ss:
    ss["lesson_slug"] = None                            # None = the gallery of openings


def open_lesson(slug: str):
    ss.lesson_slug = library.get(slug).slug
    ss.pop("_ls_engine", None)
    ss.pop("_ls_engine_err", None)


def close_lesson():
    ss.lesson_slug = None


@st.cache_data(show_spinner=False, max_entries=16)
def exported(slug: str) -> dict:
    return lesson_export.export(library.get(slug))


@st.fragment
def lesson(slug: str):
    eng = ss.get("_ls_engine")
    err = ss.get("_ls_engine_err", "")
    res = live.run("lesson", f"ls_{slug}", {**exported(slug), "engine": eng, "engine_error": err}, "engine")
    fen = getattr(res, "engine", None)
    if fen and live.valid_fen(fen) and (not eng or eng.get("fen") != fen):
        try:
            ss["_ls_engine"], ss["_ls_engine_err"] = views.engine_reply(str(fen)), ""
        except FileNotFoundError as e:
            ss["_ls_engine_err"] = str(e)
        st.rerun(scope="fragment")


def gallery():
    st.markdown("<div class='pagehead'><h1>Lessons</h1><p>Learn an opening move by move, with explanations, plans and Stockfish on tap. Pick one.</p></div>",
                unsafe_allow_html=True)
    for side, label in (("white", "Openings to play as White"), ("black", "Openings to play as Black")):
        group = [t for t in library.LIBRARY if t.side == side]
        if not group:
            continue
        st.markdown(f"<h4 class='sechead'>{label}</h4>", unsafe_allow_html=True)
        for row in range(0, len(group), 3):
            cols = st.columns(3, gap="medium")
            for col, t in zip(cols, group[row:row + 3]):
                with col:
                    with st.container(key=f"op_{t.slug}"):
                        st.markdown(f"<div class='opc'><div class='i'>{t.icon}</div><div class='h'>{t.title}</div>"
                                    f"<div class='x'>{t.blurb}</div>"
                                    f"<div class='m'><span class='chip'>{'⚪ White' if t.side == 'white' else '⚫ Black'}</span>"
                                    f"<span class='chip'>{t.level}</span><span class='chip'>{len(t.sections)} variations</span>"
                                    f"<span class='chip'>{t.count()} positions</span></div></div>", unsafe_allow_html=True)
                        st.button("Open lesson", key=f"open_{t.slug}", on_click=open_lesson, args=(t.slug,), type="primary", width="stretch")


if ss.lesson_slug is None:
    gallery()
else:
    nav_l, nav_r = st.columns([1, 3], vertical_alignment="center")
    nav_l.button("← All openings", key="lessons_back", on_click=close_lesson)
    if not ss.get("engine_ok", True):
        st.info("Stockfish isn't installed here, so the engine overlay is unavailable. The lesson itself works without it.")
    lesson(ss.lesson_slug)
