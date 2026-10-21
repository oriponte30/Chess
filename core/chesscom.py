"""Reads a player's games from chess.com's free public API (no login, no key).

    https://api.chess.com/pub/player/<user>/games/archives      -> list of monthly archive URLs
    https://api.chess.com/pub/player/<user>/games/<YYYY>/<MM>   -> that month's games, each with its PGN

chess.com asks API users to send a descriptive User-Agent, so we do."""
from __future__ import annotations

import io
import re
from dataclasses import dataclass

import chess.pgn
import requests

API = "https://api.chess.com/pub/player"
HEADERS = {"User-Agent": "ChessCoach/1.0 (free open-source game reviewer; +https://github.com/)", "Accept": "application/json"}
TIMEOUT = 20


class ChessComError(Exception):
    """A problem worth showing to the user as-is (unknown user, no games, service unreachable)."""


@dataclass
class GameInfo:
    game_id: str
    url: str
    white: str
    black: str
    white_elo: int | None
    black_elo: int | None
    result: str                  # "1-0" / "0-1" / "1/2-1/2"
    time_class: str              # bullet / blitz / rapid / daily
    time_control: str
    end_time: int                # unix seconds
    pgn: str
    user_color: bool | None = None   # chess.WHITE / chess.BLACK when it is the searched user's game

    @property
    def opponent(self) -> str:
        return self.black if self.user_color == chess.WHITE else self.white if self.user_color == chess.BLACK else f"{self.white} vs {self.black}"

    @property
    def user_result(self) -> str:
        """'win' / 'loss' / 'draw' for the searched user (or '' when unknown)."""
        if self.result == "1/2-1/2":
            return "draw"
        if self.user_color is None or self.result not in ("1-0", "0-1"):
            return ""
        return "win" if (self.result == "1-0") == (self.user_color == chess.WHITE) else "loss"


def _get(url: str, session=None):
    try:
        r = (session or requests).get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:                           # noqa: PERF203
        raise ChessComError("Couldn't reach chess.com. Check your connection and try again.") from e
    if r.status_code == 404:
        raise ChessComError("chess.com has no player with that username.")
    if r.status_code == 429:
        raise ChessComError("chess.com is asking us to slow down. Wait a minute and try again.")
    if r.status_code >= 400:
        raise ChessComError(f"chess.com answered with an error ({r.status_code}). Try again shortly.")
    try:
        return r.json()
    except ValueError as e:
        raise ChessComError("chess.com sent something unexpected. Try again shortly.") from e


def _result(white: dict, black: dict) -> str:
    wr, br = white.get("result", ""), black.get("result", "")
    if wr == "win":
        return "1-0"
    if br == "win":
        return "0-1"
    return "1/2-1/2" if wr or br else "*"


def parse_game(raw: dict, username: str | None = None) -> GameInfo | None:
    """One game from the API's JSON, or None when it can't be reviewed (variants, no PGN)."""
    if raw.get("rules", "chess") != "chess" or not raw.get("pgn"):
        return None
    w, b = raw.get("white", {}), raw.get("black", {})
    url = raw.get("url", "")
    gid = re.sub(r"\D", "", url.rsplit("/", 1)[-1]) or url
    info = GameInfo(game_id=gid, url=url, white=w.get("username", "White"), black=b.get("username", "Black"),
                    white_elo=w.get("rating"), black_elo=b.get("rating"), result=_result(w, b), time_class=raw.get("time_class", ""),
                    time_control=raw.get("time_control", ""), end_time=int(raw.get("end_time", 0)), pgn=raw["pgn"])
    if username:
        u = username.lower()
        info.user_color = chess.WHITE if info.white.lower() == u else chess.BLACK if info.black.lower() == u else None
    return info


def recent_games(username: str, limit: int = 20, session=None) -> list:
    """The user's most recent reviewable games, newest first."""
    username = username.strip().lower()
    if not re.fullmatch(r"[a-z0-9_\-]{2,40}", username):
        raise ChessComError("That doesn't look like a chess.com username.")
    archives = _get(f"{API}/{username}/games/archives", session).get("archives", [])
    if not archives:
        raise ChessComError("That player has no public games yet.")
    games: list = []
    for url in reversed(archives):
        month = _get(url, session).get("games", [])
        for raw in sorted(month, key=lambda g: g.get("end_time", 0), reverse=True):
            g = parse_game(raw, username)
            if g is not None:
                games.append(g)
        if len(games) >= limit:
            break
    return games[:limit]


def read_pgn(text: str):
    """The first game in a pasted PGN, or None."""
    return chess.pgn.read_game(io.StringIO(text.strip()))


def game_from_pgn(pgn: str):
    """Parsed PGN game for a stored/pasted game; raises ValueError when it has no moves."""
    game = read_pgn(pgn)
    if game is None or not list(game.mainline_moves()):
        raise ValueError("That doesn't look like a PGN with moves in it.")
    return game
