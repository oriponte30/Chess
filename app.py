"""Chess Coach: a free game reviewer for chess.com games, powered by Stockfish."""
from __future__ import annotations

import chess
import streamlit as st

from core import chesscom, service, store
from core.engine import find_stockfish
from ui import views
from ui.styles import CSS

st.set_page_config(page_title="Chess Coach", page_icon="♟️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

DEPTHS = {"⚡ Quick": 12, "⚖️ Standard": 14, "🔬 Deep": 18}
DEFAULTS = {"games": None, "username": "", "rev": None, "rev_id": None, "ply": 0, "pending": None, "error": None}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
ss = st.session_state


def load_games():
    ss.error = None
    try:
        with st.spinner("Fetching your games from chess.com…"):
            ss.games = chesscom.recent_games(ss.user_input, limit=ss.get("n_games", 20))
        ss.username = ss.user_input.strip().lower()
    except chesscom.ChessComError as e:
        ss.games, ss.error = None, str(e)


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
    st.rerun()


def close_review():
    ss.rev = None
    ss.rev_id = None


# ---- sidebar -------------------------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ♟️ Chess Coach")
    st.text_input("chess.com username", key="user_input", placeholder="e.g. hikaru")
    st.button("Load my games", on_click=load_games, type="primary", width="stretch", disabled=not (ss.get("user_input") or "").strip())
    st.slider("How many recent games", 5, 40, 20, 5, key="n_games")
    st.divider()
    depth_name = st.radio("Analysis depth", list(DEPTHS), index=1, key="depth_name",
                          help="Deeper = more accurate and slower. Standard takes roughly 10-60 seconds per game.")
    depth = DEPTHS[depth_name]
    sf = find_stockfish()
    st.caption("Engine: Stockfish ready." if sf else "⚠️ Stockfish isn't installed here.")
    st.caption("Reviews are saved, so opening a game twice is instant.")

st.markdown("<div class='hero'><div class='logo'>♟️</div><div><h1>Chess Coach</h1>"
            "<small>Free game review powered by Stockfish · brilliant moves, blunders and what to practise next</small></div></div>", unsafe_allow_html=True)

if ss.error:
    st.error(ss.error)
if not sf:
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
    from core import coach
    st.download_button("⬇️ Download this review (Markdown)", coach.render_markdown(rev), file_name="game-review.md", mime="text/markdown")
    st.stop()

# ---- game picker -----------------------------------------------------------------------------------------------------
tab_games, tab_pgn = st.tabs(["📋 My games", "📝 Paste a PGN"])
with tab_games:
    if ss.games is None:
        st.info("Type your chess.com username in the sidebar and press **Load my games**.")
    elif not ss.games:
        st.warning("No reviewable games found for that user.")
    else:
        reviewed = store.reviewed_ids(ss.username)
        st.caption(f"{len(ss.games)} most recent games for **{ss.username}** · analysis depth {depth}")
        clicked = views.games_list(ss.games, reviewed, depth)
        if clicked is not None:
            open_review(clicked.game_id, clicked.pgn, ss.username, depth)

with tab_pgn:
    st.caption("Any game works: paste a PGN from chess.com (Share → PGN), Lichess or anywhere else.")
    pgn_text = st.text_area("PGN", height=220, key="pgn_text", placeholder='[Event "Casual game"]\n1. e4 e5 2. Nf3 ...', label_visibility="collapsed")
    me = st.text_input("Your name in that game (optional, so the coach talks to you)", key="pgn_me")
    if st.button("Review this game", type="primary", disabled=not pgn_text.strip()):
        open_review(service.pgn_id(pgn_text), pgn_text, me.strip(), depth)
