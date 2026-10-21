"""The pieces of the review screen."""
from __future__ import annotations

import datetime as dt
from html import escape

import chess
import pandas as pd
import streamlit as st

from core import coach
from core import review as rv
from core.review import COLOR, SYMBOL, GameReview
from .board import board_svg

BAD = ("Inaccuracy", "Mistake", "Blunder", "Missed Win")


def fmt_acc(x) -> str:
    return "–" if x is None else f"{x:.0f}%"


def result_pill(res: str) -> str:
    label = {"win": "Win", "loss": "Loss", "draw": "Draw"}.get(res, "")
    return f"<span class='pill {res}'>{label}</span>" if label else ""


def move_label(m: rv.MoveReview, with_no: bool = True) -> str:
    no = f"{m.move_no}{'.' if m.color else '...'}" if with_no else ""
    return f"{no}{m.san}{SYMBOL.get(m.classification, '') if m.classification not in ('Book', 'Forced') else ''}"


# --------------------------------------------------------------------------------------------------------------------
# header, accuracy, summary
# --------------------------------------------------------------------------------------------------------------------
def game_header(rev: GameReview):
    me = rev.player_color
    res = rev.result
    user_res = ""
    if me is not None and res in ("1-0", "0-1"):
        user_res = "win" if (res == "1-0") == (me == chess.WHITE) else "loss"
    elif res == "1/2-1/2":
        user_res = "draw"
    w = f"{escape(rev.white)} ({rev.white_elo})" if rev.white_elo else escape(rev.white)
    b = f"{escape(rev.black)} ({rev.black_elo})" if rev.black_elo else escape(rev.black)
    bits = [x for x in (rev.date, rev.time_control and f"{rev.time_control}s", rev.termination) if x]
    opening = f"<span class='pill op'>{escape(rev.eco)} · {escape(rev.opening)}</span>" if rev.opening else ""
    link = f"<a href='{escape(rev.url)}' target='_blank' style='color:#8fb4ff'>open on chess.com ↗</a>" if rev.url.startswith("http") else ""
    st.markdown(f"<div class='card gh'><div class='vs'>⚪ {w} <span style='color:#8fa3b5'>vs</span> ⚫ {b}</div>{result_pill(user_res)}{opening}"
                f"<div class='meta'>{' · '.join(escape(x) for x in bits)} {link}</div></div>", unsafe_allow_html=True)


def accuracy_and_counts(rev: GameReview):
    me = rev.player_color
    c1, c2, c3 = st.columns([1, 1, 2])
    for col, color, acc, name, elo in ((c1, chess.WHITE, rev.accuracy_white, rev.white, rev.white_elo),
                                       (c2, chess.BLACK, rev.accuracy_black, rev.black, rev.black_elo)):
        with col:
            st.markdown(f"<div class='card acc {'me' if me == color else ''}'><div class='who'>{'⚪ White' if color else '⚫ Black'}</div>"
                        f"<div class='num'>{fmt_acc(acc)}</div><small>{escape(name)}{f' · {elo}' if elo else ''}</small></div>", unsafe_allow_html=True)
    with c3:
        wc, bc = rev.counts(chess.WHITE), rev.counts(chess.BLACK)
        rows = ""
        for cl in ("Brilliant", "Great", "Best", "Excellent", "Good", "Book", "Inaccuracy", "Mistake", "Blunder", "Missed Win"):
            if cl == "Missed Win" and not (wc[cl] or bc[cl]):
                continue
            rows += (f"<tr><td><span class='dot' style='background:{COLOR[cl]}'></span>{cl}</td>"
                     f"<td class='n'>{wc[cl]}</td><td class='n'>{bc[cl]}</td></tr>")
        st.markdown(f"<div class='card'><table class='mq'><tr><td></td><td class='n' style='color:#8fa3b5'>⚪</td><td class='n' style='color:#8fa3b5'>⚫</td></tr>"
                    f"{rows}</table></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------------------------------------------------
# interactive viewer (board, current move, graph, move list); runs as a fragment so stepping doesn't redraw the page
# --------------------------------------------------------------------------------------------------------------------
def _set_ply(p: int, n: int):
    st.session_state.ply = max(0, min(n, int(p)))


def _jump_key(rev: GameReview, direction: int):
    cur = st.session_state.get("ply", 0)
    ks = sorted(rev.key_moments)
    cands = [k for k in ks if (k > cur if direction > 0 else k < cur)]
    if cands:
        st.session_state.ply = cands[0] if direction > 0 else cands[-1]


def _eval_bar(wp_white: float, flipped: bool) -> str:
    top_is_black = not flipped
    black_h = 100 - wp_white if top_is_black else wp_white
    white_h = 100 - black_h
    first = f"<div class='b' style='height:{black_h:.1f}%'></div>" if top_is_black else f"<div class='w' style='height:{white_h:.1f}%'></div>"
    second = f"<div class='w' style='height:{white_h:.1f}%'></div>" if top_is_black else f"<div class='b' style='height:{black_h:.1f}%'></div>"
    return f"<div class='evalbar' style='align-self:stretch;min-height:300px'>{first}{second}</div>"


def _move_card(rev: GameReview, ply: int, show_best: bool):
    if ply == 0:
        st.markdown(f"<div class='mc' style='border-color:#8fa3b5'><div class='t'>Start of the game</div>"
                    f"<div class='e'>{escape(rev.summary)}</div></div>", unsafe_allow_html=True)
        return
    m = rev.moves[ply - 1]
    col = COLOR[m.classification]
    best = ""
    if m.classification in BAD or (m.classification in ("Good",) and m.loss > 3):
        if m.best_san and m.best_san != m.san:
            best = f"<div class='w'>Engine's choice: <b style='color:#b8e08a'>{escape(m.best_san)}</b> (green arrow)</div>"
    st.markdown(f"<div class='mc' style='border-color:{col}'><div class='t'>{escape(move_label(m))}"
                f"<i style='color:{col}'>{m.classification}</i></div><div class='e'>{escape(m.explanation)}</div>{best}</div>", unsafe_allow_html=True)


def _graph(rev: GameReview, ply: int):
    df = pd.DataFrame(rev.evals)
    keys = pd.DataFrame([{"ply": m.ply, "wp": rev.evals[m.ply]["wp"], "cls": m.classification, "color": COLOR[m.classification],
                          "label": move_label(m)} for m in rev.moves if m.ply in rev.key_moments])
    layers = [
        {"data": {"values": df.to_dict("records")}, "mark": {"type": "area", "interpolate": "monotone", "color": "#d9dee3", "opacity": 0.85},
         "encoding": {"x": {"field": "ply", "type": "quantitative", "axis": {"title": None, "labelColor": "#8fa3b5", "gridColor": "#243241",
                                                                                "labelExpr": "ceil(datum.value / 2)", "tickMinStep": 2}},
                      "y": {"field": "wp", "type": "quantitative", "scale": {"domain": [0, 100]}, "axis": {"title": None, "labelColor": "#8fa3b5", "gridColor": "#243241",
                                                                                                     "values": [0, 50, 100]}},
                      "y2": {"datum": 0}}},
        {"data": {"values": [{"y": 50}]}, "mark": {"type": "rule", "color": "#8fa3b5", "strokeDash": [4, 4]}, "encoding": {"y": {"field": "y", "type": "quantitative"}}},
        {"data": {"values": [{"x": ply}]}, "mark": {"type": "rule", "color": "#f6f669", "strokeWidth": 2}, "encoding": {"x": {"field": "x", "type": "quantitative"}}},
    ]
    if len(keys):
        layers.append({"data": {"values": keys.to_dict("records")}, "mark": {"type": "point", "filled": True, "size": 110, "stroke": "#fff", "strokeWidth": 1.5},
                       "encoding": {"x": {"field": "ply", "type": "quantitative"}, "y": {"field": "wp", "type": "quantitative"},
                                    "color": {"field": "color", "type": "nominal", "scale": None},
                                    "tooltip": [{"field": "label", "title": "Moment"}, {"field": "cls", "title": "Type"}]}})
    st.vega_lite_chart({"background": "transparent", "height": 150, "layer": layers, "config": {"view": {"stroke": None}}}, width="stretch")


@st.fragment
def viewer(rev: GameReview):
    ss = st.session_state
    n = len(rev.moves)
    ply = max(0, min(n, ss.get("ply", 0)))
    ss.ply = ply
    flipped = bool(ss.get("flip", rev.player_color == chess.BLACK))
    left, right = st.columns([1.25, 1], gap="large")
    m = rev.moves[ply - 1] if ply else None
    with left:
        fen = m.fen_after if m else chess.STARTING_FEN
        show_best = bool(ss.get("show_best", True))
        best = m.best_uci if (m and show_best and m.classification in BAD and m.best_uci != m.uci) else None
        badge = (SYMBOL.get(m.classification) or "", COLOR[m.classification]) if m and m.classification not in ("Book", "Forced", "Good") else None
        if badge and not badge[0]:
            badge = None
        wp = rev.evals[ply]["wp"] if rev.evals else 50.0
        svg = board_svg(fen, m.uci if m else None, best, flipped, badge)
        svg = svg.replace('width="520" height="520"', 'style="width:100%;height:auto"')
        st.markdown(f"<div style='display:flex;gap:10px;align-items:stretch'>{_eval_bar(wp, flipped)}"
                    f"<div style='flex:1;max-width:560px'>{svg}</div></div>", unsafe_allow_html=True)
        b1, b2, b3, b4 = st.columns(4)
        b1.button("⏮", key="nav_first", on_click=_set_ply, args=(0, n), width="stretch", help="Start")
        b2.button("◀", key="nav_prev", on_click=_set_ply, args=(ply - 1, n), width="stretch", disabled=ply <= 0, help="Previous move")
        b3.button("▶", key="nav_next", on_click=_set_ply, args=(ply + 1, n), width="stretch", disabled=ply >= n, help="Next move")
        b4.button("⏭", key="nav_last", on_click=_set_ply, args=(n, n), width="stretch", help="End")
        b5, b6 = st.columns(2)
        b5.button("◀ Previous key moment", key="nav_pk", on_click=_jump_key, args=(rev, -1), width="stretch", disabled=not rev.key_moments)
        b6.button("Next key moment ▶", key="nav_nk", on_click=_jump_key, args=(rev, 1), width="stretch", disabled=not rev.key_moments)
        t1, t2 = st.columns(2)
        t1.toggle("Show the best move", value=True, key="show_best")
        t2.toggle("Flip board", value=flipped, key="flip")
    with right:
        _move_card(rev, ply, bool(ss.get("show_best", True)))
        _graph(rev, ply)
        with st.container(height=330, key="movelist"):
            for i in range(0, n, 2):
                c0, c1, c2 = st.columns([0.55, 1.6, 1.6], gap="small")
                c0.markdown(f"<div style='padding-top:5px;color:#8fa3b5;font-weight:700'>{i // 2 + 1}.</div>", unsafe_allow_html=True)
                for j, c in ((i, c1), (i + 1, c2)):
                    if j < n:
                        mm = rev.moves[j]
                        sym = SYMBOL.get(mm.classification, "") if mm.classification not in ("Book", "Forced", "Good") else ""
                        c.button(f"{mm.san} {sym}".strip(), key=f"ml_{j + 1}", on_click=_set_ply, args=(j + 1, n),
                                 type="primary" if ply == j + 1 else "tertiary", width="stretch")


# --------------------------------------------------------------------------------------------------------------------
# key moments and verdict
# --------------------------------------------------------------------------------------------------------------------
def key_moments(rev: GameReview):
    moms = [m for m in rev.moves if m.ply in rev.key_moments]
    if not moms:
        st.markdown("<div class='card'>No big swings in this game: nothing to single out.</div>", unsafe_allow_html=True)
        return
    cols = st.columns(len(moms))
    for col, m in zip(cols, moms):
        with col:
            st.markdown(f"<div class='km' style='border-top:4px solid {COLOR[m.classification]}'><div class='h'>{escape(move_label(m))}</div>"
                        f"<div class='c' style='color:{COLOR[m.classification]}'>{m.classification}</div>"
                        f"<div class='x'>{escape(m.explanation)}</div></div>", unsafe_allow_html=True)
            st.button("Show on board", key=f"km_{m.ply}", on_click=_set_ply, args=(m.ply, len(rev.moves)), width="stretch")


def verdict(rev: GameReview):
    v = rev.verdict or {}
    st.markdown(f"<div class='card'><h4>Overview</h4><div style='font-size:16px;line-height:1.5'>{escape(rev.summary)}</div></div>", unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        items = "".join(f"<li>{escape(x)}</li>" for x in v.get("went_right", []))
        st.markdown(f"<div class='card verdict'><h4>✅ What went right</h4><ul style='margin:0;padding-left:18px'>{items}</ul></div>", unsafe_allow_html=True)
    with c2:
        items = "".join(f"<li>{escape(x)}</li>" for x in v.get("went_wrong", []))
        st.markdown(f"<div class='card verdict'><h4>⚠️ What went wrong</h4><ul style='margin:0;padding-left:18px'>{items}</ul></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(f"<div class='focus'><div style='color:#8fa3b5;font-size:12.5px;font-weight:800;letter-spacing:.6px'>FOCUS FOR YOUR NEXT GAME</div>"
                f"<div class='f'>🎯 {escape(v.get('focus', ''))}</div><div style='margin-top:4px;color:#d5dde6'>{escape(v.get('focus_tip', ''))}</div>"
                f"<span class='tag'>{escape(v.get('puzzle_trigger', ''))}</span> <span class='tag'>{escape(v.get('action_tag', ''))}</span></div>", unsafe_allow_html=True)
    if v.get("trends"):
        st.write("")
        items = "".join(f"<li>{escape(x)}</li>" for x in v["trends"])
        st.markdown(f"<div class='card verdict'><h4>📈 Patterns across your recent games</h4><ul style='margin:0;padding-left:18px'>{items}</ul></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------------------------------------------------
# games list
# --------------------------------------------------------------------------------------------------------------------
def games_list(games: list, reviewed: dict, depth: int):
    """Shows the cards; returns the GameInfo the user clicked, if any."""
    clicked = None
    for g in games:
        when = dt.datetime.fromtimestamp(g.end_time, dt.timezone.utc).strftime("%d %b %Y") if g.end_time else ""
        elo_me = g.white_elo if g.user_color == chess.WHITE else g.black_elo
        elo_op = g.black_elo if g.user_color == chess.WHITE else g.white_elo
        done = reviewed.get(g.game_id) == depth
        with st.container(border=True):
            c1, c2, c3 = st.columns([1.1, 5, 1.8], vertical_alignment="center")
            c1.markdown(result_pill(g.user_result) or "", unsafe_allow_html=True)
            c2.markdown(f"<div class='gm'><div><div class='who'>{'⚪' if g.user_color == chess.WHITE else '⚫'} vs {escape(g.opponent)} "
                        f"<span style='color:#8fa3b5;font-weight:600'>({elo_op or '?'})</span></div>"
                        f"<div class='sub'>{when} · {escape(g.time_class)} {escape(g.time_control)} · your rating {elo_me or '?'}</div></div></div>",
                        unsafe_allow_html=True)
            if c3.button("Open review" if done else "Review", key=f"rv_{g.game_id}", type="secondary" if done else "primary", width="stretch"):
                clicked = g
    return clicked
