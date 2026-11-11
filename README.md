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

## Smooth play, always-on, three lines everywhere
- **Instant boards.** The Review, Puzzles and Lessons boards run in the browser (`ui/assets/*.js`, with chess.js bundled in `ui/assets/chess.bundle.js`).
  Stepping through a game, dragging a piece, the eval bar, the graph, the move list, puzzle checking and the opponent's reply never wait for the
  server (about 3 ms per step). The server is only asked for Stockfish's lines, to save puzzle results and to pick what comes next.
  Arrow keys, Home and End work in all three. Pieces slide, wrong puzzle moves shake the board and solved ones glow.
- **Three lines from every position.** Each lesson position shows at least three lines to follow: the lesson's own lines first, then Stockfish's
  alternatives, marked with 🤖, for positions where the lesson has fewer. Only positions with fewer than three legal moves (a forced reply) can show less.
  Off the lesson tree the engine's top three are shown. Rebuild after editing a lesson with `python scripts/build_lesson_extras.py`.
- **Keep it awake.** Streamlit Community Cloud sleeps an app after about 12 hours without a visitor. `.github/workflows/keepalive.yml` opens the app in a
  headless browser every 6 hours and presses the wake-up button if it has already slept. One-time setup: in your GitHub repo go to
  *Settings → Secrets and variables → Actions → Variables* and add `APP_URL` = `https://<your-app>.streamlit.app`, then run the workflow once from the
  *Actions* tab. (GitHub pauses scheduled workflows in a repo with no activity for 60 days; re-enable it from the Actions tab if that happens.)

## What's new
- **Seven opening courses** (Lessons): Italian, Vienna, London, Queen's Gambit, Caro-Kann, Sicilian (Black) and *Playing against the Sicilian*
  (Open, Rossolimo, Alapin, Grand Prix/closed, Smith-Morra). Each has several variations, each checked move by move with Stockfish
  (`python scripts/check_lessons.py`). Add one by writing a `core/lesson_data/<name>.py` and listing it in `core/library.py`.
- **Puzzles**: ~360 Stockfish-verified puzzles in four levels (Beginner to Expert) with themes, a streak, 2-step hints and progress that is saved
  per player. Rebuild or grow the set with `scripts/build_puzzles.py find ...` then `merge ... --out data/puzzles.json`.
- **Remember me**: a one-year cookie (`cc_prefs`: username, depth, number of games) reloads your games on your next visit. "Not you? Forget me" clears it.
- **Reads your games before you ask**: after loading, a background worker analyses your last 5-40 games (capped at depth 14) while you browse.
  Insights fills in as they finish and shows results by colour and the openings you meet. Games are marked in "My games" when done.
- **Faster and nicer UI**: animated cards and bars, reduced-motion respected, cached CSS and board pictures, per-game locks so nothing is analysed twice.

> Streamlit Community Cloud keeps its SQLite file only until the app restarts, so saved reviews and puzzle progress can reset after a reboot.
> The cookie still brings you back; the background reader simply re-analyses. Use Postgres storage if you need it permanent.

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
core/lessons.py     the variation-tree engine for lessons (python-chess + Stockfish checked)
core/lesson_export.py  a lesson as data for the browser, with at least three lines per position
data/lesson_extra.json Stockfish's extra lines for positions the lessons cover thinly (scripts/build_lesson_extras.py)
core/lesson_data/   one file per opening course; core/library.py lists them
core/puzzles.py     puzzle loading, levels, judging; data/puzzles.json is the generated set
core/background.py  worker threads that read your recent games ahead of time
ui/remember.py      the remember-me cookie
ui/live.py          loads the browser components; ui/assets/ holds chess.js, the shared board toolkit and one script each for review, puzzles and lessons
scripts/keep_awake.py  what the keep-alive workflow runs
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
