"""Lessons: interactive opening lessons built on a variation tree (core/lessons.py), with optional Stockfish suggestions."""
from __future__ import annotations

import chess
import streamlit as st

from core import lessons, service
from ui import views
from ui.board import board_svg
from ui.chessboard import board_component

ss = st.session_state
TREE = lessons.CARO_KANN
if "lesson_path" not in ss:
    ss["lesson_path"] = []
if "lesson_flip" not in ss:
    ss["lesson_flip"] = True                            # the Caro-Kann is learnt from Black's side


# ---- state changes (all go through the path of UCI moves, so the board, the tree node and the text always agree) ---------------
def _board(path: list) -> chess.Board:
    b = chess.Board()
    for u in path:
        b.push_uci(u)
    return b


def play(uci: str):
    ss.lesson_path = ss.lesson_path + [uci]


def back():
    ss.lesson_path = ss.lesson_path[:-1]


def reset():
    ss.lesson_path = []


def go_section(sid: str):
    sec = next(s for s in TREE.sections if s["id"] == sid)
    ss.lesson_path = TREE.node_at_san(sec["start"]).path


def forward():
    node = TREE.effective(TREE.resolve(_board(ss.lesson_path), ss.lesson_path))
    if node is not None and node.children:
        play(node.children[0].uci)


def to_end():
    node = TREE.resolve(_board(ss.lesson_path), ss.lesson_path)
    if node is not None:
        tail = TREE.main_line(node, 99)
        if tail:
            ss.lesson_path = tail[-1].path


def own_move():
    san = ss.get("lesson_own")
    if san and san != "—":
        b = _board(ss.lesson_path)
        play(b.parse_san(san).uci())
    ss["lesson_own"] = "—"


@st.cache_data(show_spinner=False, max_entries=1024)
def top_lines(fen: str, depth: int = 12, n: int = 3) -> list:
    """Stockfish's best lines for a position: [{eval, tone, line, first}] (evaluation from White's point of view)."""
    board = chess.Board(fen)
    out = []
    for L in service.make_engine().analyse(board, depth, n):
        if L.mate is not None:
            ev = f"M{abs(L.mate)}" if L.mate > 0 else f"-M{abs(L.mate)}"
        else:
            ev = f"{L.cp / 100:+.2f}"
        b, parts = board.copy(), []
        for i, mv in enumerate(L.pv[:6]):
            no = f"{b.fullmove_number}." if b.turn == chess.WHITE else (f"{b.fullmove_number}..." if i == 0 else "")
            parts.append(f"{no}{b.san(mv)}".strip())
            b.push(mv)
        out.append({"eval": ev, "tone": "pos" if (L.cp > 25 and L.mate is None) or (L.mate or 0) > 0 else "neg" if (L.cp < -25 and L.mate is None) or (L.mate or 0) < 0 else "",
                    "line": " ".join(parts), "first": L.pv[0].uci() if L.pv else ""})
    return out


def _slide(path: list):
    """Animate the move just played (or undone), when the path changed by exactly one move since the last drawing."""
    prev = ss.get("_lesson_shown")
    ss["_lesson_shown"] = list(path)
    if prev is None:
        return None
    if len(path) == len(prev) + 1 and path[:-1] == prev:
        return (path[-1], False)
    if len(prev) == len(path) + 1 and prev[:-1] == path:
        return (prev[-1], True)
    return None


@st.fragment
def lesson():
    path = ss.lesson_path
    board = _board(path)
    node = TREE.resolve(board, path)
    eff = TREE.effective(node)
    section = TREE.section_of(node)
    flipped = bool(ss.get("lesson_flip", True))
    show_engine = bool(ss.get("lesson_engine", False))

    st.markdown(f"<div class='lesson-title'>{TREE.title}</div><div class='lesson-sub'>{TREE.intro}</div>", unsafe_allow_html=True)
    sc = st.columns(4)
    sc[0].button("🏁 Start", key="sec_start", on_click=reset, width="stretch")
    for col, s in zip(sc[1:], TREE.sections):
        col.button(f"{s['icon']} {s['title']}", key=f"sec_{s['id']}", on_click=go_section, args=(s["id"],), width="stretch",
                   type="primary" if section and section["id"] == s["id"] else "secondary")

    left, right = st.columns([1.15, 1], gap="large")
    top, engine_error = [], ""
    if show_engine and not board.is_game_over():
        try:
            top = top_lines(board.fen())
        except FileNotFoundError as e:                   # the overlay is on but Stockfish isn't installed
            engine_error = str(e)
    with left:
        last = board.peek().uci() if board.move_stack else None
        arrow = top[0]["first"] if top else None
        more = [(t["first"], c) for t, c in zip(top[1:], ("#e0a82ecc", "#d9534fcc")) if t["first"]]     # 2nd and 3rd choice in other colours
        svg = board_svg(board.fen(), last, arrow, flipped, None, slide=_slide(path), extra_arrows=more)
        svg = svg.replace('width="520" height="520"', 'style="width:100%;height:auto"')
        made = board_component("lesson_board", board.fen(), f"<div class='boardwrap'>{svg}</div>", flipped)
        if made:                                          # a click-to-move on the board: extend the path and redraw
            play(made)
            st.rerun(scope="fragment")
        b1, b2, b3, b4 = st.columns(4)
        b1.button("⏮", key="nav_first", on_click=reset, width="stretch", help="Back to the start")
        b2.button("◀", key="nav_prev", on_click=back, width="stretch", disabled=not path, help="Take back a move")
        has_next = bool(eff and eff.children)
        b3.button("▶", key="nav_next", on_click=forward, width="stretch", disabled=not has_next, help="Play the main line")
        b4.button("⏭", key="nav_last", on_click=to_end, width="stretch", help="Follow the main line to its end")
        t1, t2 = st.columns(2)
        t1.toggle("Top engine moves", key="lesson_engine", help="Shows Stockfish's three best lines for this position")
        t2.toggle("Flip board", key="lesson_flip")
        legal = ["—"] + sorted(board.san(m) for m in board.legal_moves)
        st.selectbox("Try your own move", legal, key="lesson_own", on_change=own_move,
                     help="Any legal move works. If it leaves the lesson, Stockfish's suggestions take over.")
        st.caption("Click a piece to see where it can go, then click a square (or drag). ← → on your keyboard take back / play the main line.")

    with right:
        crumbs = []
        b = chess.Board()
        for i, u in enumerate(path):
            mv = chess.Move.from_uci(u)
            n = b.fullmove_number
            crumbs.append((f"{n}.{b.san(mv)}" if b.turn == chess.WHITE else (f"{n}...{b.san(mv)}" if i == 0 else b.san(mv)), i == len(path) - 1))
            b.push(mv)
        if crumbs:
            st.markdown("<div class='crumbs'>" + "".join(f"<span class='{'cur' if cur else ''}'>{c}</span>" for c, cur in crumbs) + "</div>", unsafe_allow_html=True)

        if node is None:
            st.markdown("<div class='card exp'><h4>Off the lesson tree</h4><p>That move isn't covered by this lesson, so there is no prepared "
                        "explanation here. Turn on <b>Top engine moves</b> to see what Stockfish suggests, or take the move back to return to the lesson.</p></div>",
                        unsafe_allow_html=True)
        else:
            note = (eff.note if eff else "") or ("Book move. Keep following the plan of this variation." if path else TREE.intro)
            head = node.label if path else "Start of the lesson"
            alias = "<p class='soft'>🔀 A different move order reached this same position, so the same ideas apply.</p>" if node.alias is not None else ""
            st.markdown(f"<div class='card exp'><h4>{section['title'] if section else 'Caro-Kann'}</h4><div class='sanline'>{head}</div>"
                        f"<p>{note}</p>{alias}</div>", unsafe_allow_html=True)
            if section and path:
                st.markdown(f"<div class='card exp' style='margin-top:10px'><h4>Structure and plan</h4><p>{section['summary']}</p></div>", unsafe_allow_html=True)

            tl = TREE.top_lines(node, 3) if eff else []
            if tl:
                st.markdown(f"<h4 class='sechead'>Top {len(tl)} lines from here</h4>", unsafe_allow_html=True)
                for i, line in enumerate(tl):
                    with st.container(border=True):
                        cc = st.columns([1.3, 3], vertical_alignment="center")
                        cc[0].button(f"▶ Line {i + 1}", key=f"tl_{i}_{len(path)}", on_click=play, args=(line[0].uci,), width="stretch",
                                     help="Plays the first move of this line")
                        cc[1].markdown(f"<div class='exp'><p style='margin:0'><b>{lessons.fmt_line(line)}</b></p></div>", unsafe_allow_html=True)

            opts = TREE.look_ahead(node) if eff else []
            if opts:
                st.markdown("<h4 class='sechead'>What to do in the next few moves</h4>", unsafe_allow_html=True)
                for o in opts[:4]:
                    c = o["move"]
                    with st.container(border=True):
                        cc = st.columns([1.3, 3], vertical_alignment="center")
                        cc[0].button(f"▶ {c.label}", key=f"lc_{c.uci}_{len(path)}", on_click=play, args=(c.uci,), width="stretch")
                        replies = ""
                        if o["replies"]:
                            replies = "<br>".join(f"If <b>{r.label}</b> → then {lessons.fmt_line(cont) or 'the line ends'}" for r, cont in o["replies"][:3])
                        cc[1].markdown(f"<div class='exp'><p style='margin:0'><b>{lessons.fmt_line(o['line'])}</b></p>"
                                       f"<p style='margin:2px 0 0;font-size:13.5px'>{replies}</p></div>", unsafe_allow_html=True)
            elif path:
                st.markdown("<div class='card exp' style='margin-top:10px'><h4>End of this line</h4><p>The prepared line stops here. Use <b>Try your own move</b> "
                            "or the engine overlay to keep exploring, or go back and pick another branch.</p></div>", unsafe_allow_html=True)

        if show_engine:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if top:
                rows = "".join(f"<div class='eng'><div class='ev {t['tone']}'>{t['eval']}</div><div class='ln'>{t['line']}</div></div>" for t in top)
                st.markdown(f"<div class='card exp'><h4>Top engine moves (Stockfish)</h4>{rows}</div>", unsafe_allow_html=True)
            elif engine_error:
                st.warning(engine_error)
            elif board.is_game_over():
                st.info("The game is over in this position.")


st.markdown("<div class='pagehead'><h1>Lessons</h1><p>Learn an opening move by move, with explanations, plans and Stockfish on tap.</p></div>", unsafe_allow_html=True)
if not ss.get("engine_ok", True):
    st.info("Stockfish isn't installed here, so the engine overlay is unavailable. The lesson itself works without it.")
_ = views.keyboard_nav()
_ = lesson()
