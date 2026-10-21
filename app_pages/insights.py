"""Insights: a first look across all reviewed games, built on core.store.move_facts. This is the seed of the analytics layer."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import store
from ui.state import username

st.markdown("<div class='pagehead'><h1>Insights</h1><p>Patterns across the games you've reviewed.</p></div>", unsafe_allow_html=True)
user = username()
if not user:
    st.info("Load your games from the sidebar and review a few, then come back here.")
    st.stop()
facts = pd.DataFrame(store.move_facts(user))
if facts.empty:
    st.info("No reviewed games yet. Review a game and its numbers will show up here.")
    st.stop()
facts = facts[facts["color"] == facts["player_color"]]                      # the user's own moves only
if facts.empty:
    st.info("No reviewed games where the coach knew which side you played.")
    st.stop()
st.caption(f"{facts['game_id'].nunique()} reviewed games · {len(facts)} moves")
by_phase = facts.groupby("phase")["accuracy"].mean().reindex(["opening", "middlegame", "endgame"]).dropna().round(1)
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("##### Average move accuracy by phase")
    st.bar_chart(by_phase)
with c2:
    st.markdown("##### Move quality")
    st.bar_chart(facts["classification"].value_counts())
