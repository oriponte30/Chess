"""Turns stored review data into the numbers and coach notes shown on the Insights page. Pure functions (no Streamlit), so they're easy to test."""
from __future__ import annotations

from collections import Counter

from . import coach

PHASES = ("opening", "middlegame", "endgame")

PHASE_ADVICE = {
    "opening": "Pick one or two openings and learn their ideas rather than moves (the Lessons tab has a start). Finish development, castle, and avoid grabbing pawns early.",
    "middlegame": "Before each move run a blunder check: what are the opponent's checks, captures and threats? Then improve your worst-placed piece.",
    "endgame": "Practise king activity and basic technique: bring the king to the centre, create a passed pawn, and calculate pawn races move by move.",
}


def phase_stats(facts: list) -> dict:
    """{phase: {acc, n, bad}} for the user's own moves; every phase is always present (acc None when there are no moves yet)."""
    out = {}
    for ph in PHASES:
        rows = [f for f in facts if f["phase"] == ph and f["classification"] not in ("Book", "Forced")]
        bad = sum(1 for f in rows if f["classification"] in ("Mistake", "Blunder", "Missed Win"))
        out[ph] = {"acc": round(sum(f["accuracy"] for f in rows) / len(rows), 1) if rows else None, "n": len(rows), "bad": bad}
    return out


def quality_counts(facts: list) -> list:
    order = ("Brilliant", "Great", "Best", "Excellent", "Good", "Inaccuracy", "Mistake", "Blunder", "Missed Win")
    c = Counter(f["classification"] for f in facts)
    return [(k, c[k]) for k in order if c[k]]


def focus_areas(mistakes: list, limit: int = 3) -> list:
    """The themes that cost the most across the recent games: [{theme, count, cost, tip}]."""
    cost, count = Counter(), Counter()
    for m in mistakes:
        for t in (m["themes"] or ["Calculation"]):
            cost[t] += m["loss"]
            count[t] += 1
    out = []
    for theme, c in cost.most_common(limit):
        out.append({"theme": theme, "count": count[theme], "cost": round(c), "tip": coach.THEME_TIPS.get(theme, coach.THEME_TIPS["Calculation"])["club"]})
    return out


def coach_notes(stats: dict, mistakes: list, rows: list) -> list:
    """Plain-language coaching notes: [{icon, title, text}]. Each one names a concrete thing to work on."""
    notes = []
    played = {p: s for p, s in stats.items() if s["acc"] is not None and s["n"] >= 3}
    if len(played) >= 2:
        weakest = min(played, key=lambda p: played[p]["acc"])
        best = max(played, key=lambda p: played[p]["acc"])
        if weakest != best and played[best]["acc"] - played[weakest]["acc"] >= 3:
            notes.append({"icon": "🎯", "title": f"Focus on: the {weakest}",
                          "text": f"Your {weakest} accuracy is {played[weakest]['acc']:.0f}%, against {played[best]['acc']:.0f}% in the {best}. {PHASE_ADVICE[weakest]}"})
    for ph, s in stats.items():
        if s["n"] >= 8 and s["bad"] / s["n"] >= 0.12:
            notes.append({"icon": "⚠️", "title": f"Too many big mistakes in the {ph}",
                          "text": f"{s['bad']} of your {s['n']} {ph} moves were mistakes or blunders (about one in {round(s['n'] / s['bad'])}). Slow down on the moves where the position is sharp."})
            break
    areas = focus_areas(mistakes, 1)
    if areas:
        a = areas[0]
        notes.append({"icon": "🧩", "title": f"Recurring theme: {a['theme']}", "text": f"It shows up in {a['count']} of your recent mistakes. {a['tip']}"})
    by_open: dict = {}
    for r in rows:
        if r["opening"] and r["accuracy"] is not None:
            by_open.setdefault(r["opening"], []).append(r["accuracy"])
    rated = {o: sum(v) / len(v) for o, v in by_open.items() if len(v) >= 2}
    if len(rated) >= 2:
        worst = min(rated, key=rated.get)
        notes.append({"icon": "📖", "title": f"Opening to review: {worst}", "text": f"Your accuracy in this opening averages {rated[worst]:.0f}% over {len(by_open[worst])} games, "
                                                                                    "the lowest of your regular openings. Revisit its first ten moves and its typical plans."})
    return notes


def accuracy_trend(rows: list) -> list:
    """[(game number, accuracy)] oldest to newest, for the trend chart."""
    mine = [r["accuracy"] for r in reversed(rows) if r["accuracy"] is not None]
    return [(i + 1, round(a, 1)) for i, a in enumerate(mine)]


# ---- results and openings across the loaded games -------------------------------------------------------------------------
def outcome(row: dict) -> str:
    """'win' / 'loss' / 'draw' for the player in one review row ('' when we can't tell which side they played)."""
    res, color = row.get("result"), row.get("player_color")
    if res == "1/2-1/2":
        return "draw"
    if color is None or res not in ("1-0", "0-1"):
        return ""
    return "win" if (res == "1-0") == (color == 1) else "loss"


def _summary(rows: list) -> dict:
    accs = [r["accuracy"] for r in rows if r.get("accuracy") is not None]
    res = [outcome(r) for r in rows]
    return {"games": len(rows), "wins": res.count("win"), "draws": res.count("draw"), "losses": res.count("loss"),
            "acc": round(sum(accs) / len(accs), 1) if accs else None}


def color_split(rows: list) -> dict:
    """{'white': summary, 'black': summary}: how the player does with each colour."""
    return {"white": _summary([r for r in rows if r.get("player_color") == 1]), "black": _summary([r for r in rows if r.get("player_color") == 0])}


def opening_table(rows: list, limit: int = 6) -> list:
    """The openings the player met most: [{opening, games, wins, draws, losses, acc, score}], most-played first. `score` is the points
    percentage (a win is 1, a draw one half)."""
    groups: dict = {}
    for r in rows:
        if r.get("opening"):
            groups.setdefault(r["opening"], []).append(r)
    out = []
    for name, rs in groups.items():
        s = _summary(rs)
        decided = s["wins"] + s["draws"] + s["losses"]
        out.append({"opening": name, **s, "score": round((s["wins"] + s["draws"] / 2) / decided * 100) if decided else None})
    out.sort(key=lambda o: (-o["games"], o["opening"]))
    return out[:limit]
