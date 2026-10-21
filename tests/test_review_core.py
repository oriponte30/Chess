import chess
import pytest

from core import chesscom, coach, review as rv
from fake_engine import FakeEngine


def test_win_probability_and_accuracy_curves():
    assert rv.win_prob(0) == pytest.approx(50)
    assert rv.win_prob(300) > rv.win_prob(100) > 50 > rv.win_prob(-100) > rv.win_prob(-300)
    assert rv.win_prob(300) + rv.win_prob(-300) == pytest.approx(100)
    assert rv.win_prob(10_000) > 99.9
    assert rv.move_accuracy(0) > 99.9
    assert rv.move_accuracy(5) > rv.move_accuracy(10) > rv.move_accuracy(25) > rv.move_accuracy(60)
    assert 0 <= rv.move_accuracy(100) <= 100


def test_game_accuracy_is_weighted_and_one_disaster_hurts():
    flat = rv.game_accuracy([100] * 10, [1] * 10)
    one_bad = rv.game_accuracy([100] * 9 + [10], [1] * 10)
    assert flat == pytest.approx(100, abs=0.2) and one_bad < 90
    assert rv.game_accuracy([], []) is None


@pytest.mark.parametrize("loss,top,label", [(0, True, "Best"), (0.3, False, "Best"), (1.5, False, "Excellent"), (3, False, "Good"),
                                           (7, False, "Inaccuracy"), (15, False, "Mistake"), (40, False, "Blunder")])
def test_loss_thresholds(loss, top, label):
    assert rv.classify_loss(loss, top) == label


def test_sacrifice_detection():
    italian = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3")
    assert rv.is_sacrifice(italian, chess.Move.from_uci("c4f7"))              # bishop for a pawn
    assert not rv.is_sacrifice(italian, chess.Move.from_uci("g1f3"))          # a normal developing move
    trade = chess.Board()
    for m in ("e2e4", "d7d5"):
        trade.push_uci(m)
    assert not rv.is_sacrifice(trade, chess.Move.from_uci("e4d5"))            # pawn takes pawn, queen recaptures: even


def test_tactic_detectors():
    hang = chess.Board("4k3/8/2p5/8/8/8/8/3QK3 w - - 0 1")
    victim = coach.hanging_after(hang, chess.Move.from_uci("d1d5"))
    assert victim and victim[0] == chess.QUEEN and victim[1] == "d5"
    assert coach.hanging_after(hang, chess.Move.from_uci("d1d2")) is None
    fork = chess.Board("r3k3/8/8/3N4/8/8/8/4K3 w - - 0 1")
    assert len(coach.fork_targets(fork, chess.Move.from_uci("d5c7"))) == 2
    disc = chess.Board("4q1k1/8/8/8/8/8/4N3/4RK2 w - - 0 1")
    assert coach.discovered_attack(disc, chess.Move.from_uci("e2c3"))
    assert not coach.discovered_attack(disc, chess.Move.from_uci("f1g1"))


def test_blunder_review_with_the_scripted_engine(blunder):
    game = chesscom.game_from_pgn(blunder)
    rev = rv.analyze_game(game, FakeEngine(), depth=2, player="alice")
    coach.annotate(rev)
    queen_move = rev.moves[4]                                                  # 3. Qxe5+
    assert queen_move.san == "Qxe5+" and queen_move.classification == "Blunder"
    assert queen_move.loss > 25 and "Hanging Pieces" in queen_move.themes
    assert "queen" in queen_move.explanation or "material" in queen_move.explanation
    assert rev.player_color == chess.WHITE and rev.accuracy_white < 90
    assert rev.verdict["focus"] == "Hanging Pieces" and "PUZZLE_TRIGGER" in rev.verdict["puzzle_trigger"]
    assert rev.verdict["action_tag"].endswith("DIFFICULTY: 1100]")
    assert rev.key_moments == [5] and "lost" in rev.summary


def test_review_survives_a_round_trip_through_json(blunder):
    rev = rv.analyze_game(chesscom.game_from_pgn(blunder), FakeEngine(), depth=2)
    again = rv.GameReview.from_dict(rev.to_dict())
    assert [m.san for m in again.moves] == [m.san for m in rev.moves] and again.accuracy_white == rev.accuracy_white


def test_tiers_and_wording():
    assert coach.tier_of(500) == "beginner" and coach.tier_of(800) == "club" and coach.tier_of(1500) == "advanced" and coach.tier_of(2300) == "master"
    assert coach.tier_of(None) == "club"
    m = rv.MoveReview(ply=1, move_no=1, color=True, san="Qh5", uci="d1h5", fen_before=chess.STARTING_FEN, fen_after=chess.STARTING_FEN,
                      classification="Missed Win", best_mate=4, best_san="Nh6+", best_uci="", wp_after=90)
    assert "calculate" in coach.explain(m, "master") and "checkmate in 4" in coach.explain(m, "beginner")
    assert "Always check" in coach.explain(m, "club")


def test_trends_need_a_pattern():
    hist = [{"phases": {"endgame": 2}, "themes": {"Endgame Technique": 2}, "accuracy": 70, "time_trouble": 1} for _ in range(5)]
    out = coach.trends(hist, "club")
    assert any("endgame" in s for s in out) and any("Endgame Technique" in s for s in out)
    assert coach.trends([], "club") == [] and coach.trends(hist[:1], "club") == []
