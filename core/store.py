"""Where finished reviews live, so re-opening a game is instant and long-term trends can be computed.

SQLite by default (a file next to the app; set CHESS_COACH_DB to move it). On Streamlit Community Cloud that file is wiped
whenever the app restarts, which is fine for a cache but not for history: the schema is plain SQL, so pointing it at Postgres
later is a small change (see the README)."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

from .review import GameReview

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    game_id    TEXT NOT NULL,
    depth      INTEGER NOT NULL,
    username   TEXT NOT NULL DEFAULT '',
    reviewed   INTEGER NOT NULL,
    payload    TEXT NOT NULL,
    PRIMARY KEY (game_id, depth)
);
CREATE TABLE IF NOT EXISTS move_facts (
    game_id TEXT NOT NULL, depth INTEGER NOT NULL, ply INTEGER NOT NULL, color INTEGER NOT NULL, san TEXT NOT NULL,
    classification TEXT NOT NULL, loss REAL NOT NULL, accuracy REAL NOT NULL, phase TEXT NOT NULL, clock REAL,
    PRIMARY KEY (game_id, depth, ply)
);
CREATE TABLE IF NOT EXISTS history (
    game_id TEXT NOT NULL, username TEXT NOT NULL, reviewed INTEGER NOT NULL, entry TEXT NOT NULL,
    PRIMARY KEY (game_id, username)
);
"""


def _path() -> str:
    return os.environ.get("CHESS_COACH_DB") or str(Path(__file__).resolve().parent.parent / "data" / "coach.db")


def _conn() -> sqlite3.Connection:
    p = _path()
    if p != ":memory:":
        Path(p).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p)
    c.executescript(SCHEMA)
    return c


def save_review(game_id: str, depth: int, rev: GameReview, username: str = "", fingerprint: dict | None = None) -> None:
    now = int(time.time())
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO reviews VALUES (?,?,?,?,?)", (game_id, depth, username.lower(), now, json.dumps(rev.to_dict())))
        c.execute("DELETE FROM move_facts WHERE game_id=? AND depth=?", (game_id, depth))
        c.executemany("INSERT INTO move_facts VALUES (?,?,?,?,?,?,?,?,?,?)",
                      [(game_id, depth, m.ply, int(m.color), m.san, m.classification, m.loss, m.accuracy, m.phase, m.clock) for m in rev.moves])
        if fingerprint is not None and username:
            c.execute("INSERT OR REPLACE INTO history VALUES (?,?,?,?)", (game_id, username.lower(), now, json.dumps(fingerprint)))


def load_review(game_id: str, depth: int) -> GameReview | None:
    with _conn() as c:
        row = c.execute("SELECT payload FROM reviews WHERE game_id=? AND depth=?", (game_id, depth)).fetchone()
    return GameReview.from_dict(json.loads(row[0])) if row else None


def reviewed_ids(username: str) -> dict:
    """{game_id: depth} for the reviews already stored for this user."""
    with _conn() as c:
        rows = c.execute("SELECT game_id, MAX(depth) FROM reviews WHERE username=? GROUP BY game_id", (username.lower(),)).fetchall()
    return {g: d for g, d in rows}


def recent_history(username: str, limit: int = 10, exclude: str | None = None) -> list:
    """Per-game fingerprints (newest first) used for long-term profiling."""
    with _conn() as c:
        rows = c.execute("SELECT game_id, entry FROM history WHERE username=? ORDER BY reviewed DESC LIMIT ?",
                         (username.lower(), limit + 1)).fetchall()
    return [json.loads(e) for g, e in rows if g != exclude][:limit]
