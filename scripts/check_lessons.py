"""Asks Stockfish to sanity-check every opening lesson: no move in a prepared line may lose much by the engine's measure, and no line may end in a
position that is clearly lost for either side.

    python scripts/check_lessons.py [slug ...] [--depth 12] [--loss 150] [--end 200]

A 'loss' is how many centipawns the move gave up compared with the best move in the position before it (from the mover's point of view)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.engine import StockfishEngine                       # noqa: E402
from core.library import LIBRARY                              # noqa: E402


def nodes_of(tree):
    seen, stack = [], [tree.root]
    while stack:
        n = stack.pop()
        seen.append(n)
        stack.extend(n.children)
    return seen


def check(tree, eng, depth: int, max_loss: int, max_end: int) -> list:
    problems = []
    cache = {}

    def best_cp(board):
        """Evaluation for the side to move."""
        key = board.epd()
        if key not in cache:
            line = eng.analyse(board, depth, 1)[0]
            cache[key] = line.for_color(board.turn)
        return cache[key]

    for n in nodes_of(tree):
        if not n.san:
            continue
        board = chess.Board()
        for u in n.parent.path:
            board.push_uci(u)
        before = best_cp(board)                       # for the mover
        board.push_uci(n.uci)
        after = -best_cp(board) if not board.is_game_over() else 0       # for the mover
        loss = before - after
        mover = "White" if n.ply % 2 else "Black"
        if loss > max_loss:
            problems.append(f"{tree.slug}: {n.label} {n.san} loses {loss}cp ({mover}) after {' '.join(n.parent.path[-4:])}")
        if not n.children:
            white_cp = best_cp(board) if board.turn == chess.WHITE else -best_cp(board)
            if abs(white_cp) > max_end:
                problems.append(f"{tree.slug}: line ends at {n.label} {n.san} with eval {white_cp:+d} (white's view)")
    return problems


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--loss", type=int, default=150)
    ap.add_argument("--end", type=int, default=250)
    a = ap.parse_args()
    eng = StockfishEngine(hash_mb=64)
    bad = 0
    for t in LIBRARY:
        if a.slugs and t.slug not in a.slugs:
            continue
        probs = check(t, eng, a.depth, a.loss, a.end)
        print(f"{t.slug}: {t.count()} positions, {len(probs)} problems")
        for p in probs:
            print("   ", p)
        bad += len(probs)
    eng.close()
    sys.exit(1 if bad else 0)
