"""Reads a player's recent games in the background, so the Insights page already has numbers for them before the player opens a single game.

One worker thread per player (a process-wide registry, so it keeps going when the page reruns). It takes the games newest first, skips the ones
that are already reviewed deeply enough, and calls the same `service.review_game` the Review page uses, so the results are shared: opening a
game the worker has finished is instant, and opening one it is in the middle of waits for it instead of analysing it twice.

Set CHESS_COACH_NO_BACKGROUND=1 to turn it off (the tests do)."""
from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field

from . import service, store

MAX_BACKGROUND_DEPTH = 14          # a deeper setting still reads the games at Standard depth; opening a game at Deep re-analyses just that one


@dataclass
class Job:
    username: str
    depth: int
    ids: set = field(default_factory=set)          # every game this job is responsible for
    pending: list = field(default_factory=list)    # GameInfo objects not yet reviewed (newest first)
    done: int = 0                                  # reviewed (or already stored)
    failed: int = 0
    current: str = ""
    error: str = ""
    running: bool = False
    started: float = 0.0
    finished: float = 0.0

    @property
    def total(self) -> int:
        return len(self.ids)

    @property
    def fraction(self) -> float:
        return self.done / self.total if self.total else 1.0


_jobs: dict = {}
_lock = threading.Lock()


def enabled() -> bool:
    return not os.environ.get("CHESS_COACH_NO_BACKGROUND")


def background_depth(selected: int) -> int:
    return max(8, min(selected, MAX_BACKGROUND_DEPTH))


def start(username: str, games: list, depth: int = 14) -> "Job | None":
    """Queue these games for the player. Games already reviewed at this depth (or deeper) count as done at once. Calling it again with a
    longer list just adds the new games; the worker is started only when it isn't already running."""
    username = (username or "").strip().lower()
    if not username or not games or not enabled():
        return None
    depth = background_depth(depth)
    have = store.reviewed_ids(username)
    with _lock:
        job = _jobs.get(username)
        if job is None or (not job.running and job.depth != depth):
            job = _jobs[username] = Job(username=username, depth=depth)
        for g in games:
            if g.game_id in job.ids:
                continue
            job.ids.add(g.game_id)
            if have.get(g.game_id, 0) >= job.depth:
                job.done += 1
            else:
                job.pending.append(g)
        if job.pending and not job.running:
            job.running, job.started, job.finished, job.error = True, time.time(), 0.0, ""
            threading.Thread(target=_work, args=(job,), daemon=True, name=f"bg-{username}").start()
        return _snapshot(job)


def status(username: str) -> "Job | None":
    """A copy of the player's job as it is right now (None when there never was one)."""
    with _lock:
        job = _jobs.get((username or "").strip().lower())
        return _snapshot(job) if job else None


def stop(username: str) -> None:
    with _lock:
        job = _jobs.get((username or "").strip().lower())
        if job:
            job.pending.clear()


def reset() -> None:
    """Forget every job (tests)."""
    with _lock:
        for j in _jobs.values():
            j.pending.clear()
        _jobs.clear()


def _snapshot(job: Job) -> Job:
    return Job(username=job.username, depth=job.depth, ids=set(job.ids), pending=list(job.pending), done=job.done, failed=job.failed,
               current=job.current, error=job.error, running=job.running, started=job.started, finished=job.finished)


def _work(job: Job) -> None:
    while True:
        with _lock:
            if not job.pending:
                job.running, job.current, job.finished = False, "", time.time()
                return
            g = job.pending.pop(0)
            job.current = g.game_id
        try:
            service.review_game(g.pgn, depth=job.depth, username=job.username, game_id=g.game_id)
            ok, err = True, ""
        except FileNotFoundError as e:                  # no Stockfish on this machine: nothing more can be done
            ok, err = False, str(e)
            with _lock:
                job.pending.clear()
        except Exception as e:                          # noqa: BLE001  (one bad game must not stop the others)
            ok, err = False, f"{type(e).__name__}: {e}"
        with _lock:
            if ok:
                job.done += 1
            else:
                job.failed += 1
                job.done += 1
                job.error = err
