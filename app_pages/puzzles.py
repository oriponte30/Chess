"""Puzzles: tactics puzzles in four levels. The board runs in the browser (ui/assets/puzzle.js), so every move is checked and answered
instantly; this page chooses the puzzles and saves the results."""
from __future__ import annotations

import random

import chess
import streamlit as st

from core import puzzles as pz, store
from ui import live
from ui.state import username

ss = st.session_state
for _k, _v in {"pz_level": 0, "pz_theme": "All themes", "pz_queue": [], "pz_epoch": 0, "pz_streak": 0, "pz_best": 0, "pz_done_now": 0,
               "pz_anon": {}, "pz_seq": {}}.items():
    ss.setdefault(_k, _v)
BATCH = 25


# ---- progress ---------------------------------------------------------------------------------------------------------------
def results() -> dict:
    """{puzzle_id: solved}: saved for a loaded chess.com user, kept for this visit otherwise."""
    user = username()
    return store.puzzle_results(user) if user else dict(ss.pz_anon)


def remember(puzzle_id: str, solved: bool, attempts: int):
    user = username()
    if user:
        store.save_puzzle_result(user, puzzle_id, solved, attempts)
    elif solved:
        ss.pz_anon[puzzle_id] = True


def candidates() -> list:
    theme = None if ss.pz_theme == "All themes" else ss.pz_theme
    return pz.pool(ss.pz_level or None, theme)


def fill_queue(extra: bool = False):
    """Adds a batch of puzzles to the queue: ones you haven't solved first, in random order."""
    have = set(ss.pz_queue)
    res = results()
    pool = [p for p in candidates() if p.id not in have]
    rng = random.Random()
    fresh = [p for p in pool if not res.get(p.id)]
    done = [p for p in pool if res.get(p.id)]
    rng.shuffle(fresh)
    rng.shuffle(done)
    ss.pz_queue = list(ss.pz_queue) + [p.id for p in (fresh + done)[:BATCH]]


def new_queue():
    ss.pz_queue = []
    ss.pz_epoch += 1
    ss.pz_seq = {}


def set_level(level: int):
    ss.pz_level, ss.pz_theme = level, "All themes"
    new_queue()


def change_theme():
    new_queue()


def payload(puz: pz.Puzzle) -> dict:
    return {"id": puz.id, "fen": puz.fen, "last": puz.last or "", "moves": list(puz.moves), "level": puz.level, "levelName": puz.level_name,
            "icon": pz.LEVELS[puz.level]["icon"], "themes": list(puz.themes), "side": "w" if puz.side == chess.WHITE else "b", "solution": puz.solution_san()}


def handle(event: dict) -> bool:
    """Saves the results the page reports (it sends its whole log each time; the ones already saved are skipped). True when something new came in."""
    epoch = ss.pz_epoch
    seen = ss.pz_seq.get(epoch, 0)
    new = False
    by_id = pz.by_id()
    for item in event.get("log", []) if isinstance(event, dict) else []:
        try:
            seq, pid, solved, wrong = int(item["seq"]), str(item["id"]), bool(item["solved"]), int(item.get("wrong", 0))
        except (KeyError, TypeError, ValueError):
            continue
        if seq <= seen or pid not in by_id:
            continue
        remember(pid, solved, wrong + 1)
        seen, new = seq, True
    ss.pz_seq[epoch] = seen
    for k, key in (("streak", "pz_streak"), ("best", "pz_best"), ("done", "pz_done_now")):
        try:
            ss[key] = max(0, int(event.get(k, ss[key])))
        except (TypeError, ValueError):
            pass
    return new


# ---- page -----------------------------------------------------------------------------------------------------------------------
st.markdown("<div class='pagehead'><h1>Puzzles</h1><p>Sharpen your tactics. Every puzzle has one clearly best move, checked by Stockfish.</p></div>", unsafe_allow_html=True)
if not pz.load():
    st.warning("The puzzle library (data/puzzles.json) was not found. Run `python scripts/build_puzzles.py` to create it.")
    st.stop()

res = results()
counts = pz.counts_by_level(res)
total_solved = sum(a for a, _ in counts.values())
total = sum(b for _, b in counts.values())
tabs = [(0, "🎲", "Mixed", "All levels together", total_solved, total)] + [
    (lv, m["icon"], m["name"], m["blurb"], counts[lv][0], counts[lv][1]) for lv, m in pz.LEVELS.items()]
cols = st.columns(len(tabs), gap="small")
for col, (lv, icon, name, blurb, done, tot) in zip(cols, tabs):
    with col:
        pct = (done / tot * 100) if tot else 0
        sel = " sel" if ss.pz_level == lv else ""
        st.markdown(f"<div class='lvl{sel}'><div class='i'>{icon}</div><div class='h'>{name}</div><div class='x'>{blurb}</div>"
                    f"<div class='bar'><div style='width:{pct:.0f}%'></div></div><div class='n'>{done} / {tot} solved</div></div>", unsafe_allow_html=True)
        st.button("Selected" if ss.pz_level == lv else "Play", key=f"pz_lv_{lv}", on_click=set_level, args=(lv,), width="stretch",
                  type="primary" if ss.pz_level == lv else "secondary", disabled=(ss.pz_level == lv))

theme_options = ["All themes"] + [f"{t}" for t, _ in pz.themes(ss.pz_level or None)]
if ss.pz_theme not in theme_options:
    ss.pz_theme = "All themes"
st.selectbox("Theme", theme_options, key="pz_theme", on_change=change_theme, label_visibility="collapsed")

if not candidates():
    st.info("No puzzles match that choice. Pick another theme.")
    st.stop()
if not ss.pz_queue:
    fill_queue()
if not username():
    st.caption("Tip: load your chess.com games in the sidebar and your solved puzzles are remembered between visits.")
by_id = pz.by_id()
out = live.run("puzzle", f"pz_{ss.pz_epoch}", {"qid": ss.pz_epoch, "queue": [payload(by_id[i]) for i in ss.pz_queue],
                                                 "stats": {"streak": ss.pz_streak, "best": ss.pz_best, "done": ss.pz_done_now}}, "result", "more")
_event = getattr(out, "result", None)
_more = getattr(out, "more", None)
_changed = bool(_event) and handle(_event)
if _more is not None and str(_more).isdigit() and int(_more) >= len(ss.pz_queue):
    fill_queue()
    _changed = True
if _changed:
    st.rerun()                                              # refresh the progress bars above with the new results
