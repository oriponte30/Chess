"""Opening lessons as a variation tree.

A lesson is a tree of moves (a `Node` per move, with the explanation for the position it reaches). It is written as plain move lines with
short comments in braces, and built once into the tree:

    "e4 c6{Black prepares ...d5 with a pawn.} d4 d5 e5 Bf5"

Every move is checked for legality while the tree is built, and a position that can be reached by different move orders is recognised
(`LessonTree.by_epd`), so a transposition keeps the lesson text instead of dropping out of the tree. Every line below was also checked
with Stockfish (no final position is worse than about +1.0 for either side).

Adding an opening means adding another LESSON-style block: lines, sections and notes. The UI (app_pages/lessons.py) needs no change."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import chess


@dataclass
class Node:
    san: str = ""                              # the move that leads to this position ("" for the start)
    uci: str = ""
    epd: str = ""
    ply: int = 0                               # half-moves played to get here
    note: str = ""                             # what this move / position is about
    parent: "Node | None" = field(default=None, repr=False)
    children: list = field(default_factory=list)
    alias: "Node | None" = field(default=None, repr=False)     # set when another move order reached the same position first

    @property
    def label(self) -> str:
        """'4.Nf3' or '4...e6'."""
        if not self.san:
            return "Start"
        n = (self.ply + 1) // 2
        return f"{n}.{self.san}" if self.ply % 2 else f"{n}...{self.san}"

    def child(self, uci: str):
        return next((c for c in self.children if c.uci == uci), None)

    @property
    def path(self) -> list:
        out, n = [], self
        while n is not None and n.uci:
            out.append(n.uci)
            n = n.parent
        return out[::-1]


_TOKEN = re.compile(r"([^\s{]+)(?:\{(.*?)\})?", re.S)


class LessonTree:
    def __init__(self, title: str, lines: list, sections: list, intro: str = ""):
        self.title, self.intro, self.sections = title, intro, sections     # sections: dicts with id/title/start (SAN path)/summary
        self.root = Node(epd=chess.Board().epd())
        self.by_epd: dict = {self.root.epd: self.root}
        for line in lines:
            self._add(line)

    # ---- building ---------------------------------------------------------------------------------------------------
    def _add(self, line: str) -> None:
        board, node = chess.Board(), self.root
        for san, note in _TOKEN.findall(line):
            mv = board.parse_san(san)                       # raises ValueError on an illegal move: bad lessons fail loudly
            uci = mv.uci()
            nxt = node.child(uci)
            if nxt is None:
                real_san = board.san(mv)
                board.push(mv)
                nxt = Node(san=real_san, uci=uci, epd=board.epd(), ply=node.ply + 1, parent=node)
                node.children.append(nxt)
                first = self.by_epd.setdefault(nxt.epd, nxt)
                if first is not nxt:
                    nxt.alias = first                      # a transposition: share the explanation and the continuations
            else:
                board.push(mv)
            if note and not nxt.note:
                nxt.note = " ".join(note.split())
            if nxt.alias is not None and note and not nxt.alias.note:
                nxt.alias.note = " ".join(note.split())
            node = nxt

    # ---- lookups ----------------------------------------------------------------------------------------------------
    def node_at(self, path: list):
        """The node reached by playing these UCI moves from the start, or None when the path leaves the tree."""
        node = self.root
        for u in path:
            node = node.child(u)
            if node is None:
                return None
        return node

    def resolve(self, board: chess.Board, path: list):
        """The node for the current position: by path when the path is in the tree, otherwise by position (a transposition)."""
        return self.node_at(path) or self.by_epd.get(board.epd())

    @staticmethod
    def effective(node: "Node | None"):
        """The node whose notes and continuations apply: for a transposed position, the first node that reached it."""
        if node is not None and node.alias is not None:
            return node.alias
        return node

    def section_of(self, node: "Node | None"):
        """The section (Advance / Exchange / Classical ...) a node belongs to, found from its path."""
        if node is None:
            return None
        best = None
        for s in self.sections:
            start = self.node_at_san(s["start"])
            n = node
            while n is not None:
                if n is start:
                    best = s
                    break
                n = n.parent
        return best

    def node_at_san(self, san_path: str):
        board, node = chess.Board(), self.root
        for san in san_path.split():
            mv = board.parse_san(san)
            node = node.child(mv.uci())
            if node is None:
                return None
            board.push(mv)
        return node

    def main_line(self, node: Node, plies: int) -> list:
        """The first-listed continuation, up to `plies` moves (the lesson's main line)."""
        out = []
        node = self.effective(node)
        while node.children and len(out) < plies:
            node = self.effective(node.children[0])
            out.append(node)
        return out

    def look_ahead(self, node: Node, plies: int = 4) -> list:
        """What comes next, for the 'what to do in the next 3-4 moves' panel: for every book move from this position, the line that
        follows it and the replies the opponent can choose between, each with where it leads."""
        options = []
        node = self.effective(node)
        for c in node.children:
            line = [c] + self.main_line(c, plies - 1)
            options.append({"move": c, "line": line, "replies": [(r, self.main_line(r, 2)) for r in c.children]})
        return options

    def count(self) -> int:
        return len(self.by_epd) - 1


def fmt_line(nodes: list) -> str:
    """'4.Nf3 e6 5.Be2 c5' (black moves get a number only when the line starts with one)."""
    out = []
    for i, n in enumerate(nodes):
        if n.ply % 2 == 1:
            out.append(n.label)
        else:
            out.append(n.label if i == 0 else n.san)
    return " ".join(out)


# ------------------------------------------------------------------------------------------------------------------------------------
# The Caro-Kann Defence (1.e4 c6), from Black's side
# ------------------------------------------------------------------------------------------------------------------------------------
CARO_KANN_LINES = [
    # ---- the starting moves --------------------------------------------------------------------------------------------
    "e4{1.e4: White takes space in the centre and opens lines for the queen and the light-squared bishop.} "
    "c6{1...c6 is the Caro-Kann. Black prepares ...d5 with the c-pawn instead of the e-pawn, so the light-squared bishop on c8 stays free "
    "to develop (in the French Defence ...e6 locks it in). The price: Black has not claimed any central space yet, and the c-pawn takes the "
    "c6 square from the queen's knight. The structure Black wants is solid: pawns on c6 and d5, with ...e6 or ...g6 to follow.} "
    "d4{2.d4: White builds the classic two-pawn centre.} "
    "d5{2...d5 challenges the e4 pawn. This is the main crossroads: White has three principled ways forward. 3.e5 (Advance) gains space, "
    "3.exd5 (Exchange) simplifies into a symmetrical structure, and 3.Nc3 (Classical) keeps the tension and the pieces developing. "
    "Pick a branch with the buttons below.}",

    # ==== ADVANCE VARIATION (3.e5) ============================================================================================
    "e4 c6 d4 d5 e5{3.e5, the Advance Variation. White gains space, and the pawn chain d4-e5 cramps Black's kingside. Black has two jobs: "
    "(1) get the light-squared bishop out BEFORE playing ...e6, because afterwards it would be locked in behind its own pawns; "
    "(2) attack the base of White's chain with ...c5 (supported by ...Qb6 and ...Nc6), so that White's space becomes a target.} "
    "Bf5{3...Bf5: the bishop goes outside the pawn chain while it still can. Now ...e6 and ...c5 are on the way.} "
    "Nf3{4.Nf3 is the most natural developing move. It protects d4 and e5. Black replies ...e6 and then fights the centre with ...c5.} "
    "e6{4...e6: with the bishop already outside, ...e6 is safe. It supports d5 and leaves ...Ne7, ...Nc6 and ...Qb6 available.} "
    "Be2{5.Be2 is a calm developing move. White plans O-O and c3, keeping the d4-e5 chain protected. Black's break is ...c5.} "
    "c5{5...c5 is the key lever. It hits d4, the base of White's chain and the only pawn that is not protected by another pawn. "
    "If White plays dxc5 the e5 pawn loses its support, so White usually adds a defender with Be3 or c3.} "
    "Be3{6.Be3 defends d4 and develops. Black has several good replies: 6...Qb6 (attacks d4 and b2), 6...cxd4, or 6...Ne7.} "
    "Qb6{6...Qb6: the queen pressures d4 and b2 at the same time, so White has to be concrete. Typical follow-ups are ...cxd4 and ...Nc6, "
    "so that d4 comes under attack from several pieces.} "
    "O-O{7.O-O: White finishes development. Black keeps adding pressure on d4 (...Nc6, ...cxd4, ...Nge7) and stays alert about the b2 pawn "
    "and White's space-gaining pawn moves such as f4.}",

    "e4 c6 d4 d5 e5 Bf5 Nf3 e6 Be2 c5 Be3 cxd4{6...cxd4: Black exchanges at once, trading the c-pawn for White's d-pawn.} "
    "Nxd4{7.Nxd4: the knight recaptures and attacks the bishop on f5.} "
    "Nc6{7...Nc6 challenges the centralised knight. White keeps a small edge here because the space advantage remains, but the "
    "position is healthy for Black: the bishop on f5 is safe, and Black can continue with ...Nge7 and ...Qb6.}",

    "e4 c6 d4 d5 e5 Bf5 Nf3 e6 Be2 c5 Be3 Ne7{6...Ne7: the knight keeps the options g6 and c6 open and supports d5. The goal stays the same: "
    "pressure on d4.} "
    "c3{7.c3 gives d4 a second pawn defender and prepares Nbd2.} "
    "Nbc6{7...Nbc6 adds another attacker on d4: now the c5 pawn and the c6 knight both aim at it.} "
    "Nbd2{8.Nbd2 develops the last minor piece.} "
    "Qb6{8...Qb6: the queen adds to the pressure on d4 and b2. Black keeps piling up attackers on d4.}",

    "e4 c6 d4 d5 e5 Bf5 Nf3 e6 Be2 Ne7{5...Ne7 delays ...c5. The knight heads for g6 or c6, and Black keeps a flexible structure.} "
    "O-O{6.O-O: White castles and keeps the pawn chain protected.} "
    "Nd7{6...Nd7 prepares ...c5 with an extra supporter on e6-d7 squares and clears e7-g6 for the knight. Black will break with ...c5 "
    "once the pieces are placed.}",

    # ---- Short variation 4.h4 -------------------------------------------------------------------------------------------
    "e4 c6 d4 d5 e5 Bf5 h4{4.h4, the Short Variation (after Nigel Short). White threatens h5 and g4, to harass the bishop and gain kingside "
    "space. Black must make sure the bishop is never trapped.} "
    "h5{4...h5 takes g4 away and stops the h-pawn from advancing to h5. The bishop keeps its retreat squares (g4, and a trade on d3).} "
    "Bd3{5.Bd3 offers to trade bishops: White's good bishop for Black's best minor piece.} "
    "Bxd3{5...Bxd3: accepting makes sense, because with fewer pieces White's extra space is less dangerous.} "
    "Qxd3{6.Qxd3 recaptures with the queen, which now eyes the kingside.} "
    "e6{6...e6: the familiar structure, but the bishop Black worried about has already been traded. Next: ...Ne7, ...Nd7, ...c5.}",

    "e4 c6 d4 d5 e5 Bf5 h4 h5 c4{5.c4: White hits d5 and claims queenside space.} "
    "e6{5...e6 keeps the structure solid and prepares ...Ne7.} "
    "Nc3{6.Nc3 adds more pressure on d5.} "
    "Ne7{6...Ne7 defends d5 once more, so that cxd5 can be met by ...exd5 or ...Nxd5.} "
    "Nge2{7.Nge2 keeps the f-pawn free to advance later. Black continues with ...Nd7, ...Ng6 and the usual ...c5 break.}",

    "e4 c6 d4 d5 e5 Bf5 c4{4.c4: an immediate space grab, hitting d5 before developing the knights.} "
    "e6{4...e6: the bishop is already outside, so Black can close the chain and support d5.} "
    "Nc3{5.Nc3 puts more pressure on d5.} "
    "Ne7{5...Ne7 adds a defender to d5, so the centre holds.}",

    # ==== EXCHANGE VARIATION (3.exd5) =========================================================================================
    "e4 c6 d4 d5 exd5{3.exd5, the Exchange Variation. After the recapture the pawn structure is symmetrical, which looks drawish but has real play. "
    "White has two main plans: the quiet set-up with Bd3, c3 and Qb3, or the sharper Panov Attack with c4. Black's job: develop sensibly, "
    "trade pieces, and keep the b7 pawn safe.} "
    "cxd5{3...cxd5: Black recaptures with the c-pawn, which gives the symmetrical structure and a half-open c-file.}",

    # Panov
    "e4 c6 d4 d5 exd5 cxd5 c4{4.c4, the Panov Attack. White hits d5 at once. After the pawn exchange on d5 White often ends up with an isolated "
    "queen's pawn on d4 (an 'IQP'), which brings active pieces and attacking chances in return for a long-term weakness.} "
    "Nf6{4...Nf6 develops and defends d5. With the knight on f6, Black can meet cxd5 with ...Nxd5 and aims for ...e6, ...Be7 and ...O-O.} "
    "Nc3{5.Nc3 adds a second attacker on d5.} "
    "e6{5...e6 is the most solid reply: the pawn defends d5 and opens the bishop on f8.} "
    "Nf3{6.Nf3 develops and protects d4.} "
    "Be7{6...Be7 develops and prepares O-O.} "
    "cxd5{7.cxd5 resolves the tension. White's d4 pawn now stands alone: it is the isolated queen's pawn.} "
    "Nxd5{7...Nxd5: the knight lands on the blockading square d5. Putting a piece on the square directly in front of an isolated pawn is "
    "the standard remedy: it stops the pawn from advancing and dominates the centre.} "
    "Bd3{8.Bd3: White develops with attacking chances on the kingside (the bishop aims at h7).} "
    "Nc6{8...Nc6 attacks d4 and develops. Black wants to trade pieces, because every exchange makes an isolated pawn harder to defend.} "
    "O-O{9.O-O.} O-O{9...O-O: both sides complete development.} "
    "Re1{10.Re1: the rook supports the centre and a possible kingside attack.} "
    "Nf6{10...Nf6: the knight returns to cover the kingside (h7, e4) while Black keeps the blockade idea. Black's plan: trade White's active "
    "pieces and then target d4. Watch for White's Bg5 and queen-and-bishop attacks on h7.}",

    # transposition: 4...e6 5.Nc3 Nf6 reaches the Panov main position (a move-order lesson)
    "e4 c6 d4 d5 exd5 cxd5 c4 e6{4...e6 is a legitimate move order: after 5.Nc3 Nf6 6.Nf3 Be7 it transposes to the main Panov line.} "
    "Nc3{5.Nc3 adds a second attacker on d5.} Nf6{5...Nf6 develops and defends d5.} Nf3 Be7",

    "e4 c6 d4 d5 exd5 cxd5 c4 Nf6 Nc3 e6 Nf3 Bb4{6...Bb4 pins the c3 knight against the king, which makes it hard for White to keep "
    "putting pressure on d5.} "
    "cxd5{7.cxd5: White resolves the tension and the d4 pawn becomes isolated.} Nxd5{7...Nxd5 recaptures with the knight, which blockades d5. The c3 knight is still pinned.} Bd2{8.Bd2 breaks the pin and develops.} "
    "Nc6{8...Nc6 attacks d4 again.} "
    "Bd3{9.Bd3 develops the bishop towards the kingside.} O-O{9...O-O: Black castles and keeps the pieces ready to trade around the d4 pawn.} "
    "O-O{10.O-O: both sides are castled. Black keeps blockading d5 and aims to trade pieces.}",

    # classical exchange with Bd3 and Qb3
    "e4 c6 d4 d5 exd5 cxd5 Bd3{4.Bd3, the quiet main line of the Exchange. White develops the bishop to its best diagonal and prepares c3 and Qb3. "
    "The pawn structure stays symmetrical.} "
    "Nc6{4...Nc6 develops and puts pressure on d4.} "
    "c3{5.c3 supports d4 and prepares Qb3.} "
    "Nf6{5...Nf6 develops and keeps d5 and e4 under control.} "
    "Bf4{6.Bf4: White's dark-squared bishop develops outside the pawn chain.} "
    "Bg4{6...Bg4 attacks the queen on d1 and develops the bishop outside the chain. White's natural answer is Qb3, which moves the queen with threats.} "
    "Qb3{7.Qb3 attacks b7 and d5 at once. This is White's key idea in the Exchange: Black must meet the threat to b7 accurately.} "
    "Qd7{7...Qd7 is the standard defence: the queen guards b7 and keeps d5 covered. Black does not need to fear the queen trade or the pin.} "
    "Nd2{8.Nd2 develops the knight and supports the centre.} "
    "e6{8...e6 supports d5 and opens the f8-bishop.} "
    "Ngf3{9.Ngf3 develops the last knight.} "
    "Bd6{9...Bd6 offers to trade the dark-squared bishops: White's Bf4 is its most active piece, and exchanging it eases Black's game.} "
    "Bxd6{10.Bxd6 trades the bishops.} Qxd6{10...Qxd6: the position is level. Black's plans: castle, then use the open c-file with ...Rac8 and ...Rfd8.} "
    "O-O{11.O-O.} O-O{11...O-O: both sides are castled and the game is balanced. The better plan, on the c-file and with careful minor-piece play, wins.}",

    # ==== CLASSICAL VARIATION (3.Nc3) =========================================================================================
    "e4 c6 d4 d5 Nc3{3.Nc3, the Classical approach. White protects e4 with the knight and keeps the pawn centre. Black normally takes on e4 "
    "and develops quickly; the plan is to complete development safely and break with ...c5 or ...e5 when ready.} "
    "dxe4{3...dxe4: Black takes the pawn to open the centre and head for a simple, healthy structure.} "
    "Nxe4{4.Nxe4: the knight recaptures and is centralised. Black has three main moves: 4...Bf5 (the main line), 4...Nd7 (Smyslov), "
    "and 4...Nf6 5.Nxf6+ (the exchange of knights).}",

    "e4 c6 d4 d5 Nc3 dxe4 Nxe4 Bf5{4...Bf5: the bishop comes out with tempo, attacking the e4 knight. It is developed before ...e6 closes it in.} "
    "Ng3{5.Ng3: the knight retreats and attacks the bishop.} "
    "Bg6{5...Bg6: the bishop retreats to a safe square on the b1-h7 diagonal.} "
    "h4{6.h4 threatens h5, which would attack the bishop again.} "
    "h6{6...h6 gives the bishop the retreat square h7 and takes g5 away from White's pieces.} "
    "Nf3{7.Nf3 develops and watches e5 and h4.} "
    "Nd7{7...Nd7 develops the knight and prepares ...Ngf6 and ...e6.} "
    "h5{8.h5: the bishop has to retreat.} "
    "Bh7{8...Bh7: the bishop is safe on h7 and still works along the long diagonal.} "
    "Bd3{9.Bd3 offers to trade the active bishop.} "
    "Bxd3{9...Bxd3: Black accepts, removing the bishop that White's h-pawn had been pushing around.} "
    "Qxd3{10.Qxd3: the queen recaptures and eyes the kingside.} "
    "e6{10...e6: the pawn move comes now that the bishop is traded. It supports d5 and opens the f8-bishop.} "
    "Bf4{11.Bf4 develops outside the pawn chain.} "
    "Ngf6{11...Ngf6 finishes the kingside development.} "
    "O-O-O{12.O-O-O: White castles long, so the kings are on opposite wings and play gets sharper.} "
    "Be7{12...Be7 develops and prepares to castle. Black's plans: ...O-O, then the central break ...c5, or ...Qa5.} "
    "Kb1{13.Kb1 tucks the king away from the c-file.} O-O{13...O-O: Black castles short, opposite to White. Both sides now pursue their own plans: White the h-pawn and the kingside, "
    "Black the break ...c5 in the centre.}",

    "e4 c6 d4 d5 Nc3 dxe4 Nxe4 Nd7{4...Nd7, the Smyslov Variation. Black does not develop the bishop first: the knight heads for f6 so that "
    "Nxf6+ can be recaptured by the other knight, keeping the pawn structure intact. The bishop comes to f5 or e6 later.} "
    "Ng5{5.Ng5: White aims at f7 and h7 and tries to stop ...Ngf6. Black must handle the knight carefully.} "
    "Ngf6{5...Ngf6 develops the knight and covers h7, so the Ng5 plan does not win a pawn.} "
    "Bd3{6.Bd3 develops and adds to the pressure on h7.} "
    "e6{6...e6 opens the f8-bishop and supports the centre.} "
    "N1f3{7.N1f3 brings the other knight into play.} "
    "Bd6{7...Bd6 develops the bishop; Black is ready to meet the knight with ...h6.} "
    "Qe2{8.Qe2 supports the attack and eyes e4 and h7.} "
    "h6{8...h6 attacks the g5 knight and forces a decision.} "
    "Ne4{9.Ne4: the knight retreats to a central square. White offers a trade, and the position stays balanced.} "
    "Nxe4{9...Nxe4 trades the knights.} Qxe4{10.Qxe4: the queen comes to the centre.} "
    "Qc7{10...Qc7 develops the queen and prepares ...O-O or ...b6 with ...Bb7. Black has a solid, healthy position.}",

    "e4 c6 d4 d5 Nc3 dxe4 Nxe4 Nd7 Nf3{5.Nf3: the quiet alternative. White develops first and keeps Ng5 for later.} "
    "Ngf6{5...Ngf6: the knight develops and challenges the e4 knight.} "
    "Nxf6+{6.Nxf6+: White trades off the strong e4 knight.} "
    "Nxf6{6...Nxf6: the recapture keeps Black's pawn structure healthy.} "
    "Bd3{7.Bd3 develops.} "
    "Bg4{7...Bg4: the bishop comes outside the pawn chain and pins the f3 knight against the queen. Next: ...e6, ...Qc7 or ...Nd5 ideas.}",

    "e4 c6 d4 d5 Nc3 dxe4 Nxe4 Nf6{4...Nf6 challenges the knight at once. After 5.Nxf6+ Black has to decide how to recapture.} "
    "Nxf6+{5.Nxf6+: White removes the knight.} "
    "exf6{5...exf6: the e-pawn recaptures. The bishop on f8 is released and the e-file opens, so Black gets active piece play, at the cost "
    "of doubled f-pawns.} "
    "c3{6.c3 supports the centre and prepares the queen's development.} "
    "Bd6{6...Bd6: the bishop develops to an active diagonal and prepares ...O-O.} "
    "Bd3{7.Bd3.} O-O{7...O-O.} "
    "Qc2{8.Qc2 attacks the bishop and aims at the kingside.} "
    "Re8+{8...Re8+: a check on the open file; White has to block it.} "
    "Ne2{9.Ne2 blocks the check.} "
    "Nd7{9...Nd7 develops the last minor piece. The position is healthy for Black but slightly passive; typical plans are ...Nf8, "
    "...Bf5 to trade the light-squared bishops, and ...Qc7.}",
]

CARO_KANN_SECTIONS = [
    {"id": "advance", "title": "Advance (3.e5)", "start": "e4 c6 d4 d5 e5", "icon": "🛡️",
     "summary": "White gains space with e5. The structure: White's chain d4-e5 against Black's c6-d5. Black must free the light-squared bishop "
                "(…Bf5) BEFORE closing it in with …e6, then attack the base of the chain with …c5 and …Qb6/…Nc6. The Short System 4.h4 tries to "
                "trap or harass the bishop; answer with …h5 (or …h6) and trade it if needed."},
    {"id": "exchange", "title": "Exchange (3.exd5)", "start": "e4 c6 d4 d5 exd5", "icon": "⚖️",
     "summary": "A symmetrical structure after 3…cxd5. With 4.Bd3 White plays c3, Bf4 and Qb3, so keep the b7 pawn safe with …Qd7 and trade the dark-squared "
                "bishops. With 4.c4 (Panov) White gets an isolated queen's pawn in return for activity: blockade d5 with a knight and trade pieces."},
    {"id": "classical", "title": "Classical (3.Nc3)", "start": "e4 c6 d4 d5 Nc3", "icon": "♟️",
     "summary": "After 3…dxe4 4.Nxe4 White leads in development. The main line is 4…Bf5 5.Ng3 Bg6, with …h6 against h4-h5, then …e6 and …Ngf6. "
                "4…Nd7 (Smyslov) avoids doubled pawns and allows …Ngf6. After 4…Nf6 5.Nxf6+ exf6 Black gets solid play with the e-file open "
                "but a slightly passive structure."},
]

CARO_KANN = LessonTree(
    "Caro-Kann Defence", CARO_KANN_LINES, CARO_KANN_SECTIONS,
    intro="1.e4 c6, played from Black's side. A solid, pawn-structure-driven opening: Black prepares …d5 while keeping the light-squared bishop free.")

LESSONS = {"caro-kann": CARO_KANN}
