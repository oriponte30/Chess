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


@st.fragment
def viewer(rev: GameReview):
    ss = st.session_state
    n = len(rev.moves)
    ply = max(0, min(n, ss.get("ply", 0)))
    ss.ply = ply
    flipped = bool(ss.get("flip", rev.player_color == chess.BLACK))
    if ss.get("_explore_ply") != ply:                    # a different game position: forget the side line
        ss["explore"] = []
    ss["_explore_ply"] = ply
    line = list(ss.get("explore", []))                  # your own moves played on the board from this position
    left, right = st.columns([1.25, 1], gap="large")
    m = rev.moves[ply - 1] if ply else None
    with left:
        base_fen = m.fen_after if m else chess.STARTING_FEN
        board = chess.Board(base_fen)
        for u in line:
            board.push_uci(u)
        exploring = bool(line)
        fen = board.fen()
        show_best = bool(ss.get("show_best", True))
        show_eng = bool(ss.get("show_engine", False))
        top, engine_error = [], ""
        if (show_eng or exploring) and not board.is_game_over():
            try:
                top = top_lines(fen)
            except FileNotFoundError as e:
                engine_error = str(e)
        best, more = None, []
        if top:
            best, more = engine_arrows(top)
        elif not exploring and m and show_best and m.classification in BAD and m.best_uci != m.uci:
            best = m.best_uci
        badge = None if exploring else ((SYMBOL.get(m.classification) or "", COLOR[m.classification]) if m and m.classification not in ("Book", "Forced", "Good") else None)
        if badge and not badge[0]:
            badge = None
        if exploring:
            wp = top[0]["wp"] if top else 50.0
            last = line[-1]
        else:
            wp = rev.evals[ply]["wp"] if rev.evals else 50.0
            last = m.uci if m else None
        # the piece glides: one step through the game, or one move on a side line
        shown = ss.get("_shown")
        slide = None
        if shown is not None:
            sp, sl = shown
            if exploring and sp == ply and tuple(sl) == tuple(line[:-1]):
                slide = (line[-1], False)
            elif not exploring and sp == ply and len(sl) == 1 and not line:
                slide = (sl[-1], True)
            elif not exploring and not line and sp == ply - 1 and not sl and m:
                slide = (m.uci, False)
            elif not exploring and not line and sp == ply + 1 and not sl and ply < n:
                slide = (rev.moves[ply].uci, True)
        ss["_shown"] = (ply, list(line))
        svg = board_svg(fen, last, best, flipped, badge, slide=slide, extra_arrows=more)
        svg = svg.replace('width="520" height="520"', 'style="width:100%;height:auto"')
        html = (f"<div class='boardwrap'><div style='display:flex;gap:12px;align-items:stretch'>{_eval_bar(wp, flipped)}"
                f"<div style='flex:1;max-width:560px'>{svg}</div></div></div>")
        made = board_component(f"review_board_{ply}_{len(line)}", fen, html, flipped)
        if made:                                          # you moved a piece on the board: carry on from there
            ss["explore"] = line + [made]
            st.rerun(scope="fragment")
        b1, b2, b3, b4 = st.columns(4)
        b1.button("⏮", key="nav_first", on_click=_set_ply, args=(0, n), width="stretch", help="Start")
        if exploring:
            b2.button("◀", key="nav_prev", on_click=_explore_back, width="stretch", help="Take back your move")
            b3.button("↩ Game", key="nav_next", on_click=_explore_reset, width="stretch", help="Back to the game moves")
        else:
            b2.button("◀", key="nav_prev", on_click=_set_ply, args=(ply - 1, n), width="stretch", disabled=ply <= 0, help="Previous move")
            b3.button("▶", key="nav_next", on_click=_set_ply, args=(ply + 1, n), width="stretch", disabled=ply >= n, help="Next move")
        b4.button("⏭", key="nav_last", on_click=_set_ply, args=(n, n), width="stretch", help="End")
        b5, b6 = st.columns(2)
        b5.button("◀ Previous key moment", key="nav_pk", on_click=_jump_key, args=(rev, -1), width="stretch", disabled=not rev.key_moments)
        b6.button("Next key moment ▶", key="nav_nk", on_click=_jump_key, args=(rev, 1), width="stretch", disabled=not rev.key_moments)
        t1, t2, t3 = st.columns(3)
        t1.toggle("Best move", value=True, key="show_best")
        t2.toggle("Engine top 3", key="show_engine", help="Stockfish's three best moves for the position on the board")
        t3.toggle("Flip board", value=flipped, key="flip")
        st.caption("Click a piece to see where it can go, then click a square to try your own move. ← → step through the game · Home / End jump to the start / end")
    with right:
        if exploring:
            sans, b = [], chess.Board(base_fen)
            for u in line:
                mv = chess.Move.from_uci(u)
                no = f"{b.fullmove_number}." if b.turn == chess.WHITE else (f"{b.fullmove_number}..." if not sans else "")
                sans.append(f"{no}{b.san(mv)}".strip())
                b.push(mv)
            st.markdown("<div class='mc' style='border-color:var(--accent)'><div class='t'>Your own line<i style='color:var(--accent)'>exploring</i></div>"
                        f"<div class='e'>{escape(' '.join(sans))}<br>This is your own variation, not the game. Use ◀ to take a move back or <b>↩ Game</b> to return.</div></div>",
                        unsafe_allow_html=True)
        else:
            _move_card(rev, ply, bool(ss.get("show_best", True)))
        if top:
            st.markdown(panel_html(top), unsafe_allow_html=True)
        elif engine_error:
            st.warning(engine_error)
        elif (show_eng or exploring) and board.is_game_over():
            st.info("The game is over in this position.")
        _graph(rev, ply)
        labels = {mm.ply: _pill_label(mm) for mm in rev.moves}
        ss.ply_pick = ply or None                          # keep the list in step with the board and the arrow keys
        with st.container(height=330, key="movelist"):
            st.pills("Moves", list(labels), format_func=labels.get, selection_mode="single", key="ply_pick",
                     on_change=_pick_ply, args=(n,), label_visibility="collapsed")


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
        done = reviewed.get(g.game_id) == depth
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
