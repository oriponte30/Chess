"""Gives every position of every opening lesson at least three lines to follow.

Where a lesson has fewer than three prepared lines from a position (a quiet move with one continuation, or the end of a line), Stockfish
supplies the missing ones: reasonable alternatives that are not already in the lesson, with a short continuation and an evaluation.
The result is data/lesson_extra.json: {slug: {epd: [{"first": uci, "text": "4.Nf3 e6 5.Be2", "eval": "+0.30"}]}}.

    python scripts/build_lesson_extras.py [slug ...] [--depth 13] [--lines 3]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.engine import ParallelEngine                         # noqa: E402
from core.library import LIBRARY                               # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "lesson_extra.json"


def san_line(board: chess.Board, pv: list, plies: int = 6) -> str:
    b, parts = board.copy(), []
    for i, mv in enumerate(pv[:plies]):
        no = f"{b.fullmove_number}." if b.turn == chess.WHITE else (f"{b.fullmove_number}..." if i == 0 else "")
        parts.append(f"{no}{b.san(mv)}".strip())
        b.push(mv)
    return " ".join(parts)


def fmt_eval(line) -> str:
    if line.mate is not None:
        return f"M{abs(line.mate)}" if line.mate > 0 else f"-M{abs(line.mate)}"
    return f"{line.cp / 100:+.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--depth", type=int, default=13)
    ap.add_argument("--lines", type=int, default=3)
    a = ap.parse_args()
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    eng = ParallelEngine(workers=2)
    for tree in LIBRARY:
        if a.slugs and tree.slug not in a.slugs:
            continue
        jobs = []                                                   # (epd, board, first moves already taken, how many are missing)
        for epd, node in tree.by_epd.items():
            if node.alias is not None:
                continue
            have = tree.top_lines(node, a.lines)
            if len(have) >= a.lines:
                continue
            board = chess.Board()
            for u in node.path:
                board.push_uci(u)
            if board.is_game_over():
                continue
            if len(data.get(tree.slug, {}).get(epd, [])) >= a.lines - len(have):           # already done on an earlier run
                continue
            jobs.append((epd, board, {l[0].uci for l in have}, a.lines - len(have)))
        print(f"{tree.slug}: {len(jobs)} positions need engine lines", flush=True)
        results = eng.analyse_many([j[1] for j in jobs], a.depth, 7) if jobs else []
        out = dict(data.get(tree.slug, {}))
        for (epd, board, taken, need), lines in zip(jobs, results):
            best = lines[0].for_color(board.turn)
            pool = [l for l in lines if l.pv and l.pv[0].uci() not in taken]
            def loss(l):
                return best - l.for_color(board.turn)
            ranked = sorted(pool, key=loss)                         # sound alternatives first, then the least bad, so there are always enough
            picks = ranked[:need]
            out[epd] = [{"first": l.pv[0].uci(), "text": san_line(board, l.pv), "eval": fmt_eval(l)} for l in picks]
        data[tree.slug] = out
        short = [j[0] for j in jobs if len(out.get(j[0], [])) < j[3]]
        print(f"  filled {len(out)}; still short: {len(short)}", flush=True)
        OUT.write_text(json.dumps(data, separators=(",", ":")))
    eng.close() if hasattr(eng, "close") else None


if __name__ == "__main__":
    main()
