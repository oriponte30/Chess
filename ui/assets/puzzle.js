/* Puzzle trainer: moves are checked, answered and animated in the browser. Python picks the puzzles, and is told about each result. */
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  injectCss();
  let I = parentElement.__pz;
  if (I && I.id === data.qid) { I.add(data.queue); return; }
  if (I && I.dispose) I.dispose();
  parentElement.innerHTML = '';
  I = parentElement.__pz = { id: data.qid };
  const queue = [], seen = new Set(); let qi = -1;
  const log = []; let seq = 0, moreAsked = 0;
  let P = null, chess = null, step = 0, status = 'play', wrong = 0, hint = 0, busy = false, timer = null;
  let streak = data.stats.streak || 0, best = data.stats.best || 0, doneNow = data.stats.done || 0;

  const root = el('div', { class: 'cc-root' });
  root.innerHTML = `<div class="strip" style="margin:0 0 14px"><div class="s"><b>🔥 <span data-s="streak"></span></b>streak</div><div class="s"><b>🏆 <span data-s="best"></span></b>best streak</div><div class="s"><b>✅ <span data-s="done"></span></b>solved this visit</div></div>
    <div class="cc-grid" style="grid-template-columns:minmax(0,1.15fr) minmax(0,1fr)"><div class="L"><div class="bw" data-w><div class="brow"><div class="bcol"></div></div></div></div>
    <div class="R"><div class="card exp pzcard" data-card></div><div data-msg style="margin-top:10px"></div>
    <div class="cc-btns c3" data-play><button class="cc-btn" data-a="hint">💡 Hint</button><button class="cc-btn" data-a="reveal">👁️ Solution</button><button class="cc-btn" data-a="skip">⏭️ Skip</button></div>
    <div class="cc-btns" data-after style="display:none"><button class="cc-btn primary" data-a="next">Next puzzle ▶</button></div></div></div>`;
  parentElement.appendChild(root);
  const q = (s) => root.querySelector(s);
  const wrap = q('[data-w]');

  const board = new Board(q('.bcol'), {
    interactive: () => P && status === 'play' && !busy,
    canMove: (from) => { if (!chess || chess.isGameOver()) return []; return legalMap(chess)[from] || []; },
    onMove: (from, to, promo, dropped) => attempt(from, to, promo, dropped),
  });

  function stats() { for (const k of ['streak', 'best', 'done']) q(`[data-s=${k}]`).textContent = { streak, best, done: doneNow }[k]; }
  function send(kind, solved) {
    log.push({ seq: ++seq, id: P.id, solved, wrong, kind }); setTriggerValue('result', { log, streak, best, done: doneNow });
  }
  function load(i) {
    qi = i; P = queue[i]; if (!P) { empty(); return; }
    clearTimeout(timer); busy = false; step = 0; status = 'play'; wrong = 0; hint = 0;
    chess = new Chess(P.fen); board.setFlipped(P.side === 'b'); board.show(P.fen, { last: P.last ? [P.last.slice(0, 2), P.last.slice(2, 4)] : null });
    wrap.classList.remove('shake', 'glow');
    if (queue.length - i <= 3 && moreAsked < queue.length) { moreAsked = queue.length; setTriggerValue('more', queue.length); }
    paint();
  }
  function empty() { q('[data-card]').innerHTML = `<h4>Puzzle</h4><div class="sanline">🎉 You've reached the end of this set</div><p class="soft">Pick another level or theme above, or come back later for new puzzles.</p>`; q('[data-play]').style.display = 'none'; q('[data-after]').style.display = 'none'; }
  function dots() { const total = Math.ceil(P.moves.length / 2), done = Math.ceil(step / 2); let h = ''; for (let k = 0; k < total; k++) h += `<span class="${k < done ? 'ok' : (k === done && status === 'play') ? 'now' : ''}"></span>`; return `<div class="dots">${h}</div>`; }
  function paint() {
    const w = P.side === 'w', playing = status === 'play';
    let head, sub;
    if (playing) { head = `${w ? '⚪ White' : '⚫ Black'} to move`; sub = busy ? 'Good move! The opponent replies…' : 'Find the best move.'; }
    else if (status === 'solved') { head = '✅ Puzzle solved!'; sub = wrong === 0 ? 'First try, well done.' : `Solved after ${wrong} wrong guess${wrong !== 1 ? 'es' : ''}.`; }
    else { head = '💡 The solution'; sub = 'Study it, then try the next one.'; }
    let chips = `<span class="chip lv${P.level}">${P.icon} ${esc(P.levelName)}</span>`;
    if (!playing) chips += P.themes.map((t) => `<span class="chip">${esc(t)}</span>`).join('');
    const body = playing ? '' : `<p class="soft" style="margin-top:8px">Solution: <b>${esc(P.solution)}</b></p>`;
    const card = q('[data-card]'); card.className = `card exp pzcard ${status}`;
    card.innerHTML = `<h4>Puzzle</h4><div class="sanline">${head}</div><p class="soft">${sub}</p>${dots()}<div class="m">${chips}</div>${body}`;
    q('[data-msg]').innerHTML = (playing && wrong) ? `<div class="cc-warn">Not quite: that is not the best move. ${wrong} wrong guess${wrong !== 1 ? 'es' : ''} so far.</div>` : '';
    q('[data-play]').style.display = playing ? '' : 'none'; q('[data-after]').style.display = playing ? 'none' : '';
    const hb = root.querySelector('[data-a=hint]'); hb.disabled = hint >= 2 || busy; root.querySelector('[data-a=reveal]').disabled = busy; root.querySelector('[data-a=skip]').disabled = busy;
    stats(); overlays();
  }
  function overlays() {
    const marks = [], arrows = [];
    if (status === 'play' && !busy && step < P.moves.length) {
      const m = P.moves[step];
      if (hint === 1) marks.push({ sq: m.slice(0, 2), color: 'rgba(255,214,0,.55)', cls: 'hintpulse' });
      if (hint >= 2) arrows.push({ from: m.slice(0, 2), to: m.slice(2, 4), color: '#7fa650cc' });
    }
    if (status === 'shown' && step < P.moves.length) { const m = P.moves[step]; arrows.push({ from: m.slice(0, 2), to: m.slice(2, 4), color: '#7fa650cc' }); }
    board.marks = marks; board.arrows = arrows; board.redrawOverlays();
  }
  function lastOf(u) { return [u.slice(0, 2), u.slice(2, 4)]; }
  function attempt(from, to, promo, dropped) {
    const c = new Chess(chess.fen()); let mv;
    try { mv = c.move({ from, to, promotion: promo || 'q' }); } catch (e) { return false; }
    const uci = from + to + (mv.promotion || '');
    const expected = P.moves[step];
    if (!(c.isCheckmate() || uci === expected)) {                       // wrong move: shake, put the piece back
      wrong++; streak = 0; wrap.classList.remove('shake'); void wrap.offsetWidth; wrap.classList.add('shake');
      setTimeout(() => wrap.classList.remove('shake'), 500); paint(); return false;
    }
    chess = c; step = Math.max(step + 1, 0);
    const done = c.isCheckmate() || step >= P.moves.length;
    board.show(c.fen(), { last: [from, to], move: dropped ? null : { from, to } });
    if (done) { solved(); return true; }
    busy = true; paint();
    timer = setTimeout(() => {                                          // the opponent answers
      const r = P.moves[step], rc = new Chess(chess.fen()); const rm = rc.move({ from: r.slice(0, 2), to: r.slice(2, 4), promotion: r[4] });
      chess = rc; step++; busy = false;
      board.show(rc.fen(), { last: lastOf(r), move: { from: r.slice(0, 2), to: r.slice(2, 4) } });
      if (rc.isGameOver() || step >= P.moves.length) solved(); else paint();
    }, 520);
    return true;
  }
  function solved() {
    status = 'solved'; busy = false; streak += 1; best = Math.max(best, streak); doneNow += 1;
    wrap.classList.remove('glow'); void wrap.offsetWidth; wrap.classList.add('glow'); paint(); send('solved', true);
  }
  const act = {
    hint: () => { hint = Math.min(2, hint + 1); paint(); },
    reveal: () => { status = 'shown'; streak = 0; clearTimeout(timer); busy = false; send('shown', false); paint(); },
    skip: () => { streak = 0; send('skip', false); load(qi + 1); },
    next: () => load(qi + 1),
  };
  root.addEventListener('click', (e) => { const b = e.target.closest('[data-a]'); if (b && !b.disabled && act[b.dataset.a]) act[b.dataset.a](); });
  I.add = (items) => { for (const it of items) if (!seen.has(it.id)) { seen.add(it.id); queue.push(it); } if (!P && queue.length) load(0); else if (qi >= 0 && !queue[qi]) load(qi); };
  const stopKeys = keys({ Enter: () => { if (!root.isConnected) return false; if (status !== 'play') act.next(); else return false; }, n: () => { if (!root.isConnected) return false; if (status !== 'play') act.next(); else return false; } });
  I.dispose = () => { stopKeys(); clearTimeout(timer); };
  I.state = () => ({ P, step, status, wrong, hint });
  I.add(data.queue); if (!queue.length) empty();
}
