"""One call that does a whole review: cache lookup, engine pass, coach notes, storage."""
from __future__ import annotations

import io
import re
import atexit
import hashlib
import threading

import chess.engine
import chess.pgn

from . import chesscom, coach, review as rv, store
from .engine import ParallelEngine


_shared = None
_shared_lock = threading.Lock()


def make_engine():
    """The engine pool every review uses. It is created once and kept alive (starting Stockfish costs about a second), and it is a
    separate function so tests, or a future hosted engine, can swap it out."""
    global _shared
    with _shared_lock:
        if _shared is None:
            _shared = ParallelEngine(keep_alive=True)
            try:                                       # shut the Stockfish processes down when the app exits (before Python waits for threads)
                threading._register_atexit(reset_engine)
            except AttributeError:
                atexit.register(reset_engine)
        return _shared


def reset_engine():
    """Throw the shared pool away (used if an engine process died); the next review starts a fresh one."""
    global _shared
    with _shared_lock:
        old, _shared = _shared, None
    if old is not None:
        old.close()


def pgn_id(pgn: str) -> str:
    """Stable id for a pasted PGN: it depends on the moves only, so the same game pasted twice (even with other headers or clock
    comments) hits the cache."""
    try:
        game = chess.pgn.read_game(io.StringIO(pgn.strip()))
        moves = " ".join(m.uci() for m in game.mainline_moves()) if game is not None else ""
    except Exception:                                                  # noqa: BLE001
        moves = ""
    if not moves:
        moves = " ".join(re.sub(r"\{[^}]*\}", "", pgn).split())
    return "pgn" + hashlib.sha1(moves.encode()).hexdigest()[:14]


def review_game(pgn: str, depth: int = 14, username: str = "", game_id: str | None = None, progress=None,
                use_cache: bool = True) -> rv.GameReview:
    """Review one game (PGN text). Returns the stored review when it already exists at this depth."""
    gid = game_id or pgn_id(pgn)
    if use_cache:
        hit = store.load_review(gid, depth)
        if hit is not None:
            return hit
    game = chesscom.game_from_pgn(pgn)
    try:
        with make_engine() as eng:
            rev = rv.analyze_game(game, eng, depth=depth, progress=progress, player=username or None)
    except (chess.engine.EngineError, BrokenPipeError):          # an engine process died: start a fresh pool and try once more
        reset_engine()
        with make_engine() as eng:
            rev = rv.analyze_game(chesscom.game_from_pgn(pgn), eng, depth=depth, progress=progress, player=username or None)
    history = store.recent_history(username, exclude=gid) if username else []
    coach.annotate(rev, history=history)
    store.save_review(gid, depth, rev, username=username, fingerprint=coach.history_entry(rev) if rev.player_color is not None else None)
    return rev


def warm_up() -> None:
    """Start the engine pool in the background so the first review doesn't wait for Stockfish to launch."""
    import os
    if os.environ.get("CHESS_COACH_NO_WARMUP"):
        return
    def go():
        try:
            make_engine()
        except Exception:                                              # noqa: BLE001  (no Stockfish: the app shows its own message)
            pass
    threading.Thread(target=go, daemon=True).start()
