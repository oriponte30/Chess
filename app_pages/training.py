"""Training hub: Chess Puzzles, Puzzle Duels and Coach Practice (positions from your own mistakes, via the Insights data)."""
from __future__ import annotations

from html import escape

import chess
import streamlit as st

from core import insights as ins, store
from ui.board import board_svg
from ui.state import username

ss = st.session_state
if "train_mode" not in ss:
    ss["train_mode"] = None
if "cp_i" not in ss:
    ss["cp_i"] = 0
if "cp_state" not in ss:
    ss["cp_state"] = "ask"
if "cp_tries" not in ss:
    ss["cp_tries"] = 0


def open_mode(m):
    ss.train_mode = m
    ss.cp_i, ss.cp_state, ss.cp_tries = 0, "ask", 0


def nxt(n):
    ss.cp_i = (ss.cp_i + 1) % max(1, n)
    ss.cp_state, ss.cp_tries, ss.cp_hint = "ask", 0, False
    ss["cp_answer"] = "—"


def check(m, board):
    san = ss.get("cp_answer")
    if not san or san == "—":
        return
    if board.parse_san(san).uci() == m["best_uci"]:
        ss.cp_state = "solved"
    else:
        ss.cp_tries += 1
        ss["cp_answer"] = "—"


def reveal():
    ss.cp_state = "revealed"


def hub():
    st.markdown("<div class='pagehead'><h1>Training</h1><p>Practice that grows from your own games.</p></div>", unsafe_allow_html=True)
    cols = st.columns(3, gap="medium")
    cards = [("🧩", "Chess Puzzles", "Tactics puzzles sorted by theme and difficulty, to sharpen pattern recognition.", "Coming soon", "#6c8cff"),
             ("⚔️", "Puzzle Duels", "Race an opponent to solve the same puzzle first. Head-to-head tactics.", "Coming soon", "#e6a23c"),
             ("🎯", "Coach Practice", "Positions from your own mistakes, picked by what the Insights page says you need most.", "Live", "#7fa650")]
    for col, (icon, head, text, badge, orb) in zip(cols, cards):
        col.markdown(f"<div class='hub' style='--orb:{orb}'><div class='i'>{icon}</div><div class='h'>{head}</div><div class='x'>{text}</div>"
                     f"<span class='badge {'live' if badge == 'Live' else ''}'>{badge}</span></div>", unsafe_allow_html=True)
        if badge == "Live":
            col.button("Start Coach Practice", key="open_cp", on_click=open_mode, args=("coach",), type="primary", width="stretch")
        else:
            col.button("Coming soon", key=f"soon_{head}", disabled=True, width="stretch")


def coach_practice():
    st.button("← Training", on_click=open_mode, args=(None,))
    st.markdown("<div class='pagehead'><h1>Coach Practice</h1><p>Find the move you missed. Positions come from your reviewed games.</p></div>", unsafe_allow_html=True)
    user = username()
    if not user:
        st.info("Load your games from the sidebar and review a few. The coach builds your practice from your own mistakes.")
        return
    ms = store.mistakes(user)
    if not ms:
        st.info("No serious mistakes found in your reviewed games yet. Review more games and they'll appear here.")
        return
    areas = ins.focus_areas(ms, 5)
    themes = ["Everything the coach picked"] + [a["theme"] for a in areas]
    pick = st.selectbox("Practise", themes, key="cp_theme", on_change=lambda: (ss.update(cp_i=0, cp_state="ask", cp_tries=0)))
    pool = ms if pick == themes[0] else [m for m in ms if pick in (m["themes"] or ["Calculation"])]
    pool = sorted(pool, key=lambda m: -m["loss"])
    if not pool:
        st.info("No positions for that theme.")
        return
    i = ss.cp_i % len(pool)
    m = pool[i]
    board = chess.Board(m["fen"])
    flipped = board.turn == chess.BLACK
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        arrow = m["best_uci"] if ss.cp_state != "ask" else None
        svg = board_svg(m["fen"], None, arrow, flipped).replace('width="520" height="520"', 'style="width:100%;height:auto"')
        st.markdown(f"<div class='boardwrap'>{svg}</div>", unsafe_allow_html=True)
    with right:
        side = "White" if board.turn == chess.WHITE else "Black"
        st.markdown(f"<div class='card exp'><h4>Position {i + 1} of {len(pool)}</h4><div class='sanline'>{side} to move: find the best move</div>"
                    f"<p class='soft'>From your game vs {escape(m['opponent'] or 'an opponent')} · {escape(m['phase'])}"
                    f"{' · ' + escape(', '.join(m['themes'])) if m['themes'] else ''}</p></div>", unsafe_allow_html=True)
        st.write("")
        if ss.cp_state == "ask":
            legal = ["—"] + sorted(board.san(mv) for mv in board.legal_moves)
            st.selectbox("Your move", legal, key="cp_answer", on_change=check, args=(m, board))
            if ss.cp_tries:
                st.warning(f"Not quite. {ss.cp_tries} wrong guess{'es' if ss.cp_tries != 1 else ''} so far. Think about what the opponent threatens.")
            c = st.columns(2)
            c[0].button("💡 Hint", key="cp_hint", on_click=lambda: ss.update(cp_hint=True))
            c[1].button("Show the answer", key="cp_reveal", on_click=reveal)
            if ss.get("cp_hint"):
                sq = chess.square_name(chess.Move.from_uci(m["best_uci"]).from_square)
                st.caption(f"Hint: look at the piece on {sq}.")
        else:
            ok = ss.cp_state == "solved"
            st.markdown(f"<div class='mc' style='border-color:{'var(--win)' if ok else 'var(--loss)'}'><div class='t'>{'Correct! ' if ok else 'The best move was '}{escape(m['best_san'])}</div>"
                        f"<div class='e'>In the game you played <b>{escape(m['played'])}</b> ({m['classification'].lower()}, about {m['loss']:.0f} win-% lost). "
                        f"{escape(m['explanation'])}</div></div>", unsafe_allow_html=True)
            st.write("")
            st.button("Next position ▶", key="cp_next", on_click=nxt, args=(len(pool),), type="primary")


if ss.train_mode == "coach":
    coach_practice()
else:
    hub()
