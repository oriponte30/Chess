import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault('CHESS_COACH_NO_WARMUP', '1')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("CHESS_COACH_DB", str(tmp_path / "test.db"))


OPERA = """[Event "Opera"]
[White "Paul Morphy"]
[Black "Duke"]
[WhiteElo "2200"]
[BlackElo "1500"]
[Result "1-0"]
[Termination "Paul Morphy won by checkmate"]
[TimeControl "600"]

1. e4 {[%clk 0:09:58.1]} e5 {[%clk 0:09:57.0]} 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7 8. Nc3 c6 9. Bg5 b5
10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7 14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0
"""
BLUNDER = """[White "Alice"]
[Black "Bob"]
[WhiteElo "1100"]
[BlackElo "1050"]
[Result "0-1"]
[Termination "Bob won by resignation"]

1. e4 e5 2. Qh5 Nc6 3. Qxe5+ Nxe5 0-1
"""


@pytest.fixture
def opera():
    return OPERA


@pytest.fixture
def blunder():
    return BLUNDER


def real_engine_path():
    from core.engine import find_stockfish
    return find_stockfish()
