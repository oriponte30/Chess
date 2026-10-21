"""All CSS in one place."""
CSS = """
<style>
.block-container { padding-top: 1.4rem; max-width: 1250px; }
[data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #0f1720 0%, #16222d 100%); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #121c26; }
h1, h2, h3, h4 { color: #fff !important; }
.hero { display:flex; align-items:center; gap:14px; margin: 0 0 6px; }
.hero .logo { font-size: 38px; line-height: 1; }
.hero h1 { margin:0; font-size: 30px; letter-spacing: -.5px; }
.hero small { color:#8fa3b5; font-weight:600; display:block; font-size:13.5px; }
.card { background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.09); border-radius: 16px; padding: 14px 18px; }
.card h4 { margin: 0 0 8px; font-size: 15px; letter-spacing:.3px; text-transform: uppercase; color:#8fa3b5 !important; }
.gh { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
.gh .vs { font-weight:800; font-size:19px; color:#fff; }
.gh .meta { color:#8fa3b5; font-size:13.5px; font-weight:600; }
.pill { display:inline-block; border-radius:999px; padding:2px 11px; font-weight:800; font-size:12.5px; }
.pill.win { background:#1f6f43; color:#b8f5d0; } .pill.loss { background:#7a2a2a; color:#ffd0d0; } .pill.draw { background:#4a5563; color:#e0e6ec; }
.pill.op { background:rgba(255,255,255,.09); color:#cfd8e3; }
.acc { text-align:center; }
.acc .who { font-size:13px; font-weight:700; color:#8fa3b5; text-transform:uppercase; letter-spacing:.6px; }
.acc .num { font-size:40px; font-weight:900; line-height:1.1; color:#fff; }
.acc.me { border-color:#7fa650; box-shadow: 0 0 0 1px #7fa65066 inset; }
.acc small { color:#8fa3b5; font-weight:600; }
.mq { width:100%; border-collapse: collapse; font-size:14.5px; }
.mq td { padding: 5px 4px; border-bottom: 1px solid rgba(255,255,255,.07); }
.mq td.n { text-align:center; font-weight:800; width:54px; }
.mq .dot { display:inline-block; width:12px; height:12px; border-radius:50%; margin-right:8px; vertical-align:-1px; }
.mc { border-left: 6px solid #888; border-radius: 12px; padding: 12px 16px; background: rgba(255,255,255,.05); }
.mc .t { font-weight:900; font-size:18px; color:#fff; } .mc .t i { font-style:normal; font-weight:800; margin-left:10px; }
.mc .e { margin-top:6px; color:#d5dde6; font-size:15px; line-height:1.45; }
.mc .w { margin-top:8px; color:#8fa3b5; font-size:13px; font-weight:600; }
.evalbar { width:26px; border-radius:8px; overflow:hidden; border:1px solid rgba(255,255,255,.18); display:flex; flex-direction:column; background:#262626; }
.evalbar .b { background:#1a1a1a; } .evalbar .w { background:#f0f0f0; }
.evalbar span { font-size:10.5px; font-weight:800; text-align:center; padding:2px 0; }
.km { min-height: 190px; border-radius:14px; padding:12px 14px; background: rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.09); height:100%; }
.km .h { font-weight:900; color:#fff; font-size:16px; } .km .c { font-weight:800; font-size:13px; margin:2px 0 6px; } .km .x { color:#cdd6df; font-size:13.5px; line-height:1.4; }
.verdict li { margin-bottom: 4px; line-height:1.45; }
.tag { font-family: ui-monospace, Menlo, Consolas, monospace; font-size:12.5px; background:#0b1117; border:1px solid #2a3947; color:#7fe0b0; border-radius:8px; padding:3px 9px; display:inline-block; margin-top:6px; }
.focus { border:1px solid #7fa65066; background: rgba(127,166,80,.10); border-radius:14px; padding:12px 16px; }
.focus .f { font-weight:900; font-size:17px; color:#fff; }
div[data-testid="stButton"] button { border-radius: 10px; font-weight: 700; }
.st-key-movelist button { padding: 1px 6px; min-height: 28px; font-size: 14px; justify-content: flex-start; }
.st-key-movelist button p { text-align: left; width: 100%; font-weight: 700; }
.st-key-movelist [data-testid="stColumn"] { min-width: 0; }
.gm { display:flex; align-items:center; gap:12px; }
.gm .who { font-weight:800; color:#fff; font-size:16px; } .gm .sub { color:#8fa3b5; font-size:13px; font-weight:600; }
</style>
"""
