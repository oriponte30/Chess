"""Builds data/puzzles.json: tactics puzzles that Stockfish finds in games it plays against itself at a low skill level (so the games
are full of mistakes and missed chances, like real club games).

    # 1. find candidate puzzles (run it a few times with different seeds, in parallel if you like)
    python scripts/build_puzzles.py find --games 200 --seed 1 --out /tmp/p1.jsonl
    # 2. merge, balance the four levels and write the data file
    python scripts/build_puzzles.py merge /tmp/p1.jsonl /tmp/p2.jsonl --out data/puzzles.json

A position becomes a puzzle when the side to move has ONE clearly best move: either a forced mate in 1-4, or a move that turns the game into a
clear win while every other move gives most of that away (win probability gap of 20+ points). Every candidate is re-checked at a deeper search,
and the follow-up moves of the solution are checked one by one, so the answers are not just a shallow guess."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import chess
import chess.engine

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import coach, review as rv                      # noqa: E402
from core.engine import StockfishEngine, find_stockfish   # noqa: E402

SCAN_DEPTH, CHECK_DEPTH = 12, 16
LEVELS = {1: "Beginner", 2: "Intermediate", 3: "Advanced", 4: "Expert"}


def wp(cp: float) -> float:
    return rv.win_prob(cp)


# ------------------------------------------------------------------------------------------------------------------------------------
# step 1: games with plenty of mistakes
# ------------------------------------------------------------------------------------------------------------------------------------
def play_game(player: chess.engine.SimpleEngine, scout: StockfishEngine, rng: random.Random) -> list:
    """A list of moves. The first few are varied on purpose (a random choice among Stockfish's top moves), the rest is a weak Stockfish."""
    board = chess.Board()
    player.configure({"Skill Level": rng.randint(6, 16)})
    opening_plies = rng.randint(4, 12)
    while not board.is_game_over(claim_draw=True) and len(board.move_stack) < rng.randint(90, 200):
        if len(board.move_stack) < opening_plies:
            lines = scout.analyse(board, 6, 4)
            weights = [0.45, 0.3, 0.15, 0.1][:len(lines)]
            move = rng.choices([l.pv[0] for l in lines if l.pv], weights=weights[:len([l for l in lines if l.pv])])[0]
        else:
            move = player.play(board, chess.engine.Limit(depth=rng.choice((4, 5, 6)))).move
        board.push(move)
    return list(board.move_stack)


# ------------------------------------------------------------------------------------------------------------------------------------
# step 2: look for positions with one clear answer
# ------------------------------------------------------------------------------------------------------------------------------------
def pv_ok(board: chess.Board, pv: list) -> list:
    """The prefix of the principal variation that is legal (it always should be)."""
    b, out = board.copy(stack=False), []
    for m in pv:
        if m not in b.legal_moves:
            break
        out.append(m)
        b.push(m)
    return out


def candidate(board: chess.Board, eng: StockfishEngine, depth: int):
    """('mate', n, first_line, second_line) / ('tactic', None, ...) / None for this position."""
    if board.is_game_over() or board.legal_moves.count() < 3:
        return None
    lines = eng.analyse(board, depth, 2)
    if len(lines) < 2 or not lines[0].pv:
        return None
    L1, L2, me = lines[0], lines[1], board.turn
    m1, m2 = L1.mate_for(me), L2.mate_for(me)
    if m1 is not None:
        if 1 <= m1 <= 4 and (m1 == 1 or not (m2 is not None and 1 <= m2 <= m1)):      # several mates in 1 are fine: any checkmate is accepted
            return ("mate", m1, L1, L2)
        return None
    if m2 is not None and m2 > 0:
        return None
    w1, w2 = wp(L1.for_color(me)), wp(L2.for_color(me))
    if w1 >= 70 and w1 - w2 >= 20 and w2 <= 65:
        return ("tactic", None, L1, L2)
    return None


def build_solution(board: chess.Board, kind: str, mate_in, L1, eng: StockfishEngine):
    """[S1, O1, S2, ...] as Move objects, ending with the solver's move, or None when the line can't be trusted."""
    pv = pv_ok(board, L1.pv)
    if kind == "mate":
        need = 2 * mate_in - 1
        if len(pv) < need:
            return None
        sol = pv[:need]
        b = board.copy(stack=False)
        for m in sol:
            b.push(m)
        return sol if b.is_checkmate() else None
    sol = pv[:5]
    if len(sol) % 2 == 0:
        sol = sol[:-1]
    # every later move of the solver must also be clearly the best one, otherwise the puzzle ends before it
    b = board.copy(stack=False)
    me = board.turn
    keep = 1
    b.push(sol[0])
    for j in range(1, len(sol), 2):
        b.push(sol[j])                                    # the opponent's reply
        if j + 1 >= len(sol):
            break
        if b.is_game_over():
            break
        lines = eng.analyse(b, SCAN_DEPTH, 2)
        if len(lines) < 2 or not lines[0].pv or lines[0].pv[0] != sol[j + 1]:
            break
        if wp(lines[0].for_color(me)) - wp(lines[1].for_color(me)) < 12 and lines[0].mate_for(me) is None:
            break
        b.push(sol[j + 1])
        keep = j + 2
    return sol[:keep]


def material_gain(board: chess.Board, sol: list) -> int:
    me = board.turn
    b = board.copy(stack=False)
    before = rv._diff(b, me)
    for m in sol:
        b.push(m)
    return rv._diff(b, me) - before


def themes_for(board: chess.Board, sol: list, kind: str, mate_in) -> list:
    me = board.turn
    out = []
    final = board.copy(stack=False)
    mine = []
    b = board.copy(stack=False)
    for i, m in enumerate(sol):
        if i % 2 == 0:
            mine.append((b.copy(stack=False), m))
        b.push(m)
    final = b
    first_b, first = mine[0]
    if kind == "mate":
        out.append(f"Mate in {mate_in}")
        ksq = final.king(final.turn)
        last = sol[-1]
        mover_pt = board.copy(stack=False)
        for m in sol[:-1]:
            mover_pt.push(m)
        piece = mover_pt.piece_type_at(last.from_square)
        back = chess.square_rank(ksq) == (0 if final.turn == chess.WHITE else 7)
        if back and piece in (chess.ROOK, chess.QUEEN):
            out.append("Back-rank mate")
        if piece == chess.KNIGHT:
            around = [final.piece_at(s) for s in chess.SquareSet(chess.BB_KING_ATTACKS[ksq])]
            if all(p is not None and p.color == final.turn for p in around):
                out.append("Smothered mate")
    else:
        gain = material_gain(board, sol)
        if gain >= 2:
            out.append("Win material")
    for bb, m in mine:
        if coach.fork_targets(bb, m) and "Fork" not in out:
            out.append("Fork")
        if coach.discovered_attack(bb, m) and "Discovered attack" not in out:
            out.append("Discovered attack")
        if m.promotion and "Promotion" not in out:
            out.append("Promotion")
    if rv.is_sacrifice(first_b, first):
        out.append("Sacrifice")
    elif first_b.is_capture(first) and rv.exchange_result(first_b, first) >= 3 and not first_b.gives_check(first):
        out.append("Free piece")
    if not first_b.is_capture(first) and not first_b.gives_check(first) and kind != "mate":
        out.append("Quiet move")
    if rv.phase_of(board) == "endgame":
        out.append("Endgame")
    return out


def difficulty(board: chess.Board, sol: list, kind: str, mate_in, themes: list, gap: float) -> float:
    n_me = (len(sol) + 1) // 2
    d = 0.9 * (n_me - 1)
    if kind == "mate":
        d += 0.75 * (mate_in - 1)
    if "Quiet move" in themes:
        d += 0.9
    if "Sacrifice" in themes:
        d += 1.1
    if "Fork" in themes or "Discovered attack" in themes:
        d += 0.45
    if "Smothered mate" in themes:
        d += 0.8
    if "Free piece" in themes:
        d -= 0.25
    if gap < 30 and kind == "tactic":
        d += 0.4
    if len(board.piece_map()) >= 26:
        d += 0.25
    return round(max(0.0, d), 2)


def level_of(d: float) -> int:
    return 1 if d < 0.8 else 2 if d < 1.9 else 3 if d < 3.2 else 4


def puzzle_id(fen: str) -> str:
    return hashlib.sha1(fen.encode()).hexdigest()[:8]


def find(args) -> None:
    sf = find_stockfish()
    if not sf:
        sys.exit("Stockfish not found (set STOCKFISH_PATH)")
    rng = random.Random(args.seed)
    player = chess.engine.SimpleEngine.popen_uci(sf)
    scout = StockfishEngine(sf, hash_mb=32)
    eng = StockfishEngine(sf, hash_mb=64)
    seen, made, t0 = set(), 0, time.time()
    out = open(args.out, "a", encoding="utf-8")
    for g in range(args.games):
        try:
            moves = play_game(player, scout, rng)
        except chess.engine.EngineError:
            continue
        board, per_game, last_made = chess.Board(), 0, -99
        for ply, mv in enumerate(moves):
            last = mv
            board.push(mv)
            if ply < 8 or per_game >= 5 or ply - last_made < 8 or board.epd() in seen:      # spread the puzzles of one game out
                continue
            cand = candidate(board, eng, SCAN_DEPTH)
            if cand is None:
                continue
            kind, mate_in, L1, L2 = cand
            deep = candidate(board, eng, CHECK_DEPTH)                  # the same position must still qualify at a deeper search
            if deep is None or deep[0] != kind or deep[1] != mate_in or deep[2].pv[0] != L1.pv[0]:
                continue
            sol = build_solution(board, kind, mate_in, deep[2], eng)
            if not sol:
                continue
            me = board.turn
            gap = wp(deep[2].for_color(me)) - wp(deep[3].for_color(me))
            themes = themes_for(board, sol, kind, mate_in)
            d = difficulty(board, sol, kind, mate_in, themes, gap)
            seen.add(board.epd())
            last_made = ply
            per_game += 1
            made += 1
            rec = {"id": puzzle_id(board.fen()), "fen": board.fen(), "last": last.uci(), "moves": [m.uci() for m in sol],
                   "themes": themes, "d": d, "level": level_of(d), "mate": mate_in or 0}
            out.write(json.dumps(rec) + "\n")
            out.flush()
        if (g + 1) % 5 == 0:
            print(f"[seed {args.seed}] {g + 1}/{args.games} games, {made} puzzles, {time.time() - t0:.0f}s", flush=True)
    player.quit()
    scout.close()
    eng.close()


# ------------------------------------------------------------------------------------------------------------------------------------
# step 3: balance the levels and write the data file
# ------------------------------------------------------------------------------------------------------------------------------------
def merge(args) -> None:
    pool, seen = [], set()
    for f in args.files:
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            key = chess.Board(r["fen"]).epd()
            if key in seen:
                continue
            seen.add(key)
            pool.append(r)
    rng = random.Random(7)
    by_level = {l: [p for p in pool if p["level"] == l] for l in LEVELS}
    for l, ps in by_level.items():
        print(f"level {l} ({LEVELS[l]}): {len(ps)} found")
    chosen = []
    for l, ps in by_level.items():
        rng.shuffle(ps)
        # keep the theme mix wide: at most 45% of a level may share one theme
        count, picked = {}, []
        cap = max(8, int(args.per_level * 0.45))
        for p in ps:
            key = p["themes"][0] if p["themes"] else "-"
            if count.get(key, 0) >= cap:
                continue
            count[key] = count.get(key, 0) + 1
            picked.append(p)
            if len(picked) >= args.per_level:
                break
        chosen += picked
    chosen.sort(key=lambda p: (p["level"], p["d"], p["id"]))
    Path(args.out).write_text(json.dumps({"v": 1, "puzzles": chosen}, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(chosen)} puzzles to {args.out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find")
    f.add_argument("--games", type=int, default=100)
    f.add_argument("--seed", type=int, default=1)
    f.add_argument("--out", required=True)
    m = sub.add_parser("merge")
    m.add_argument("files", nargs="+")
    m.add_argument("--out", required=True)
    m.add_argument("--per-level", type=int, default=150)
    a = ap.parse_args()
    find(a) if a.cmd == "find" else merge(a)
