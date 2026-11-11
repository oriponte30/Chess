"""The puzzle library: loading data/puzzles.json, filtering by level and theme, picking the next puzzle and judging a move.

A puzzle is a position plus a solution line [S1, O1, S2, ...]: the solver (the side to move) plays S1, the opponent answers O1 and so on. The
solver's moves are checked here; the opponent's replies are played automatically. Any move that gives checkmate also counts as correct, because
a mate can often be delivered in more than one way. Built by scripts/build_puzzles.py (Stockfish finds and verifies them)."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import chess

_FILE = Path(__file__).resolve().parent.parent / "data" / "puzzles.json"

LEVELS = {
    1: {"name": "Beginner", "icon": "🌱", "blurb": "Mate in one, free pieces, simple forks."},
    2: {"name": "Intermediate", "icon": "🌿", "blurb": "Two-move combinations and clear tactical shots."},
    3: {"name": "Advanced", "icon": "🌳", "blurb": "Longer lines, quiet moves and sacrifices."},
    4: {"name": "Expert", "icon": "🏔️", "blurb": "Deep mates and multi-step combinations."},
}


@dataclass(frozen=True)
class Puzzle:
    id: str
    fen: str
    last: str                    # the opponent's last move (UCI), shown on the board so you can see what just happened
    moves: tuple                 # solver, opponent, solver, ... (UCI)
    themes: tuple
    level: int
    d: float = 0.0

    @property
    def side(self) -> bool:
        """The colour of the solver (the side to move in the starting position)."""
        return chess.Board(self.fen).turn

    @property
    def solver_moves(self) -> int:
        return (len(self.moves) + 1) // 2

    @property
    def level_name(self) -> str:
        return LEVELS[self.level]["name"]

    def board_at(self, step: int) -> chess.Board:
        """The position after the first `step` moves of the solution."""
        b = chess.Board(self.fen)
        for u in self.moves[:step]:
            b.push_uci(u)
        return b

    def solution_san(self) -> str:
        b = chess.Board(self.fen)
        out = []
        for u in self.moves:
            mv = chess.Move.from_uci(u)
            no = f"{b.fullmove_number}." if b.turn == chess.WHITE else (f"{b.fullmove_number}..." if not out else "")
            out.append(f"{no}{b.san(mv)}".strip())
            b.push(mv)
        return " ".join(out)


def _from_record(r: dict) -> Puzzle:
    return Puzzle(id=r["id"], fen=r["fen"], last=r.get("last", ""), moves=tuple(r["moves"]), themes=tuple(r.get("themes", ())),
                  level=int(r["level"]), d=float(r.get("d", 0)))


@lru_cache(maxsize=1)
def load() -> tuple:
    """Every puzzle in the library, easiest first (an empty tuple when the data file is missing)."""
    try:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    return tuple(_from_record(r) for r in data.get("puzzles", []))


@lru_cache(maxsize=1)
def by_id() -> dict:
    return {p.id: p for p in load()}


def themes(level: int | None = None) -> list:
    """[(theme, count)] for the puzzles of this level (all levels when None), most common first."""
    count: dict = {}
    for p in load():
        if level is None or p.level == level:
            for t in p.themes:
                count[t] = count.get(t, 0) + 1
    return sorted(count.items(), key=lambda kv: (-kv[1], kv[0]))


def pool(level: int | None = None, theme: str | None = None) -> list:
    return [p for p in load() if (level is None or p.level == level) and (not theme or theme in p.themes)]


def counts_by_level(results: dict | None = None) -> dict:
    """{level: (solved, total)}."""
    results = results or {}
    out = {}
    for lv in LEVELS:
        ps = [p for p in load() if p.level == lv]
        out[lv] = (sum(1 for p in ps if results.get(p.id)), len(ps))
    return out


def pick(candidates: list, results: dict | None = None, avoid: str | None = None, rng: random.Random | None = None) -> Puzzle | None:
    """A random puzzle from the candidates: unsolved ones first, and never the one you just had (unless it's the only one)."""
    rng = rng or random
    results = results or {}
    options = [p for p in candidates if p.id != avoid] or list(candidates)
    fresh = [p for p in options if not results.get(p.id)]
    chosen = fresh or options
    return rng.choice(chosen) if chosen else None


def judge(puz: Puzzle, step: int, uci: str) -> str:
    """How a move fares when `step` moves of the solution have been played (step is even: it's the solver's turn).
    Returns 'wrong', 'correct' (play on: the opponent now replies) or 'solved'."""
    board = puz.board_at(step)
    try:
        mv = chess.Move.from_uci(uci)
    except ValueError:
        return "wrong"
    if mv not in board.legal_moves:
        return "wrong"
    expected = puz.moves[step] if step < len(puz.moves) else None
    board.push(mv)
    if board.is_checkmate():
        return "solved"                                    # any mating move is fine
    if expected is None or uci != expected:
        return "wrong"
    return "solved" if step == len(puz.moves) - 1 else "correct"


def hint_square(puz: Puzzle, step: int) -> str:
    """The square of the piece to move (the first hint)."""
    return puz.moves[step][:2]
