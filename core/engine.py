"""Stockfish through UCI (python-chess). Anything with the same `analyse` method can stand in for it, which is how the tests run
without an engine binary."""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import chess
import chess.engine

MATE_CP = 10_000          # a forced mate counts as this many centipawns (minus the distance), so win-probability saturates


@dataclass
class Line:
    """One candidate line for the side to move."""
    cp: int                               # evaluation from WHITE's point of view, centipawns (mate mapped to +/- ~10000)
    mate: int | None = None               # moves to mate, from WHITE's point of view (positive = white mates), else None
    pv: list = field(default_factory=list)  # principal variation as chess.Move objects
    depth: int = 0

    def for_color(self, color: bool) -> int:
        return self.cp if color == chess.WHITE else -self.cp

    def mate_for(self, color: bool):
        """Mate distance from `color`'s point of view: positive = `color` mates, negative = `color` gets mated."""
        if self.mate is None:
            return None
        return self.mate if color == chess.WHITE else -self.mate


class Analyser(Protocol):
    def analyse(self, board: chess.Board, depth: int, multipv: int = 1) -> list: ...


def find_stockfish() -> str | None:
    """Path of a Stockfish binary: $STOCKFISH_PATH, PATH, the usual Debian/Ubuntu location, or ./bin."""
    env = os.environ.get("STOCKFISH_PATH")
    if env and Path(env).exists():
        return env
    for cand in (shutil.which("stockfish"), "/usr/games/stockfish", "/usr/bin/stockfish", "/usr/local/bin/stockfish"):
        if cand and Path(cand).exists():
            return cand
    for p in sorted((Path(__file__).resolve().parent.parent / "bin").glob("stockfish*")):
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return None


def _terminal(board: chess.Board) -> Line | None:
    if board.is_checkmate():
        # the side to move has been mated
        return Line(cp=-MATE_CP if board.turn == chess.WHITE else MATE_CP, mate=0)
    if board.is_game_over(claim_draw=False):
        return Line(cp=0)
    return None


class StockfishEngine:
    def __init__(self, path: str | None = None, threads: int = 1, hash_mb: int = 64):
        path = path or find_stockfish()
        if not path:
            raise FileNotFoundError("Stockfish was not found. Install it (apt: stockfish) or set STOCKFISH_PATH.")
        self.path = path
        self._eng = chess.engine.SimpleEngine.popen_uci(path)
        try:
            self._eng.configure({"Threads": threads, "Hash": hash_mb})
        except chess.engine.EngineError:
            pass
        self._cache: dict = {}
        self.version = self._eng.id.get("name", "Stockfish")

    def analyse(self, board: chess.Board, depth: int, multipv: int = 1) -> list:
        term = _terminal(board)
        if term is not None:
            return [term]
        key = (board.epd(), depth, multipv)
        if key in self._cache:
            return self._cache[key]
        n = min(multipv, board.legal_moves.count())
        infos = self._eng.analyse(board, chess.engine.Limit(depth=depth), multipv=n)
        if isinstance(infos, dict):
            infos = [infos]
        lines = []
        for info in infos:
            sc = info["score"].white()
            mate = sc.mate()
            lines.append(Line(cp=sc.score(mate_score=MATE_CP), mate=mate, pv=list(info.get("pv", [])), depth=info.get("depth", depth)))
        self._cache[key] = lines
        return lines

    def close(self):
        try:
            self._eng.quit()
        except Exception:                                    # noqa: BLE001
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
