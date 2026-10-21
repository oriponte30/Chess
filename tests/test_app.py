from pathlib import Path

import chess
from streamlit.testing.v1 import AppTest

from core import chesscom, service
from fake_engine import FakeEngine
from test_data_layer import PGN, raw


def _app(monkeypatch):
    monkeypatch.setattr(service, "make_engine", lambda: FakeEngine())
    t = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=60)
    t.run()
    assert not t.exception, t.exception
    return t


def test_paste_a_pgn_and_step_through_the_review(monkeypatch, blunder):
    t = _app(monkeypatch)
    t.text_area(key="pgn_text").set_value(blunder).run()
    t.text_input(key="pgn_me").set_value("Alice").run()
    next(b for b in t.button if b.label == "Review this game").click().run()
    assert not t.exception, t.exception
    rev = t.session_state["rev"]
    assert rev is not None and rev.player_color == chess.WHITE
    labels = [b.label for b in t.button]
    assert "← Back to games" in labels and any(b.key == "nav_next" for b in t.button)
    next(b for b in t.button if b.key == "nav_next").click().run()
    assert t.session_state["ply"] == 1 and not t.exception, t.exception
    next(b for b in t.button if b.key == "nav_last").click().run()
    assert t.session_state["ply"] == len(rev.moves)
    next(b for b in t.button if b.key == "nav_pk").click().run()                         # previous key moment
    assert t.session_state["ply"] in rev.key_moments
    t.session_state["ply_pick"] = 3                                                      # what clicking move 3 in the list does
    from ui import views
    import streamlit as st
    assert views._pill_label(rev.moves[2]).startswith("2.") and views._pill_label(rev.moves[1]) == rev.moves[1].san + (
        "" if rev.moves[1].classification in ("Book", "Forced", "Good") else views.SYMBOL.get(rev.moves[1].classification, ""))
    next(b for b in t.button if b.label == "← Back to games").click().run()
    assert t.session_state["rev"] is None and not t.exception


def test_load_games_then_review_one(monkeypatch):
    games = [chesscom.parse_game(raw(), "bob")]
    monkeypatch.setattr(chesscom, "recent_games", lambda u, limit=20, session=None: games)
    t = _app(monkeypatch)
    t.text_input(key="user_input").set_value("Bob").run()
    next(b for b in t.button if b.label == "Load my games").click().run()
    assert t.session_state["username"] == "bob" and not t.exception, t.exception
    next(b for b in t.button if b.key == "rv_123456789").click().run()
    assert t.session_state["rev"] is not None and t.session_state["rev"].player_color == chess.BLACK, t.exception
    next(b for b in t.button if b.label == "← Back to games").click().run()
    assert any(b.label == "Open ✓" for b in t.button)                              # it was saved


def test_friendly_error_for_an_unknown_user(monkeypatch):
    def boom(u, limit=20, session=None):
        raise chesscom.ChessComError("chess.com has no player with that username.")
    monkeypatch.setattr(chesscom, "recent_games", boom)
    t = _app(monkeypatch)
    t.text_input(key="user_input").set_value("nobody123").run()
    next(b for b in t.button if b.label == "Load my games").click().run()
    assert any("no player" in e.value for e in t.error) and not t.exception


def test_bad_pgn_shows_an_error_not_a_crash(monkeypatch):
    t = _app(monkeypatch)
    t.text_area(key="pgn_text").set_value("this is not chess").run()
    next(b for b in t.button if b.label == "Review this game").click().run()
    assert any("PGN" in e.value for e in t.error) and not t.exception
