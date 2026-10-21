"""A board you can play on: click a piece to see every square it can move to, click a square to move (or press, drag and release).

It is a Streamlit "v2 component": the board picture is the same SVG as everywhere else (ui/board.py, so the slide animation and arrows work),
and a little JavaScript on top handles the clicking. Python stays in charge of the rules: it sends the list of legal moves, and every move
that comes back is checked again against the real position before it is used."""
from __future__ import annotations

import chess
import streamlit as st

CSS = """
.cb-root { position: relative; }
.cb-root svg { touch-action: none; user-select: none; -webkit-user-select: none; }
.cb-root svg.cb-live { cursor: pointer; }
.cb-promo { position:absolute; left:50%; top:50%; transform: translate(-50%,-50%); display:flex; gap:8px; padding:10px 12px; border-radius:14px;
  background: var(--glass, #16222e); border:1px solid var(--line, #444); box-shadow: 0 12px 30px rgba(0,0,0,.4); z-index:5; }
.cb-promo button { font-size:26px; line-height:1; width:52px; height:52px; border-radius:12px; border:1px solid var(--line, #555); background: var(--surface2, #222);
  color: var(--text, #fff); cursor:pointer; }
.cb-promo button:hover { background: var(--accent, #7fa650); color:#fff; }
"""

JS = """
export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  let root = parentElement.querySelector(':scope > .cb-root');
  if (!root) { root = document.createElement('div'); root.className = 'cb-root'; parentElement.appendChild(root); }
  root.innerHTML = data.html;
  const svg = root.querySelector('svg');
  if (!svg || !data.interactive) return;
  svg.classList.add('cb-live');
  const NS = 'http://www.w3.org/2000/svg', M = 15, Q = 45, files = 'abcdefgh';
  const legal = data.legal, caps = new Set(data.captures), promos = new Set(data.promos);
  let sel = null, downSq = null;

  const squareAt = (e) => {
    const r = svg.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width * 390, y = (e.clientY - r.top) / r.height * 390;
    const c = Math.floor((x - M) / Q), rw = Math.floor((y - M) / Q);
    if (c < 0 || c > 7 || rw < 0 || rw > 7) return null;
    const f = data.flipped ? 7 - c : c, rk = data.flipped ? rw : 7 - rw;
    return files[f] + (rk + 1);
  };
  const xy = (sq) => {
    const f = files.indexOf(sq[0]), rk = parseInt(sq[1]) - 1;
    return [M + (data.flipped ? 7 - f : f) * Q, M + (data.flipped ? rk : 7 - rk) * Q];
  };
  const clear = () => { svg.querySelectorAll('.cb-hint').forEach((n) => n.remove()); const p = root.querySelector('.cb-promo'); if (p) p.remove(); };
  const mk = (tag, attrs) => { const n = document.createElementNS(NS, tag); n.setAttribute('class', 'cb-hint'); for (const k in attrs) n.setAttribute(k, attrs[k]); return n; };

  const show = (sq) => {
    clear(); sel = sq;
    if (!sq) return;
    const [sx, sy] = xy(sq);
    svg.insertBefore(mk('rect', { x: sx, y: sy, width: Q, height: Q, fill: 'rgba(255,214,0,.45)', 'pointer-events': 'none' }), svg.querySelector('use') );
    for (const to of legal[sq] || []) {
      const [x, y] = xy(to);
      if (caps.has(sq + to)) svg.appendChild(mk('circle', { cx: x + Q / 2, cy: y + Q / 2, r: 20, fill: 'none', stroke: 'rgba(20,90,40,.65)', 'stroke-width': 5, 'pointer-events': 'none' }));
      else svg.appendChild(mk('circle', { cx: x + Q / 2, cy: y + Q / 2, r: 7.5, fill: 'rgba(20,90,40,.6)', 'pointer-events': 'none' }));
    }
  };
  const send = (uci) => { clear(); sel = null; setTriggerValue('move', uci); };
  const tryMove = (from, to) => {
    if (!(legal[from] || []).includes(to)) return false;
    if (promos.has(from + to)) {
      clear();
      const box = document.createElement('div'); box.className = 'cb-promo';
      for (const [p, g] of [['q', '♛'], ['r', '♜'], ['b', '♝'], ['n', '♞']]) {
        const b = document.createElement('button'); b.textContent = g; b.title = p; b.onclick = () => send(from + to + p); box.appendChild(b);
      }
      root.appendChild(box);
      return true;
    }
    send(from + to);
    return true;
  };
  const down = (e) => {
    const sq = squareAt(e);
    if (!sq) { show(null); return; }
    if (sel && sel !== sq && tryMove(sel, sq)) { downSq = null; return; }
    if (legal[sq]) { downSq = sq; show(sel === sq ? null : sq); if (sel === null && downSq) {} }
    else { downSq = null; show(null); }
  };
  const up = (e) => {                                  // press a piece, drag, and release on a target square
    const sq = squareAt(e);
    if (downSq && sq && sq !== downSq && (legal[downSq] || []).includes(sq)) { const f = downSq; downSq = null; tryMove(f, sq); }
    else downSq = null;
  };
  svg.addEventListener('pointerdown', down);
  svg.addEventListener('pointerup', up);
  return () => { svg.removeEventListener('pointerdown', down); svg.removeEventListener('pointerup', up); };
}
"""

_component = st.components.v2.component("chess_coach_board", css=CSS, js=JS, isolate_styles=False)


def legal_map(board: chess.Board) -> tuple:
    """(legal, captures, promos) for the JavaScript: where every piece of the side to move can go."""
    legal, caps, promos = {}, [], []
    for mv in board.legal_moves:
        f, t = chess.square_name(mv.from_square), chess.square_name(mv.to_square)
        if t not in legal.setdefault(f, []):
            legal[f].append(t)
        if board.is_capture(mv):
            caps.append(f + t)
        if mv.promotion:
            promos.append(f + t)
    return legal, sorted(set(caps)), sorted(set(promos))


def board_component(key: str, fen: str, html: str, flipped: bool = False, interactive: bool = True):
    """Shows `html` (the board SVG, possibly with an eval bar around it) and returns the UCI move the user just made, or None.
    The move is checked against the position before it is returned."""
    board = chess.Board(fen)
    legal, caps, promos = legal_map(board) if interactive and not board.is_game_over() else ({}, [], [])
    res = _component(key=key, data={"html": html, "legal": legal, "captures": caps, "promos": promos, "flipped": bool(flipped),
                                    "interactive": bool(legal)}, on_move_change=lambda: None)
    uci = getattr(res, "move", None)
    if not uci:
        return None
    try:
        mv = chess.Move.from_uci(str(uci))
    except ValueError:
        return None
    return mv.uci() if mv in board.legal_moves else None
