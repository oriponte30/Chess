import chess
import pytest

from core import chesscom, coach, review as rv, service, store
from conftest import real_engine_path
from fake_engine import FakeEngine

PGN = '[White "Alice"]\n[Black "Bob"]\n[Result "1-0"]\n\n1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0\n'


def raw(**kw):
    base = {"url": "https://www.chess.com/game/live/123456789", "pgn": PGN, "time_class": "blitz", "time_control": "300", "end_time": 1_700_000_000,
            "rules": "chess", "white": {"username": "Alice", "rating": 1100, "result": "win"},
            "black": {"username": "Bob", "rating": 1050, "result": "checkmated"}}
    base.update(kw)
    return base


class Resp:
    def __init__(self, status, body):
        self.status_code, self._b = status, body

    def json(self):
        return self._b


class Session:
    def __init__(self, routes):
        self.routes, self.seen = routes, []

    def get(self, url, headers=None, timeout=None):
        self.seen.append((url, headers))
        return self.routes.get(url, Resp(404, {}))


def test_parse_game_reads_players_result_and_colour():
    g = chesscom.parse_game(raw(), "bob")
    assert g.game_id == "123456789" and g.result == "1-0" and g.user_color == chess.BLACK
    assert g.opponent == "Alice" and g.user_result == "loss" and g.white_elo == 1100
    assert chesscom.parse_game(raw(), "alice").user_result == "win"
    assert chesscom.parse_game(raw(rules="chess960"), "bob") is None and chesscom.parse_game(raw(pgn=""), "bob") is None
    draw = chesscom.parse_game(raw(white={"username": "Alice", "rating": 1, "result": "agreed"}, black={"username": "Bob", "rating": 1, "result": "agreed"}), "bob")
    assert draw.result == "1/2-1/2" and draw.user_result == "draw"


def test_recent_games_newest_first_and_skips_variants():
    arch = "https://api.chess.com/pub/player/bob/games/archives"
    s = Session({arch: Resp(200, {"archives": ["https://x/2024/01", "https://x/2024/02"]}),
                 "https://x/2024/01": Resp(200, {"games": [raw(end_time=1, url="https://c/game/live/1")]}),
                 "https://x/2024/02": Resp(200, {"games": [raw(end_time=5, url="https://c/game/live/5"), raw(end_time=9, url="https://c/game/live/9", rules="chess960"),
                                                           raw(end_time=7, url="https://c/game/live/7")]})})
    games = chesscom.recent_games("Bob", limit=10, session=s)
    assert [g.game_id for g in games] == ["7", "5", "1"]
    assert "ChessCoach" in s.seen[0][1]["User-Agent"]
    assert len(chesscom.recent_games("Bob", limit=2, session=s)) == 2


@pytest.mark.parametrize("status,msg", [(404, "no player"), (429, "slow down"), (500, "error")])
def test_friendly_errors(status, msg):
    s = Session({"https://api.chess.com/pub/player/bob/games/archives": Resp(status, {})})
    with pytest.raises(chesscom.ChessComError, match=msg):
        chesscom.recent_games("bob", session=s)
    with pytest.raises(chesscom.ChessComError, match="username"):
        chesscom.recent_games("???")


def test_pgn_helpers():
    assert len(list(chesscom.game_from_pgn(PGN).mainline_moves())) == 7
    with pytest.raises(ValueError):
        chesscom.game_from_pgn("hello")
    assert service.pgn_id(PGN) == service.pgn_id(PGN.replace("[White", "[Event \"x\"]\n[White"))


def test_store_round_trip_and_history(blunder):
    rev = rv.analyze_game(chesscom.game_from_pgn(blunder), FakeEngine(), depth=2, player="alice")
    coach.annotate(rev)
    store.save_review("g1", 12, rev, "Alice", fingerprint=coach.history_entry(rev))
    store.save_review("g2", 12, rev, "Alice", fingerprint={"themes": {"Forks": 1}})
    assert store.load_review("g1", 12).accuracy_white == rev.accuracy_white and store.load_review("g1", 14) is None
    assert store.reviewed_ids("alice") == {"g1": 12, "g2": 12}
    assert len(store.recent_history("alice")) == 2 and len(store.recent_history("alice", exclude="g1")) == 1


def test_service_uses_the_cache(monkeypatch, blunder):
    eng = FakeEngine()
    monkeypatch.setattr(service, "make_engine", lambda: eng)
    seen = []
    a = service.review_game(blunder, depth=2, username="alice", progress=lambda d, t: seen.append((d, t)))
    calls = eng.calls
    assert seen[-1][0] == seen[-1][1] and calls > 0
    b = service.review_game(blunder, depth=2, username="alice")
    assert eng.calls == calls and b.accuracy_white == a.accuracy_white           # second time comes from storage


@pytest.mark.skipif(real_engine_path() is None, reason="Stockfish is not installed")
def test_real_stockfish_finds_the_queen_sacrifice(opera):
    from core.engine import StockfishEngine
    game = chesscom.game_from_pgn(opera)
    with StockfishEngine() as eng:
        rev = rv.analyze_game(game, eng, depth=12, player="Paul Morphy")
    coach.annotate(rev, player_elo=2200)
    assert rev.opening and rev.eco.startswith("C")                              # Philidor
    sac = next(m for m in rev.moves if m.san == "Qb8+")
    assert sac.sacrifice and sac.best_mate == 2 and sac.classification in ("Brilliant", "Great", "Best")   # Brilliant with Stockfish 17
    assert rev.moves[-1].san == "Rd8#" and rev.moves[-1].classification != "Blunder"
    assert 70 <= rev.accuracy_white <= 100 and rev.accuracy_white > 0
    assert sac.classification != "Brilliant" or sac.ply in rev.key_moments
