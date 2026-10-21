"""Board drawing: python-chess SVG plus a move-quality badge on the destination square."""
from __future__ import annotations

import re

import chess
import chess.svg

SQ, MARGIN = 45, 15          # chess.svg geometry with coordinates on: 390 x 390 viewBox


def _xy(square: int, flipped: bool):
    f, r = chess.square_file(square), chess.square_rank(square)
    x = MARGIN + (7 - f if flipped else f) * SQ
    y = MARGIN + (r if flipped else 7 - r) * SQ
    return x, y


def _slide_pairs(move: chess.Move, board_after: chess.Board, backward: bool) -> list:
    """[(square the piece is drawn on, square it should slide in from)] for a move: the piece itself, plus the rook when castling.
    Going backwards the position shown is the one BEFORE the move, so the piece slides from where it had been back to its origin."""
    f, t = move.from_square, move.to_square
    pairs = [(f, t)] if backward else [(t, f)]
    # castling: the king moves two files
    if abs(chess.square_file(f) - chess.square_file(t)) == 2 and chess.square_rank(f) == chess.square_rank(t):
        rank = chess.square_rank(f)
        king_side = chess.square_file(t) > chess.square_file(f)
        rf, rt = chess.square(7 if king_side else 0, rank), chess.square(5 if king_side else 3, rank)
        pairs.append((rf, rt) if backward else (rt, rf))
    return pairs


def _animate_pieces(svg: str, pairs: list, flipped: bool) -> str:
    """Gives the pieces that just moved a CSS slide animation (the cubic-bezier lives in ui/styles.py). The moved piece is moved to the
    end of the SVG so it travels above the others."""
    for dst, src in pairs:
        dx, dy = _xy(dst, flipped)
        sx, sy = _xy(src, flipped)
        pat = re.compile(r'<use href="#([a-z-]+)" xlink:href="#[a-z-]+" transform="translate\(%d, %d\)" />' % (dx, dy))
        m = pat.search(svg)
        if not m:
            continue
        el = (f'<use href="#{m.group(1)}" xlink:href="#{m.group(1)}" transform="translate({dx}, {dy})" class="pslide" '
              f'style="--fx:{sx}px;--fy:{sy}px;--tx:{dx}px;--ty:{dy}px" />')
        svg = svg[:m.start()] + svg[m.end():]
        svg = svg.replace("</svg>", el + "</svg>")
    return svg


def board_svg(fen: str, last_uci: str | None = None, best_uci: str | None = None, flipped: bool = False,
              badge: tuple | None = None, size: int = 520, slide: tuple | None = None, extra_arrows: list | None = None) -> str:
    """badge = (symbol, hex colour) drawn on the square the last move went to.
    extra_arrows = [(uci, "#rrggbbaa")]: more arrows.
    slide = (uci, backward): animate that move (forward) or its undoing (backward) when the board appears."""
    board = chess.Board(fen)
    last = chess.Move.from_uci(last_uci) if last_uci else None
    arrows = []
    if best_uci:
        bm = chess.Move.from_uci(best_uci)
        arrows.append(chess.svg.Arrow(bm.from_square, bm.to_square, color="#7fa650cc"))
    for uci, color in (extra_arrows or []):                      # e.g. the engine's 2nd and 3rd choices in other colours
        em = chess.Move.from_uci(uci)
        arrows.append(chess.svg.Arrow(em.from_square, em.to_square, color=color))
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
        svg = svg.replace("</svg>", g.replace("<g>", "<g class='badge-pop'>") + "</svg>")
    if slide:
        mv = chess.Move.from_uci(slide[0])
        svg = _animate_pieces(svg, _slide_pairs(mv, board, bool(slide[1])), flipped)
    return svg
