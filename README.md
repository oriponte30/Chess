# ♟️ Chess Coach

A free game reviewer for chess.com games, powered by [Stockfish](https://stockfishchess.org). Enter your chess.com username (or paste any PGN) and
get what chess.com charges a subscription for: an accuracy score for both players, every move labelled (Brilliant, Great, Best, Excellent, Good,
Inaccuracy, Mistake, Blunder, Missed Win), an evaluation graph, the key moments of the game and a coach's verdict with something concrete to
practise. Explanations are written for your rating.

## How a review works

1. **Games** come from chess.com's free public API (`/pub/player/<user>/games/...`), or from a pasted PGN.
2. **Stockfish** analyses every position once, with its two best lines (MultiPV 2), at a depth you choose (Quick 12 / Standard 14 / Deep 18).
3. **Win probability** is computed from each evaluation: `WP = 50 + 50 * (2 / (1 + e^(-0.00368208 * cp)) - 1)`. A move's *loss* is the win
   probability it threw away compared with the engine's best move.
4. **Labels** come from that loss: Best (0-0.5) | Excellent (-2) | Good (-5) | Inaccuracy (-10) | Mistake (-25) | Blunder (>25), plus
   * **Brilliant**: a real material sacrifice that is still sound, the only good path (the second-best move is at least 10 points worse) and
     that looked worse at a shallow search (or forces a mate). Strict on purpose, so it is rare.
   * **Great**: the only move that holds the position (second-best is 15+ points worse), and not a plain recapture.
   * **Missed Win**: a forced mate you didn't play, or a clearly winning position you let slip.
   * **Book** (known opening positions, from the bundled lichess opening list) and **Forced** moves aren't counted in the accuracy.
5. **The coach** (`core/coach.py`) turns that into text: it spots hanging pieces, forks, discovered attacks, missed mates and time trouble
   (from the clocks in chess.com PGNs), adapts the wording to the player's rating (under 800 / 800-1499 / 1500-1999 / 2000+), writes the
   2-sentence summary, the key moments (max 4), what went right / wrong, a focus area and the `[PUZZLE_TRIGGER: ...]` /
   `[ACTION: TRIGGER_PUZZLES | THEME: ... | DIFFICULTY: ...]` tags the training tab will use. Across games it also notices patterns ("60% of your
   mistakes are in the endgame").

The coach is **rule-based**: free, instant, deterministic, no API key. All the truth comes from Stockfish's numbers.

### Where this deliberately differs from the original brief
* **Accuracy curve.** The brief's `100 - (WP before - WP after)` is too forgiving (a 25-point blunder would still score 75%). Each move uses the
  Lichess curve `103.1668 * e^(-0.04354 * loss) - 3.1669`, and the game score is a volatility-weighted mean blended with the harmonic mean, so
  one disaster still hurts.
* **Gaps in the thresholds.** A move losing under 1 point wasn't covered; anything within 0.5 is Best and up to 2 is Excellent.
  "Missed Win" overlaps the other labels, so it takes priority when it applies.
* **Brilliant's depth rule** ("looks like a blunder at depth 10 but brilliant at 20") would need two full analyses of every game. Instead the
  candidate sacrifice is re-checked at a shallow depth (5) and must look at least 6 points worse there, or lead to a forced mate.
* **Rating bands** overlapped at the edges; they are now <800, 800-1499, 1500-1999, 2000+.
* **No language model.** The brief reads like an LLM prompt; the same rules are implemented as code so reviews are free and reproducible.

## Run it

```bash
pip install -r requirements.txt
sudo apt install stockfish        # or: brew install stockfish, or set STOCKFISH_PATH to a binary
streamlit run app.py
```

### Deploy on Streamlit Community Cloud (free)
1. Push this folder to a new GitHub repo (`packages.txt` makes the platform install Stockfish).
2. On <https://share.streamlit.io> choose the repo and `app.py`.
3. Reviews are saved in SQLite (`data/coach.db`). On Streamlit Cloud that file resets when the app restarts, so it works as a cache; for
   permanent history point `core/store.py` at Postgres (the schema is plain SQL).

## Tests
`python -m pytest -q`. They use a scripted material-only engine, so they run anywhere; one extra test uses a real Stockfish if present.

## Layout
```
app.py              the shell: page setup, shared sidebar, navigation (nothing feature-specific lives here)
app_pages/          one file per feature: review.py (game reviewer), lessons.py (interactive opening lessons), training.py (hub + Coach Practice), insights.py
ui/features.py     the list of pages; add a line here to register a new feature
ui/state.py         shared session state and settings (depth, username)
ui/sidebar.py       the sidebar every page shares
ui/views.py         review-screen components (board viewer, key moments, verdict, game cards)
ui/styles.py        all CSS, driven by a few design tokens at the top
core/chesscom.py    chess.com API client
core/engine.py      Stockfish over UCI (a pool of engines that split a game's positions between them)
core/review.py      win probability, labels, accuracy, key moments
core/coach.py       explanations, verdict, trends, puzzle tags
core/lessons.py     opening lessons as a variation tree (Caro-Kann included), verified with python-chess and Stockfish
core/insights.py    turns stored reviews into coach notes and focus areas
core/store.py       SQLite storage (reviews, per-move facts, history) and store.move_facts() for cross-game features
core/service.py     one call: cache -> engine -> coach -> store
```

### Adding a feature
1. Create `app_pages/<name>.py`. It is an ordinary Streamlit script; read the user and depth from `ui/state.py`, and past games from `core/store.py`.
2. Add one `Feature(...)` line to `ui/features.py`. The page shows up in the top navigation.

## Next
Training tab (openings from your own losses, tactics from your own blunders, endgames), a warehouse/analytics layer over `move_facts`,
Postgres storage, and Lichess import.

## Notes
Stockfish is GPLv3 and runs as a separate program. This project is not affiliated with chess.com; it only reads their public API.
