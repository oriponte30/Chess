"""Training: placeholder. The review already stores everything this needs (core.store.move_facts and the puzzle tags in each verdict)."""
from __future__ import annotations

import streamlit as st

st.markdown("<div class='pagehead'><h1>Training</h1><p>Practice built from your own games. Coming next.</p></div>", unsafe_allow_html=True)
c = st.columns(3, gap="medium")
for col, (icon, head, text) in zip(c, [
    ("📖", "Openings", "Lines you lose or leave book in early, drilled until they stick."),
    ("⚔️", "Tactics", "Puzzles made from your own blunders and missed wins, tagged by theme (forks, hanging pieces, mates)."),
    ("🏁", "Endgames", "The endings you actually reach, with the technique you were missing."),
]):
    col.markdown(f"<div class='soon'><div class='i'>{icon}</div><div class='h'>{head}</div><div class='x'>{text}</div></div>", unsafe_allow_html=True)
