"""The Vienna Game (1.e4 e5 2.Nc3), from White's side."""
from ..lessons import LessonTree

LINES = [
    "e4{1.e4: White takes the centre and opens lines for the queen and the light-squared bishop.} "
    "e5{1...e5: Black mirrors White and fights for the centre.} "
    "Nc3{2.Nc3, the Vienna Game. Instead of the usual 2.Nf3, White develops the queen's knight first. It guards the e4 pawn, keeps the f-pawn free "
    "to push to f4, and keeps the choice between a quiet game and a sharp gambit. White has not yet decided where the king's knight goes.} "
    "Nf6{2...Nf6 is Black's most natural reply: it develops with a threat on e4. White now picks a plan: the sharp 3.f4 (Vienna Gambit), the classical "
    "3.Bc4, or the calm 3.g3 and 3.Nf3.}",

    # ==== Vienna Gambit (3.f4) ==============================================================================================
    "e4 e5 Nc3 Nf6 f4{3.f4, the Vienna Gambit. White attacks the e5 pawn at once and wants to build a big centre with d3/d4. The price: the king "
    "gets a little exposed and the pawn on e4 needs care.} "
    "d5{3...d5 is Black's most principled reply: strike in the centre before White's pawns get going.} "
    "fxe5{4.fxe5 wins a pawn and attacks the knight on f6, but it also opens the f-file and the e1-h4 diagonal towards White's own king.} "
    "Nxe4{4...Nxe4: the knight lands in the centre and the pawn is won back. White must now develop quickly and challenge the knight.} "
    "Nf3{5.Nf3 develops and protects e5. The pawn on e5 cramps Black, and White plans d4 and Bd3 to kick the knight.} "
    "Be7{5...Be7 prepares to castle. Black's plan is ...O-O and ...f6 or ...f5 to attack the e5 pawn.} "
    "d4{6.d4 builds the centre. Now Bd3 is coming, and the e4 knight will soon have to move or be traded.} "
    "O-O{6...O-O gets the king safe before the position opens.} "
    "Bd3{7.Bd3 attacks the knight on e4.} "
    "f5{7...f5: the knight on e4 is supported and the e5 pawn comes under fire. White can capture en passant.} "
    "exf6{8.exf6: capturing en passant opens the e-file and the a2-g8 diagonal. Black recaptures with the bishop.} "
    "Bxf6{8...Bxf6: Black's bishop looks at the long diagonal and the c3 knight.} "
    "O-O{9.O-O: White castles. Black can now trade the strong e4 knight for the c3 knight.} "
    "Nxc3{9...Nxc3: removing the defender of White's centre.} "
    "bxc3{10.bxc3: White gets a strong centre and the open b-file, but a weakened pawn structure on the queenside. A sharp, balanced fight.}",

    "e4 e5 Nc3 Nf6 f4 exf4{3...exf4: Black accepts the pawn.} "
    "e5{4.e5: White drives the knight away and opens the e-file. A real gambit line: White gets a lead in development for the pawn.} "
    "Qe7{4...Qe7: the queen attacks the e5 pawn and the knight on f6 has to find a new square.} "
    "Qe2{5.Qe2 protects e5 and keeps an eye on the e-file.} "
    "Ng8{5...Ng8: the knight goes home. (5...Ng4?? loses a piece to Qxg4.)} "
    "Nf3{6.Nf3 develops and gives e5 another defender. White has a big lead in development for the pawn, and the engine likes White here. "
    "That is why Black's best answer to 3.f4 is 3...d5, not the pawn grab.}",

    # ==== Bishop's Vienna (3.Bc4) ===========================================================================================
    "e4 e5 Nc3 Nf6 Bc4{3.Bc4: the bishop aims at f7, the weak square next to the king, while the knight guards e4. White builds quietly "
    "and keeps f4 in reserve.} "
    "Nxe4{3...Nxe4 is the critical test. Black takes a pawn, but the knight is exposed and White has two sharp replies.} "
    "Qh5{4.Qh5! threatens both Qxf7# and Qxe5+. The queen attacks e5 and f7 at once.} "
    "Nd6{4...Nd6 is forced: it blocks the bishop's attack on f7 and attacks the bishop on c4.} "
    "Bb3{5.Bb3 keeps the bishop on the a2-g8 diagonal.} "
    "Be7{5...Be7 develops safely. Black's extra pawn is not hurting White's initiative.} "
    "Nf3{6.Nf3 develops with a threat on e5, which is now defended only by the knight's help.} "
    "Nc6{6...Nc6 defends e5 and develops.} "
    "Nxe5{7.Nxe5 takes the pawn back. The knight on d6 and the king stay under pressure.} "
    "Nxe5{7...Nxe5.} "
    "Qxe5{8.Qxe5: material is equal again and White's queen is active in the centre.} "
    "O-O{8...O-O: Black gets safe. White is a little more active, but nothing is decided.}",

    "e4 e5 Nc3 Nf6 Bc4 Nxe4 Qh5 Nd6 Bb3 Nc6{5...Nc6: a wild alternative that invites chaos (the Frankenstein-Dracula Variation).} "
    "Nb5{6.Nb5!? attacks c7 and d6. White heads for a mating attack.} "
    "g6{6...g6 attacks the queen.} "
    "Qf3{7.Qf3 eyes f7 and c6.} "
    "f5{7...f5 holds f7 and prepares ...Qe7.} "
    "Qd5{8.Qd5 attacks a8, b7 and e5 together.} "
    "Qe7{8...Qe7 protects the rook and prepares to meet Nxc7+.} "
    "Nxc7+{9.Nxc7+: the knight forks the king and the rook on a8.} "
    "Kd8{9...Kd8.} "
    "Nxa8{10.Nxa8 wins the rook, but the knight on a8 is trapped.} "
    "b6{10...b6 traps it. Both sides have extra material and attacking chances. It is a famous trap opening, mostly for fun.}",

    "e4 e5 Nc3 Nf6 Bc4 Nxe4 Nxe4{4.Nxe4: the calm reply. White trades the pawn-grabbing knight.} "
    "d5{4...d5 forks the bishop on c4 and the knight on e4.} "
    "Bd3{5.Bd3 keeps the bishop. If Black takes on e4, White recaptures and has a lead in development.} "
    "dxe4{5...dxe4.} "
    "Bxe4{6.Bxe4: material is level, White has the bishop pair's pressure on the b1-h7 diagonal and an easy development.}",

    # ==== Quiet Vienna (3.g3 / 3.Nf3) =======================================================================================
    "e4 e5 Nc3 Nf6 g3{3.g3: the quiet Vienna. White fianchettoes the bishop to g2, builds slowly and keeps the f-pawn at home.} "
    "d5{3...d5: Black strikes in the centre.} "
    "exd5{4.exd5.} "
    "Nxd5{4...Nxd5.} "
    "Bg2{5.Bg2: the bishop eyes the d5 knight and the long diagonal.} "
    "Nxc3{5...Nxc3: Black trades the strong knight.} "
    "bxc3{6.bxc3: White gets a flexible centre of c3, d4 and e4, plus the long diagonal for the bishop.} "
    "Bd6{6...Bd6.} "
    "Nf3{7.Nf3 attacks e5.} "
    "O-O{7...O-O.} "
    "O-O{8.O-O: White is ready for d4. Plans: d4, Re1 and a central pawn break.} "
    "Nc6{8...Nc6 defends e5 and keeps the centre under control.}",

    "e4 e5 Nc3 Nf6 Nf3{3.Nf3: the Vienna often reaches the Four Knights Game.} "
    "Nc6{3...Nc6.} "
    "Bb5{4.Bb5, the Spanish Four Knights.} "
    "Bb4{4...Bb4 mirrors White.} "
    "O-O{5.O-O.} "
    "O-O{5...O-O.} "
    "d3{6.d3.} "
    "Bxc3{6...Bxc3: Black trades the bishop for the knight to double the pawns.} "
    "bxc3{7.bxc3: White's bishop pair and open b-file make up for the pawn structure.} "
    "d6{7...d6.} "
    "Bg5{8.Bg5 pins the f6 knight.} "
    "Qe7{8...Qe7.} "
    "Re1{9.Re1.} "
    "Nd8{9...Nd8 heads for e6 and prepares ...Ne6.} "
    "d4{10.d4 takes the centre.} "
    "Ne6{10...Ne6: a classic Four Knights position, balanced and rich.}",

    # ==== Other replies by Black ============================================================================================
    "e4 e5 Nc3 Nc6{2...Nc6 develops without committing the g8 knight.} "
    "g3{3.g3: White builds the fianchetto.} "
    "Nf6{3...Nf6.} "
    "Bg2{4.Bg2.} "
    "Bc5{4...Bc5.} "
    "Nge2{5.Nge2: the knight goes to e2 so the f-pawn stays free for f4.} "
    "d6{5...d6.} "
    "O-O{6.O-O: White follows with d3 and f4. A calm game where White has more space.}",

    "e4 e5 Nc3 Bc5{2...Bc5 develops the bishop early and aims at f2.} "
    "Nf3{3.Nf3: develops and attacks e5.} "
    "d6{3...d6.} "
    "Na4{4.Na4! hits the bishop. If it retreats White has the bishop pair.} "
    "Bb6{4...Bb6.} "
    "Nxb6{5.Nxb6.} "
    "axb6{5...axb6: Black gets the a-file but a worse pawn structure.} "
    "d4{6.d4 strikes in the centre.} "
    "Nf6{6...Nf6.} "
    "Bd3{7.Bd3: White is a little more comfortable.}",
]

SECTIONS = [
    {"id": "gambit", "title": "Vienna Gambit (3.f4)", "start": "e4 e5 Nc3 Nf6 f4", "icon": "🔥",
     "summary": "White fights for the centre at once with f4. After 3…d5 4.fxe5 Nxe4 5.Nf3 the plan is d4, Bd3 and castling, with the open f-file "
                "as an asset. Black's counter is …Be7, …O-O and …f5. In the accepted line 3…exf4 4.e5, White gets quick development for the pawn."},
    {"id": "bishop", "title": "Bishop's Vienna (3.Bc4)", "start": "e4 e5 Nc3 Nf6 Bc4", "icon": "🎯",
     "summary": "The bishop aims at f7. If Black grabs the pawn with 3…Nxe4, the move Qh5 creates double threats (Qxf7# and Qxe5+) and White "
                "wins the pawn back with a lead in development. 4.Nxe4 d5 5.Bd3 is the calm way to get a pleasant game."},
    {"id": "quiet", "title": "Quiet Vienna (g3 / Nf3)", "start": "e4 e5 Nc3 Nf6 g3", "icon": "♟️",
     "summary": "With 3.g3 White builds a flexible fianchetto and a central pawn trio. With 3.Nf3 the game usually transposes to the Four Knights. "
                "These lines are great for players who prefer plans to memorised theory."},
    {"id": "other", "title": "Other 2nd moves", "start": "e4 e5 Nc3 Nc6", "icon": "🔀",
     "summary": "If Black answers 2.Nc3 with 2…Nc6 or 2…Bc5 White simply develops. Against 2…Nc6 build with g3 and Bg2, against 2…Bc5 "
                "use Na4 to win the bishop pair."},
]

VIENNA = LessonTree(
    "Vienna Game", LINES, SECTIONS,
    intro="1.e4 e5 2.Nc3, played from White's side. A flexible opening: develop the knight first, then decide between a sharp attack and a calm, strategic game.",
    slug="vienna", side="white", icon="🏰", level="Beginner",
    blurb="A flexible, attacking choice for White with a sharp gambit (f4) and calm alternatives.")
