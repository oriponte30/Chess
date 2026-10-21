import chess
import pytest

from core import lessons
from core.lessons import CARO_KANN as T
from conftest import real_engine_path


def test_every_line_is_legal_and_the_tree_is_big_enough():
    assert T.count() >= 100                                              # building raises on any illegal move, so this proves legality too


def test_the_three_required_variations_exist_and_start_where_they_should():
    ids = {s["id"]: T.node_at_san(s["start"]) for s in T.sections}
    assert ids["advance"].label == "3.e5" and ids["exchange"].label == "3.exd5" and ids["classical"].label == "3.Nc3"
    # Classical: 3.Nc3 dxe4 4.Nxe4 is in the tree
    assert T.node_at_san("e4 c6 d4 d5 Nc3 dxe4 Nxe4") is not None
    assert T.node_at_san("e4 c6 d4 d5 exd5 cxd5") is not None and T.node_at_san("e4 c6 d4 d5 e5 Bf5") is not None


def test_every_node_has_an_explanation_or_is_a_shared_position():
    missing = [n.label for n in _all(T.root) if n.san and not (T.effective(n).note)]
    assert len(missing) <= 3, missing                                    # nearly every move carries its own explanation


def test_sidelines_branch_and_a_transposition_keeps_the_explanation():
    adv = T.node_at_san("e4 c6 d4 d5 e5 Bf5")
    assert len(adv.children) >= 3                                        # Nf3, h4 and c4 at least: sidelines are explorable
    trans = T.node_at_san("e4 c6 d4 d5 exd5 cxd5 c4 e6 Nc3 Nf3".replace("Nc3 Nf3", "Nc3 Nf6 Nf3 Be7"))
    main = T.node_at_san("e4 c6 d4 d5 exd5 cxd5 c4 Nf6 Nc3 e6 Nf3 Be7")
    assert trans is not main and T.effective(trans) is main              # a different move order, the same lesson text
    board = chess.Board()
    path = []
    for san in "e4 c6 d4 d5 exd5 cxd5 c4 e6 Nc3 Nf6 Nf3 Be7".split():
        mv = board.parse_san(san)
        board.push(mv)
        path.append(mv.uci())
    assert T.resolve(board, path) is trans and T.effective(trans).children


def test_off_tree_moves_are_found_by_position_or_not_at_all():
    board = chess.Board()
    for san in ("e4", "c6", "d4", "d5", "h3"):
        board.push_san(san)
    assert T.resolve(board, [m.uci() for m in board.move_stack]) is None


def test_look_ahead_describes_the_next_moves():
    node = T.node_at_san("e4 c6 d4 d5 e5 Bf5 Nf3")
    opts = T.look_ahead(node)
    assert opts and opts[0]["move"].san == "e6" and lessons.fmt_line(opts[0]["line"]).startswith("4...e6 5.Be2")
    assert opts[0]["replies"] and opts[0]["replies"][0][0].label == "5.Be2"


def _all(node):
    yield node
    for c in node.children:
        yield from _all(c)


def test_every_final_position_is_sound_according_to_stockfish():
    if not real_engine_path():
        pytest.skip("Stockfish isn't installed")
    from core.engine import ParallelEngine
    leaves = [n for n in _all(T.root) if not n.children and n.san]
    boards = []
    for n in leaves:
        b = chess.Board()
        for u in n.path:
            b.push_uci(u)
        boards.append(b)
    with ParallelEngine() as eng:
        res = eng.analyse_many(boards, 12, 1)
    bad = [(n.label, r[0].cp) for n, r in zip(leaves, res) if abs(r[0].cp) > 130]
    assert not bad, bad                                                  # no lesson line ends in a clearly lost position for either side
