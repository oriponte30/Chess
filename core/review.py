"""Game review: turns Stockfish evaluations into win-probability losses, move labels and accuracy scores.

Everything here is pure logic on top of an `Analyser` (see engine.py), so it is fully testable with a scripted engine.

How a move is judged
  * Each position is analysed once with the two best lines (MultiPV 2).
  * The evaluation before the move (best line) and after it (the played move) become win probabilities for the mover; the
    drop is the move's "loss": Best 0-0.5 | Excellent -2 | Good -5 | Inaccuracy -10 | Mistake -25 | Blunder > 25 (points of win%).
  * Brilliant needs a real sacrifice + still sound + the only good path + it looked worse at a shallow search.
  * Great = the only move that keeps the position (the second-best line is much worse) and not a plain recapture.
  * Missed Win = a forced mate you didn't play, or a clearly winning position that you let slip.
  * Book moves (known opening positions) and forced moves are not counted in the accuracy.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass, field

import chess
import chess.pgn

from . import openings
from .engine import MATE_CP

VALUE = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
PIECE_NAME = {chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop", chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king"}

# classification thresholds, in points of win probability lost
EXCELLENT, GOOD, INACCURACY, MISTAKE, BLUNDER = 2.0, 5.0, 10.0, 25.0, 25.0
BEST_TOLERANCE = 0.5          # within this of the engine's choice still counts as "Best"
GREAT_GAP = 15.0              # the second-best move must be this much worse for a move to be "the only move"
BRILLIANT_GAP = 10.0
SHALLOW_DEPTH = 5
MISSED_WIN_BEFORE, MISSED_WIN_AFTER = 80.0, 70.0
MAX_BOOK_PLY = 40

CLASSES = ["Brilliant", "Great", "Best", "Excellent", "Good", "Book", "Forced", "Inaccuracy", "Mistake", "Blunder", "Missed Win"]
SYMBOL = {"Brilliant": "!!", "Great": "!", "Best": "★", "Excellent": "✓", "Good": "", "Book": "📖", "Forced": "▫",
          "Inaccuracy": "?!", "Mistake": "?", "Blunder": "??", "Missed Win": "✗"}
COLOR = {"Brilliant": "#1baca6", "Great": "#5c8bb0", "Best": "#7fa650", "Excellent": "#8cb85a", "Good": "#9aa78c", "Book": "#a88865",
         "Forced": "#8b8b8b", "Inaccuracy": "#e6a23c", "Mistake": "#e58f2a", "Blunder": "#d64545", "Missed Win": "#c0392b"}


# --------------------------------------------------------------------------------------------------------------------
# win probability and accuracy
# --------------------------------------------------------------------------------------------------------------------
def win_prob(cp: float) -> float:
    """Win chance (0-100) for the side the centipawn score favours: 50 + 50 * (2 / (1 + e^(-0.00368208 * cp)) - 1)."""
    cp = max(-MATE_CP, min(MATE_CP, cp))
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def move_accuracy(loss: float) -> float:
    """Accuracy of one move from the win probability it threw away. Perfect play = 100.
    Uses the exponential curve from Lichess instead of a plain `100 - loss`, which is far too forgiving (a 25-point blunder
    would still score 75%)."""
    return max(0.0, min(100.0, 103.1668 * math.exp(-0.04354 * max(0.0, loss)) - 3.1669))


def game_accuracy(accs: list, volatility: list) -> float | None:
    """Volatility-weighted mean blended with the harmonic mean (so one disaster still hurts)."""
    if not accs:
        return None
    wsum = sum(volatility)
    weighted = sum(a * w for a, w in zip(accs, volatility)) / wsum if wsum else sum(accs) / len(accs)
    harmonic = len(accs) / sum(1 / max(a, 1.0) for a in accs)
    return round((weighted + harmonic) / 2, 1)


# --------------------------------------------------------------------------------------------------------------------
# material and sacrifices
# --------------------------------------------------------------------------------------------------------------------
def material(board: chess.Board, color: bool) -> int:
    return sum(VALUE[p.piece_type] for p in board.piece_map().values() if p.color == color)


def _diff(board: chess.Board, color: bool) -> int:
    return material(board, color) - material(board, not color)


def _noisy(board: chess.Board):
    moves = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
    def key(m):
        victim = board.piece_type_at(m.to_square) or chess.PAWN
        att = board.piece_type_at(m.from_square) or chess.PAWN
        return -(VALUE[victim] * 10 - VALUE[att]) - (50 if m.promotion else 0)
    return sorted(moves, key=key)


def _qsearch(board: chess.Board, alpha: int, beta: int, depth: int) -> int:
    stand = _diff(board, board.turn)
    if stand >= beta:
        return beta
    if depth == 0:
        return stand
    alpha = max(alpha, stand)
    for m in _noisy(board):
        board.push(m)
        score = -_qsearch(board, -beta, -alpha, depth - 1)
        board.pop()
        if score >= beta:
            return beta
        alpha = max(alpha, score)
    return alpha


def exchange_result(board: chess.Board, move: chess.Move, depth: int = 6) -> int:
    """Material the mover is up (+) or down (-) after `move` and the capture exchanges that follow it, compared with before
    the move. Negative = the move costs material by force."""
    mover = board.turn
    before = _diff(board, mover)
    board.push(move)
    try:
        after = -_qsearch(board, -10_000, 10_000, depth)
    finally:
        board.pop()
    return after - before


def is_sacrifice(board: chess.Board, move: chess.Move) -> bool:
    """Gives up at least two points of material (a minor piece for a pawn or worse) by force."""
    return exchange_result(board, move) <= -2


def phase_of(board: chess.Board) -> str:
    non_pawn = sum(VALUE[p.piece_type] for p in board.piece_map().values() if p.piece_type not in (chess.PAWN, chess.KING))
    if board.fullmove_number <= 10 and non_pawn >= 50:
        return "opening"
    return "endgame" if non_pawn <= 24 else "middlegame"


# --------------------------------------------------------------------------------------------------------------------
# data model
# --------------------------------------------------------------------------------------------------------------------
@dataclass
class MoveReview:
    ply: int                       # 1 = White's first move
    move_no: int
    color: bool                    # chess.WHITE / chess.BLACK
    san: str
    uci: str
    fen_before: str
    fen_after: str
    classification: str = "Good"
    loss: float = 0.0              # win probability points thrown away (0 for the engine's choice)
    accuracy: float = 100.0
    wp_before: float = 50.0        # mover's win chance before the move (best play)
    wp_after: float = 50.0         # mover's win chance after the move actually played
    cp_after: int = 0              # evaluation after the move, White's point of view
    best_uci: str = ""
    best_san: str = ""
    best_pv_san: list = field(default_factory=list)
    best_mate: int | None = None   # mate distance for the mover if he had one (positive = mover mates)
    kept_mate: bool = False
    mate_after: int | None = None  # mate distance after the move from the mover's view (negative = he can be mated)
    second_wp: float | None = None
    sacrifice: bool = False
    recapture: bool = False
    phase: str = "middlegame"
    clock: float | None = None     # seconds left on the mover's clock after the move
    themes: list = field(default_factory=list)
    explanation: str = ""
    counted: bool = True           # False for book and forced moves


@dataclass
class GameReview:
    white: str = "White"
    black: str = "Black"
    white_elo: int | None = None
    black_elo: int | None = None
    result: str = "*"
    termination: str = ""
    time_control: str = ""
    base_seconds: float | None = None
    date: str = ""
    url: str = ""
    opening: str = ""
    eco: str = ""
    depth: int = 14
    engine: str = "Stockfish"
    moves: list = field(default_factory=list)          # [MoveReview]
    evals: list = field(default_factory=list)          # [{"ply", "cp", "wp"}] White's point of view, ply 0 = start
    accuracy_white: float | None = None
    accuracy_black: float | None = None
    key_moments: list = field(default_factory=list)    # plies, chronological
    summary: str = ""
    verdict: dict = field(default_factory=dict)
    player_color: bool | None = None                   # whose game this is (None = both sides shown equally)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "GameReview":
        d = dict(d)
        moves = [MoveReview(**m) for m in d.pop("moves", [])]
        return GameReview(moves=moves, **d)

    def counts(self, color: bool) -> dict:
        out = {c: 0 for c in CLASSES}
        for m in self.moves:
            if m.color == color:
                out[m.classification] += 1
        return out


# --------------------------------------------------------------------------------------------------------------------
# classification of one move
# --------------------------------------------------------------------------------------------------------------------
def classify_loss(loss: float, is_top: bool = False) -> str:
    if is_top or loss <= BEST_TOLERANCE:
        return "Best"
    if loss <= EXCELLENT:
        return "Excellent"
    if loss <= GOOD:
        return "Good"
    if loss <= INACCURACY:
        return "Inaccuracy"
    if loss <= MISTAKE:
        return "Mistake"
    return "Blunder"


def _parse_base_seconds(tc: str) -> float | None:
    try:
        if not tc or tc in ("-", "?"):
            return None
        base = tc.split("+")[0]
        if "/" in base:
            base = base.split("/")[1]
        return float(base)
    except ValueError:
        return None


def _san_line(board: chess.Board, pv: list, n: int = 6) -> list:
    b = board.copy(stack=False)
    out = []
    for m in pv[:n]:
        if m not in b.legal_moves:
            break
        out.append(b.san(m))
        b.push(m)
    return out


def _volatility_weights(wps_white: list, n_moves: int) -> list:
    """Weight of each move = how much the win chance was swinging around it (quiet, decided positions count for less)."""
    w = max(2, min(8, len(wps_white) // 10))
    weights = []
    for i in range(n_moves):
        lo, hi = max(0, i - w // 2), min(len(wps_white), i + w // 2 + 2)
        seg = wps_white[lo:hi]
        sd = statistics.pstdev(seg) if len(seg) > 1 else 0.0
        weights.append(max(0.5, min(12.0, sd)))
    return weights


def analyze_game(game: chess.pgn.Game, engine, depth: int = 14, progress=None, player: str | None = None) -> GameReview:
    """Review a parsed PGN game. `progress(done, total)` is called after each position. `player` = the user's name (case
    insensitive) to pick which side the coach speaks to."""
    h = game.headers
    rev = GameReview(white=h.get("White", "White"), black=h.get("Black", "Black"), result=h.get("Result", "*"),
                     termination=h.get("Termination", ""), time_control=h.get("TimeControl", ""),
                     date=h.get("UTCDate", h.get("Date", "")).replace(".", "-"), url=h.get("Link", h.get("Site", "")), depth=depth,
                     engine=getattr(engine, "version", "Stockfish"))
    rev.base_seconds = _parse_base_seconds(rev.time_control)
    for key, attr in (("WhiteElo", "white_elo"), ("BlackElo", "black_elo")):
        try:
            setattr(rev, attr, int(h.get(key, "")))
        except ValueError:
            pass
    if player:
        if rev.white.lower() == player.lower():
            rev.player_color = chess.WHITE
        elif rev.black.lower() == player.lower():
            rev.player_color = chess.BLACK

    # ---- walk the game ---------------------------------------------------------------------------------------------
    board = game.board()
    boards, played, clocks = [board.copy()], [], []
    for node in game.mainline():
        played.append(node.move)
        clocks.append(node.clock())
        board = board.copy()
        board.push(node.move)
        boards.append(board.copy())
    n = len(played)
    if n == 0:
        return rev

    # ---- engine pass: every position once, two lines ---------------------------------------------------------------
    lines = []
    for i, b in enumerate(boards):
        lines.append(engine.analyse(b, depth, 2))
        if progress:
            progress(i + 1, len(boards))

    pos_wp_white = [win_prob(l[0].cp) for l in lines]
    rev.evals = [{"ply": i, "cp": max(-1500, min(1500, l[0].cp)), "wp": round(pos_wp_white[i], 1)} for i, l in enumerate(lines)]

    deepest_book = None
    for i, mv in enumerate(played):
        b = boards[i]
        color = b.turn
        after = boards[i + 1]
        L0 = lines[i][0]
        L1 = lines[i][1] if len(lines[i]) > 1 else None
        wp_before = win_prob(L0.for_color(color))
        second_wp = win_prob(L1.for_color(color)) if L1 is not None else None
        best_move = L0.pv[0] if L0.pv else None
        is_top = best_move == mv
        is_second = L1 is not None and L1.pv and L1.pv[0] == mv
        if is_top:
            wp_after = wp_before
        elif is_second:
            wp_after = second_wp
        else:
            wp_after = win_prob(lines[i + 1][0].for_color(color))
        loss = 0.0 if is_top else max(0.0, wp_before - wp_after)

        best_mate = L0.mate_for(color)
        best_mate = best_mate if (best_mate is not None and best_mate > 0) else None
        after_mate = lines[i + 1][0].mate_for(color)
        kept_mate = after_mate is not None and after_mate >= 0

        prev_cap_sq = played[i - 1].to_square if i > 0 and boards[i - 1].is_capture(played[i - 1]) else None
        recapture = prev_cap_sq is not None and mv.to_square == prev_cap_sq and b.is_capture(mv)
        legal_n = b.legal_moves.count()
        sac = exchange_result(b, mv) <= -2

        m = MoveReview(ply=i + 1, move_no=b.fullmove_number, color=color, san=b.san(mv), uci=mv.uci(), fen_before=b.fen(),
                       fen_after=after.fen(), loss=round(loss, 2), wp_before=round(wp_before, 1), wp_after=round(wp_after, 1),
                       cp_after=max(-1500, min(1500, lines[i + 1][0].cp)), best_uci=best_move.uci() if best_move else "",
                       best_san=b.san(best_move) if best_move else "", best_pv_san=_san_line(b, L0.pv),
                       best_mate=best_mate, kept_mate=kept_mate, mate_after=after_mate, second_wp=round(second_wp, 1) if second_wp is not None else None,
                       sacrifice=sac, recapture=recapture, phase=phase_of(b), clock=clocks[i])

        # ---- label -------------------------------------------------------------------------------------------------
        in_book = i < MAX_BOOK_PLY and openings.is_book(after)
        if in_book:
            deepest_book = after
        gap = (wp_before - second_wp) if second_wp is not None else None
        label = classify_loss(loss, is_top)

        if legal_n == 1:
            label = "Forced"
        elif in_book and loss <= GOOD:
            label = "Book"
        else:
            missed_mate = best_mate is not None and best_mate <= 8 and not is_top and not kept_mate
            missed_win = missed_mate or (loss >= INACCURACY and wp_before >= MISSED_WIN_BEFORE and wp_after < MISSED_WIN_AFTER)
            if missed_win and not is_top:
                label = "Missed Win"
            elif label in ("Best", "Excellent") and sac and wp_after >= 50 and (gap is None or gap >= BRILLIANT_GAP) and loss <= EXCELLENT:
                shallow = engine.analyse(after, SHALLOW_DEPTH, 1)[0]
                looked_bad = win_prob(lines[i + 1][0].for_color(color)) - win_prob(shallow.for_color(color)) >= 6.0
                mating = best_mate is not None and best_mate >= 2
                if looked_bad or mating:
                    label = "Brilliant"
            elif (label == "Best" and gap is not None and gap >= GREAT_GAP and 25 <= wp_before < 95 and not recapture
                  and not after.is_checkmate()):
                label = "Great"
        m.classification = label
        m.counted = label not in ("Book", "Forced")
        m.accuracy = round(move_accuracy(loss), 1) if m.counted else 100.0
        rev.moves.append(m)

    # ---- game level -------------------------------------------------------------------------------------------------
    if deepest_book is not None:
        hit = openings.lookup(deepest_book)
        if hit:
            rev.eco, rev.opening = hit
    weights = _volatility_weights(pos_wp_white, n)
    for color, attr in ((chess.WHITE, "accuracy_white"), (chess.BLACK, "accuracy_black")):
        idx = [k for k, m in enumerate(rev.moves) if m.color == color and m.counted]
        setattr(rev, attr, game_accuracy([rev.moves[k].accuracy for k in idx], [weights[k] for k in idx]))
    return rev


# --------------------------------------------------------------------------------------------------------------------
# key moments
# --------------------------------------------------------------------------------------------------------------------
def pick_key_moments(rev: GameReview, limit: int = 4) -> list:
    """Up to `limit` plies that decided the game, chronological. The player's own moves weigh a little more."""
    scored = []
    for m in rev.moves:
        if m.classification in ("Blunder", "Mistake", "Missed Win"):
            base = m.loss + (10 if m.classification == "Missed Win" else 0)
        elif m.classification == "Brilliant":
            base = 45.0
        elif m.classification == "Great":
            base = 20.0 + (m.wp_before - (m.second_wp or 0)) * 0.3
        else:
            continue
        mine = rev.player_color is None or m.color == rev.player_color
        scored.append((base * (1.0 if mine else 0.8), m.ply))
    scored.sort(reverse=True)
    return sorted(p for _, p in scored[:limit])
