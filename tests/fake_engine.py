"""A tiny stand-in engine: 2-ply material search. Enough to produce blunders, captures and mates without a Stockfish binary."""
import chess

from core.engine import MATE_CP, Line

V = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def _mat(board):
    return sum((V[p.piece_type] if p.color == chess.WHITE else -V[p.piece_type]) for p in board.piece_map().values())


def _score(board, depth):
    """Material from White's view after `depth` more plies of best play for both sides."""
    if board.is_checkmate():
        return -MATE_CP if board.turn == chess.WHITE else MATE_CP
    if depth == 0 or board.is_game_over():
        return _mat(board)
    vals = []
    for m in board.legal_moves:
        board.push(m)
        vals.append(_score(board, depth - 1))
        board.pop()
    return max(vals) if board.turn == chess.WHITE else min(vals)


class FakeEngine:
    version = "FakeFish 0"

    def __init__(self):
        self.calls = 0

    def analyse(self, board, depth, multipv=1):
        self.calls += 1
        if board.is_checkmate():
            return [Line(cp=-MATE_CP if board.turn == chess.WHITE else MATE_CP, mate=0)]
        if board.is_game_over():
            return [Line(cp=0)]
        scored = []
        for m in board.legal_moves:
            board.push(m)
            s = _score(board, 1)
            mate = 1 if board.is_checkmate() else None
            board.pop()
            scored.append((s, m, mate))
        scored.sort(key=lambda t: -t[0] if board.turn == chess.WHITE else t[0])
        out = []
        for s, m, mate in scored[:multipv]:
            mt = (mate if board.turn == chess.WHITE else -mate) if mate else None
            out.append(Line(cp=s, mate=mt, pv=[m], depth=depth))
        return out

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass
