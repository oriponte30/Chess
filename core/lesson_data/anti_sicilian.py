"""How to play against the Sicilian (1.e4 c5), from White's side: the Open Sicilian, the Rossolimo, the Alapin, the Grand Prix / Closed set-ups
and the Smith-Morra Gambit."""
from ..lessons import LessonTree

OPEN = "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3"

LINES = [
    "e4{1.e4.} "
    "c5{1...c5, the Sicilian. Black does not copy White; the c-pawn trades itself for White's d-pawn, giving Black an unbalanced game with real winning chances. "
    "White has four sensible ways to play against it: the Open Sicilian (2.Nf3 and 3.d4), the Rossolimo (2.Nf3 Nc6 3.Bb5), the Alapin (2.c3) and the Grand Prix / "
    "Closed systems with 2.Nc3. Pick one of the buttons above to see the plans.}",

    # ==== Open Sicilian ========================================================================================================
    "e4 c5 Nf3{2.Nf3 prepares d4, the main idea.} "
    "d6{2...d6.} "
    "d4{3.d4: the Open Sicilian. White gets a lead in space and development; Black gets the half-open c-file.} "
    "cxd4{3...cxd4.} "
    "Nxd4{4.Nxd4.} "
    "Nf6{4...Nf6.} "
    "Nc3{5.Nc3 defends e4. Black now decides on the set-up, and White prepares the matching plan.} "
    "a6{5...a6, the Najdorf.} "
    "Be3{6.Be3, the English Attack: the most aggressive set-up against the Najdorf. The plan is f3, Qd2, O-O-O and then g4-g5 to attack Black's king.} "
    "e5{6...e5.} "
    "Nb3{7.Nb3: you do not mind the retreat. The knight eyes a5 and c5, and the bishop on e3 is safe.} "
    "Be6{7...Be6.} "
    "f3{8.f3: protects e4 and gets the pawn storm ready.} "
    "Be7{8...Be7.} "
    "Qd2{9.Qd2.} "
    "O-O{9...O-O.} "
    "O-O-O{10.O-O-O: opposite-side castling. From here on speed matters more than anything else.} "
    "Nbd7{10...Nbd7.} "
    "g4{11.g4: the pawn storm. Your plan is g5, h4 and h5.} "
    "b5{11...b5: Black counters with the same speed.} "
    "g5{12.g5: wins time by attacking the knight.} "
    "b4{12...b4.} "
    "Ne2{13.Ne2: you keep the c3 knight safe and still have the attack.} "
    "Ne8{13...Ne8.} "
    "f4{14.f4: the pawns roll forward. Both attacks are in full swing.} "
    "a5{14...a5.}",

    OPEN + " g6{5...g6, the Dragon.} "
    "Be3{6.Be3: set up the Yugoslav Attack.} "
    "Bg7{6...Bg7.} "
    "f3{7.f3.} "
    "O-O{7...O-O.} "
    "Qd2{8.Qd2: now Bh6 is a threat, to trade off Black's powerful dragon bishop.} "
    "Nc6{8...Nc6.} "
    "Bc4{9.Bc4: develops with tempo on f7 and prepares Bb3.} "
    "Bd7{9...Bd7.} "
    "O-O-O{10.O-O-O.} "
    "Rc8{10...Rc8.} "
    "Bb3{11.Bb3.} "
    "Ne5{11...Ne5.} "
    "h4{12.h4: the pawn rush starts. The plan: h5, then Bh6 or hxg6. Only the open h-file wins the game.} "
    "h5{12...h5: Black stops the pawn from advancing.}",

    OPEN + " Nc6{5...Nc6: the Classical Sicilian.} "
    "Bg5{6.Bg5, the Richter-Rauzer Attack. The bishop pins the knight on f6 and prepares Qd2 and O-O-O.} "
    "e6{6...e6.} "
    "Qd2{7.Qd2.} "
    "Be7{7...Be7.} "
    "O-O-O{8.O-O-O.} "
    "O-O{8...O-O.} "
    "f4{9.f4: a space-gaining move that supports an eventual e5.} "
    "Nxd4{9...Nxd4: trading to relieve the pressure.} "
    "Qxd4{10.Qxd4: the queen in the centre. White is slightly better developed and has more space.}",

    # ==== Rossolimo ============================================================================================================
    "e4 c5 Nf3 Nc6{2...Nc6.} "
    "Bb5{3.Bb5, the Rossolimo. White avoids the heavy theory of the Open Sicilian. The idea is to damage Black's pawns with Bxc6 and then play a solid positional game.} "
    "g6{3...g6.} "
    "Bxc6{4.Bxc6: doubling the pawns. White gets the better structure.} "
    "dxc6{4...dxc6.} "
    "d3{5.d3: a quiet set-up. White will play h3, Nc3 and Be3.} "
    "Bg7{5...Bg7.} "
    "h3{6.h3: prevents ...Bg4, which would be annoying.} "
    "Nf6{6...Nf6.} "
    "Nc3{7.Nc3.} "
    "Qc7{7...Qc7.} "
    "Be3{8.Be3.} "
    "b6{8...b6.} "
    "Qd2{9.Qd2.} "
    "e5{9...e5: Black gets the centre. White aims for an edge in a long game.}",

    "e4 c5 Nf3 Nc6 Bb5 e6{3...e6.} "
    "O-O{4.O-O.} "
    "Nge7{4...Nge7.} "
    "Re1{5.Re1.} "
    "a6{5...a6: Black asks the bishop what it wants.} "
    "Bf1{6.Bf1: keeps the bishop and the option of d4.} "
    "d5{6...d5: Black strikes in the centre.} "
    "exd5{7.exd5.} "
    "exd5{7...exd5.} "
    "d4{8.d4: White opens the centre, and Black's king is still in the middle. The knight on e7 is now pinned against it.} "
    "cxd4{8...cxd4.} "
    "Nxd4{9.Nxd4: you are more active. The pin on the e-file is awkward for Black, so it is wise not to hurry with ...d5.}",

    # ==== Alapin ================================================================================================================
    "e4 c5 c3{2.c3, the Alapin. White prepares d4 to build an ideal pawn centre. The idea is the e4 + d4 duo, supported by the c3 pawn, and quiet development.} "
    "d5{2...d5: Black strikes at the centre at once. This is the sharpest reply.} "
    "exd5{3.exd5.} "
    "Qxd5{3...Qxd5.} "
    "d4{4.d4: you get the centre and gain time on the queen.} "
    "Nf6{4...Nf6.} "
    "Nf3{5.Nf3.} "
    "Bg4{5...Bg4: Black pins the knight.} "
    "Be2{6.Be2.} "
    "e6{6...e6.} "
    "h3{7.h3: you ask the bishop what it wants. White wins the bishop pair if the bishop takes.} "
    "Bh5{7...Bh5.} "
    "O-O{8.O-O.} "
    "Nc6{8...Nc6.} "
    "Be3{9.Be3.} "
    "cxd4{9...cxd4.} "
    "cxd4{10.cxd4: White has a healthy centre. Next: Nc3, Qb3 or Rc1.} "
    "Bb4{10...Bb4: Black pins the knight, but the game is balanced.}",

    "e4 c5 c3 Nf6{2...Nf6: the other principled reply.} "
    "e5{3.e5: gain space and a tempo.} "
    "Nd5{3...Nd5.} "
    "d4{4.d4.} "
    "cxd4{4...cxd4.} "
    "Nf3{5.Nf3: you protect e5 and plan cxd4 or Bc4.} "
    "Nc6{5...Nc6.} "
    "cxd4{6.cxd4: now you have a full centre again.} "
    "d6{6...d6: Black immediately attacks the e5 pawn.} "
    "Bc4{7.Bc4: pressure on the d5 knight and the f7 square.} "
    "Nb6{7...Nb6.} "
    "Bb5{8.Bb5: you pin the knight on c6 and add pressure on e5.} "
    "dxe5{8...dxe5.} "
    "Nxe5{9.Nxe5: the position is balanced, but White has a lead in development.} "
    "Bd7{9...Bd7.}",

    # ==== Grand Prix / Closed ==================================================================================================
    "e4 c5 Nc3{2.Nc3: the start of the Closed Sicilian and Grand Prix systems. White avoids the Open Sicilian and builds a position of his own choice.} "
    "Nc6{2...Nc6.} "
    "f4{3.f4, the Grand Prix Attack. White plays for a quick attack on the kingside with f4, Nf3 and Bc4, and often f5.} "
    "g6{3...g6.} "
    "Nf3{4.Nf3.} "
    "Bg7{4...Bg7.} "
    "Bc4{5.Bc4: the bishop aims at f7. A threat arises when f5 comes.} "
    "e6{5...e6: solid, controls the d5 and f5 squares.} "
    "f5{6.f5: the pawn storm starts.} "
    "Nge7{6...Nge7.} "
    "fxe6{7.fxe6: you open the f-file against f7.} "
    "fxe6{7...fxe6.} "
    "d3{8.d3.} "
    "O-O{8...O-O.} "
    "O-O{9.O-O.} "
    "d5{9...d5: Black strikes in the centre.} "
    "exd5{10.exd5.} "
    "exd5{10...exd5.} "
    "Bb3{11.Bb3: the bishop stays on the a2-g8 diagonal and the position is balanced, with chances for both sides.}",

    "e4 c5 Nc3 Nc6 g3{3.g3, the Closed Sicilian. White fianchettoes the bishop and plays slowly: the bishop on g2 controls the long diagonal, "
    "and d3, Be3 and Qd2 follow. A positional game for White.} "
    "g6{3...g6.} "
    "Bg2{4.Bg2.} "
    "Bg7{4...Bg7.} "
    "d3{5.d3.} "
    "d6{5...d6.} "
    "Be3{6.Be3.} "
    "e6{6...e6.} "
    "Qd2{7.Qd2.} "
    "Nge7{7...Nge7.} "
    "Nge2{8.Nge2: keeps the f-pawn free for the f4 advance.} "
    "O-O{8...O-O.} "
    "O-O{9.O-O: next comes f4 and a kingside attack.} "
    "Nd4{9...Nd4: Black plants a knight in the centre.}",

    # ==== Smith-Morra Gambit ===================================================================================================
    "e4 c5 d4{2.d4: the Smith-Morra Gambit begins. White offers a pawn for fast development, hoping for an attack.} "
    "cxd4{2...cxd4.} "
    "c3{3.c3: the gambit. White offers the c-pawn to open lines and develop quickly.} "
    "dxc3{3...dxc3: Black accepts. Declining with 3...d5 is also possible.} "
    "Nxc3{4.Nxc3: White has two open files, a lead in development and the possibility of Bc4 and Qe2.} "
    "Nc6{4...Nc6.} "
    "Nf3{5.Nf3.} "
    "d6{5...d6.} "
    "Bc4{6.Bc4: the bishop eyes f7. All your pieces point at Black's kingside.} "
    "e6{6...e6.} "
    "O-O{7.O-O.} "
    "Nf6{7...Nf6.} "
    "Qe2{8.Qe2: the queen supports e4 and e5, and prepares Rd1.} "
    "Be7{8...Be7.} "
    "Rd1{9.Rd1.} "
    "e5{9...e5: Black stops the attack in the centre.} "
    "Bg5{10.Bg5: pin the f6 knight and keep up the pressure. White has good compensation for the pawn.} "
    "O-O{10...O-O.}",

    "e4 c5 d4 cxd4 c3 d5{3...d5!? declines the gambit and strikes back in the centre.} "
    "exd5{4.exd5.} "
    "Qxd5{4...Qxd5.} "
    "cxd4{5.cxd4: you have a pawn centre. Black's queen is exposed to Nc3.} "
    "Nf6{5...Nf6.} "
    "Nf3{6.Nf3.} "
    "e6{6...e6.} "
    "Nc3{7.Nc3: attack the queen with tempo.} "
    "Qd6{7...Qd6.} "
    "Bd3{8.Bd3: a strong, open position for White with the isolated d4 pawn supported by active pieces.}",
]

SECTIONS = [
    {"id": "open", "title": "Open Sicilian (2.Nf3, 3.d4)", "start": "e4 c5 Nf3", "icon": "⚔️",
     "summary": "The main road. After 3.d4 cxd4 4.Nxd4 you get space and a lead in development. Against the Najdorf play the English Attack (Be3, f3, Qd2, "
                "O-O-O, g4); against the Dragon the Yugoslav Attack with the h-pawn rush; against the Classical set-up the Richter-Rauzer with Bg5."},
    {"id": "rossolimo", "title": "Rossolimo (3.Bb5)", "start": "e4 c5 Nf3 Nc6 Bb5", "icon": "🎓",
     "summary": "A low-theory way to play against 2…Nc6. After Bxc6 Black has doubled pawns and you play a calm positional game with d3, h3, Nc3 and Be3. "
                "Against …e6 keep the bishop with Bf1 and open the centre with d4."},
    {"id": "alapin", "title": "Alapin (2.c3)", "start": "e4 c5 c3", "icon": "🏛️",
     "summary": "White prepares to build the ideal e4 + d4 pawn centre. After 2…d5 3.exd5 Qxd5 4.d4 you have the centre and gain time; after 2…Nf6 3.e5 Nd5 "
                "4.d4 cxd4 5.Nf3 you have space and quick development."},
    {"id": "closed", "title": "Grand Prix / Closed (2.Nc3)", "start": "e4 c5 Nc3", "icon": "🛡️",
     "summary": "Skip the heavy theory. The Grand Prix Attack (f4, Nf3, Bc4) is a quick kingside attack. The Closed Sicilian (g3, Bg2, d3, Be3, Qd2) "
                "is a slow strategic plan with a later f4."},
    {"id": "morra", "title": "Smith-Morra Gambit (2.d4)", "start": "e4 c5 d4", "icon": "🎁",
     "summary": "Sacrifice a pawn for development and attack. After 2.d4 cxd4 3.c3 dxc3 4.Nxc3 your pieces flow out with Bc4, Nf3, O-O and Qe2. "
                "If Black declines with 3…d5, take on d5 and recapture on d4 for an active centre."},
]

ANTI_SICILIAN = LessonTree(
    "Playing against the Sicilian", LINES, SECTIONS,
    intro="1.e4 c5, from White's side. The Sicilian is Black's sharpest reply, so here are five clear plans against it, from the main-line Open Sicilian to quiet "
          "systems with little theory.",
    slug="vs-sicilian", side="white", icon="⚔️", level="Intermediate",
    blurb="Five ways to meet 1…c5: Open Sicilian, Rossolimo, Alapin, Grand Prix and the Smith-Morra Gambit.")
