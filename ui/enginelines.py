"""Stockfish's top lines for any position (shared by Lessons and Game review)."""
from __future__ import annotations

import chess
import streamlit as st

from core import service
from core.review import win_prob

ARROW_COLORS = ("#7fa650cc", "#e0a82ecc", "#d9534fcc")      # best, second and third choice


@st.cache_data(show_spinner=False, max_entries=2048)
def top_lines(fen: str, depth: int = 12, n: int = 3) -> list:
    """[{eval, tone, line, first, wp}] for a position; eval is from White's point of view, wp is White's win probability (0-100)."""
    board = chess.Board(fen)
    out = []
    for L in service.make_engine().analyse(board, depth, n):
        if L.mate is not None:
            ev = f"M{abs(L.mate)}" if L.mate > 0 else f"-M{abs(L.mate)}"
            wp = 100.0 if L.mate > 0 else 0.0
        else:
            ev = f"{L.cp / 100:+.2f}"
            wp = win_prob(L.cp)
        b, parts = board.copy(), []
        for i, mv in enumerate(L.pv[:6]):
            no = f"{b.fullmove_number}." if b.turn == chess.WHITE else (f"{b.fullmove_number}..." if i == 0 else "")
            parts.append(f"{no}{b.san(mv)}".strip())
            b.push(mv)
        out.append({"eval": ev, "tone": "pos" if (L.cp > 25 and L.mate is None) or (L.mate or 0) > 0 else "neg" if (L.cp < -25 and L.mate is None) or (L.mate or 0) < 0 else "",
                    "line": " ".join(parts), "first": L.pv[0].uci() if L.pv else "", "wp": wp})
    return out


def arrows(top: list) -> tuple:
    """(best_uci, [(uci, colour), ...] for the 2nd and 3rd choices)."""
    best = top[0]["first"] if top else None
    return best, [(t["first"], c) for t, c in zip(top[1:], ARROW_COLORS[1:]) if t["first"]]


def panel_html(top: list) -> str:
    rows = "".join(f"<div class='eng'><div class='ev {t['tone']}'>{t['eval']}</div><div class='ln'>{t['line']}</div></div>" for t in top)
    return f"<div class='card exp'><h4>Top engine lines (Stockfish)</h4>{rows}</div>"
