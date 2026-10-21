"""Insights: what the coach sees across all the games you've reviewed (built on core.store and core.insights)."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from core import insights as ins, store
from core.review import COLOR
from ui import theme
from ui.state import username

PHASE_COLORS = {"opening": ("#6c8cff", "#4cc3b0"), "middlegame": ("#7fa650", "#c3d94a"), "endgame": ("#e6a23c", "#ff7b72")}

st.markdown("<div class='pagehead'><h1>Insights</h1><p>What the coach sees across your reviewed games, and what to work on next.</p></div>", unsafe_allow_html=True)
user = username()
if not user:
    st.info("Load your games from the sidebar and review a few, then come back here.")
    st.stop()

rows = store.review_rows(user)
facts_all = pd.DataFrame(store.move_facts(user))
if not rows or facts_all.empty:
    st.info("No reviewed games yet. Review a game and its numbers will show up here.")
    st.stop()
facts_all = facts_all[facts_all["color"] == facts_all["player_color"]]                      # the user's own moves only
facts = facts_all.to_dict("records")
if not facts:
    st.info("None of your reviewed games had a known side, so the coach can't tell which moves were yours. Use your chess.com username.")
    st.stop()

stats = ins.phase_stats(facts)
mistakes = store.mistakes(user)
T = theme.tokens()
accs = [r["accuracy"] for r in rows if r["accuracy"] is not None]
avg = sum(accs) / len(accs) if accs else None
wins = sum(1 for r in rows if (r["result"] == "1-0" and r["player_color"] == 1) or (r["result"] == "0-1" and r["player_color"] == 0))
bad_moves = sum(s["bad"] for s in stats.values())
total_moves = sum(s["n"] for s in stats.values())

# ---- headline numbers ---------------------------------------------------------------------------------------------------
st.markdown(
    "<div class='glass'><div class='kpi'>"
    f"<div class='k'><small>Games reviewed</small><b>{len(rows)}</b><span>{wins} won</span></div>"
    f"<div class='k'><small>Average accuracy</small><b class='grad-text'>{'–' if avg is None else f'{avg:.0f}%'}</b><span>across your games</span></div>"
    f"<div class='k'><small>Serious mistakes</small><b>{bad_moves}</b><span>{(bad_moves / total_moves * 100 if total_moves else 0):.1f}% of your moves</span></div>"
    f"<div class='k'><small>Moves analysed</small><b>{total_moves}</b><span>your side only</span></div>"
    "</div></div>", unsafe_allow_html=True)
st.write("")

# ---- coach notes + focus areas ------------------------------------------------------------------------------------------
left, right = st.columns([1.25, 1], gap="large")
with left:
    notes = ins.coach_notes(stats, mistakes, rows)
    body = "".join(f"<div class='note'><div class='ic'>{n['icon']}</div><div><div class='t'>{escape(n['title'])}</div><div class='d'>{escape(n['text'])}</div></div></div>"
                   for n in notes) or "<div class='note'><div class='ic'>✅</div><div><div class='t'>Nothing stands out yet</div><div class='d'>Review a few more games and the coach will start spotting patterns.</div></div></div>"
    st.markdown(f"<div class='glass'><h4 style='margin:0 0 12px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)!important'>Coach notes</h4>{body}</div>", unsafe_allow_html=True)
with right:
    areas = ins.focus_areas(mistakes)
    if areas:
        items = "".join(f"<div class='note'><div class='ic'>🎯</div><div><div class='t'>Focus on: {escape(a['theme'])}</div>"
                        f"<div class='d'>{a['count']} mistake{'s' if a['count'] != 1 else ''} · about {a['cost']} win-% lost. {escape(a['tip'])}</div></div></div>" for a in areas)
    else:
        items = "<div class='note'><div class='ic'>🌟</div><div><div class='t'>No recurring weakness</div><div class='d'>No serious mistakes in your recent games.</div></div></div>"
    st.markdown(f"<div class='glass'><h4 style='margin:0 0 12px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)!important'>Your focus areas</h4>{items}</div>", unsafe_allow_html=True)
st.write("")

# ---- accuracy by phase (always all three) and move quality --------------------------------------------------------------
c1, c2 = st.columns(2, gap="large")
with c1:
    bars = ""
    for ph in ins.PHASES:
        s = stats[ph]
        a, b = PHASE_COLORS[ph]
        if s["acc"] is None:
            bars += f"<div class='phasebar empty'><div class='n'>{ph.title()}</div><div class='tr'></div><div class='v'>no data yet</div></div>"
        else:
            bars += (f"<div class='phasebar' style='--c1:{a};--c2:{b}'><div class='n'>{ph.title()}</div><div class='tr'><div class='fl' style='width:{s['acc']:.0f}%'></div></div>"
                     f"<div class='v'>{s['acc']:.0f}%</div></div><div class='soft' style='margin:-6px 0 0 108px;font-size:12.5px'>{s['n']} moves · {s['bad']} serious mistake{'s' if s['bad'] != 1 else ''}</div>")
    st.markdown(f"<div class='glass'><h4 style='margin:0 0 6px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)!important'>Average move accuracy by phase</h4>{bars}</div>", unsafe_allow_html=True)
with c2:
    q = ins.quality_counts(facts)
    mx = max((n for _, n in q), default=1)
    rows_html = "".join(
        f"<div class='phasebar' style='--c1:{COLOR[k]};--c2:{COLOR[k]}'><div class='n'>{k}</div><div class='tr'><div class='fl' style='width:{n / mx * 100:.0f}%'></div></div><div class='v'>{n}</div></div>"
        for k, n in q)
    st.markdown(f"<div class='glass'><h4 style='margin:0 0 6px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)!important'>Move quality</h4>{rows_html}</div>", unsafe_allow_html=True)
st.write("")

# ---- accuracy trend -------------------------------------------------------------------------------------------------------
trend = ins.accuracy_trend(rows)
if len(trend) >= 2:
    df = pd.DataFrame(trend, columns=["game", "accuracy"])
    st.markdown("<div class='glass' style='padding-bottom:6px'><h4 style='margin:0 0 6px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)!important'>Accuracy, game by game</h4></div>", unsafe_allow_html=True)
    grad = {"gradient": "linear", "x1": 1, "y1": 1, "x2": 1, "y2": 0, "stops": [{"offset": 0, "color": "rgba(76,195,176,0)"}, {"offset": 1, "color": "rgba(108,140,255,.45)"}]}
    st.vega_lite_chart({
        "background": "transparent", "height": 190, "data": {"values": df.to_dict("records")},
        "layer": [{"mark": {"type": "area", "interpolate": "monotone", "color": grad}, "encoding": {"x": {"field": "game", "type": "quantitative", "axis": {"title": None, "tickMinStep": 1, "labelColor": T["muted"], "gridColor": T["line"]}},
                                                                                                    "y": {"field": "accuracy", "type": "quantitative", "scale": {"domain": [0, 100]}, "axis": {"title": None, "labelColor": T["muted"], "gridColor": T["line"]}}}},
                  {"mark": {"type": "line", "interpolate": "monotone", "strokeWidth": 3, "color": "#6c8cff", "point": {"filled": True, "size": 70, "color": "#4cc3b0"}},
                   "encoding": {"x": {"field": "game", "type": "quantitative"}, "y": {"field": "accuracy", "type": "quantitative"}, "tooltip": [{"field": "game"}, {"field": "accuracy"}]}}],
        "config": {"view": {"stroke": None}}}, width="stretch")
