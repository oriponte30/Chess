from core import insights as ins, service, store
from fake_engine import FakeEngine


def _facts():
    f = []
    for ph, acc, cls in (("opening", 95, "Best"), ("opening", 90, "Good"), ("opening", 92, "Best"), ("middlegame", 60, "Mistake"),
                         ("middlegame", 50, "Blunder"), ("middlegame", 80, "Good"), ("middlegame", 70, "Inaccuracy")):
        f.append({"phase": ph, "accuracy": acc, "classification": cls})
    return f


def test_phase_stats_always_has_all_three_phases():
    s = ins.phase_stats(_facts())
    assert list(s) == ["opening", "middlegame", "endgame"]
    assert s["endgame"] == {"acc": None, "n": 0, "bad": 0}                 # no endgame moves yet: still listed, not dropped
    assert s["opening"]["acc"] == 92.3 and s["middlegame"]["bad"] == 2


def test_coach_notes_name_a_concrete_focus_area():
    notes = ins.coach_notes(ins.phase_stats(_facts()), [], [])
    assert notes and notes[0]["title"] == "Focus on: the middlegame" and "blunder check" in notes[0]["text"]


def test_practice_positions_and_rows_come_from_stored_reviews(monkeypatch, blunder):
    monkeypatch.setattr(service, "make_engine", lambda: FakeEngine())
    service.review_game(blunder, depth=12, username="Alice", game_id="g1")
    rows = store.review_rows("alice")
    assert len(rows) == 1 and rows[0]["player_color"] == 1 and rows[0]["accuracy"] is not None
    ms = store.mistakes("alice")
    assert ms and all(m["best_uci"] and m["fen"] and m["loss"] >= 15 for m in ms)
    areas = ins.focus_areas(ms)
    assert areas and {"theme", "count", "cost", "tip"} <= set(areas[0])
    assert store.mistakes("nobody") == []
