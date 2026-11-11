/* Opening lesson player: the whole lesson tree is in the page, so every step, line and section jump is instant.
   Python is asked only for Stockfish's lines (the engine overlay, and positions the lesson does not cover). */
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  injectCss();
  let I = parentElement.__ls;
  if (I && I.id === data.slug) { I.data = data; I.engineUpdated(); return; }
  if (I && I.dispose) I.dispose();
  parentElement.innerHTML = '';
  I = parentElement.__ls = { id: data.slug, data };
  const N = data.nodes, D = () => I.data;
  const byEpd = {}; N.forEach((n, i) => { if (!(n.ep in byEpd)) byEpd[n.ep] = i; });
  let path = [], flipped = data.side === 'black', showEng = false, engTimer = null;

  const root = el('div', { class: 'cc-root' });
  root.innerHTML = `<div class="lesson-title">${data.icon} ${esc(data.title)}</div><div class="lesson-sub">${data.intro}</div>
    <div class="cc-btns" data-secs style="grid-template-columns:repeat(${data.sections.length + 1}, minmax(0,1fr));margin:10px 0 16px"></div>
    <div class="cc-grid" style="grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)"><div class="L"><div class="bw"><div class="brow"><div class="bcol"></div></div></div>
    <div class="cc-btns c4"><button class="cc-btn" data-a="first" title="Back to the start (Home)">⏮</button><button class="cc-btn" data-a="prev" title="Take back a move (←)">◀</button><button class="cc-btn" data-a="next" title="Play the main line (→)">▶</button><button class="cc-btn" data-a="last" title="Follow the main line to its end (End)">⏭</button></div>
    <div class="cc-tog"><label><input type="checkbox" data-t="eng">Top engine moves</label><label><input type="checkbox" data-t="flip">Flip board</label></div>
    <div style="margin-top:12px"><select class="cc-sel" data-own><option value="">Try your own move…</option></select></div>
    <div class="cc-hint">Click a piece to see where it can go, then click a square (or drag). ← → on your keyboard take back / play the main line.</div></div>
    <div class="R"><div class="crumbs" data-crumbs></div><div data-card></div><div data-lines></div><div data-ahead></div><div data-eng></div></div></div>`;
  parentElement.appendChild(root);
  const q = (s) => root.querySelector(s);
  const secBox = q('[data-secs]');
  const startB = el('button', { class: 'cc-btn', 'data-sec': '-1' }, '🏁 Start'); secBox.appendChild(startB);
  data.sections.forEach((s, i) => secBox.appendChild(el('button', { class: 'cc-btn', 'data-sec': i }, `${s.icon} ${esc(s.title)}`)));

  const fenOf = (p) => { const c = new Chess(); for (const u of p) c.move({ from: u.slice(0, 2), to: u.slice(2, 4), promotion: u[4] }); return c; };
  const epd = (fen) => fen.split(' ').slice(0, 4).join(' ');
  function resolve(p, c) {
    let id = 0;
    for (const u of p) { const nx = N[id].c.find((k) => N[k].u === u); if (nx === undefined) { id = -1; break; } id = nx; }
    if (id >= 0) return id;
    const e = byEpd[epd(c.fen())]; return e === undefined ? -1 : e;
  }
  const effOf = (id) => (id >= 0 ? (N[id].al >= 0 ? N[id].al : id) : -1);
  function pathTo(id) { const out = []; while (id > 0) { out.push(N[id].u); id = N[id].p; } return out.reverse(); }
  function engineFor(fen) { const e = D().engine; return e && e.fen === fen ? e : null; }

  let chess = new Chess();
  const board = new Board(q('.bcol'), {
    flipped, interactive: () => true,
    canMove: (from) => (chess.isGameOver() ? [] : legalMap(chess)[from] || []),
    onMove: (from, to, promo, dropped) => {
      let m; try { m = chess.move({ from, to, promotion: promo || 'q' }); chess.undo(); } catch (e) { return false; }
      path = path.concat([from + to + (m.promotion || '')]); render({ move: { from, to }, back: false, dropped }); return true;
    },
  });

  function render(anim) {
    chess = fenOf(path); const fen = chess.fen();
    const id = resolve(path, chess), eff = effOf(id), node = id >= 0 ? N[id] : null, onTree = id >= 0;
    const eng = (showEng || !onTree) ? engineFor(fen) : null;
    let arrows = [];
    if (eng && eng.lines.length) { const cols = ['#7fa650cc', '#e0a82ecc', '#d9534fcc']; eng.lines.slice(0, 3).forEach((l, i) => { if (l.first) arrows.push({ from: l.first.slice(0, 2), to: l.first.slice(2, 4), color: cols[i] }); }); }
    const lastU = path.length ? path[path.length - 1] : null;
    board.show(fen, { last: lastU ? [lastU.slice(0, 2), lastU.slice(2, 4)] : null, arrows, move: anim && !anim.dropped ? anim.move : null, back: anim && anim.back });
    // crumbs
    const b = new Chess(), cr = [];
    path.forEach((u, i) => { const no = b.moveNumber(), w = b.turn() === 'w'; const m = b.move({ from: u.slice(0, 2), to: u.slice(2, 4), promotion: u[4] }); cr.push(`<span class="${i === path.length - 1 ? 'cur' : ''}">${w ? no + '.' + m.san : (i === 0 ? no + '...' + m.san : m.san)}</span>`); });
    q('[data-crumbs]').innerHTML = cr.join('');
    // explanation
    const sec = node && node.sec >= 0 ? data.sections[node.sec] : null;
    const cardBox = q('[data-card]');
    if (!node) {
      cardBox.innerHTML = `<div class="card exp fade"><h4>Off the lesson tree</h4><p>That move isn't covered by this lesson, so there is no prepared explanation here. Stockfish's three best lines for this position are below. Take the move back to return to the lesson.</p></div>`;
    } else {
      const note = N[eff].n || (path.length ? 'Book move. Keep following the plan of this variation.' : data.intro);
      const alias = node.al >= 0 ? `<p class="soft">🔀 A different move order reached this same position, so the same ideas apply.</p>` : '';
      cardBox.innerHTML = `<div class="card exp fade"><h4>${esc(sec ? sec.title : data.title)}</h4><div class="sanline">${node.l}</div><p>${note}</p>${alias}</div>` +
        (sec && path.length ? `<div class="card exp fade" style="margin-top:10px"><h4>Structure and plan</h4><p>${sec.summary}</p></div>` : '');
    }
    // lines: always at least three
    let L = [];
    if (node) L = D().lines[eff] || [];
    else if (eng) L = eng.lines.slice(0, 3).map((l) => ({ first: l.first, text: l.line, src: 'engine', eval: l.eval }));
    const lb = q('[data-lines]');
    if (L.length) {
      lb.innerHTML = `<h4 class="sechead">Top ${L.length} lines from here</h4>` + L.map((l, i) => `<div class="cc-line fade"><button class="cc-btn" data-play="${l.first}">▶ Line ${i + 1}</button><div class="exp"><p style="margin:0"><b>${esc(l.text)}</b>${l.src === 'engine' ? ` <span class="chip" title="Suggested by Stockfish, not part of the lesson">🤖 engine ${esc(l.eval || '')}</span>` : ''}</p></div></div>`).join('');
    } else if (!node && !chess.isGameOver()) lb.innerHTML = `<h4 class="sechead">Top lines from here</h4><div class="cc-line"><div class="exp"><p style="margin:0;color:var(--muted)">${D().engine_error ? esc(D().engine_error) : 'Stockfish is thinking…'}</p></div></div>`;
    else lb.innerHTML = '';
    const A = node ? (D().ahead[eff] || []) : [];
    q('[data-ahead]').innerHTML = A.length ? `<h4 class="sechead">What to do in the next few moves</h4>` + A.map((o) => `<div class="cc-line fade"><button class="cc-btn" data-play="${o.u}">▶ ${o.l}</button><div class="exp"><p style="margin:0"><b>${esc(o.text)}</b></p>${o.r.length ? `<p style="margin:2px 0 0;font-size:13.5px">${o.r.map((r) => `If <b>${r.l}</b> → then ${esc(r.text)}`).join('<br>')}</p>` : ''}</div></div>`).join('')
      : (node && path.length && !(D().lines[eff] || []).length ? `<div class="card exp" style="margin-top:10px"><h4>End of this line</h4><p>The prepared line stops here. Try your own move on the board, or go back and pick another branch.</p></div>` : '');
    const eb = q('[data-eng]');
    if (showEng && eng && eng.lines.length) eb.innerHTML = `<div class="card exp" style="margin-top:10px"><h4>Top engine lines (Stockfish)</h4>${eng.lines.map((l) => `<div class="eng"><div class="ev ${l.tone}">${esc(l.eval)}</div><div class="ln">${esc(l.line)}</div></div>`).join('')}</div>`;
    else if (showEng && chess.isGameOver()) eb.innerHTML = `<div class="card exp" style="margin-top:10px"><p>The game is over in this position.</p></div>`;
    else if (showEng && !eng) eb.innerHTML = `<div class="card exp" style="margin-top:10px"><h4>Top engine lines (Stockfish)</h4><div class="eng"><div class="ev"></div><div class="ln" style="color:var(--muted)">Thinking…</div></div></div>`;
    else eb.innerHTML = '';
    // controls
    root.querySelector('[data-a=prev]').disabled = !path.length;
    root.querySelector('[data-a=next]').disabled = !(eff >= 0 && N[eff].c.length);
    secBox.querySelectorAll('[data-sec]').forEach((b2) => { const k = +b2.dataset.sec; b2.classList.toggle('primary', k >= 0 && node && node.sec === k); });
    const sel = q('[data-own]'); sel.innerHTML = '<option value="">Try your own move…</option>' + chess.moves().sort().map((s) => `<option>${s}</option>`).join('');
    wantEngine();
  }
  function wantEngine() {
    clearTimeout(engTimer);
    const c = chess, id = resolve(path, c);
    if (!(showEng || id < 0) || c.isGameOver()) return;
    const fen = c.fen(); if (engineFor(fen)) return;
    engTimer = setTimeout(() => setTriggerValue('engine', fen), 300);
  }
  I.engineUpdated = () => render(null);
  const mainNext = () => { const id = effOf(resolve(path, chess)); return id >= 0 && N[id].c.length ? N[N[id].c[0]].u : null; };
  function step(u) { path = path.concat([u]); const f = u.slice(0, 2), t = u.slice(2, 4); render({ move: { from: f, to: t }, back: false }); }
  const act = {
    first: () => { path = []; render(null); },
    prev: () => { if (!path.length) return; const u = path[path.length - 1]; path = path.slice(0, -1); render({ move: { from: u.slice(0, 2), to: u.slice(2, 4) }, back: true }); },
    next: () => { const u = mainNext(); if (u) step(u); },
    last: () => { let id = effOf(resolve(path, chess)); const p = path.slice(); while (id >= 0 && N[id].c.length) { const k = N[id].c[0]; p.push(N[k].u); id = effOf(k); } path = p; render(null); },
  };
  root.addEventListener('click', (e) => {
    const a = e.target.closest('[data-a]'); if (a && !a.disabled) { act[a.dataset.a](); return; }
    const pl = e.target.closest('[data-play]'); if (pl) { step(pl.dataset.play); return; }
    const s = e.target.closest('[data-sec]');
    if (s) { const k = +s.dataset.sec; path = k < 0 ? [] : pathTo(data.sections[k].start); render(null); }
  });
  root.addEventListener('change', (e) => {
    const t = e.target.dataset.t;
    if (t === 'eng') { showEng = e.target.checked; render(null); }
    if (t === 'flip') { flipped = e.target.checked; board.setFlipped(flipped); render(null); }
    if (e.target.dataset.own !== undefined && e.target.value) { const m = chess.move(e.target.value); chess.undo(); step(m.from + m.to + (m.promotion || '')); }
  });
  q('input[data-t=flip]').checked = flipped;
  const stopKeys = keys({ ArrowLeft: () => root.isConnected && act.prev(), ArrowRight: () => root.isConnected && act.next(), Home: () => root.isConnected && act.first(), End: () => root.isConnected && act.last() });
  I.dispose = () => stopKeys(); I.state = () => ({ path, id: resolve(path, chess) });
  render(null);
}
