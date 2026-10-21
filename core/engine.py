"""Stockfish through UCI (python-chess). Anything with the same `analyse` method can stand in for it, which is how the tests run
without an engine binary."""
from __future__ import annotations

import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        if len(self._cache) > 5000:                          # a long-lived engine shouldn't grow without limit
            self._cache.clear()
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
        if not getattr(self, "keep_alive", False):
            self.close()


def default_workers() -> int:
    """How many engine processes to run side by side: one per CPU core, at most 4 (the hosted app has ~2 cores)."""
    try:
        cores = len(os.sched_getaffinity(0))
    except AttributeError:                                           # non-Linux
        cores = os.cpu_count() or 1
    return max(1, min(4, cores))


class ParallelEngine:
    """Several single-threaded Stockfish processes that split a game's positions between them. Roughly twice as fast as one process on
    two cores, and it keeps the same `analyse` method (plus `analyse_many`) so the rest of the code doesn't care."""

    def __init__(self, workers: int | None = None, path: str | None = None, hash_mb: int = 64, keep_alive: bool = False):
        n = workers or default_workers()
        self.keep_alive = keep_alive          # True = `with` doesn't shut the engines down (a shared, long-lived pool)
        self._engines = [StockfishEngine(path=path, threads=1, hash_mb=hash_mb) for _ in range(n)]
        self.version = self._engines[0].version
        self._free = list(self._engines)
        self._lock = threading.Lock()
        self._sem = threading.Semaphore(n)

    def _take(self):
        self._sem.acquire()
        with self._lock:
            return self._free.pop()

    def _give(self, eng):
        with self._lock:
            self._free.append(eng)
        self._sem.release()

    def analyse(self, board: chess.Board, depth: int, multipv: int = 1) -> list:
        eng = self._take()
        try:
            return eng.analyse(board, depth, multipv)
        finally:
            self._give(eng)

    def analyse_many(self, boards: list, depth: int, multipv: int = 1, progress=None) -> list:
        """Analyse every board (results in the same order). progress(done, total) is always called from the calling thread, which
        matters for Streamlit: its progress bar can't be updated from a worker thread."""
        total = len(boards)
        if len(self._engines) == 1:
            out = []
            for i, b in enumerate(boards):
                out.append(self.analyse(b, depth, multipv))
                if progress:
                    progress(i + 1, total)
            return out
        out = [None] * total
        with ThreadPoolExecutor(max_workers=len(self._engines)) as pool:
            futures = {pool.submit(self.analyse, b, depth, multipv): i for i, b in enumerate(boards)}
            for k, fut in enumerate(as_completed(futures), 1):
                out[futures[fut]] = fut.result()
                if progress:
                    progress(k, total)
        return out

    def close(self):
        for e in self._engines:
            e.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if not getattr(self, "keep_alive", False):
            self.close()
