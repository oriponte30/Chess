"""The coach: plain-English explanations tailored to the player's rating, recurring-weakness profiling and puzzle tags.

It is rule-based on purpose: the engine numbers already carry the truth, so the words are generated deterministically (free, instant,
no API key, and the same game always gets the same review). Everything that depends on the player's level lives in `TIERS`."""
from __future__ import annotations

from collections import Counter

import chess

from . import review as rv
from .review import GameReview, MoveReview, PIECE_NAME, VALUE

TIERS = [(0, 800, "beginner"), (800, 1500, "club"), (1500, 2000, "advanced"), (2000, 10_000, "master")]


def tier_of(elo: int | None) -> str:
    elo = elo or 1200
    return next(name for lo, hi, name in TIERS if lo <= elo < hi)


def wp_word(wp: float) -> str:
    return ("winning" if wp >= 90 else "clearly better" if wp >= 70 else "a bit better" if wp >= 57 else "about equal" if wp >= 43 else
            "a bit worse" if wp >= 30 else "clearly worse" if wp >= 12 else "close to lost")


def _name(pt: int | None) -> str:
    return PIECE_NAME.get(pt, "piece")


def _san_join(moves: list, n: int = 5) -> str:
    return " ".join(moves[:n])


# --------------------------------------------------------------------------------------------------------------------
# tactical patterns
# --------------------------------------------------------------------------------------------------------------------
def fork_targets(board: chess.Board, move: chess.Move) -> list:
    """Enemy pieces attacked at once by the piece that just moved (only if it makes real threats)."""
    b = board.copy(stack=False)
    mover = b.turn
    pt = b.piece_type_at(move.from_square)
    b.push(move)
    if pt is None or pt == chess.KING:
        return []
    out = []
    for sq in b.attacks(move.to_square):
        p = b.piece_at(sq)
        if p is None or p.color == mover or p.piece_type == chess.PAWN:
            continue
        if p.piece_type == chess.KING or VALUE[p.piece_type] > VALUE[pt] or not b.is_attacked_by(not mover, sq):
            out.append((p.piece_type, chess.square_name(sq)))
    return out if len(out) >= 2 else []


def discovered_attack(board: chess.Board, move: chess.Move) -> bool:
    """The move opens a line so that a *different* piece of ours now attacks something valuable."""
    mover = board.turn
    b = board.copy(stack=False)
    b.push(move)
    for sq, p in b.piece_map().items():
        if p.color == mover or (p.piece_type != chess.KING and VALUE[p.piece_type] < 3):
            continue
        before = {a for a in board.attackers(mover, sq)}
        after = {a for a in b.attackers(mover, sq) if a != move.to_square}
        new = after - before - {move.from_square}
        if any(b.piece_type_at(a) in (chess.BISHOP, chess.ROOK, chess.QUEEN) for a in new):
            return True
    return False


def hanging_after(board: chess.Board, move: chess.Move):
    """What the opponent can win for free after `move`: (piece_type, square_name, material_gain) or None."""
    b = board.copy(stack=False)
    b.push(move)
    best = None
    for m2 in list(b.legal_moves):
        if not b.is_capture(m2):
            continue
        gain = rv.exchange_result(b, m2)
        victim = b.piece_type_at(m2.to_square) if not b.is_en_passant(m2) else chess.PAWN
        if gain >= 2 and (best is None or gain > best[2]):
            best = (victim, chess.square_name(m2.to_square), gain)
    return best


def describe_move(board: chess.Board, move: chess.Move) -> str:
    """A short phrase for what a move does: 'captures the knight on f6', 'forks the rook and the queen', 'gives checkmate'."""
    b = board.copy(stack=False)
    pt = b.piece_type_at(move.from_square)
    forks = fork_targets(board, move)
    captured = b.piece_type_at(move.to_square) if b.is_capture(move) and not b.is_en_passant(move) else (chess.PAWN if b.is_en_passant(move) else None)
    gives_check = b.gives_check(move)
    b.push(move)
    if b.is_checkmate():
        return "delivers checkmate"
    if forks:
        names = " and the ".join(_name(t) for t, _ in forks[:2])
        return f"forks the {names} with the {_name(pt)}"
    if move.promotion:
        return f"promotes to a {_name(move.promotion)}"
    if board.is_castling(move):
        return "castles to safety"
    if captured is not None:
        return f"captures the {_name(captured)} on {chess.square_name(move.to_square)}" + (" with check" if gives_check else "")
    if gives_check:
        return "gives check and keeps the initiative"
    if discovered_attack(board, move):
        return "uncovers an attack with the piece behind it"
    sq = chess.square_name(move.to_square)
    if pt in (chess.KNIGHT, chess.BISHOP) and chess.square_rank(move.from_square) in (0, 7):
        return f"develops the {_name(pt)} to {sq}"
    return f"is the more accurate square for the {_name(pt)}: {sq}"


# --------------------------------------------------------------------------------------------------------------------
# themes (what kind of mistake was it?)
# --------------------------------------------------------------------------------------------------------------------
THEME_TIPS = {
    "Hanging Pieces": {"beginner": "Before every move, check: is anything of mine left unprotected, and can he capture it?",
                       "club": "Do a blunder check before you release the piece: what does the opponent's best capture win?",
                       "advanced": "Run a loose-pieces scan every move: undefended pieces and overloaded defenders are where your points go.",
                       "master": "Your hanging pieces come from tunnel vision on your own plan: re-scan the opponent's captures and checks first."},
    "Missed Mates": {"beginner": "When the enemy king looks exposed, list every check first: checks are forcing and easy to calculate.",
                     "club": "Make 'checks, captures, threats' a habit, and look at every check against the king before anything quiet.",
                     "advanced": "Calculate forcing lines to the very end before settling for material: write down the king's escape squares.",
                     "master": "Treat any king with fewer than three free squares as a mating candidate and exhaust the forcing tree."},
    "Forks": {"beginner": "Look for one piece that can attack two things at once, especially with your knights.",
              "club": "Before each move, ask where your knight could land to hit two pieces, and where his could land to hit yours.",
              "advanced": "Spot fork squares in advance: which squares attack two weaknesses, and can you force a piece there with check?",
              "master": "Fork squares usually arise from forcing zwischenzugs: look for the check that drags a piece onto the fork square."},
    "Discovered Attacks": {"beginner": "When a piece moves away and uncovers an attack from the piece behind it, you get two threats at once.",
                           "club": "Lined-up pieces (bishop or rook behind your own piece) are a loaded gun: move the front piece with a threat.",
                           "advanced": "Look for batteries and discoveries where the moving piece also makes a threat of its own.",
                           "master": "Prepare discoveries: place the front piece so that its move comes with tempo (check or capture)."},
    "Winning Material": {"beginner": "Before you play a quiet move, check whether you can capture something that is not protected.",
                         "club": "Scan every enemy piece: which are undefended or defended only by something worth more than they are?",
                         "advanced": "Re-count attackers and defenders on his loose pieces every move, including after his last move.",
                         "master": "Look for overloaded defenders and the exchange sacrifice that cashes in on them."},
    "Time Management": {"beginner": "Try to spend your time on the moves that matter: slow down when the position gets tense.",
                        "club": "Set a rule: no more than a quarter of your clock before move 15, then keep a reserve for tactics.",
                        "advanced": "Play the opening quickly from knowledge and save your thinking time for the first critical middlegame decision.",
                        "master": "Allocate time to critical moments: pre-decide candidate sets so late-game decisions take seconds."},
    "Endgame Technique": {"beginner": "In endgames, activate your king and push your passed pawns: they are your winning chances.",
                          "club": "Practise king and pawn endings and the basic rook-ending rules (rook behind passed pawns, active rook).",
                          "advanced": "Study technique: opposition, outside passed pawns, and when to trade into a won pawn ending.",
                          "master": "Drill theoretical endings (Lucena, Philidor, opposite bishops) so the conversion is automatic."},
    "Opening Principles": {"beginner": "Develop your knights and bishops, castle early and don't move the same piece twice without a reason.",
                           "club": "Learn the main line of your openings 8-10 moves deep and the ideas behind them, not just the moves.",
                           "advanced": "Review where you left your preparation: build a repertoire file with the lines you actually reach.",
                           "master": "Tighten your repertoire against the sidelines that cost you tempo or structure."},
    "Calculation": {"beginner": "Before you move, ask: what does this move allow? Then check his best reply.",
                    "club": "For each candidate, find the opponent's most dangerous reply and calculate it two or three moves deep.",
                    "advanced": "Practise structured calculation: candidates, then forcing lines, then evaluate the final position.",
                    "master": "Train long forcing lines and quiet-move calculation: set up positions and verify the whole line before moving."},
}
PUZZLE_THEME = {"Hanging Pieces": "Hanging Pieces", "Missed Mates": "Mate in 2-3", "Forks": "Forks", "Discovered Attacks": "Discovered Attacks",
                "Winning Material": "Win Material", "Time Management": "Quick Tactics", "Endgame Technique": "Endgame Tactics",
                "Opening Principles": "Opening Traps", "Calculation": "Calculation Practice"}


def time_trouble(m: MoveReview, rev: GameReview) -> bool:
    if m.clock is None:
        return False
    limit = max(15.0, 0.08 * rev.base_seconds) if rev.base_seconds else 20.0
    return m.clock < limit


def detect_themes(m: MoveReview, rev: GameReview) -> list:
    board = chess.Board(m.fen_before)
    mv = chess.Move.from_uci(m.uci)
    best = chess.Move.from_uci(m.best_uci) if m.best_uci else None
    themes = []
    if m.best_mate is not None and m.best_mate <= 6 and not m.kept_mate:
        themes.append("Missed Mates")
    elif hanging_after(board, mv):
        themes.append("Hanging Pieces")
    if best is not None and "Missed Mates" not in themes:
        forks = fork_targets(board, best)
        if forks:
            themes.append("Knight Forks" if board.piece_type_at(best.from_square) == chess.KNIGHT else "Forks")
        elif discovered_attack(board, best):
            themes.append("Discovered Attacks")
        elif board.is_capture(best) and rv.exchange_result(board, best) >= 2:
            themes.append("Winning Material")
    if time_trouble(m, rev):
        themes.append("Time Management")
    if not themes:
        themes.append({"endgame": "Endgame Technique", "opening": "Opening Principles"}.get(m.phase, "Calculation"))
    return themes


def _tip(theme: str, tier: str) -> str:
    key = "Forks" if theme == "Knight Forks" else theme
    return THEME_TIPS.get(key, THEME_TIPS["Calculation"])[tier]


# --------------------------------------------------------------------------------------------------------------------
# move explanations
# --------------------------------------------------------------------------------------------------------------------
def explain(m: MoveReview, tier: str, opening: str = "") -> str:
    board = chess.Board(m.fen_before)
    mv = chess.Move.from_uci(m.uci)
    best = chess.Move.from_uci(m.best_uci) if m.best_uci else None
    pt = board.piece_type_at(mv.from_square)
    c = m.classification
    line = _san_join(m.best_pv_san)

    if c == "Book":
        return f"A known opening move{f' in the {opening}' if opening else ''}."
    if c == "Forced":
        return "The only legal move."
    if c in ("Best", "Excellent", "Good"):
        word = {"Best": "The engine's top choice.", "Excellent": "Almost as good as the best move.", "Good": "A reasonable move."}[c]
        if c != "Best" and m.best_san and m.best_san != m.san:
            word += f" {m.best_san} was slightly stronger."
        return word
    if c == "Brilliant":
        mate = f"forces checkmate in {m.best_mate}" if m.best_mate else "keeps a sound position"
        what = f"You gave up your {_name(pt)} on {chess.square_name(mv.to_square)} on purpose, and it works: it {mate}"
        if tier == "beginner":
            return f"Brilliant! {what}. Real sacrifices like this are what chess is all about."
        if tier == "club":
            return f"Brilliant! {what}, and every other move was clearly worse. Spotting a sacrifice that works is a big step."
        gap = f" The alternatives drop to about {m.second_wp:.0f}% win chance." if m.second_wp is not None else ""
        return f"{what}.{gap}" + (f" Main line: {line}." if line else "")
    if c == "Great":
        if tier == "beginner":
            return f"Great find! {m.san} was the only move that kept your position in good shape."
        gap = f" Anything else drops you to {m.second_wp:.0f}% win chance." if m.second_wp is not None else ""
        what = "keeps your advantage" if m.wp_before >= 60 else "holds the position"
        return f"The only move that {what} ({wp_word(m.wp_after)} after it).{gap}"

    # ---- inaccuracy / mistake / blunder / missed win ----------------------------------------------------------------
    hang = hanging_after(board, mv)
    reason = ""
    if m.mate_after is not None and m.mate_after < 0:
        reason = f"it allows checkmate in {abs(m.mate_after)}"
    elif hang and VALUE.get(hang[0], 0) >= 1 and m.loss >= rv.INACCURACY:
        if tier == "beginner":
            reason = f"it leaves your {_name(hang[0])} on {hang[1]} unprotected, so it can just be captured"
        else:
            reason = f"it drops material: your {_name(hang[0])} on {hang[1]} can be won"
    elif m.wp_before - m.wp_after >= 5:
        if wp_word(m.wp_before) != wp_word(m.wp_after):
            reason = f"it lets the position slip from {wp_word(m.wp_before)} to {wp_word(m.wp_after)}"
        elif m.wp_before < 43:
            reason = "it makes a difficult position even harder"
        elif m.wp_before >= 57:
            reason = "it gives away part of your advantage"
        else:
            reason = "it loosens your grip on the position"
    better = ""
    if best is not None and m.best_san != m.san:
        better = f" {m.best_san} was better: it {describe_move(board, best)}."
        if tier in ("advanced", "master") and line:
            better += f" Main line: {line}."

    if c == "Missed Win":
        if m.best_mate:
            if tier == "beginner":
                tail = " but you still kept a strong position. Great job keeping the pressure!" if m.wp_after >= 70 else " and the win slipped away."
                return f"You missed a checkmate in {m.best_mate} here,{tail}{better}"
            if tier == "club":
                return f"Missed win: {m.best_san} forced mate in {m.best_mate}. Always check every check against the king before choosing a quiet move.{better if m.best_san != m.san else ''}"
            return (f"Missed win. You played {m.san}, but {m.best_san} forces mate in {m.best_mate}. At your level, you need to calculate "
                    f"these forced sequences to the end." + (f" Main line: {line}." if line else ""))
        base = f"You were {wp_word(m.wp_before)}, but {reason or 'this lets the win slip away'}."
        return base + better
    label = {"Inaccuracy": "A slightly inaccurate move", "Mistake": "A mistake", "Blunder": "A blunder"}[c]
    head = f"{label}: {reason}." if reason else f"{label}."
    if tier == "beginner" and c == "Blunder" and "unprotected" not in reason:
        head += " Take an extra second to check what your move allows."
    return head + better


# --------------------------------------------------------------------------------------------------------------------
# whole-game summary and verdict
# --------------------------------------------------------------------------------------------------------------------
def player_stats(rev: GameReview):
    color = rev.player_color
    return (color, rev.accuracy_white if color == chess.WHITE else rev.accuracy_black)


def _result_text(rev: GameReview, color) -> str:
    res = rev.result
    term = rev.termination
    how = ""
    low = term.lower()
    for key, txt in (("checkmate", "by checkmate"), ("resign", "by resignation"), ("time", "on time"), ("abandon", "by abandonment"),
                     ("stalemate", "by stalemate"), ("repetition", "by repetition"), ("agreement", "by agreement"), ("insufficient", "on insufficient material")):
        if key in low:
            how = " " + txt
            break
    if res == "1/2-1/2":
        return f"drew{how.replace('by ', 'by ') if how else ''}"
    if color is None:
        w = res == "1-0"
        return f"{'White' if w else 'Black'} won{how}" if res in ("1-0", "0-1") else "the result is unknown"
    won = (res == "1-0") == (color == chess.WHITE) and res in ("1-0", "0-1")
    lost = res in ("1-0", "0-1") and not won
    return f"{'won' if won else 'lost'}{how}" if (won or lost) else "the result is unknown"


def summarize(rev: GameReview, tier: str) -> str:
    color, acc = player_stats(rev)
    who = "You" if color is not None else "The game"
    outcome = _result_text(rev, color)
    if color is not None and acc is not None:
        style = "a very clean" if acc >= 90 else "a solid" if acc >= 80 else "a decent" if acc >= 65 else "a rough"
        first = f"You played {style} game ({acc:.0f}% accuracy) and {outcome}." if "unknown" not in outcome else f"You played {style} game ({acc:.0f}% accuracy)."
    else:
        first = f"{rev.white} ({_fmt(rev.accuracy_white)}%) vs {rev.black} ({_fmt(rev.accuracy_black)}%): {outcome}."
    moments = [m for m in rev.moves if m.ply in rev.key_moments]
    swing = {"Brilliant": 45.0, "Great": 15.0}
    turning = max(moments, key=lambda m: swing.get(m.classification, m.loss), default=None)
    if turning is None:
        second = {"beginner": "No big swings: keep checking your pieces are safe.", "club": "There were no big swings: a steady game.",
                  "advanced": "The game stayed balanced with no decisive error from either side.",
                  "master": "No decisive inaccuracy: the result came down to small positional margins."}[tier]
    else:
        who_moved = "you" if color is None or turning.color == color else "your opponent"
        who_moved = who_moved if color is not None else ("White" if turning.color else "Black")
        n = f"{turning.move_no}{'.' if turning.color else '...'}{turning.san}"
        verb = {"Brilliant": "found a brilliant sacrifice with", "Great": "found the only move with", "Blunder": "blundered with",
                "Mistake": "made a mistake with", "Missed Win": "missed a win with"}.get(turning.classification, "played")
        second = f"The game turned on move {turning.move_no}, when {who_moved} {verb} {n}."
    return f"{first} {second}"


def _fmt(x) -> str:
    return "-" if x is None else f"{x:.0f}"


def build_verdict(rev: GameReview, tier: str, history: list | None = None) -> dict:
    color = rev.player_color
    mine = [m for m in rev.moves if color is None or m.color == color]
    bad = [m for m in mine if m.classification in ("Mistake", "Blunder", "Missed Win")]
    right, wrong = [], []
    brill = [m for m in mine if m.classification == "Brilliant"]
    great = [m for m in mine if m.classification == "Great"]
    if brill:
        right.append(f"A brilliant move: {brill[0].move_no}{'.' if brill[0].color else '...'}{brill[0].san}.")
    if great:
        right.append(f"You found {len(great)} great move{'s' if len(great) > 1 else ''} (only-moves) when it mattered.")
    acc = rev.accuracy_white if color in (None, chess.WHITE) else rev.accuracy_black
    if acc is not None and acc >= 85:
        right.append(f"Strong accuracy overall ({acc:.0f}%).")
    opening_moves = [m for m in mine if m.phase == "opening" and m.counted]
    if opening_moves and all(m.loss <= rv.GOOD for m in opening_moves):
        right.append(f"A clean opening{f' ({rev.opening})' if rev.opening else ''}.")
    wins = (rev.result == "1-0" and color == chess.WHITE) or (rev.result == "0-1" and color == chess.BLACK)
    if wins and any(m.wp_before >= 80 for m in mine) and not any(m.classification == "Missed Win" for m in mine):
        right.append("You converted your advantage without letting it slip.")
    if not right:
        right.append("You kept playing and fighting: every game is data for the next one.")

    # themes of the real mistakes
    theme_cost: Counter = Counter()
    for m in bad:
        for t in m.themes or detect_themes(m, rev):
            theme_cost[t] += m.loss
    by_phase = Counter(m.phase for m in bad)
    if bad:
        n_bl = sum(1 for m in bad if m.classification == "Blunder")
        top_phase = by_phase.most_common(1)[0]
        wrong.append(f"{len(bad)} serious mistake{'s' if len(bad) > 1 else ''} ({n_bl} blunder{'s' if n_bl != 1 else ''}), most in the {top_phase[0]}.")
        tt = [m for m in bad if time_trouble(m, rev)]
        if tt:
            wrong.append(f"{len(tt)} of them came when you were low on time.")
        if "Hanging Pieces" in theme_cost:
            wrong.append("Pieces were left unprotected at critical moments.")
        if "Missed Mates" in theme_cost or any(m.classification == "Missed Win" for m in bad):
            wrong.append("You missed winning chances you could have calculated.")
    else:
        wrong.append("No serious mistakes: nothing to fix big this time.")

    # the focus area: this game's costliest theme, unless a theme that keeps coming back across games is also present here
    trend_lines = trends(history, tier) if history else []
    recurring: Counter = Counter()
    for h in history or []:
        for t, k in (h.get("themes") or {}).items():
            recurring[t] += 1 if k else 0
    focus = theme_cost.most_common(1)[0][0] if theme_cost else None
    for t, k in recurring.most_common(3):
        if k >= 3 and (focus is None or t in theme_cost):
            focus = t
            break
    focus = focus or ("Calculation" if tier != "master" else "Endgame Technique")
    elo = (rev.white_elo if color == chess.WHITE else rev.black_elo) if color is not None else (rev.white_elo or rev.black_elo)
    difficulty = int(round((elo or 1200) / 100.0) * 100)
    puzzle = PUZZLE_THEME.get(focus.replace("Knight Forks", "Forks"), focus)
    if focus == "Knight Forks":
        puzzle = "Knight Forks"
    return {"went_right": right[:3], "went_wrong": wrong[:3], "focus": focus, "focus_tip": _tip(focus, tier), "trends": trend_lines,
            "puzzle_trigger": f"[PUZZLE_TRIGGER: {puzzle}]",
            "action_tag": f'[ACTION: TRIGGER_PUZZLES | THEME: "{puzzle}" | DIFFICULTY: {difficulty}]'}


def history_entry(rev: GameReview) -> dict:
    """The small per-game fingerprint the app stores for long-term profiling."""
    color = rev.player_color
    mine = [m for m in rev.moves if color is None or m.color == color]
    bad = [m for m in mine if m.classification in ("Mistake", "Blunder", "Missed Win")]
    themes: Counter = Counter()
    for m in bad:
        for t in m.themes:
            themes[t] += 1
    return {"phases": dict(Counter(m.phase for m in bad)), "themes": dict(themes), "blunders": sum(1 for m in bad if m.classification == "Blunder"),
            "mistakes": len(bad), "time_trouble": sum(1 for m in bad if time_trouble(m, rev)), "accuracy": player_stats(rev)[1]}


def trends(history: list, tier: str) -> list:
    """Sentences about patterns across the last games (needs the fingerprints from history_entry)."""
    if not history or len(history) < 2:
        return []
    n = len(history)
    out = []
    phases: Counter = Counter()
    themes: Counter = Counter()
    for h in history:
        phases.update(h.get("phases") or {})
        for t, k in (h.get("themes") or {}).items():
            themes[t] += 1 if k else 0
    total = sum(phases.values())
    if total >= 4:
        ph, k = phases.most_common(1)[0]
        if k / total >= 0.5:
            out.append(f"In your last {n} games, {k / total:.0%} of your serious mistakes happened in the {ph}.")
    if themes:
        t, k = themes.most_common(1)[0]
        if k >= max(2, n // 3):
            out.append(f"'{t}' showed up in {k} of your last {n} games.")
    tt = sum(h.get("time_trouble", 0) for h in history)
    if tt >= 3:
        out.append(f"{tt} of your mistakes in the last {n} games came in time trouble.")
    accs = [h["accuracy"] for h in history if h.get("accuracy") is not None]
    if len(accs) >= 4:
        half = len(accs) // 2
        recent, older = sum(accs[:half]) / half, sum(accs[half:]) / (len(accs) - half)
        if recent - older >= 3:
            out.append(f"Your accuracy is trending up ({older:.0f}% to {recent:.0f}%). Keep it going!")
        elif older - recent >= 3:
            out.append(f"Your accuracy has dipped recently ({older:.0f}% to {recent:.0f}%).")
    return out[:3]


# --------------------------------------------------------------------------------------------------------------------
# main entry: fill in everything the UI shows
# --------------------------------------------------------------------------------------------------------------------
def annotate(rev: GameReview, player_elo: int | None = None, history: list | None = None) -> GameReview:
    color = rev.player_color
    elo = player_elo or ((rev.white_elo if color == chess.WHITE else rev.black_elo) if color is not None else None) \
        or rev.white_elo or rev.black_elo
    tier = tier_of(elo)
    for m in rev.moves:
        if m.classification in ("Mistake", "Blunder", "Missed Win"):
            m.themes = detect_themes(m, rev)
        m.explanation = explain(m, tier, rev.opening)
    rev.key_moments = rv.pick_key_moments(rev)
    rev.summary = summarize(rev, tier)
    rev.verdict = build_verdict(rev, tier, history)
    rev.verdict["tier"] = tier
    return rev


def render_markdown(rev: GameReview) -> str:
    """The review in the app's text format: overview, key moments and the coach's verdict."""
    v = rev.verdict or {}
    lines = [f"## Overview", f"- White Accuracy: {_fmt(rev.accuracy_white)}% | Black Accuracy: {_fmt(rev.accuracy_black)}%", f"- {rev.summary}", "",
             "## Key Moments"]
    for m in rev.moves:
        if m.ply in rev.key_moments:
            lines += [f"- **{m.move_no}{'.' if m.color else '...'} {m.san}{rv.SYMBOL.get(m.classification, '')}**: {m.classification}", f"  - {m.explanation}"]
    lines += ["", "## Coach's Verdict"]
    lines += [f"- What went right: {' '.join(v.get('went_right', []))}", f"- What went wrong: {' '.join(v.get('went_wrong', []))}",
              f"- **Focus Area:** {v.get('focus', '')}: {v.get('focus_tip', '')}", f"- {v.get('puzzle_trigger', '')}"]
    return "\n".join(lines)
