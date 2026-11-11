"""Openings library, puzzles, background reading of games, remember-me cookie and the new insights helpers."""
import random
import time

import chess
import pytest

from core import background, chesscom, insights, library, puzzles, service, store
from fake_engine import FakeEngine
from test_data_layer import PGN, raw
from ui import remember


# ---------- openings library
def test_library_has_every_opening_and_each_has_versions():
    slugs = [t.slug for t in library.LIBRARY]
    assert {"italian", "vienna", "london", "queens-gambit", "caro-kann", "sicilian", "vs-sicilian"} <= set(slugs)
    assert len(set(slugs)) == len(slugs) and library.get("sicilian").side == "black" and library.get("vienna").side == "white"
    for t in library.LIBRARY:
        assert len(t.sections) >= 3, t.slug                      # several versions of every opening
        assert len(t.by_epd) > 40, t.slug


def test_every_section_starts_on_a_real_position():
    for t in library.LIBRARY:
        for sec in t.sections:
            assert t.node_at_san(sec["start"]) is not None, (t.slug, sec["id"])


# ---------- puzzles
def test_puzzle_data_is_legal_and_levelled():
    ps = puzzles.load()
    assert len(ps) >= 200 and len({p.id for p in ps}) == len(ps)
    assert all(puzzles.pool(lv) for lv in puzzles.LEVELS)
    for p in random.Random(3).sample(list(ps), 40):
        b = chess.Board(p.fen)
        assert p.moves and len(p.moves) % 2 == 1                  # solver moves first and last
        for u in p.moves:
            assert chess.Move.from_uci(u) in b.legal_moves
            b.push_uci(u)


def test_judge_accepts_the_solution_and_any_mate():
    p = next(x for x in puzzles.load() if len(x.moves) == 1)
    assert puzzles.judge(p, 0, p.moves[0]) == "solved" and puzzles.judge(p, 0, "zzzz") == "wrong"
    q = next(x for x in puzzles.load() if len(x.moves) >= 3)
    assert puzzles.judge(q, 0, q.moves[0]) == "correct"
    b = q.board_at(0)
    bad = next(m for m in b.legal_moves if m.uci() != q.moves[0])
    b.push(bad)
    assert not b.is_checkmate() and puzzles.judge(q, 0, bad.uci()) == "wrong" and puzzles.hint_square(q, 0) == q.moves[0][:2]


def test_pick_prefers_unsolved_and_avoids_repeat():
    ps = list(puzzles.pool(1))[:6]
    done = {p.id: True for p in ps[:5]}
    assert puzzles.pick(ps, done, rng=random.Random(1)).id == ps[5].id
    assert puzzles.pick(ps, {}, avoid=ps[0].id, rng=random.Random(1)).id != ps[0].id
    assert puzzles.pick([]) is None
    solved, total = puzzles.counts_by_level(done)[1]
    assert solved == 5 and total == len(puzzles.pool(1))


def test_puzzle_results_are_stored_and_a_solve_sticks():
    store.save_puzzle_result("alice", "p1", False, 2)
    assert store.puzzle_results("alice") == {"p1": False}
    store.save_puzzle_result("alice", "p1", True, 3)
    store.save_puzzle_result("alice", "p1", False, 1)
    assert store.puzzle_results("alice") == {"p1": True} and store.puzzle_results("bob") == {}


# ---------- background reading of games
def test_background_reads_games_and_skips_ones_already_done(monkeypatch):
    monkeypatch.delenv("CHESS_COACH_NO_BACKGROUND", raising=False)
    monkeypatch.setattr(service, "make_engine", lambda: FakeEngine())
    background.reset()
    games = [chesscom.parse_game(raw(url=f"https://www.chess.com/game/live/{i}"), "alice") for i in (101, 102, 103)]
    job = background.start("Alice", games, 2)
    assert job is not None and job.total == 3
    for _ in range(200):
        s = background.status("alice")
        if not s.running:
            break
        time.sleep(0.05)
    s = background.status("alice")
    assert not s.running and s.done == 3 and s.failed == 0 and s.fraction == 1
    assert set(store.reviewed_ids("alice")) == {"101", "102", "103"}
    again = background.start("alice", games, 2)                   # nothing left to do
    assert again.done == 3 and not again.running
    background.reset()


def test_background_is_off_in_tests_by_default():
    assert not background.enabled() and background.start("alice", [object()], 2) is None
    assert background.background_depth(30) <= 14


# ---------- remember me
def test_cookie_round_trip_and_bad_input():
    raw_v = remember.serialize("Alice", "⚖️ Standard", 30)
    got = remember.parse(raw_v)
    assert got["u"] == "alice" and got["n"] == 30
    for bad in (None, "", "%%%", "{}", '{"u":"a b; drop","d":0,"n":20}', '{"u":"ok_name","d":99,"n":999}'):
        out = remember.parse(bad)
        assert out.get("u", "ok_name") in ("ok_name",) and out.get("n", 20) <= 40


# ---------- insights helpers and store windows
def test_store_windows_filter_by_game_id(blunder):
    from core import coach, review as rv
    rev = rv.analyze_game(chesscom.game_from_pgn(blunder), FakeEngine(), depth=2, player="alice")
    coach.annotate(rev)
    for gid in ("a", "b", "c"):
        store.save_review(gid, 12, rev, "alice", fingerprint=coach.history_entry(rev))
    assert len(store.review_rows("alice", 60)) == 3
    assert {r["game_id"] for r in store.review_rows("alice", 60, game_ids={"a", "c"})} == {"a", "c"}
    assert store.load_review("a", 14) is None and store.load_review("a", 14, at_least=False) is None
    assert store.load_review("a", 8, at_least=True) is not None                # a deeper review serves a shallower request


def test_insight_summaries():
    rows = [
        {"result": "win", "color": "white", "opening": "Italian Game", "accuracy": 80},
        {"result": "loss", "color": "black", "opening": "Italian Game", "accuracy": 60},
        {"result": "draw", "color": "black", "opening": "Sicilian Defense", "accuracy": 70},
    ]
    rows = [{"result": "1-0", "player_color": 1, "opening": "Italian Game", "accuracy": 80},
            {"result": "1-0", "player_color": 0, "opening": "Italian Game", "accuracy": 60},
            {"result": "1/2-1/2", "player_color": 0, "opening": "Sicilian Defense", "accuracy": 70}]
    assert [insights.outcome(r) for r in rows] == ["win", "loss", "draw"] and insights.outcome({"result": "1-0"}) == ""
    split = insights.color_split(rows)
    assert split["white"]["wins"] == 1 and split["black"]["losses"] == 1 and split["black"]["draws"] == 1
    table = insights.opening_table(rows, limit=1)
    assert len(table) == 1 and table[0]["opening"] == "Italian Game" and table[0]["games"] == 2 and table[0]["score"] == 50
