"""Game review: pick a game (from chess.com or a pasted PGN), run Stockfish, then explore the review."""
from __future__ import annotations

import streamlit as st

from core import background, coach, service, store
from ui import views
from ui.state import depth as current_depth, username as current_user

ss = st.session_state
depth = current_depth()


def open_review(game_id: str, pgn: str, username: str, depth: int):
    """Runs (or loads) the review and opens it."""
    ss.error = None
    bar = st.progress(0.0, text="Starting Stockfish…")

    def progress(done, total):
        bar.progress(done / total, text=f"Analysing position {done} of {total}…")

    try:
        rev = service.review_game(pgn, depth=depth, username=username, game_id=game_id, progress=progress)
    except (FileNotFoundError, ValueError) as e:
        bar.empty()
        ss.error = str(e)
        st.rerun()                                     # show the message at the top of the page
    bar.empty()
    ss.rev, ss.rev_id, ss.ply = rev, game_id, 0
    ss.pop("flip", None)
    ss.pop("_shown", None)
    st.rerun()


def close_review():
    ss.rev = None
    ss.rev_id = None


if ss.error:
    st.error(ss.error)
if not ss.get("engine_ok", True):
    st.warning("Stockfish wasn't found. On Streamlit Cloud add a `packages.txt` containing the word `stockfish`; locally install it "
               "(`sudo apt install stockfish` or `brew install stockfish`) or set the STOCKFISH_PATH environment variable.")

# ---- a review is open ----------------------------------------------------------------------------------------------
if ss.rev is not None:
    rev = ss.rev
    st.button("← Back to games", on_click=close_review)
    views.game_header(rev)
    st.write("")
    views.viewer(rev)
    st.write("")
    views.accuracy_and_counts(rev)
    st.markdown("#### Key moments")
    views.key_moments(rev)
    st.write("")
    views.verdict(rev)
    st.write("")
    st.download_button("⬇️ Download this review (Markdown)", coach.render_markdown(rev), file_name="game-review.md", mime="text/markdown")
    st.stop()

# ---- game picker ---------------------------------------------------------------------------------------------------
st.markdown("<div class='pagehead'><h1>Game review</h1><p>Brilliant moves, blunders and what to practise next, free, powered by Stockfish.</p></div>",
            unsafe_allow_html=True)
def bg_banner(job) -> str:
    """A thin progress strip while the coach reads the loaded games in the background."""
    if job is None or not job.total or not job.running:
        return ""
    return (f"<div class='bgbar'><div class='t'><span class='pulse'></span>The coach is reading your games in the background: <b>{job.done} of {job.total}</b> done. "
            f"Games marked ✓ open instantly, and the <b>Insights</b> tab fills up as they finish.</div>"
            f"<div class='tr'><div class='fl' style='width:{job.fraction * 100:.0f}%'></div></div></div>")


def games_panel(watching: bool):
    """The 'My games' list. While the background analysis runs this redraws itself every few seconds, so the ✓ marks appear as games finish."""
    job = background.status(current_user())
    banner = bg_banner(job)
    if banner:
        st.markdown(banner, unsafe_allow_html=True)
    if ss.games is None:
        st.info("Type your chess.com username in the sidebar and press **Load my games**.")
    elif not ss.games:
        st.warning("No reviewable games found for that user.")
    else:
        reviewed = store.reviewed_ids(current_user())
        st.caption(f"{len(ss.games)} most recent games for **{current_user()}** · analysis depth {depth}")
        views.games_summary(ss.games)
        clicked = views.games_list(ss.games, reviewed, depth)
        if clicked is not None:
            open_review(clicked.game_id, clicked.pgn, current_user(), depth)
    if watching and not (job and job.running):                  # the analysis just finished: redraw once without the auto-refresh
        st.rerun()


tab_games, tab_pgn = st.tabs(["📋 My games", "📝 Paste a PGN"])
with tab_games:
    _job = background.status(current_user())
    _running = bool(_job and _job.running)
    st.fragment(run_every=3 if _running else None)(games_panel)(_running)

with tab_pgn:
    st.caption("Any game works: paste a PGN from chess.com (Share → PGN), Lichess or anywhere else.")
    pgn_text = st.text_area("PGN", height=220, key="pgn_text", placeholder='[Event "Casual game"]\n1. e4 e5 2. Nf3 ...', label_visibility="collapsed")
    me = st.text_input("Your name in that game (optional, so the coach talks to you)", key="pgn_me")
    if st.button("Review this game", type="primary", disabled=not pgn_text.strip()):
        open_review(service.pgn_id(pgn_text), pgn_text, me.strip(), depth)
