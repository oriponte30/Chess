"""All CSS in one place (design tokens first, so the look is changed by editing a handful of variables)."""
CSS = """
<style>
:root {
  --bg: #0b1118; --bg2: #101a24; --surface: rgba(255,255,255,.04); --surface2: rgba(255,255,255,.07);
  --line: rgba(255,255,255,.09); --text: #e8eef4; --muted: #8b9db0; --accent: #7fa650; --accent2: #a3d160;
  --win: #4caf7d; --loss: #e5645a; --draw: #8b9db0; --radius: 18px;
}
[data-testid="stAppViewContainer"] { background: radial-gradient(1200px 600px at 80% -10%, #1a2a36 0%, transparent 60%), var(--bg); }
[data-testid="stHeader"] { background: rgba(11,17,24,.72); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
[data-testid="stSidebar"] { background: var(--bg2); border-right: 1px solid var(--line); }
.block-container { padding-top: 4.2rem; max-width: 1240px; }
h1, h2, h3, h4 { color: #fff !important; letter-spacing: -.01em; }

/* ---- brand + page headers */
.brand { display:flex; align-items:center; gap:10px; margin: 2px 0 10px; }
.brand .logo { width:38px; height:38px; border-radius:12px; display:grid; place-items:center; font-size:22px;
  background: linear-gradient(135deg, var(--accent), #4f7a2c); box-shadow: 0 6px 18px rgba(127,166,80,.35); }
.brand b { font-size:18px; color:#fff; letter-spacing:-.02em; } .brand small { display:block; color:var(--muted); font-size:12px; margin-top:-2px; }
.pagehead { margin: 0 0 14px; } .pagehead h1 { margin:0; padding:0; font-size:28px; font-weight:800; line-height:1.15; } .pagehead p { margin:4px 0 0; color:var(--muted); font-size:15px; }

/* ---- cards */
.card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px 20px; box-shadow: 0 8px 24px rgba(0,0,0,.18); }
.card h4 { margin: 0 0 10px; font-size: 12px; letter-spacing:.08em; text-transform: uppercase; color: var(--muted) !important; font-weight:800; }
.soft { color: var(--muted); }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: var(--radius); }
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button { border-radius: 12px; font-weight: 700; transition: transform .08s ease, box-shadow .15s ease; }
div[data-testid="stButton"] button:active { transform: scale(.97); }
div[data-testid="stButton"] button[kind="primary"] { background: linear-gradient(135deg, var(--accent), #5d8a35); border: 0; color:#fff; box-shadow: 0 6px 16px rgba(127,166,80,.28); }

/* ---- game header, pills */
.gh { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
.gh .vs { font-weight:800; font-size:19px; color:#fff; } .gh .meta { color:var(--muted); font-size:13.5px; font-weight:600; }
.pill { display:inline-block; border-radius:999px; padding:3px 12px; font-weight:800; font-size:12.5px; }
.pill.win { background:rgba(76,175,125,.18); color:#7be0a8; } .pill.loss { background:rgba(229,100,90,.18); color:#ff9b93; } .pill.draw { background:rgba(139,157,176,.2); color:#c4d0dc; }
.pill.op { background: var(--surface2); color:#cfd8e3; }

/* ---- accuracy rings and counts */
.acc { display:flex; align-items:center; gap:14px; } .acc.me { border-color: rgba(127,166,80,.55); box-shadow: 0 0 0 1px rgba(127,166,80,.25) inset, 0 8px 24px rgba(0,0,0,.18); }
.acc .who { font-size:12px; font-weight:800; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; }
.acc .nm { font-weight:800; color:#fff; font-size:15px; margin-top:2px; } .acc .sub { color:var(--muted); font-size:12.5px; font-weight:600; }
.ring { position:relative; width:78px; height:78px; flex:none; } .ring svg { width:78px; height:78px; transform: rotate(-90deg); }
.ring .v { position:absolute; inset:0; display:grid; place-items:center; font-weight:900; font-size:20px; color:#fff; }
.mq { width:100%; border-collapse: collapse; font-size:14.5px; }
.mq td { padding: 5px 4px; border-bottom: 1px solid rgba(255,255,255,.06); }
.mq td.n { text-align:center; font-weight:800; width:54px; }
.mq .dot { display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:9px; vertical-align:-1px; }

/* ---- current move card, eval bar */
.mc { border-left: 5px solid #888; border-radius: 14px; padding: 14px 18px; background: var(--surface); border-top:1px solid var(--line); border-right:1px solid var(--line); border-bottom:1px solid var(--line); }
.mc .t { font-weight:900; font-size:19px; color:#fff; } .mc .t i { font-style:normal; font-weight:800; margin-left:10px; font-size:15px; }
.mc .e { margin-top:6px; color:#d5dde6; font-size:15px; line-height:1.5; } .mc .w { margin-top:8px; color:var(--muted); font-size:13px; font-weight:600; }
.evalbar { width:24px; border-radius:10px; overflow:hidden; border:1px solid rgba(255,255,255,.16); display:flex; flex-direction:column; background:#262626; }
.evalbar .b { background:#1a1a1a; transition: height .25s ease; } .evalbar .w { background:#f0f0f0; transition: height .25s ease; }
.boardwrap { background: var(--surface); border:1px solid var(--line); border-radius: var(--radius); padding: 14px; }
.boardwrap svg { border-radius: 10px; display:block; }

/* ---- key moments, verdict */
.km { min-height: 190px; border-radius:16px; padding:14px 16px; background: var(--surface); border:1px solid var(--line); height:100%; }
.km .h { font-weight:900; color:#fff; font-size:16px; } .km .c { font-weight:800; font-size:13px; margin:2px 0 6px; } .km .x { color:#cdd6df; font-size:13.5px; line-height:1.45; }
.verdict li { margin-bottom: 5px; line-height:1.5; }
.tag { font-family: ui-monospace, Menlo, Consolas, monospace; font-size:12.5px; background:#0a1016; border:1px solid #2a3947; color:#7fe0b0; border-radius:8px; padding:3px 9px; display:inline-block; margin-top:6px; }
.focus { border:1px solid rgba(127,166,80,.45); background: linear-gradient(135deg, rgba(127,166,80,.14), rgba(127,166,80,.05)); border-radius: var(--radius); padding:16px 20px; }
.focus .f { font-weight:900; font-size:18px; color:#fff; }

/* ---- invisible helper frame for the keyboard shortcuts */
.st-key-kbnav { height:0; overflow:hidden; margin:0; padding:0; }

/* ---- move list (pills) */
.st-key-movelist { border-radius: 14px; }
.st-key-movelist [data-testid="stButtonGroup"] { gap: 4px; }
.st-key-movelist button { padding: 2px 9px; min-height: 30px; font-size: 13.5px; font-weight:700; border-radius: 9px; }

/* ---- game cards */
[class*="st-key-gc_"] { padding: 14px 16px; border-radius: var(--radius); background: var(--surface); border:1px solid var(--line); transition: border-color .15s ease, transform .15s ease; }
[class*="st-key-gc_"]:hover { border-color: rgba(127,166,80,.5); transform: translateY(-1px); }
[class*="st-key-gc_"]:has(.stripe.win) { border-left: 5px solid var(--win); } [class*="st-key-gc_"]:has(.stripe.loss) { border-left: 5px solid var(--loss); }
[class*="st-key-gc_"]:has(.stripe.draw) { border-left: 5px solid var(--draw); }
.gm .who { font-weight:800; color:#fff; font-size:16px; } .gm .sub { color:var(--muted); font-size:13px; font-weight:600; margin-top:2px; }
.chip { display:inline-block; background: var(--surface2); color:#cfd8e3; border-radius:8px; padding:1px 8px; font-size:12px; font-weight:700; margin-right:6px; }
.strip { display:flex; gap:10px; flex-wrap:wrap; margin: 4px 0 14px; }
.strip .s { background: var(--surface); border:1px solid var(--line); border-radius:14px; padding:8px 14px; font-size:13px; color:var(--muted); font-weight:700; }
.strip .s b { display:block; font-size:20px; color:#fff; line-height:1.15; }

/* ---- coming-soon feature cards */
.soon { border:1px dashed rgba(255,255,255,.18); border-radius: var(--radius); padding:18px 20px; background: var(--surface); height:100%; }
.soon .i { font-size:26px; } .soon .h { font-weight:900; color:#fff; font-size:17px; margin:6px 0 4px; } .soon .x { color:var(--muted); font-size:14px; line-height:1.5; }
@media (max-width: 760px) { .block-container { padding-left: 1rem; padding-right: 1rem; } .acc { flex-direction:column; align-items:flex-start; } }
</style>
"""
