"""Board drawing: python-chess SVG plus a move-quality badge on the destination square."""
from __future__ import annotations

import chess
import chess.svg

SQ, MARGIN = 45, 15          # chess.svg geometry with coordinates on: 390 x 390 viewBox


def _xy(square: int, flipped: bool):
    f, r = chess.square_file(square), chess.square_rank(square)
    x = MARGIN + (7 - f if flipped else f) * SQ
    y = MARGIN + (r if flipped else 7 - r) * SQ
    return x, y


def board_svg(fen: str, last_uci: str | None = None, best_uci: str | None = None, flipped: bool = False,
              badge: tuple | None = None, size: int = 520) -> str:
    """badge = (symbol, hex colour) drawn on the square the last move went to."""
    board = chess.Board(fen)
    last = chess.Move.from_uci(last_uci) if last_uci else None
    arrows = []
    if best_uci:
        bm = chess.Move.from_uci(best_uci)
        arrows.append(chess.svg.Arrow(bm.from_square, bm.to_square, color="#7fa650cc"))
    svg = chess.svg.board(board, lastmove=last, arrows=arrows, flipped=flipped, size=size, coordinates=True,
                          colors={"square light": "#eeeed2", "square dark": "#769656", "square light lastmove": "#f6f669",
                                  "square dark lastmove": "#baca2b", "margin": "#1f2933", "coord": "#c9d1d9"})
    if badge and last is not None:
        sym, color = badge
        x, y = _xy(last.to_square, flipped)
        cx, cy = x + SQ - 8, y + 9
        g = (f"<g><circle cx='{cx}' cy='{cy}' r='10' fill='{color}' stroke='#fff' stroke-width='1.6'/>"
             f"<text x='{cx}' y='{cy + 3.6}' font-size='{10 if len(sym) > 1 else 12}' font-weight='800' fill='#fff' text-anchor='middle' "
             f"font-family='Segoe UI, Arial, sans-serif'>{sym}</text></g>")
        svg = svg.replace("</svg>", g + "</svg>")
    return svg
