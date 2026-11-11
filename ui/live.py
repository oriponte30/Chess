"""The browser-side components (Review, Puzzles, Lessons). Each is the shared toolkit in ui/assets (chess.js + a board drawn in SVG) plus
one small script, so stepping, moving and animating happen in the page without a round trip to the server. Python is asked only for
what needs it: Stockfish, saving results, and choosing what to show next."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import chess
import chess.svg
import streamlit as st

ASSETS = Path(__file__).resolve().parent / "assets"


@lru_cache(maxsize=1)
def _sprites() -> str:
    out = {}
    for sym, svg in chess.svg.PIECES.items():
        out[sym] = svg.replace('id="', 'data-id="')
    return json.dumps(out)


@lru_cache(maxsize=8)
def source(mode: str) -> str:
    """chess.js + sprites + shared toolkit + the script for one mode, as one ES module."""
    return "\n".join([(ASSETS / "chess.bundle.js").read_text(), f"const SPRITES = {_sprites()};", (ASSETS / "core.js").read_text(),
                      (ASSETS / f"{mode}.js").read_text()])


@lru_cache(maxsize=None)
def component(mode: str, *triggers: str):
    """The v2 component for a mode. Triggers are the events the page can send back to Python (e.g. 'engine', 'result')."""
    return st.components.v2.component(f"chess_coach_{mode}", js=source(mode), isolate_styles=False)


def run(mode: str, key: str, data: dict, *triggers: str):
    comp = component(mode)
    return comp(key=key, data=data, **{f"on_{t}_change": (lambda: None) for t in triggers})


def valid_fen(fen) -> bool:
    try:
        b = chess.Board(str(fen))
        return b.is_valid()
    except (ValueError, TypeError):
        return False
