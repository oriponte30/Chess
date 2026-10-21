"""All CSS in one place. Every colour is a design token (a CSS variable) and there are two token sets, so the app reads well on
Streamlit's light theme and its dark theme. `css(mode)` picks the set; ui/theme.py works out the mode."""

TOKENS = {
    "dark": {
        "bg": "#0b1118", "bg2": "#111b26", "glow": "#1a2a36", "surface": "rgba(255,255,255,.055)", "surface2": "rgba(255,255,255,.10)",
        "line": "rgba(255,255,255,.13)", "text": "#F8FAFC", "body": "#E2E8F0", "muted": "#B4C2D0", "accent": "#7fa650", "accent2": "#B6E36F",
        "accent_text": "#B6E36F", "win": "#4cc38a", "loss": "#ff7b72", "draw": "#B4C2D0", "link": "#8fb4ff", "shadow": "rgba(0,0,0,.28)",
        "glass": "rgba(22,34,46,.62)", "ring_bg": "rgba(255,255,255,.12)", "tag_bg": "#0a1016", "tag_text": "#7fe0b0", "chart_area": "#d9dee3",
    },
    "light": {
        "bg": "#f1f4f8", "bg2": "#ffffff", "glow": "#dfe8f1", "surface": "#ffffff", "surface2": "#eaeff5",
        "line": "rgba(15,23,42,.14)", "text": "#0F172A", "body": "#1A1A1A", "muted": "#475569", "accent": "#4f7a2c", "accent2": "#3d6b1f",
        "accent_text": "#3a6a1c", "win": "#16794a", "loss": "#c0352b", "draw": "#475569", "link": "#1d4ed8", "shadow": "rgba(15,23,42,.10)",
        "glass": "rgba(255,255,255,.72)", "ring_bg": "rgba(15,23,42,.12)", "tag_bg": "#eef2f6", "tag_text": "#1c6b45", "chart_area": "#94a3b8",
    },
}

_BASE = """
<style>
:root { __VARS__ --radius: 18px; }
[data-testid="stAppViewContainer"] { background: radial-gradient(1200px 600px at 80% -10%, var(--glow) 0%, transparent 60%), var(--bg); }
[data-testid="stHeader"] { background: color-mix(in srgb, var(--bg) 78%, transparent); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
[data-testid="stSidebar"] { background: var(--bg2); border-right: 1px solid var(--line); }
.block-container { padding-top: 4.2rem; max-width: 1240px; }
h1, h2, h3, h4, h5 { color: var(--text) !important; letter-spacing: -.01em; }
.stApp, .stMarkdown, .stMarkdown p, .stMarkdown li, label, [data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"] { color: var(--body); }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted) !important; }
[data-testid="stSidebar"] label p, [data-testid="stSidebar"] .stMarkdown p { color: var(--body) !important; }

/* ---- top navigation */
[data-testid="stTopNavLink"] { color: var(--text) !important; font-weight: 700 !important; font-size: 15px; border-radius: 10px; padding: 6px 14px; opacity: 1 !important; transition: background .15s ease; }
[data-testid="stTopNavLink"] * { color: inherit !important; font-weight: inherit !important; }
[data-testid="stTopNavLink"]:hover { background: var(--surface2); }
[data-testid="stTopNavLink"][aria-current="page"] { background: color-mix(in srgb, var(--accent) 24%, transparent); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 60%, transparent); }

/* ---- brand + page headers */
.brand { display:flex; align-items:center; gap:10px; margin: 2px 0 10px; }
.brand .logo { width:38px; height:38px; border-radius:12px; display:grid; place-items:center; font-size:22px;
  background: linear-gradient(135deg, #8cbc58, #4f7a2c); box-shadow: 0 6px 18px rgba(127,166,80,.35); }
.brand b { font-size:18px; color: var(--text); letter-spacing:-.02em; } .brand small { display:block; color: var(--muted); font-size:12px; margin-top:-2px; }
.pagehead { margin: 0 0 14px; } .pagehead h1 { margin:0; padding:0; font-size:28px; font-weight:800; line-height:1.15; } .pagehead p { margin:4px 0 0; color: var(--muted); font-size:15px; }

/* ---- cards (solid) and glass cards */
.card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px 20px; box-shadow: 0 8px 24px var(--shadow); color: var(--body); }
.card h4 { margin: 0 0 10px; font-size: 12px; letter-spacing:.08em; text-transform: uppercase; color: var(--muted) !important; font-weight:800; }
.glass { background: var(--glass); backdrop-filter: blur(14px) saturate(1.3); -webkit-backdrop-filter: blur(14px) saturate(1.3); border: 1px solid var(--line);
  border-radius: 22px; padding: 18px 22px; box-shadow: 0 14px 40px var(--shadow); color: var(--body); position: relative; overflow: hidden; }
.glass::before { content:""; position:absolute; inset:0 0 auto 0; height:3px; background: linear-gradient(90deg, #7fa650, #4cc3b0, #6c8cff); opacity:.9; }
.soft { color: var(--muted); }
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button { border-radius: 12px; font-weight: 700; transition: transform .08s ease, box-shadow .15s ease; }
div[data-testid="stButton"] button:active { transform: scale(.97); }
div[data-testid="stButton"] button[kind="primary"] { background: linear-gradient(135deg, #7fa650, #4f7a2c); border: 0; color:#fff; box-shadow: 0 6px 16px rgba(127,166,80,.30); }

/* ---- game header, pills */
.gh { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
.gh .vs { font-weight:800; font-size:19px; color: var(--text); } .gh .meta { color: var(--muted); font-size:13.5px; font-weight:600; } .gh a { color: var(--link); }
.pill { display:inline-block; border-radius:999px; padding:3px 12px; font-weight:800; font-size:12.5px; }
.pill.win { background: color-mix(in srgb, var(--win) 20%, transparent); color: var(--win); } .pill.loss { background: color-mix(in srgb, var(--loss) 20%, transparent); color: var(--loss); }
.pill.draw { background: color-mix(in srgb, var(--draw) 22%, transparent); color: var(--draw); }
.pill.op { background: var(--surface2); color: var(--body); }

/* ---- accuracy rings and counts */
.acc { display:flex; align-items:center; gap:14px; } .acc.me { border-color: color-mix(in srgb, var(--accent) 70%, transparent); box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 35%, transparent) inset, 0 8px 24px var(--shadow); }
.acc .who { font-size:12px; font-weight:800; color: var(--muted); text-transform:uppercase; letter-spacing:.08em; }
.acc .nm { font-weight:800; color: var(--text); font-size:15px; margin-top:2px; } .acc .sub { color: var(--muted); font-size:12.5px; font-weight:600; }
.ring { position:relative; width:78px; height:78px; flex:none; } .ring svg { width:78px; height:78px; transform: rotate(-90deg); }
.ring .v { position:absolute; inset:0; display:grid; place-items:center; font-weight:900; font-size:20px; color: var(--text); }
.mq { width:100%; border-collapse: collapse; font-size:14.5px; color: var(--body); }
.mq td { padding: 5px 4px; border-bottom: 1px solid var(--line); }
.mq td.n { text-align:center; font-weight:800; width:54px; }
.mq .dot { display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:9px; vertical-align:-1px; }

/* ---- current move card, eval bar, board */
.mc { border-left: 5px solid #888; border-radius: 14px; padding: 14px 18px; background: var(--surface); border-top:1px solid var(--line); border-right:1px solid var(--line); border-bottom:1px solid var(--line); }
.mc .t { font-weight:900; font-size:19px; color: var(--text); } .mc .t i { font-style:normal; font-weight:800; margin-left:10px; font-size:15px; }
.mc .e { margin-top:6px; color: var(--body); font-size:15px; line-height:1.5; } .mc .w { margin-top:8px; color: var(--muted); font-size:13px; font-weight:600; } .mc .w b { color: var(--accent_text); }
.evalbar { width:24px; border-radius:10px; overflow:hidden; border:1px solid rgba(128,128,128,.55); display:flex; flex-direction:column; background:#262626; }
.evalbar .b { background:#1a1a1a; } .evalbar .w { background:#f4f4f4; }
.evalbar .b, .evalbar .w { animation: barfill .45s cubic-bezier(.25,1,.5,1) both; transform-origin: top; }
@keyframes barfill { from { transform: scaleY(.0); opacity:.4 } to { transform: scaleY(1); opacity:1 } }
.boardwrap { background: var(--surface); border:1px solid var(--line); border-radius: var(--radius); padding: 14px; }
.boardwrap svg { border-radius: 10px; display:block; }
@keyframes pieceslide { 0% { transform: translate(var(--fx), var(--fy)) scale(1); filter: drop-shadow(0 0 0 rgba(0,0,0,0)); }
  45% { transform: translate(calc(var(--fx) + (var(--tx) - var(--fx)) * .8), calc(var(--fy) + (var(--ty) - var(--fy)) * .8)) scale(1.22); filter: drop-shadow(0 5px 4px rgba(0,0,0,.4)); }
  75% { transform: translate(var(--tx), var(--ty)) scale(.95); filter: drop-shadow(0 1px 1px rgba(0,0,0,.2)); }
  100% { transform: translate(var(--tx), var(--ty)) scale(1); filter: drop-shadow(0 0 0 rgba(0,0,0,0)); } }
.pslide { animation: pieceslide .42s cubic-bezier(.22,1,.36,1) both; transform-box: fill-box; transform-origin: center; }
@keyframes pop { from { transform: scale(.6); opacity:0 } to { transform: scale(1); opacity:1 } }
.badge-pop { animation: pop .3s cubic-bezier(.34,1.56,.64,1) .12s both; transform-box: fill-box; transform-origin: center; }
@media (prefers-reduced-motion: reduce) { .pslide, .badge-pop, .evalbar .b, .evalbar .w { animation: none !important; } }

/* ---- key moments, verdict */
.km { min-height: 190px; border-radius:16px; padding:14px 16px; background: var(--surface); border:1px solid var(--line); height:100%; }
.km .h { font-weight:900; color: var(--text); font-size:16px; } .km .c { font-weight:800; font-size:13px; margin:2px 0 6px; } .km .x { color: var(--body); font-size:13.5px; line-height:1.45; }
.verdict li { margin-bottom: 5px; line-height:1.5; color: var(--body); }
.tag { font-family: ui-monospace, Menlo, Consolas, monospace; font-size:12.5px; background: var(--tag_bg); border:1px solid var(--line); color: var(--tag_text); border-radius:8px; padding:3px 9px; display:inline-block; margin-top:6px; }
.focus { border:1px solid color-mix(in srgb, var(--accent) 55%, transparent); background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 20%, transparent), color-mix(in srgb, var(--accent) 6%, transparent)); border-radius: var(--radius); padding:16px 20px; }
.focus .f { font-weight:900; font-size:18px; color: var(--text); } .focus .k { color: var(--muted); font-size:12.5px; font-weight:800; letter-spacing:.6px; } .focus .d { margin-top:4px; color: var(--body); }
.invisible-frame, .st-key-kbnav { height:0; overflow:hidden; margin:0; padding:0; }

/* ---- move list (pills) */
.st-key-movelist { border-radius: 14px; }
.st-key-movelist [data-testid="stButtonGroup"] { gap: 4px; }
.st-key-movelist button { padding: 2px 9px; min-height: 30px; font-size: 13.5px; font-weight:700; border-radius: 9px; }

/* ---- game cards */
[class*="st-key-gc_"] { padding: 14px 16px; border-radius: var(--radius); background: var(--surface); border:1px solid var(--line); transition: border-color .15s ease, transform .15s ease; }
[class*="st-key-gc_"]:hover { border-color: color-mix(in srgb, var(--accent) 65%, transparent); transform: translateY(-1px); }
[class*="st-key-gc_"]:has(.stripe.win) { border-left: 5px solid var(--win); } [class*="st-key-gc_"]:has(.stripe.loss) { border-left: 5px solid var(--loss); }
[class*="st-key-gc_"]:has(.stripe.draw) { border-left: 5px solid var(--draw); }
.gm .who { font-weight:800; color: var(--text); font-size:16px; } .gm .sub { color: var(--muted); font-size:13px; font-weight:600; margin-top:2px; }
.chip { display:inline-block; background: var(--surface2); color: var(--body); border-radius:8px; padding:1px 8px; font-size:12px; font-weight:700; margin-right:6px; }
.strip { display:flex; gap:10px; flex-wrap:wrap; margin: 4px 0 14px; }
.strip .s { background: var(--surface); border:1px solid var(--line); border-radius:14px; padding:8px 14px; font-size:13px; color: var(--muted); font-weight:700; }
.strip .s b { display:block; font-size:20px; color: var(--text); line-height:1.15; }

/* ---- hub cards, coming-soon badges */
.hub { border:1px solid var(--line); border-radius: 22px; padding:20px 22px; background: var(--glass); backdrop-filter: blur(12px); box-shadow: 0 12px 34px var(--shadow); height:100%; position:relative; overflow:hidden; }
.hub::after { content:""; position:absolute; right:-40px; top:-40px; width:140px; height:140px; border-radius:50%; background: var(--orb, #7fa650); opacity:.16; filter: blur(8px); }
.hub .i { font-size:30px; } .hub .h { font-weight:900; color: var(--text); font-size:19px; margin:8px 0 4px; } .hub .x { color: var(--body); font-size:14.5px; line-height:1.5; }
.badge { display:inline-block; font-size:11.5px; font-weight:800; letter-spacing:.06em; text-transform:uppercase; border-radius:999px; padding:3px 10px; margin-top:10px; background: var(--surface2); color: var(--muted); }
.badge.live { background: color-mix(in srgb, var(--accent) 24%, transparent); color: var(--accent_text); }

/* ---- insights */
.kpi { display:flex; gap:14px; flex-wrap:wrap; margin-bottom: 4px; }
.kpi .k { flex:1; min-width:150px; }
.kpi .k small { color: var(--muted); font-weight:800; font-size:11.5px; letter-spacing:.08em; text-transform:uppercase; }
.kpi .k b { display:block; font-size:30px; font-weight:900; line-height:1.15; color: var(--text); }
.kpi .k span { color: var(--muted); font-size:13px; font-weight:600; }
.grad-text { background: linear-gradient(90deg, #7fa650, #3fb7a4, #6c8cff); -webkit-background-clip:text; background-clip:text; color: transparent !important; }
.note { display:flex; gap:12px; align-items:flex-start; padding:12px 14px; border-radius:14px; background: var(--surface); border:1px solid var(--line); margin-bottom:10px; }
.note .ic { font-size:20px; line-height:1.3; } .note .t { font-weight:800; color: var(--text); } .note .d { color: var(--body); font-size:14.5px; line-height:1.5; margin-top:2px; }
.phasebar { display:grid; grid-template-columns: 96px 1fr 56px; align-items:center; gap:12px; margin:10px 0; }
.phasebar .n { font-weight:800; color: var(--text); } .phasebar .v { font-weight:900; color: var(--text); text-align:right; }
.phasebar .tr { height:14px; border-radius:999px; background: var(--ring_bg); overflow:hidden; } .phasebar .fl { height:100%; border-radius:999px; background: linear-gradient(90deg, var(--c1), var(--c2)); animation: grow .7s cubic-bezier(.25,1,.5,1) both; transform-origin:left; }
@keyframes grow { from { transform: scaleX(0) } to { transform: scaleX(1) } }
.phasebar.empty .tr { opacity:.5; } .phasebar.empty .v { color: var(--muted); font-weight:700; font-size:12.5px; }

/* ---- lessons */
.lesson-title { font-size:22px; font-weight:900; color: var(--text); margin:0; } .lesson-sub { color: var(--muted); margin:2px 0 8px; }
.card h4, .exp h4, .glass h4 { padding:0 !important; }
.sechead { margin: 14px 0 8px !important; padding:0 !important; font-size:12px !important; letter-spacing:.08em; text-transform:uppercase; color: var(--muted) !important; font-weight:800 !important; }
.exp h4 { margin:0 0 6px; font-size:12px; letter-spacing:.08em; text-transform:uppercase; color: var(--muted) !important; font-weight:800; }
.exp p { color: var(--body); line-height:1.55; margin:0 0 8px; font-size:15px; } .exp .sanline { font-weight:900; color: var(--text); font-size:17px; margin-bottom:6px; }
.exp ul { margin:0 0 4px; padding-left:18px; color: var(--body); } .exp li { margin-bottom:4px; line-height:1.5; }
.eng { display:grid; grid-template-columns: 64px 1fr; gap:10px; align-items:baseline; padding:7px 0; border-bottom:1px solid var(--line); }
.eng:last-child { border-bottom:0; } .eng .ev { font-weight:900; color: var(--text); font-variant-numeric: tabular-nums; } .eng .ln { color: var(--body); font-size:14px; }
.eng .ev.pos { color: var(--win); } .eng .ev.neg { color: var(--loss); }
.crumbs { display:flex; flex-wrap:wrap; gap:6px; margin: 2px 0 10px; } .crumbs span { font-weight:800; font-size:13.5px; padding:2px 9px; border-radius:8px; background: var(--surface2); color: var(--text); }
.crumbs span.cur { background: color-mix(in srgb, var(--accent) 35%, transparent); }
@media (max-width: 760px) { .block-container { padding-left: 1rem; padding-right: 1rem; } .acc { flex-direction:column; align-items:flex-start; } }
</style>
"""


def css(mode: str = "dark") -> str:
    tok = TOKENS.get(mode, TOKENS["dark"])
    return _BASE.replace("__VARS__", " ".join(f"--{k}: {v};" for k, v in tok.items()))


CSS = css("dark")        # kept for anything that still imports the old name
