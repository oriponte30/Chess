"""Puzzles: tactics puzzles in four levels. Click or drag a piece to play; the opponent answers automatically."""
from __future__ import annotations

import time
from html import escape

import chess
import streamlit as st

from core import puzzles as pz, store
from ui.board import SQ, _xy, board_svg
from ui.chessboard import board_component
from ui.state import username

ss = st.session_state
for _k, _v in {"pz_level": 0, "pz_theme": "All themes", "pz_id": None, "pz_played": [], "pz_status": "play", "pz_wrong": 0, "pz_hint": 0,
               "pz_pending": False, "pz_flash": None, "pz_streak": 0, "pz_best": 0, "pz_done_now": 0, "pz_anon": {}, "pz_shown": None}.items():
    ss.setdefault(_k, _v)


# ---- progress ---------------------------------------------------------------------------------------------------------------
def results() -> dict:
    """{puzzle_id: solved}: saved for a loaded chess.com user, kept for this visit otherwise."""
    user = username()
    return store.puzzle_results(user) if user else dict(ss.pz_anon)


def remember(puzzle_id: str, solved: bool):
    user = username()
    if user:
        store.save_puzzle_result(user, puzzle_id, solved, ss.pz_wrong + 1)
    elif solved:
        ss.pz_anon[puzzle_id] = True


# ---- state changes ------------------------------------------------------------------------------------------------------------
def start(puzzle_id: str):
    ss.pz_id, ss.pz_played, ss.pz_status = puzzle_id, [], "play"
    ss.pz_wrong, ss.pz_hint, ss.pz_pending, ss.pz_flash, ss.pz_shown = 0, 0, False, None, None


def candidates() -> list:
    theme = None if ss.pz_theme == "All themes" else ss.pz_theme
    return pz.pool(ss.pz_level or None, theme)


def next_puzzle():
    p = pz.pick(candidates(), results(), avoid=ss.pz_id)
    if p is not None:
        start(p.id)


def set_level(level: int):
    ss.pz_level, ss.pz_theme, ss.pz_id = level, "All themes", None


def change_theme():
    ss.pz_id = None


def hint():
    ss.pz_hint = min(2, ss.pz_hint + 1)


def reveal():
    ss.pz_status = "shown"
    ss.pz_streak = 0
    remember(ss.pz_id, False)


# ---- drawing ------------------------------------------------------------------------------------------------------------------
def _square_glow(svg: str, square: int, flipped: bool, color: str) -> str:
    x, y = _xy(square, flipped)
    return svg.replace("</svg>", f"<rect x='{x}' y='{y}' width='{SQ}' height='{SQ}' fill='{color}' class='hintpulse' pointer-events='none'/></svg>")


def _dots(puz: pz.Puzzle, done: int, status: str) -> str:
    dots = []
    for i in range(puz.solver_moves):
        cls = "ok" if i < done else "now" if (i == done and status == "play") else ""
        dots.append(f"<span class='{cls}'></span>")
    return "<div class='dots'>" + "".join(dots) + "</div>"


@st.fragment
def play():
    puz = pz.by_id()[ss.pz_id]
    played = list(ss.pz_played)
    step = len(played)
    board = puz.board_at(0)
    for u in played:
        board.push_uci(u)
    flipped = puz.side == chess.BLACK
    status = ss.pz_status
    solver_done = (step + 1) // 2

    # the move that was just made is animated (the opponent's last move is animated when a puzzle opens)
    shown = ss.pz_shown
    if shown is None:
        slide = (puz.last, False) if puz.last else None
        last = puz.last or None
    else:
        slide = (played[-1], False) if step == shown + 1 else None
        last = played[-1] if played else (puz.last or None)
    ss.pz_shown = step

    best = None
    if status == "shown" and step < len(puz.moves):
        best = puz.moves[step]
    elif ss.pz_hint >= 2 and status == "play" and not ss.pz_pending and step < len(puz.moves):
        best = puz.moves[step]
    svg = board_svg(board.fen(), last, best, flipped, None, slide=slide)
    if ss.pz_hint == 1 and status == "play" and not ss.pz_pending and step < len(puz.moves):
        svg = _square_glow(svg, chess.parse_square(pz.hint_square(puz, step)), flipped, "rgba(255,214,0,.55)")
    svg = svg.replace('width="520" height="520"', 'style="width:100%;height:auto"')
    wrap = "boardwrap" + (" shake" if ss.pz_flash == "wrong" else "") + (" glow" if status == "solved" else "")
    ss.pz_flash = None

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        made = board_component("pz_board", board.fen(), f"<div class='{wrap}'>{svg}</div>", flipped,
                               interactive=(status == "play" and not ss.pz_pending))
        if made and status == "play" and not ss.pz_pending:
            verdict = pz.judge(puz, step, made)
            if verdict == "wrong":
                ss.pz_wrong += 1
                ss.pz_streak = 0
                ss.pz_flash = "wrong"
            else:
                ss.pz_played = played + [made]
                if verdict == "solved":
                    ss.pz_status = "solved"
                    remember(puz.id, True)
                    ss.pz_streak += 1
                    ss.pz_best = max(ss.pz_best, ss.pz_streak)
                    ss.pz_done_now += 1
                    st.toast("Correct! 🎉", icon="✅")
                else:
                    ss.pz_pending = True                      # the opponent answers in a moment
            st.rerun(scope="fragment")

    with right:
        side = "White" if puz.side == chess.WHITE else "Black"
        who = "⚪" if puz.side == chess.WHITE else "⚫"
        if status == "play":
            head = f"{who} {side} to move"
            sub = "Find the best move." if not ss.pz_pending else "Good move! The opponent replies…"
        elif status == "solved":
            head, sub = "✅ Puzzle solved!", ("First try, well done." if ss.pz_wrong == 0 else f"Solved after {ss.pz_wrong} wrong guess{'es' if ss.pz_wrong != 1 else ''}.")
        else:
            head, sub = "💡 The solution", "Study it, then try the next one."
        chips = f"<span class='chip lv{puz.level}'>{pz.LEVELS[puz.level]['icon']} {puz.level_name}</span>"
        if status != "play":
            chips += "".join(f"<span class='chip'>{escape(t)}</span>" for t in puz.themes)
        body = ""
        if status != "play":
            body = f"<p class='soft' style='margin-top:8px'>Solution: <b>{escape(puz.solution_san())}</b></p>"
        st.markdown(f"<div class='card exp pzcard {status}'><h4>Puzzle</h4><div class='sanline'>{head}</div><p class='soft'>{sub}</p>"
                    f"{_dots(puz, solver_done if status != 'shown' else 0, status)}<div class='m'>{chips}</div>{body}</div>", unsafe_allow_html=True)
        st.write("")
        if status == "play":
            if ss.pz_wrong:
                st.warning(f"Not quite: that is not the best move. {ss.pz_wrong} wrong guess{'es' if ss.pz_wrong != 1 else ''} so far.")
            c1, c2, c3 = st.columns(3)
            c1.button("💡 Hint", key="pz_hint_btn", on_click=hint, width="stretch", disabled=ss.pz_hint >= 2 or ss.pz_pending,
                      help="Once: shows the piece to move. Twice: shows the move.")
            c2.button("👁️ Solution", key="pz_reveal_btn", on_click=reveal, width="stretch", disabled=ss.pz_pending)
            if c3.button("⏭️ Skip", key="pz_skip_btn", width="stretch", disabled=ss.pz_pending):
                ss.pz_streak = 0
                next_puzzle()
                st.rerun()
        else:
            if st.button("Next puzzle ▶", key="pz_next_btn", type="primary", width="stretch"):
                next_puzzle()
                st.rerun()

    if ss.pz_pending:                                          # let the player see their own move, then play the opponent's reply
        time.sleep(0.6)
        ss.pz_played = list(ss.pz_played) + [puz.moves[len(ss.pz_played)]]
        ss.pz_pending = False
        st.rerun(scope="fragment")


# ---- page -----------------------------------------------------------------------------------------------------------------------
st.markdown("<div class='pagehead'><h1>Puzzles</h1><p>Sharpen your tactics. Every puzzle has one clearly best move, checked by Stockfish.</p></div>", unsafe_allow_html=True)
if not pz.load():
    st.warning("The puzzle library (data/puzzles.json) was not found. Run `python scripts/build_puzzles.py` to create it.")
    st.stop()

res = results()
counts = pz.counts_by_level(res)
total_solved = sum(a for a, _ in counts.values())
total = sum(b for _, b in counts.values())
tabs = [(0, "🎲", "Mixed", "All levels together", total_solved, total)] + [
    (lv, m["icon"], m["name"], m["blurb"], counts[lv][0], counts[lv][1]) for lv, m in pz.LEVELS.items()]
cols = st.columns(len(tabs), gap="small")
for col, (lv, icon, name, blurb, done, tot) in zip(cols, tabs):
    with col:
        pct = (done / tot * 100) if tot else 0
        sel = " sel" if ss.pz_level == lv else ""
        st.markdown(f"<div class='lvl{sel}'><div class='i'>{icon}</div><div class='h'>{name}</div><div class='x'>{blurb}</div>"
                    f"<div class='bar'><div style='width:{pct:.0f}%'></div></div><div class='n'>{done} / {tot} solved</div></div>", unsafe_allow_html=True)
        st.button("Selected" if ss.pz_level == lv else "Play", key=f"pz_lv_{lv}", on_click=set_level, args=(lv,), width="stretch",
                  type="primary" if ss.pz_level == lv else "secondary", disabled=(ss.pz_level == lv))

theme_options = ["All themes"] + [f"{t}" for t, _ in pz.themes(ss.pz_level or None)]
if ss.pz_theme not in theme_options:
    ss.pz_theme = "All themes"
t1, t2 = st.columns([1, 2.2], vertical_alignment="center")
t1.selectbox("Theme", theme_options, key="pz_theme", on_change=change_theme, label_visibility="collapsed")
t2.markdown(f"<div class='strip' style='margin:0'><div class='s'><b>🔥 {ss.pz_streak}</b>streak</div><div class='s'><b>🏆 {ss.pz_best}</b>best streak</div>"
            f"<div class='s'><b>✅ {ss.pz_done_now}</b>solved this visit</div></div>", unsafe_allow_html=True)

pool_now = candidates()
if not pool_now:
    st.info("No puzzles match that choice. Pick another theme.")
    st.stop()
if ss.pz_id is None or ss.pz_id not in {p.id for p in pool_now}:
    next_puzzle()
if not username():
    st.caption("Tip: load your chess.com games in the sidebar and your solved puzzles are remembered between visits.")
play()
