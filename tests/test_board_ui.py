import re

import chess

from ui import views
from ui.board import board_svg


def _heights(html):
    return {k: float(v) for k, v in re.findall(r"class='([bw])' style='height:([\d.]+)%", html)}


def test_eval_bar_fills_white_when_white_is_winning_whichever_way_the_board_faces():
    for flipped in (False, True):
        h = _heights(views._eval_bar(80.0, flipped))
        assert h == {"w": 80.0, "b": 20.0}, (flipped, h)           # +big for White -> mostly white
        h = _heights(views._eval_bar(15.0, flipped))
        assert h == {"w": 15.0, "b": 85.0}, (flipped, h)
    # White's side of the board is at the bottom normally, at the top when the board is flipped
    assert views._eval_bar(70, False).index("class='b'") < views._eval_bar(70, False).index("class='w'")
    assert views._eval_bar(70, True).index("class='w'") < views._eval_bar(70, True).index("class='b'")


def test_moved_piece_gets_a_slide_animation_from_its_origin():
    b = chess.Board()
    b.push_san("e4")
    svg = board_svg(b.fen(), "e2e4", slide=("e2e4", False))
    assert "pslide" in svg and "--fx:195px;--fy:285px" in svg and "--tx:195px;--ty:195px" in svg      # e2 -> e4, white at the bottom
    back = board_svg(chess.Board().fen(), None, slide=("e2e4", True))                                  # undoing it: e4 -> e2
    assert "--fx:195px;--fy:195px" in back and "--tx:195px;--ty:285px" in back


def test_castling_slides_the_rook_too():
    b = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    b.push_san("O-O")
    svg = board_svg(b.fen(), "e1g1", slide=("e1g1", False))
    assert svg.count("pslide") == 2
