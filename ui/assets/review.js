/* Game review player: all the stepping, the eval bar, the graph, the move list and your own moves happen here in the browser.
   Python only supplies the analysed game once, and (on request) Stockfish's lines for a position. */
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  injectCss();
  let I = parentElement.__rv;
  if (I && I.id === data.id) { I.data = data; I.engineUpdated(); return; }
  if (I && I.dispose) I.dispose();
  parentElement.innerHTML = '';
  I = parentElement.__rv = { id: data.id, data };
  const D = () => I.data, n = data.plies.length;
  let ply = Math.max(0, Math.min(n, data.start || 0)), ex = null, flipped = !!data.flipped, showBest = true, showEng = false, engTimer = null, lastWp = 50;

  const root = el('div', { class: 'cc-root' });
  root.innerHTML = `<div class="cc-grid"><div class="L"><div class="bw"><div class="brow"><div class="eb"></div><div class="bcol"></div></div></div>
    <div class="cc-btns c4"><button class="cc-btn" data-a="first" title="Start (Home)">⏮</button><button class="cc-btn" data-a="prev" title="Previous (←)">◀</button><button class="cc-btn" data-a="next" title="Next (→)">▶</button><button class="cc-btn" data-a="last" title="End">⏭</button></div>
    <div class="cc-btns c2"><button class="cc-btn" data-a="pk">◀ Previous key moment</button><button class="cc-btn" data-a="nk">Next key moment ▶</button></div>
    <div class="cc-tog"><label><input type="checkbox" data-t="best" checked>Best move</label><label><input type="checkbox" data-t="eng">Engine top 3</label><label><input type="checkbox" data-t="flip">Flip board</label></div>
    <div class="cc-hint">Click a piece to see where it can go, then click a square (or drag) to try your own move. ← → step through the game · Home / End jump to the start / end</div></div>
    <div class="R"><div class="card-slot"></div><div class="eng-slot"></div><div class="bw" style="padding:8px 10px;margin-top:12px"><div class="gr"></div></div><div class="cc-pills" style="margin-top:12px"></div></div></div>`;
  parentElement.appendChild(root);
  const q = (s) => root.querySelector(s);
  const bar = evalBar(q('.eb'));
  const BAD = new Set(['Inaccuracy', 'Mistake', 'Blunder', 'Miss']);

  const fenAt = (p) => (p ? data.plies[p - 1].fen : data.startFen);
  const cur = () => (ex ? ex.chess : new Chess(fenAt(ply)));
  const board = new Board(q('.bcol'), {
    flipped,
    interactive: () => true,
    canMove: (from) => { const c = cur(); if (c.isGameOver()) return []; return legalMap(c)[from] || []; },
    onMove: (from, to, promo, dropped) => {
      const c = cur(); let m; try { m = c.move({ from, to, promotion: promo || 'q' }); } catch (e) { return false; }
      if (!ex) ex = { chess: c, moves: [] };
      ex.moves.push({ from, to, san: m.san, uci: from + to + (m.promotion || ''), before: m.before, color: m.color });
      render(dropped ? null : { move: { from, to }, back: false }); wantEngine(true); return true;
    },
  });
  const pills = q('.cc-pills');
  data.plies.forEach((m, i) => { const b = el('button', { class: 'cc-pill', 'data-p': i + 1 }); b.textContent = m.pill; pills.appendChild(b); });

  const gr = graph(q('.gr'), (p) => go(p));
  function engineFor(fen) { const e = D().engine; return e && e.fen === fen ? e : null; }

  function render(anim) {
    const c = cur(), fen = c.fen(); let last = null, badge = null, arrows = [], wp, bestShown = null;
    const m = ply ? data.plies[ply - 1] : null;
    if (ex) { const l = ex.moves[ex.moves.length - 1]; last = [l.from, l.to]; }
    else if (m) { last = [m.from, m.to]; if (m.sym) badge = { sym: m.sym, color: m.color }; }
    const eng = (showEng || ex) ? engineFor(fen) : null;
    if (eng && eng.lines.length) {
      const cols = ['#7fa650cc', '#e0a82ecc', '#d9534fcc'];
      eng.lines.slice(0, 3).forEach((l, i) => { if (l.first) arrows.push({ from: l.first.slice(0, 2), to: l.first.slice(2, 4), color: cols[i] }); });
      wp = eng.lines[0].wp;
    } else if (!ex && m && showBest && m.best) arrows.push({ from: m.best.slice(0, 2), to: m.best.slice(2, 4), color: '#7fa650cc' });
    if (wp === undefined) wp = ex ? lastWp : data.wps[ply];
    lastWp = wp;
    board.show(fen, { last, badge, arrows, move: anim && anim.move, back: anim && anim.back });
    bar.set(wp, flipped);
    // right side
    const cs = q('.card-slot');
    if (ex) {
      const b = new Chess(fenAt(ply)), sans = [];
      for (const mv of ex.moves) { const no = b.turn() === 'w' ? b.moveNumber() + '.' : (sans.length ? '' : b.moveNumber() + '...'); sans.push((no + mv.san).trim()); b.move({ from: mv.from, to: mv.to, promotion: mv.uci[4] || undefined }); }
      cs.innerHTML = `<div class="mc fade" style="border-color:var(--accent)"><div class="t">Your own line<i style="color:var(--accent)">exploring</i></div><div class="e">${esc(sans.join(' '))}<br>This is your own variation, not the game. Use ◀ to take a move back or <b>↩ Game</b> to return.</div></div>`;
    } else cs.innerHTML = `<div class="fade">${ply ? data.plies[ply - 1].card : data.startCard}</div>`;
    const es = q('.eng-slot');
    if (eng && eng.lines.length) es.innerHTML = `<div class="card exp" style="margin-top:12px"><h4>Top engine lines (Stockfish)</h4>${eng.lines.map((l) => `<div class="eng"><div class="ev ${l.tone}">${esc(l.eval)}</div><div class="ln">${esc(l.line)}</div></div>`).join('')}</div>`;
    else if ((showEng || ex) && c.isGameOver()) es.innerHTML = `<div class="card exp" style="margin-top:12px"><p>The game is over in this position.</p></div>`;
    else if (showEng || ex) es.innerHTML = D().engine_error ? `<div class="card exp" style="margin-top:12px"><p>${esc(D().engine_error)}</p></div>` : `<div class="card exp" style="margin-top:12px"><h4>Top engine lines (Stockfish)</h4><div class="eng"><div class="ev"></div><div class="ln" style="color:var(--muted)">Thinking…</div></div></div>`;
    else es.innerHTML = '';
    // controls
    root.querySelector('[data-a=prev]').disabled = ex ? false : ply <= 0;
    const nx = root.querySelector('[data-a=next]'); nx.disabled = ex ? false : ply >= n; nx.textContent = ex ? '↩ Game' : '▶';
    nx.title = ex ? 'Back to the game moves' : 'Next (→)'; root.querySelector('[data-a=prev]').title = ex ? 'Take back your move' : 'Previous (←)';
    const ks = data.keys; root.querySelector('[data-a=pk]').disabled = root.querySelector('[data-a=nk]').disabled = !ks.length;
    pills.querySelectorAll('.cc-pill').forEach((b) => b.classList.toggle('cur', !ex && +b.dataset.p === ply));
    const act = pills.querySelector('.cc-pill.cur'); if (act) { const t = act.offsetTop - pills.offsetTop; if (t < pills.scrollTop || t + act.offsetHeight > pills.scrollTop + pills.clientHeight) pills.scrollTop = t - pills.clientHeight / 2; }
    gr.draw(data.wps, data.keyDots, ply, data.colors);
  }
  function go(p, force) {
    p = Math.max(0, Math.min(n, p)); const was = ply, wasEx = !!ex;
    if (p === ply && !ex && !force) return;
    ex = null; ply = p;
    render(!wasEx && p === was + 1 ? { move: data.plies[p - 1], back: false } : !wasEx && p === was - 1 ? { move: data.plies[was - 1], back: true } : null);
    wantEngine(false);
  }
  function wantEngine(now) {
    clearTimeout(engTimer);
    if (!(showEng || ex)) return;
    const fen = cur().fen(); if (engineFor(fen) || cur().isGameOver()) return;
    engTimer = setTimeout(() => setTriggerValue('engine', fen), now ? 120 : 380);
  }
  I.engineUpdated = () => { if (showEng || ex) render(null); };
  const act = {
    first: () => go(0), last: () => go(n),
    prev: () => { if (ex) { const l = ex.moves.pop(); if (!ex.moves.length) { ex = null; render({ move: { from: l.from, to: l.to }, back: true }); } else { ex.chess.undo(); render({ move: { from: l.from, to: l.to }, back: true }); } wantEngine(true); } else go(ply - 1); },
    next: () => { if (ex) { ex = null; render(null); wantEngine(false); } else go(ply + 1); },
    pk: () => { const k = data.keys.filter((x) => x < ply); if (k.length) go(k[k.length - 1]); },
    nk: () => { const k = data.keys.filter((x) => x > ply); if (k.length) go(k[0]); },
  };
  root.addEventListener('click', (e) => {
    const b = e.target.closest('[data-a]'); if (b && act[b.dataset.a]) { act[b.dataset.a](); return; }
    const p = e.target.closest('.cc-pill'); if (p && p.dataset.p) go(+p.dataset.p);
  });
  root.addEventListener('change', (e) => {
    const t = e.target.dataset.t; if (!t) return;
    if (t === 'best') { showBest = e.target.checked; render(null); }
    if (t === 'eng') { showEng = e.target.checked; render(null); wantEngine(true); }
    if (t === 'flip') { flipped = e.target.checked; board.setFlipped(flipped); render(null); }
  });
  q('input[data-t=flip]').checked = flipped;
  const stopKeys = keys({ ArrowLeft: () => root.isConnected && act.prev(), ArrowRight: () => root.isConnected && act.next(), Home: () => root.isConnected && act.first(), End: () => root.isConnected && act.last() });
  I.dispose = () => { stopKeys(); };
  render(null);
}
