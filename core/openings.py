"""Opening names and "book" detection from a bundled position table (lichess chess-openings dataset, CC0)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import chess

_FILE = Path(__file__).resolve().parent.parent / "data" / "openings.json"


@lru_cache(maxsize=1)
def _book() -> dict:
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def lookup(board: chess.Board):
    """(eco, name) when this exact position is a known opening position, else None."""
    hit = _book().get(board.epd())
    return (hit[0], hit[1]) if hit else None


def is_book(board: chess.Board) -> bool:
    return board.epd() in _book()
