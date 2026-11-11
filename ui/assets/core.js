/* Shared browser-side chess toolkit for the Review, Puzzles and Lessons components.
   Everything here runs in the page, so stepping, moving and animating never wait for the server.
   Needs: globalThis.__Chess (chess.js) and SPRITES (piece drawings), both put in front of this file by ui/live.py. */
const Chess = globalThis.__Chess;
const NS = 'http://www.w3.org/2000/svg';
const FILES = 'abcdefgh', M = 15, Q = 45;
const el = (tag, attrs = {}, html) => { const n = document.createElement(tag); for (const k in attrs) n.setAttribute(k, attrs[k]); if (html !== undefined) n.innerHTML = html; return n; };
const sv = (tag, attrs = {}) => { const n = document.createElementNS(NS, tag); for (const k in attrs) n.setAttribute(k, attrs[k]); return n; };
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const sqName = (f, r) => FILES[f] + (r + 1);

class Board {
  /* opts: { flipped, interactive, canMove(from)->[to...] | null, onMove(from, to, promo)->bool (true = accepted), sideToMove(): 'w'|'b' } */
  constructor(host, opts = {}) {
    this.o = opts; this.flipped = !!opts.flipped; this.fen = null; this.host = host;
    this.pieces = new Map();                       // square -> <g>
    const svg = this.svg = sv('svg', { viewBox: '0 0 390 390', class: 'cb-svg' });
    svg.style.cssText = 'width:100%;height:auto;display:block;border-radius:10px;touch-action:none;user-select:none;-webkit-user-select:none';
    const defs = sv('defs'); for (const k in SPRITES) { const g = sv('g', { id: 'pc-' + k }); g.innerHTML = SPRITES[k]; defs.appendChild(g); }
    svg.appendChild(defs);
    svg.appendChild(sv('rect', { x: 0, y: 0, width: 390, height: 390, fill: '#1f2933' }));
    this.sqLayer = sv('g'); this.hiLayer = sv('g'); this.coordLayer = sv('g'); this.pcLayer = sv('g'); this.arrowLayer = sv('g'); this.topLayer = sv('g');
    this.arrowLayer.style.pointerEvents = 'none'; this.topLayer.style.pointerEvents = 'none'; this.hiLayer.style.pointerEvents = 'none';
    [this.sqLayer, this.hiLayer, this.coordLayer, this.pcLayer, this.arrowLayer, this.topLayer].forEach((g) => svg.appendChild(g));
    for (let r = 0; r < 8; r++) for (let f = 0; f < 8; f++) {
      const rect = sv('rect', { width: Q, height: Q, fill: (f + r) % 2 ? '#eeeed2' : '#769656' }); rect.dataset.sq = sqName(f, r); this.sqLayer.appendChild(rect);
    }
    this.drawCoords(); this.layoutSquares();
    host.appendChild(svg);
    this.sel = null; this.drag = null; this.last = null; this.arrows = []; this.badge = null; this.marks = [];
    svg.addEventListener('pointerdown', (e) => this.down(e));
    svg.addEventListener('pointermove', (e) => this.move(e));
    svg.addEventListener('pointerup', (e) => this.up(e));
    svg.addEventListener('pointercancel', () => this.cancelDrag());
  }
  xy(sq) { const f = FILES.indexOf(sq[0]), r = parseInt(sq[1]) - 1; return [M + (this.flipped ? 7 - f : f) * Q, M + (this.flipped ? r : 7 - r) * Q]; }
  center(sq) { const [x, y] = this.xy(sq); return [x + Q / 2, y + Q / 2]; }
  layoutSquares() { this.sqLayer.querySelectorAll('rect').forEach((r) => { const [x, y] = this.xy(r.dataset.sq); r.setAttribute('x', x); r.setAttribute('y', y); }); }
  drawCoords() {
    this.coordLayer.innerHTML = '';
    for (let i = 0; i < 8; i++) {
      const f = this.flipped ? 7 - i : i, r = this.flipped ? i : 7 - i;
      const a = sv('text', { x: M + i * Q + Q / 2, y: 10, 'text-anchor': 'middle', 'font-size': 10, fill: '#c9d1d9' }); a.textContent = FILES[f]; this.coordLayer.appendChild(a);
      const b = sv('text', { x: 6, y: M + i * Q + Q / 2 + 3.5, 'text-anchor': 'middle', 'font-size': 10, fill: '#c9d1d9' }); b.textContent = r + 1; this.coordLayer.appendChild(b);
      const c = sv('text', { x: M + i * Q + Q / 2, y: 387, 'text-anchor': 'middle', 'font-size': 10, fill: '#c9d1d9' }); c.textContent = FILES[f]; this.coordLayer.appendChild(c);
      const d = sv('text', { x: 384, y: M + i * Q + Q / 2 + 3.5, 'text-anchor': 'middle', 'font-size': 10, fill: '#c9d1d9' }); d.textContent = r + 1; this.coordLayer.appendChild(d);
    }
  }
  setFlipped(f) {
    f = !!f; if (f === this.flipped) return; this.flipped = f; this.layoutSquares(); this.drawCoords();
    for (const [sq, g] of this.pieces) this.place(g, sq, false);
    this.redrawOverlays();
  }
  place(g, sq, animate) {
    const [x, y] = this.xy(sq);
    g.style.transition = animate ? 'transform .2s cubic-bezier(.3,.8,.3,1)' : 'none';
    g.style.transform = `translate(${x}px,${y}px)`; g.dataset.sq = sq;
  }
  mkPiece(sym, sq, animate = false) {
    const g = sv('g', { class: 'pc' }); g.dataset.p = sym; g.appendChild(sv('use', { href: '#pc-' + sym })); this.place(g, sq, false); this.pcLayer.appendChild(g); this.pieces.set(sq, g); return g;
  }
  /* put the pieces of `fen` on the board (diffing, so unchanged pieces keep their elements) */
  sync(fen) {
    const want = new Map(); const rows = fen.split(' ')[0].split('/');
    rows.forEach((row, i) => { let f = 0; for (const ch of row) { if (/\d/.test(ch)) f += +ch; else { want.set(sqName(f, 7 - i), ch); f++; } } });
    for (const [sq, g] of [...this.pieces]) { if (want.get(sq) !== g.dataset.p) { g.remove(); this.pieces.delete(sq); } }
    for (const [sq, p] of want) if (!this.pieces.has(sq)) this.mkPiece(p, sq);
    const live = new Set(this.pieces.values()); [...this.pcLayer.children].forEach((c) => { if (!live.has(c)) c.remove(); });
    this.fen = fen;
  }
  /* show a position. mv = {from,to,promotion?,san?} animates that move (back=true: the move being taken back). */
  show(fen, o = {}) {
    clearTimeout(this._t);
    if (this.fen) this.sync(this.fen === fen ? fen : this.fen);   // settle any animation in progress
    const mv = o.move;
    if (mv && this.fen && this.fen !== fen) {
      const from = o.back ? mv.to : mv.from, to = o.back ? mv.from : mv.to;
      const g = this.pieces.get(from);
      if (g) {
        const cap = this.pieces.get(to);
        if (cap && !o.back) { cap.style.transition = 'opacity .18s'; cap.style.opacity = '0'; }
        this.pcLayer.appendChild(g);                                   // travel above the others
        this.pieces.delete(from); this.pieces.set(to, g); this.place(g, to, true);
        if (!o.back && g.dataset.p.toLowerCase() === 'k' && Math.abs(FILES.indexOf(from[0]) - FILES.indexOf(to[0])) === 2) {   // castling: the rook too
          const rk = from[1], ks = to[0] > from[0], rf = (ks ? 'h' : 'a') + rk, rt = (ks ? 'f' : 'd') + rk, rg = this.pieces.get(rf);
          if (rg) { this.pieces.delete(rf); this.pieces.set(rt, rg); this.place(rg, rt, true); }
        }
        if (o.back && g.dataset.p.toLowerCase() === 'k' && Math.abs(FILES.indexOf(from[0]) - FILES.indexOf(to[0])) === 2) {
          const rk = to[1], ks = from[0] > to[0], rf = (ks ? 'f' : 'd') + rk, rt = (ks ? 'h' : 'a') + rk, rg = this.pieces.get(rf);
          if (rg) { this.pieces.delete(rf); this.pieces.set(rt, rg); this.place(rg, rt, true); }
        }
        this._t = setTimeout(() => this.sync(fen), 210);
      } else this.sync(fen);
    } else this.sync(fen);
    this.fen = fen;
    this.last = o.last || null; this.arrows = o.arrows || []; this.badge = o.badge || null; this.marks = o.marks || [];
    this.sel = null; this.redrawOverlays();
  }
  redrawOverlays() {
    this.hiLayer.innerHTML = ''; this.arrowLayer.innerHTML = ''; this.topLayer.innerHTML = '';
    const dark = (sq) => { const f = FILES.indexOf(sq[0]), r = parseInt(sq[1]) - 1; return (f + r) % 2 === 0; };
    if (this.last) for (const sq of this.last) { const [x, y] = this.xy(sq); this.hiLayer.appendChild(sv('rect', { x, y, width: Q, height: Q, fill: dark(sq) ? '#baca2b' : '#f6f669' })); }
    for (const m of this.marks) { const [x, y] = this.xy(m.sq); this.hiLayer.appendChild(sv('rect', { x, y, width: Q, height: Q, fill: m.color || 'rgba(255,214,0,.5)', class: m.cls || '' })); }
    if (this.sel) { const [x, y] = this.xy(this.sel); this.hiLayer.appendChild(sv('rect', { x, y, width: Q, height: Q, fill: 'rgba(255,214,0,.45)' })); }
    for (const a of this.arrows) this.arrow(a.from, a.to, a.color);
    if (this.sel && this.o.canMove) {
      const targets = this.o.canMove(this.sel) || [];
      for (const to of targets) {
        const [cx, cy] = this.center(to);
        if (this.pieces.has(to)) this.topLayer.appendChild(sv('circle', { cx, cy, r: 20, fill: 'none', stroke: 'rgba(20,90,40,.65)', 'stroke-width': 5 }));
        else this.topLayer.appendChild(sv('circle', { cx, cy, r: 7.5, fill: 'rgba(20,90,40,.6)' }));
      }
    }
    if (this.badge && this.last) {
      const [x, y] = this.xy(this.last[1]); const cx = x + Q - 8, cy = y + 9, b = this.badge;
      const g = sv('g', { class: 'badge-pop' }); g.appendChild(sv('circle', { cx, cy, r: 10, fill: b.color, stroke: '#fff', 'stroke-width': 1.6 }));
      const t = sv('text', { x: cx, y: cy + 3.6, 'font-size': b.sym.length > 1 ? 10 : 12, 'font-weight': 800, fill: '#fff', 'text-anchor': 'middle' }); t.textContent = b.sym; g.appendChild(t); this.topLayer.appendChild(g);
    }
  }
  arrow(from, to, color) {
    const [x1, y1] = this.center(from), [x2, y2] = this.center(to);
    const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len, head = 13, w = 3.4;
    const ex = x2 - ux * head, ey = y2 - uy * head;
    this.arrowLayer.appendChild(sv('line', { x1: x1 + ux * 8, y1: y1 + uy * 8, x2: ex, y2: ey, stroke: color, 'stroke-width': w * 2, 'stroke-linecap': 'butt' }));
    this.arrowLayer.appendChild(sv('polygon', { points: `${x2},${y2} ${ex - uy * 9},${ey + ux * 9} ${ex + uy * 9},${ey - ux * 9}`, fill: color }));
  }
  /* ---- clicking and dragging ---- */
  squareAt(e) {
    const r = this.svg.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width * 390, y = (e.clientY - r.top) / r.height * 390;
    const c = Math.floor((x - M) / Q), rw = Math.floor((y - M) / Q); if (c < 0 || c > 7 || rw < 0 || rw > 7) return null;
    return sqName(this.flipped ? 7 - c : c, this.flipped ? rw : 7 - rw);
  }
  down(e) {
    if (!this.o.interactive || !this.o.interactive() || e.button > 0) return;
    const sq = this.squareAt(e); this.closePromo();
    if (!sq) { this.sel = null; this.redrawOverlays(); return; }
    if (this.sel && this.sel !== sq && (this.o.canMove(this.sel) || []).includes(sq)) { this.attempt(this.sel, sq); return; }
    const targets = this.o.canMove(sq);
    if (targets && targets.length && this.pieces.has(sq)) {
      this.sel = this.sel === sq ? null : sq; this.redrawOverlays();
      if (this.sel) { this.drag = { from: sq, g: this.pieces.get(sq), moved: false }; this.drag.g.style.transition = 'none'; try { this.svg.setPointerCapture(e.pointerId); } catch (_) {} }
    } else { this.sel = null; this.redrawOverlays(); }
  }
  move(e) {
    const d = this.drag; if (!d) return;
    const r = this.svg.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width * 390, y = (e.clientY - r.top) / r.height * 390;
    if (!d.moved && Math.hypot(x - this.center(d.from)[0], y - this.center(d.from)[1]) < 6) return;
    d.moved = true; this.pcLayer.appendChild(d.g); d.g.style.transform = `translate(${x - Q / 2}px,${y - Q / 2}px)`; d.g.style.cursor = 'grabbing';
  }
  up(e) {
    const d = this.drag; this.drag = null; if (!d) return;
    d.g.style.cursor = '';
    if (!d.moved) return;
    const sq = this.squareAt(e);
    if (sq && sq !== d.from && (this.o.canMove(d.from) || []).includes(sq)) this.attempt(d.from, sq, true);
    else { this.place(d.g, d.from, true); }
  }
  cancelDrag() { const d = this.drag; this.drag = null; if (d) this.place(d.g, d.from, true); }
  attempt(from, to, dropped) {
    const g = this.pieces.get(from), p = g ? g.dataset.p : '';
    const last = to[1];
    if (p.toLowerCase() === 'p' && ((p === 'P' && last === '8') || (p === 'p' && last === '1'))) { this.promo(from, to, p === 'P'); return; }
    this.commit(from, to, undefined, dropped);
  }
  commit(from, to, promo, dropped) {
    this.sel = null; this.redrawOverlays();
    const ok = this.o.onMove(from, to, promo, !!dropped);
    if (ok === false) { const g = this.pieces.get(from); if (g) this.place(g, from, true); }
  }
  promo(from, to, white) {
    this.closePromo(); const box = el('div', { class: 'cb-promo' });
    for (const [p, g] of [['q', white ? '♕' : '♛'], ['r', white ? '♖' : '♜'], ['b', white ? '♗' : '♝'], ['n', white ? '♘' : '♞']]) {
      const b = el('button', { title: p }, g); b.onclick = () => { this.closePromo(); this.commit(from, to, p); }; box.appendChild(b);
    }
    this.host.appendChild(box); this._promo = box;
  }
  closePromo() { if (this._promo) { this._promo.remove(); this._promo = null; } const g = this.pieces; }
}

/* the legal moves of the side to move, as {from: [to...]} */
function legalMap(chess) {
  const out = {};
  for (const m of chess.moves({ verbose: true })) { const a = (out[m.from] = out[m.from] || []); if (!a.includes(m.to)) a.push(m.to); }
  return out;
}

function evalBar(host) {
  host.style.cssText = 'display:flex;align-self:stretch';
  const bar = el('div', { class: 'evalbar cc-evalbar', style: 'flex:1;min-height:300px;position:relative' });
  const b = el('div', { class: 'b' }), w = el('div', { class: 'w' });
  for (const n of [b, w]) { n.style.animation = 'none'; n.style.transition = 'height .35s cubic-bezier(.25,1,.5,1)'; n.style.flex = 'none'; }
  bar.append(b, w); host.appendChild(bar);
  return { set(wp, flipped) {
    wp = Math.max(0, Math.min(100, wp)); bar.title = `White ${wp.toFixed(0)}% / Black ${(100 - wp).toFixed(0)}%`;
    b.style.height = (100 - wp) + '%'; w.style.height = wp + '%';
    bar.style.flexDirection = flipped ? 'column-reverse' : 'column';
  } };
}

/* page-wide keyboard handler that follows whichever component is showing */
function keys(map) {
  const w = window, prev = w.__ccKeys; if (prev) document.removeEventListener('keydown', prev, true);
  const h = (e) => {
    const f = map[e.key]; if (!f || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    const t = e.target, tag = t && t.tagName ? t.tagName.toLowerCase() : '';
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || (t && t.isContentEditable)) return;
    if (f() === false) return;
    e.preventDefault();
  };
  w.__ccKeys = h; document.addEventListener('keydown', h, true);
  return () => { if (w.__ccKeys === h) { document.removeEventListener('keydown', h, true); w.__ccKeys = null; } };
}

const CC_CSS = `
.cc-root { color: var(--body); font-family: inherit; }
.cc-root .cc-grid { display:grid; grid-template-columns: minmax(0,1.2fr) minmax(0,1fr); gap: 28px; align-items:start; }
@media (max-width: 900px) { .cc-root .cc-grid { grid-template-columns: 1fr; } }
.cc-root .bw { background: var(--surface); border:1px solid var(--line); border-radius: var(--radius, 16px); padding: 14px; transition: box-shadow .3s ease, border-color .3s ease; }
.cc-root .brow { display:flex; gap:12px; align-items:stretch; } .cc-root .bcol { flex:1; position:relative; min-width:0; }
.cc-btns { display:grid; gap:8px; margin-top:12px; }
.cc-btns.c4 { grid-template-columns: repeat(4, 1fr); } .cc-btns.c2 { grid-template-columns: 1fr 1fr; } .cc-btns.c3 { grid-template-columns: repeat(3, 1fr); }
.cc-btn { font: inherit; font-weight: 700; font-size: 15px; padding: 9px 10px; border-radius: 12px; border:1px solid var(--line); background: var(--surface); color: var(--text); cursor:pointer;
  transition: transform .12s ease, background .15s ease, box-shadow .15s ease, opacity .15s; min-height: 42px; }
.cc-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px var(--shadow); border-color: color-mix(in srgb, var(--accent) 55%, var(--line)); }
.cc-btn:active:not(:disabled) { transform: translateY(0) scale(.97); }
.cc-btn:disabled { opacity:.4; cursor:default; }
.cc-btn.primary { background: linear-gradient(135deg,#7fa650,#5b8a3a); color:#fff; border-color: transparent; }
.cc-btn.on { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }
.cc-tog { display:flex; gap:14px; flex-wrap:wrap; margin-top:12px; }
.cc-tog label { display:flex; align-items:center; gap:8px; cursor:pointer; font-size:14.5px; color: var(--text); user-select:none; }
.cc-tog input { appearance:none; width:38px; height:22px; border-radius:99px; background: var(--ring_bg, #888); position:relative; cursor:pointer; transition: background .2s; flex:none; }
.cc-tog input::after { content:''; position:absolute; top:3px; left:3px; width:16px; height:16px; border-radius:50%; background:#fff; transition: transform .2s cubic-bezier(.3,1.4,.5,1); }
.cc-tog input:checked { background: var(--accent); } .cc-tog input:checked::after { transform: translateX(16px); }
.cc-warn { padding: 10px 14px; border-radius: 12px; background: color-mix(in srgb, var(--loss, #d9534f) 14%, transparent); border:1px solid color-mix(in srgb, var(--loss, #d9534f) 45%, transparent); color: var(--text); font-size: 14px; }
.cc-root .shake { animation: shake .45s cubic-bezier(.36,.07,.19,.97) both !important; border-color: var(--loss) !important; }
.cc-root .glow { animation: winglow 1.1s ease-out both !important; border-color: var(--win) !important; }
.cc-line { display:grid; grid-template-columns: 112px minmax(0,1fr); gap: 12px; align-items:center; border:1px solid var(--line); border-radius: 14px; padding: 10px 12px; background: var(--surface); margin-bottom: 8px; }
.cc-sel { width:100%; font: inherit; font-size: 15px; padding: 10px 12px; border-radius: 12px; border:1px solid var(--line); background: var(--surface); color: var(--text); }
.cc-hint { color: var(--muted); font-size: 13px; margin-top: 10px; line-height: 1.45; }
.cc-root .mc, .cc-root .card, .cc-root .glass { animation: none !important; }
.cc-root .fade { animation: ccfade .16s ease both; } @keyframes ccfade { from { opacity:.0; transform: translateY(3px); } to { opacity:1; transform:none; } }
.cb-promo { position:absolute; left:50%; top:50%; transform: translate(-50%,-50%); display:flex; gap:8px; padding:10px 12px; border-radius:14px; background: var(--surface); border:1px solid var(--line); box-shadow: 0 12px 30px rgba(0,0,0,.4); z-index:5; }
.cb-promo button { font-size:28px; line-height:1; width:54px; height:54px; border-radius:12px; border:1px solid var(--line); background: var(--surface2); color: var(--text); cursor:pointer; }
.cb-promo button:hover { background: var(--accent); color:#fff; }
.cc-root .pc { will-change: transform; } .cc-root svg.cb-svg { cursor: default; }
.cc-pills { display:flex; flex-wrap:wrap; gap:6px; max-height: 300px; overflow:auto; padding: 2px; }
.cc-pill { font: inherit; font-size: 13.5px; font-weight: 700; padding: 4px 10px; border-radius: 99px; border:1px solid var(--line); background: var(--surface); color: var(--text); cursor:pointer; transition: background .12s, transform .1s; }
.cc-pill:hover { background: var(--surface2); } .cc-pill.cur { background: var(--accent); color:#fff; border-color: var(--accent); }
.cc-pill.no { background: transparent; border-color: transparent; color: var(--muted); cursor: default; padding-right: 2px; }
`;

function injectCss() {
  if (document.getElementById('cc-css')) return;
  const st = document.createElement('style'); st.id = 'cc-css'; st.textContent = CC_CSS; document.head.appendChild(st);
}
/* a game-position graph: win chance over the moves; clicking it jumps. points: [{wp}], keys: [{ply,color}] */
function graph(host, onPick) {
  const W = 600, H = 150, svg = sv('svg', { viewBox: `0 0 ${W} ${H + 18}`, style: 'width:100%;height:auto;display:block;cursor:pointer' });
  host.appendChild(svg);
  let st = null;
  const X = (i, n) => 8 + (W - 16) * (n ? i / n : 0), Y = (wp) => 6 + (H - 12) * (1 - wp / 100);
  svg.addEventListener('pointerdown', (e) => { if (!st) return; const r = svg.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width * W; onPick(Math.max(0, Math.min(st.n, Math.round((x - 8) / (W - 16) * st.n)))); });
  return { draw(wps, keys, ply, c) {
    const n = wps.length - 1; st = { n }; svg.innerHTML = '';
    let d = `M ${X(0, n)} ${H - 6}`; wps.forEach((w, i) => { d += ` L ${X(i, n)} ${Y(w)}`; }); d += ` L ${X(n, n)} ${H - 6} Z`;
    svg.appendChild(sv('path', { d, fill: c.area, opacity: .85 }));
    svg.appendChild(sv('line', { x1: 8, x2: W - 8, y1: Y(50), y2: Y(50), stroke: c.muted, 'stroke-dasharray': '4 4' }));
    for (const v of [0, 100]) svg.appendChild(sv('line', { x1: 8, x2: W - 8, y1: Y(v), y2: Y(v), stroke: c.line, 'stroke-width': .6 }));
    for (const k of keys) svg.appendChild(sv('circle', { cx: X(k.ply, n), cy: Y(wps[k.ply]), r: 5.5, fill: k.color, stroke: c.text, 'stroke-width': 1.3 }));
    svg.appendChild(sv('line', { x1: X(ply, n), x2: X(ply, n), y1: 2, y2: H - 4, stroke: '#e6b800', 'stroke-width': 2.2 }));
    for (let m = 5; m <= n / 2; m += 5) { const t = sv('text', { x: X(m * 2, n), y: H + 12, 'font-size': 11, fill: c.muted, 'text-anchor': 'middle' }); t.textContent = m; svg.appendChild(t); }
  } };
}
