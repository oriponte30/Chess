"""A lesson tree as plain data for the browser (ui/assets/lesson.js), so the whole lesson can be stepped through without the server.

Every position carries at least three lines to follow: the lesson's own prepared lines first, then Stockfish's alternatives from
data/lesson_extra.json (built by scripts/build_lesson_extras.py) for the positions where the lesson has fewer than three."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .lessons import LessonTree, fmt_line

EXTRA = Path(__file__).resolve().parent.parent / "data" / "lesson_extra.json"
MIN_LINES = 3


@lru_cache(maxsize=1)
def _extras() -> dict:
    try:
        return json.loads(EXTRA.read_text())
    except (OSError, ValueError):
        return {}


def node_list(tree: LessonTree) -> list:
    out, stack = [], [tree.root]
    while stack:
        n = stack.pop()
        out.append(n)
        stack.extend(reversed(n.children))
    return out


def lines_for(tree: LessonTree, node) -> list:
    """The lines to show from a position: [{first, text, src, eval?}] with at least MIN_LINES where the engine data allows."""
    eff = tree.effective(node)
    out = [{"first": l[0].uci, "text": fmt_line(l), "src": "lesson"} for l in tree.top_lines(eff, MIN_LINES)]
    if len(out) < MIN_LINES:
        have = {o["first"] for o in out}
        for e in _extras().get(tree.slug, {}).get(eff.epd, []):
            if e["first"] not in have and len(out) < MIN_LINES:
                out.append({"first": e["first"], "text": e["text"], "src": "engine", "eval": e["eval"]})
                have.add(e["first"])
    return out


def export(tree: LessonTree) -> dict:
    nodes = node_list(tree)
    ids = {id(n): i for i, n in enumerate(nodes)}
    sec_index = {s["id"]: i for i, s in enumerate(tree.sections)}
    out_nodes, lines, ahead = [], {}, {}
    for i, n in enumerate(nodes):
        eff = tree.effective(n)
        sec = tree.section_of(n)
        note = (eff.note if eff else "") or ("Book move. Keep following the plan of this variation." if n.uci else tree.intro)
        out_nodes.append({"p": ids[id(n.parent)] if n.parent is not None else -1, "s": n.san, "u": n.uci, "l": n.label if n.uci else "Start of the lesson",
                          "n": note, "al": ids[id(n.alias)] if n.alias is not None else -1, "c": [ids[id(c)] for c in n.children],
                          "sec": sec_index.get(sec["id"], -1) if sec else -1, "ep": n.epd})
        if n.alias is None:
            lines[i] = lines_for(tree, n)
            opts = []
            for o in tree.look_ahead(n)[:4]:
                c = o["move"]
                opts.append({"u": c.uci, "l": c.label, "text": fmt_line(o["line"]),
                             "r": [{"l": r.label, "text": fmt_line(cont) or "the line ends"} for r, cont in o["replies"][:3]]})
            if opts:
                ahead[i] = opts
    secs = []
    for s in tree.sections:
        start = tree.node_at_san(s["start"])
        secs.append({"id": s["id"], "title": s["title"], "icon": s["icon"], "summary": s["summary"], "start": ids[id(start)]})
    return {"slug": tree.slug, "title": tree.title, "icon": tree.icon, "intro": tree.intro, "side": tree.side, "sections": secs,
            "nodes": out_nodes, "lines": lines, "ahead": ahead}
