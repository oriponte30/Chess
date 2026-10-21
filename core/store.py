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


_ready: set = set()


def _conn() -> sqlite3.Connection:
    p = _path()
    if p != ":memory:":
        Path(p).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p)
    if p not in _ready or p == ":memory:":                 # create the tables once per database, not on every call
        c.executescript(SCHEMA)
        _ready.add(p)
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


def move_facts(username: str, limit_games: int = 200) -> list:
    """Per-move rows (dicts) for the user's reviewed games, newest games first (player_color says which side the user played: 1 white, 0 black). The building block for stats, training and any other
    feature that wants to look across games instead of at one."""
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT f.game_id, f.depth, f.ply, f.color, f.san, f.classification, f.loss, f.accuracy, f.phase, f.clock, r.reviewed, "
            "json_extract(r.payload, '$.player_color') AS player_color "
            "FROM move_facts f JOIN reviews r ON r.game_id = f.game_id AND r.depth = f.depth "
            "WHERE r.username = ? AND r.game_id IN (SELECT game_id FROM reviews WHERE username = ? ORDER BY reviewed DESC LIMIT ?) "
            "ORDER BY r.reviewed DESC, f.game_id, f.ply", (username.lower(), username.lower(), limit_games)).fetchall()
    return [dict(r) for r in rows]


def review_rows(username: str, limit: int = 60) -> list:
    """One row per reviewed game (newest first, deepest review kept): who the user was, their accuracy, the opening and the result."""
    with _conn() as c:
        rows = c.execute(
            "SELECT game_id, depth, reviewed, json_extract(payload,'$.player_color'), json_extract(payload,'$.accuracy_white'), "
            "json_extract(payload,'$.accuracy_black'), json_extract(payload,'$.opening'), json_extract(payload,'$.result'), "
            "json_extract(payload,'$.white'), json_extract(payload,'$.black') "
            "FROM reviews WHERE username=? ORDER BY reviewed DESC, depth DESC", (username.lower(),)).fetchall()
    seen, out = set(), []
    for gid, depth, reviewed, color, aw, ab, opening, result, white, black in rows:
        if gid in seen:
            continue
        seen.add(gid)
        mine = aw if color == 1 else ab if color == 0 else None
        out.append({"game_id": gid, "depth": depth, "reviewed": reviewed, "player_color": color, "accuracy": mine,
                    "opening": opening or "", "result": result or "", "white": white or "", "black": black or ""})
    return out[:limit]


def mistakes(username: str, limit_games: int = 40, min_loss: float = 15.0) -> list:
    """The user's own serious mistakes across their latest reviewed games, ready to be turned into practice positions."""
    ids = [r["game_id"] for r in review_rows(username, limit_games)]
    out = []
    with _conn() as c:
        for gid in ids:
            row = c.execute("SELECT payload FROM reviews WHERE game_id=? AND username=? ORDER BY depth DESC LIMIT 1", (gid, username.lower())).fetchone()
            if not row:
                continue
            rev = json.loads(row[0])
            color = rev.get("player_color")
            if color is None:
                continue
            for m in rev.get("moves", []):
                if m["color"] == color and m["classification"] in ("Mistake", "Blunder", "Missed Win") and m["loss"] >= min_loss and m.get("best_uci"):
                    out.append({"game_id": gid, "ply": m["ply"], "fen": m["fen_before"], "played": m["san"], "played_uci": m["uci"],
                                "best_san": m["best_san"], "best_uci": m["best_uci"], "best_line": m.get("best_pv_san") or [],
                                "classification": m["classification"], "loss": m["loss"], "phase": m["phase"], "themes": m.get("themes") or [],
                                "explanation": m.get("explanation", ""), "opening": rev.get("opening", ""),
                                "opponent": rev["black"] if color == 1 else rev["white"]})
    return out
