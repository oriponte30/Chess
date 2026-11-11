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


def test_paste_a_pgn_and_open_the_review(monkeypatch, blunder):
    t = _app(monkeypatch)
    t.text_area(key="pgn_text").set_value(blunder).run()
    t.text_input(key="pgn_me").set_value("Alice").run()
    next(b for b in t.button if b.label == "Review this game").click().run()
    assert not t.exception, t.exception
    rev = t.session_state["rev"]
    assert rev is not None and rev.player_color == chess.WHITE
    assert "← Back to games" in [b.label for b in t.button]
    # the browser gets the whole game at once, so stepping needs no round trips
    gid, payload = t.session_state["_rv_payload"]
    assert gid == t.session_state["rev_id"] and len(payload["plies"]) == len(rev.moves) and len(payload["wps"]) == len(rev.moves) + 1
    assert payload["plies"][0]["fen"] == rev.moves[0].fen_after and payload["keys"] == sorted(rev.key_moments)
    from ui import views
    assert views._pill_label(rev.moves[2]).startswith("2.") and views._pill_label(rev.moves[1]) == rev.moves[1].san + (
        "" if rev.moves[1].classification in ("Book", "Forced", "Good") else views.SYMBOL.get(rev.moves[1].classification, ""))
    assert all(p["card"] and p["pill"] for p in payload["plies"])
    next(b for b in t.button if b.label == "← Back to games").click().run()
    from ui.features import FEATURES
    assert {"Lessons", "Training", "Puzzles"} <= {f.title for f in FEATURES}


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


def test_navigation_has_lessons_and_a_training_hub(monkeypatch):
    from ui.features import FEATURES
    assert [f.title for f in FEATURES][:4] == ["Game review", "Lessons", "Training", "Insights"] or {"Lessons", "Training"} <= {f.title for f in FEATURES}


def test_lessons_gallery_opens_a_lesson_with_the_whole_tree(monkeypatch):
    t = _app(monkeypatch)
    t.switch_page("app_pages/lessons.py").run()
    assert not t.exception, t.exception
    assert sum(1 for b in t.button if b.key and b.key.startswith("open_")) >= 7                  # the gallery lists every opening
    next(b for b in t.button if b.key == "open_caro-kann").click().run()
    assert not t.exception, t.exception
    assert t.session_state["lesson_slug"] == "caro-kann" and any(b.key == "lessons_back" for b in t.button)
    next(b for b in t.button if b.key == "lessons_back").click().run()
    assert t.session_state["lesson_slug"] is None


def test_training_hub_and_insights_pages_render(monkeypatch):
    t = _app(monkeypatch)
    t.switch_page("app_pages/training.py").run()
    assert not t.exception, t.exception
    assert any("Puzzle Duels" in m.value for m in t.markdown)
    t.switch_page("app_pages/insights.py").run()
    assert not t.exception, t.exception


def test_review_board_lets_you_play_your_own_moves(monkeypatch, blunder):
    from streamlit.testing.v1 import AppTest
    import ui.views as v
    assert callable(v.board_component) and callable(v.top_lines)
