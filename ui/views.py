"""The pieces of the review screen."""
from __future__ import annotations

import datetime as dt
import math
from html import escape

import chess
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core import coach
from core import review as rv
from core.review import COLOR, SYMBOL, GameReview
from . import theme
from .board import board_svg
from .chessboard import board_component
from . import live
from .enginelines import arrows as engine_arrows, panel_html, top_lines

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
    link = f"<a href='{escape(rev.url)}' target='_blank'>open on chess.com ↗</a>" if rev.url.startswith("http") else ""
    st.markdown(f"<div class='card gh'><div class='vs'>⚪ {w} <span class='soft'>vs</span> ⚫ {b}</div>{result_pill(user_res)}{opening}"
                f"<div class='meta'>{' · '.join(escape(x) for x in bits)} {link}</div></div>", unsafe_allow_html=True)


def _ring(pct) -> str:
    """A circular accuracy gauge (SVG)."""
    if pct is None:
        return "<div class='ring'><div class='v'>–</div></div>"
    col = "#7fa650" if pct >= 85 else "#c3c94a" if pct >= 70 else "#e6a23c" if pct >= 55 else "#e5645a"
    r = 32
    c = 2 * math.pi * r
    return (f"<div class='ring'><svg viewBox='0 0 78 78'><circle cx='39' cy='39' r='{r}' fill='none' style='stroke:var(--ring_bg)' stroke-width='7'/>"
            f"<circle cx='39' cy='39' r='{r}' fill='none' stroke='{col}' stroke-width='7' stroke-linecap='round' "
            f"stroke-dasharray='{c:.1f}' stroke-dashoffset='{c * (1 - max(0, min(100, pct)) / 100):.1f}'/></svg>"
            f"<div class='v'>{pct:.0f}</div></div>")


def accuracy_and_counts(rev: GameReview):
    me = rev.player_color
    c1, c2, c3 = st.columns([1, 1, 1.6])
    for col, color, acc, name, elo in ((c1, chess.WHITE, rev.accuracy_white, rev.white, rev.white_elo),
                                       (c2, chess.BLACK, rev.accuracy_black, rev.black, rev.black_elo)):
        with col:
            st.markdown(f"<div class='card acc {'me' if me == color else ''}'>{_ring(acc)}<div><div class='who'>{'⚪ White' if color else '⚫ Black'} accuracy</div>"
                        f"<div class='nm'>{escape(name)}</div><div class='sub'>{f'{elo} rating' if elo else ''}{' · you' if me == color else ''}</div></div></div>",
                        unsafe_allow_html=True)
    with c3:
        wc, bc = rev.counts(chess.WHITE), rev.counts(chess.BLACK)
        rows = ""
        for cl in ("Brilliant", "Great", "Best", "Excellent", "Good", "Book", "Inaccuracy", "Mistake", "Blunder", "Missed Win"):
            if cl == "Missed Win" and not (wc[cl] or bc[cl]):
                continue
            rows += (f"<tr><td><span class='dot' style='background:{COLOR[cl]}'></span>{cl}</td>"
                     f"<td class='n'>{wc[cl]}</td><td class='n'>{bc[cl]}</td></tr>")
        st.markdown(f"<div class='card'><table class='mq'><tr><td></td><td class='n soft'>⚪</td><td class='n soft'>⚫</td></tr>"
                    f"{rows}</table></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------------------------------------------------
# interactive viewer (board, current move, graph, move list); runs as a fragment so stepping doesn't redraw the page
# --------------------------------------------------------------------------------------------------------------------
def _set_ply(p: int, n: int):
    st.session_state.ply = max(0, min(n, int(p)))
    st.session_state.explore = []                        # stepping through the game leaves any side line you were trying


def _explore_back():
    st.session_state.explore = st.session_state.get("explore", [])[:-1]


def _explore_reset():
    st.session_state.explore = []


def _jump_key(rev: GameReview, direction: int):
    cur = st.session_state.get("ply", 0)
    ks = sorted(rev.key_moments)
    cands = [k for k in ks if (k > cur if direction > 0 else k < cur)]
    st.session_state.explore = []
    if cands:
        st.session_state.ply = cands[0] if direction > 0 else cands[-1]


def _pill_label(m: rv.MoveReview) -> str:
    sym = SYMBOL.get(m.classification, "") if m.classification not in ("Book", "Forced", "Good") else ""
    return f"{m.move_no}. {m.san}{sym}" if m.color == chess.WHITE else f"{m.san}{sym}"


def _pick_ply(n: int):
    v = st.session_state.get("ply_pick")
    if v is not None:                                    # clicking the selected move again deselects it: ignore that
        st.session_state.explore = []
        st.session_state.ply = max(0, min(n, int(v)))


def _eval_bar(wp_white: float, flipped: bool) -> str:
    """Vertical bar next to the board. White's share is its win probability and Black's is the rest, whichever way the board faces:
    +2.5 for White fills white from White's side of the board, a Black advantage fills black from Black's side."""
    white_h = max(0.0, min(100.0, wp_white))
    black_h = 100.0 - white_h
    w = f"<div class='w' style='height:{white_h:.1f}%;transform-origin:{'top' if flipped else 'bottom'}'></div>"
    b = f"<div class='b' style='height:{black_h:.1f}%;transform-origin:{'bottom' if flipped else 'top'}'></div>"
    first, second = (w, b) if flipped else (b, w)       # White's side of the board is at the bottom, unless the board is flipped
    return f"<div class='evalbar' title='White {white_h:.0f}% / Black {black_h:.0f}%' style='align-self:stretch;min-height:300px'>{first}{second}</div>"


def _move_card(rev: GameReview, ply: int, show_best: bool):
    if ply == 0:
        st.markdown(f"<div class='mc' style='border-color:var(--muted)'><div class='t'>Start of the game</div>"
                    f"<div class='e'>{escape(rev.summary)}</div></div>", unsafe_allow_html=True)
        return
    m = rev.moves[ply - 1]
    col = COLOR[m.classification]
    best = ""
    if m.classification in BAD or (m.classification in ("Good",) and m.loss > 3):
        if m.best_san and m.best_san != m.san:
            best = f"<div class='w'>Engine's choice: <b>{escape(m.best_san)}</b> (green arrow)</div>"
    st.markdown(f"<div class='mc' style='border-color:{col}'><div class='t'>{escape(move_label(m))}"
                f"<i style='color:{col}'>{m.classification}</i></div><div class='e'>{escape(m.explanation)}</div>{best}</div>", unsafe_allow_html=True)


def _graph(rev: GameReview, ply: int):
    T = theme.tokens()
    df = pd.DataFrame(rev.evals)
    keys = pd.DataFrame([{"ply": m.ply, "wp": rev.evals[m.ply]["wp"], "cls": m.classification, "color": COLOR[m.classification],
                          "label": move_label(m)} for m in rev.moves if m.ply in rev.key_moments])
    layers = [
        {"data": {"values": df.to_dict("records")}, "mark": {"type": "area", "interpolate": "monotone", "color": T["chart_area"], "opacity": 0.85},
         "encoding": {"x": {"field": "ply", "type": "quantitative", "axis": {"title": None, "labelColor": T["muted"], "gridColor": T["line"],
                                                                                "labelExpr": "ceil(datum.value / 2)", "tickMinStep": 2}},
                      "y": {"field": "wp", "type": "quantitative", "scale": {"domain": [0, 100]}, "axis": {"title": None, "labelColor": T["muted"], "gridColor": T["line"],
                                                                                                     "values": [0, 50, 100]}},
                      "y2": {"datum": 0}}},
        {"data": {"values": [{"y": 50}]}, "mark": {"type": "rule", "color": T["muted"], "strokeDash": [4, 4]}, "encoding": {"y": {"field": "y", "type": "quantitative"}}},
        {"data": {"values": [{"x": ply}]}, "mark": {"type": "rule", "color": "#e6b800", "strokeWidth": 2}, "encoding": {"x": {"field": "x", "type": "quantitative"}}},
    ]
    if len(keys):
        layers.append({"data": {"values": keys.to_dict("records")}, "mark": {"type": "point", "filled": True, "size": 110, "stroke": T["text"], "strokeWidth": 1.5},
                       "encoding": {"x": {"field": "ply", "type": "quantitative"}, "y": {"field": "wp", "type": "quantitative"},
                                    "color": {"field": "color", "type": "nominal", "scale": None},
                                    "tooltip": [{"field": "label", "title": "Moment"}, {"field": "cls", "title": "Type"}]}})
    st.vega_lite_chart({"background": "transparent", "height": 150, "layer": layers, "config": {"view": {"stroke": None}}}, width="stretch")


_KEYS_JS = """
<script>
(function () {
  var doc;
  try { doc = window.parent.document; } catch (e) { return; }
  var w = window.parent;
  if (w.__chessKeys) doc.removeEventListener("keydown", w.__chessKeys, true);
  var map = {ArrowLeft: "nav_prev", ArrowRight: "nav_next", Home: "nav_first", End: "nav_last"};
  w.__chessKeys = function (e) {
    var key = map[e.key];
    if (!key || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var t = e.target, tag = t && t.tagName ? t.tagName.toLowerCase() : "";
    if (tag === "input" || tag === "textarea" || tag === "select" || (t && t.isContentEditable)) return;
    var btn = doc.querySelector(".st-key-" + key + " button");
    if (!btn) return;
    e.preventDefault();
    if (!btn.disabled) btn.click();
  };
  doc.addEventListener("keydown", w.__chessKeys, true);
})();
</script>
"""


def keyboard_nav():
    """Left/Right arrows step through the moves, Home/End jump to the start/end (clicks the nav buttons)."""
    with st.container(key="kbnav"):                      # zero-height holder for the invisible script frame
        if hasattr(st, "iframe"):                       # current Streamlit
            st.iframe(_KEYS_JS, height=1)
        else:                                           # older Streamlit versions
            components.html(_KEYS_JS, height=0)


def _card_html(rev: GameReview, ply: int) -> str:
    """The text card for a move (or the start of the game), as the browser will show it."""
    if ply == 0:
        return f"<div class='mc' style='border-color:var(--muted)'><div class='t'>Start of the game</div><div class='e'>{escape(rev.summary)}</div></div>"
    m = rev.moves[ply - 1]
    col = COLOR[m.classification]
    best = ""
    if m.classification in BAD or (m.classification in ("Good",) and m.loss > 3):
        if m.best_san and m.best_san != m.san:
            best = f"<div class='w'>Engine's choice: <b>{escape(m.best_san)}</b> (green arrow)</div>"
    return (f"<div class='mc' style='border-color:{col}'><div class='t'>{escape(move_label(m))}<i style='color:{col}'>{m.classification}</i></div>"
            f"<div class='e'>{escape(m.explanation)}</div>{best}</div>")


def review_payload(rev: GameReview, game_id: str) -> dict:
    """Everything the browser needs to step through a game without asking the server again."""
    T = theme.tokens()
    plies = []
    for m in rev.moves:
        shows_badge = m.classification not in ("Book", "Forced", "Good") and SYMBOL.get(m.classification)
        plies.append({"uci": m.uci, "from": m.uci[:2], "to": m.uci[2:4], "san": m.san, "fen": m.fen_after, "cls": m.classification,
                      "sym": SYMBOL.get(m.classification) if shows_badge else "", "color": COLOR[m.classification],
                      "best": m.best_uci if (m.classification in BAD and m.best_uci and m.best_uci != m.uci) else "",
                      "card": _card_html(rev, m.ply), "pill": _pill_label(m)})
    wps = [round(e["wp"], 1) for e in rev.evals] if rev.evals else [50.0] * (len(rev.moves) + 1)
    keys = sorted(k for k in rev.key_moments if 0 < k <= len(rev.moves))
    return {"id": game_id, "startFen": chess.STARTING_FEN, "startCard": _card_html(rev, 0), "plies": plies, "wps": wps, "keys": keys,
            "keyDots": [{"ply": k, "color": COLOR[rev.moves[k - 1].classification]} for k in keys],
            "flipped": rev.player_color == chess.BLACK, "start": 0,
            "colors": {"area": T["chart_area"], "muted": T["muted"], "line": T["line"], "text": T["text"]}}


def engine_reply(fen: str) -> dict:
    top = top_lines(fen)
    return {"fen": fen, "lines": [{"eval": t["eval"], "tone": t["tone"], "line": t["line"], "first": t["first"], "wp": t["wp"]} for t in top]}


@st.fragment
def viewer(rev: GameReview):
    """The interactive board, move card, graph and move list. It all runs in the browser (ui/assets/review.js); the server only answers
    when the page asks for Stockfish's lines for a position."""
    ss = st.session_state
    gid = ss.get("rev_id") or "game"
    cache = ss.get("_rv_payload")
    if not cache or cache[0] != gid:
        cache = ss["_rv_payload"] = (gid, review_payload(rev, gid))
    eng = ss.get("_rv_engine")
    err = ss.get("_rv_engine_err", "")
    res = live.run("review", f"rv_{gid}", {**cache[1], "engine": eng, "engine_error": err}, "engine")
    fen = getattr(res, "engine", None)
    if fen and live.valid_fen(fen) and (not eng or eng.get("fen") != fen):
        try:
            ss["_rv_engine"], ss["_rv_engine_err"] = engine_reply(str(fen)), ""
        except FileNotFoundError as e:
            ss["_rv_engine_err"] = str(e)
        st.rerun(scope="fragment")


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
    st.markdown(f"<div class='focus'><div class='k'>FOCUS FOR YOUR NEXT GAME</div>"
                f"<div class='f'>🎯 {escape(v.get('focus', ''))}</div><div class='d'>{escape(v.get('focus_tip', ''))}</div>"
                f"<span class='tag'>{escape(v.get('puzzle_trigger', ''))}</span> <span class='tag'>{escape(v.get('action_tag', ''))}</span></div>", unsafe_allow_html=True)
    if v.get("trends"):
        st.write("")
        items = "".join(f"<li>{escape(x)}</li>" for x in v["trends"])
        st.markdown(f"<div class='card verdict'><h4>📈 Patterns across your recent games</h4><ul style='margin:0;padding-left:18px'>{items}</ul></div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------------------------------------------------
# games list
# --------------------------------------------------------------------------------------------------------------------
_TC_ICON = {"bullet": "🚀", "blitz": "⚡", "rapid": "⏱️", "daily": "✉️"}


def games_summary(games: list):
    """A small strip above the list: results and average opponent rating across the loaded games."""
    res = [g.user_result for g in games]
    opp = [g.black_elo if g.user_color == chess.WHITE else g.white_elo for g in games]
    opp = [o for o in opp if o]
    cells = [(res.count("win"), "wins"), (res.count("draw"), "draws"), (res.count("loss"), "losses")]
    if opp:
        cells.append((round(sum(opp) / len(opp)), "avg opponent"))
    st.markdown("<div class='strip'>" + "".join(f"<div class='s'><b>{v}</b>{k}</div>" for v, k in cells) + "</div>", unsafe_allow_html=True)


def games_list(games: list, reviewed: dict, depth: int):
    """Shows the games as a two-column grid of cards; returns the GameInfo the user clicked, if any."""
    clicked = None
    cols = st.columns(2, gap="medium")
    for i, g in enumerate(games):
        when = dt.datetime.fromtimestamp(g.end_time, dt.timezone.utc).strftime("%d %b %Y") if g.end_time else ""
        elo_me = g.white_elo if g.user_color == chess.WHITE else g.black_elo
        elo_op = g.black_elo if g.user_color == chess.WHITE else g.white_elo
        done = reviewed.get(g.game_id, 0) >= depth
        with cols[i % 2]:
            with st.container(key=f"gc_{g.game_id}"):
                c1, c2 = st.columns([3.2, 1.4], vertical_alignment="center")
                c1.markdown(f"<div class='stripe {g.user_result}'></div><div class='gm'><div class='who'>{'⚪' if g.user_color == chess.WHITE else '⚫'} vs {escape(g.opponent)} "
                            f"<span class='soft' style='font-weight:600'>({elo_op or '?'})</span> {result_pill(g.user_result)}</div>"
                            f"<div class='sub'><span class='chip'>{_TC_ICON.get(g.time_class, '♟️')} {escape(g.time_class)} {escape(g.time_control)}</span>"
                            f"{when} · you {elo_me or '?'}</div></div>", unsafe_allow_html=True)
                if c2.button("Open ✓" if done else "Review", key=f"rv_{g.game_id}", type="secondary" if done else "primary", width="stretch"):
                    clicked = g
    return clicked
