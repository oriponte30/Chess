"""One call that does a whole review: cache lookup, engine pass, coach notes, storage."""
from __future__ import annotations

import io
import re
import hashlib

import chess.pgn

from . import chesscom, coach, review as rv, store
from .engine import StockfishEngine


def make_engine():
    """Separate function so tests (and a future hosted engine) can swap the engine out."""
    return StockfishEngine()


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
    with make_engine() as eng:
        rev = rv.analyze_game(game, eng, depth=depth, progress=progress, player=username or None)
    history = store.recent_history(username, exclude=gid) if username else []
    coach.annotate(rev, history=history)
    store.save_review(gid, depth, rev, username=username, fingerprint=coach.history_entry(rev) if rev.player_color is not None else None)
    return rev
