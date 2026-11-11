"""The Italian Game (1.e4 e5 2.Nf3 Nc6 3.Bc4), from White's side."""
from ..lessons import LessonTree

LINES = [
    "e4{1.e4: take the centre and open lines for the bishop and the queen.} "
    "e5{1...e5.} "
    "Nf3{2.Nf3 develops and attacks e5 at the same time.} "
    "Nc6{2...Nc6 defends e5.} "
    "Bc4{3.Bc4, the Italian Game. The bishop eyes f7, the weakest square in Black's camp, and you can castle quickly. The ideas are simple: develop, castle, "
    "then hit the centre with d3-c3 or d4. Black has three main replies: 3...Bc5, 3...Nf6 and, less often, 3...Be7.}",

    # ==== Giuoco Piano ==========================================================================================================
    "e4 e5 Nf3 Nc6 Bc4 Bc5{3...Bc5, the Giuoco Piano ('quiet game'). Black copies White's development and also eyes f2.} "
    "c3{4.c3 prepares d4 to build a big pawn centre and gives the bishop a retreat square on b3.} "
    "Nf6{4...Nf6 attacks e4.} "
    "d3{5.d3, the Giuoco Pianissimo ('very quiet'). White protects e4 solidly and keeps the position closed. Plans: O-O, Re1, Nbd2-f1-g3 and h3.} "
    "d6{5...d6.} "
    "O-O{6.O-O.} "
    "O-O{6...O-O.} "
    "Re1{7.Re1: protects e4 and prepares the knight manoeuvre.} "
    "a6{7...a6 gives the bishop on c5 an escape square.} "
    "Bb3{8.Bb3: you keep the bishop on the a2-g8 diagonal.} "
    "Ba7{8...Ba7: Black saves the bishop from the pawn push d4.} "
    "h3{9.h3 stops ...Bg4, which would pin your knight.} "
    "h6{9...h6.} "
    "Nbd2{10.Nbd2: the knight heads to f1 and then g3.} "
    "Re8{10...Re8.} "
    "Nf1{11.Nf1.} "
    "Be6{11...Be6: Black trades off your strong bishop. A slow, strategic game where White has more space.}",

    "e4 e5 Nf3 Nc6 Bc4 Bc5 c3 Nf6 d4{5.d4, the sharp main line. White strikes in the centre at once.} "
    "exd4{5...exd4.} "
    "cxd4{6.cxd4: now you have a big centre, and the bishop on c5 is attacked.} "
    "Bb4+{6...Bb4+ is a check that must be answered.} "
    "Bd2{7.Bd2.} "
    "Bxd2+{7...Bxd2+.} "
    "Nbxd2{8.Nbxd2: the knight recaptures and keeps the b1 knight out of the way of the c-pawn.} "
    "d5{8...d5! Black strikes back in the centre and the position is double-edged.} "
    "exd5{9.exd5.} "
    "Nxd5{9...Nxd5.} "
    "Qb3{10.Qb3: the queen attacks the d5 knight and b7.} "
    "Nce7{10...Nce7: Black keeps the knight and protects.} "
    "O-O{11.O-O.} "
    "O-O{11...O-O.} "
    "Rfe1{12.Rfe1.} "
    "c6{12...c6: a solid position. White has the more active pieces, Black the sturdier structure.}",

    "e4 e5 Nf3 Nc6 Bc4 Bc5 c3 Nf6 d4 exd4 cxd4 Bb4+ Nc3{7.Nc3, the Møller Attack. A real fighting line: White sacrifices a pawn for a strong centre and open lines.} "
    "Nxe4{7...Nxe4.} "
    "O-O{8.O-O.} "
    "Bxc3{8...Bxc3: Black gives up the bishop pair to win the d4 pawn.} "
    "d5{9.d5! The pawn attacks the c6 knight and opens the bishop.} "
    "Bf6{9...Bf6.} "
    "Re1{10.Re1: a pin on the e4 knight.} "
    "Ne7{10...Ne7.} "
    "Rxe4{11.Rxe4: you take the knight back. White has two pieces' worth of activity for the pawn.} "
    "d6{11...d6.}",

    # ==== Evans Gambit ==========================================================================================================
    "e4 e5 Nf3 Nc6 Bc4 Bc5 b4{4.b4!? The Evans Gambit. White gives up a pawn for a big pawn centre and a lead in development. It was a favourite of Kasparov's and is "
    "a great choice to learn tactics.} "
    "Bxb4{4...Bxb4.} "
    "c3{5.c3 attacks the bishop and prepares d4.} "
    "Ba5{5...Ba5: the bishop stays on the a5-d8 diagonal and pins the c3 pawn.} "
    "d4{6.d4: the big centre appears.} "
    "exd4{6...exd4.} "
    "O-O{7.O-O: you leave the pawn on d4 hanging because lines are about to open on Black's king.} "
    "d6{7...d6: a solid reply that gives the king safety.} "
    "cxd4{8.cxd4: the pawns e4 and d4 are back.} "
    "Bb6{8...Bb6.} "
    "Nc3{9.Nc3: more pressure on the centre. White's lead in development is worth the pawn.}",

    # ==== Two Knights Defence ===================================================================================================
    "e4 e5 Nf3 Nc6 Bc4 Nf6{3...Nf6, the Two Knights Defence. Black counterattacks e4 right away and does not allow a quiet game.} "
    "Ng5{4.Ng5! White ignores the threat and attacks f7 with two pieces.} "
    "d5{4...d5: the only good reply. Black strikes at the bishop and takes control of the centre.} "
    "exd5{5.exd5.} "
    "Na5{5...Na5! The best move. Black attacks the bishop and avoids the dangerous 5...Nxd5.} "
    "Bb5+{6.Bb5+: you keep the bishop pair.} "
    "c6{6...c6.} "
    "dxc6{7.dxc6.} "
    "bxc6{7...bxc6.} "
    "Be2{8.Be2: the bishop retreats and Black has to look after the h7 pawn.} "
    "h6{8...h6.} "
    "Nf3{9.Nf3.} "
    "e4{9...e4: Black gains time against the knight.} "
    "Ne5{10.Ne5.} "
    "Bd6{10...Bd6.} "
    "f4{11.f4: you keep the centre knight and the bishop. A sharp, double-edged fight.}",

    "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5 d5 exd5 Nxd5{5...Nxd5? is the natural capture, but it falls into the Fried Liver Attack.} "
    "Nxf7{6.Nxf7!? The Fried Liver. White sacrifices a knight to pull the king into the open.} "
    "Kxf7{6...Kxf7.} "
    "Qf3+{7.Qf3+.} "
    "Ke6{7...Ke6: the king is in the open, but it is hard to attack.} "
    "Nc3{8.Nc3: a new piece joins the attack. Black has a lot of material, and White has a ferocious initiative.} "
    "Nb4{8...Nb4: Black attacks c2 and fights back.} "
    "Qe4{9.Qe4: the queen protects c2 and keeps the pressure.} "
    "c6{9...c6.} "
    "a3{10.a3.} "
    "Na6{10...Na6.} "
    "d4{11.d4: White has plenty of compensation, with the king stuck in the middle of the board.}",

    "e4 e5 Nf3 Nc6 Bc4 Nf6 d3{4.d3: the quiet 4.d3 aims for a Giuoco Pianissimo structure.} "
    "Bc5{4...Bc5.} "
    "c3{5.c3.} "
    "d6{5...d6: the same pawn structure as in the Giuoco Pianissimo, so you can transpose.} "
    "O-O{6.O-O.} "
    "O-O{6...O-O.} "
    "Re1{7.Re1.} "
    "a6{7...a6.} "
    "Bb3{8.Bb3.} "
    "Ba7{8...Ba7: the same position as in the Pianissimo.}",
]

SECTIONS = [
    {"id": "piano", "title": "Giuoco Piano (3…Bc5)", "start": "e4 e5 Nf3 Nc6 Bc4 Bc5", "icon": "🎻",
     "summary": "Both sides develop naturally. The slow plan c3-d3, O-O, Re1, Nbd2-f1-g3 (the Pianissimo) wins by manoeuvring. The sharper c3-d4 grabs the centre, "
                "and the Møller Attack sacrifices a pawn for the initiative."},
    {"id": "evans", "title": "Evans Gambit (4.b4)", "start": "e4 e5 Nf3 Nc6 Bc4 Bc5 b4", "icon": "🎁",
     "summary": "Give up the b-pawn to deflect Black's bishop, play c3 and d4, and build a pawn centre while your pieces rush out. "
                "Attacking chances are the compensation: keep the initiative and open lines."},
    {"id": "two-knights", "title": "Two Knights (3…Nf6)", "start": "e4 e5 Nf3 Nc6 Bc4 Nf6", "icon": "🐴",
     "summary": "4.Ng5 attacks f7. After 4…d5 5.exd5 the best reply is 5…Na5, and White gets a small edge after Bb5+ c6 dxc6 bxc6 Be2. "
                "If Black greedily plays 5…Nxd5, the Fried Liver shows the attack. The quiet 4.d3 transposes to the Giuoco Pianissimo."},
]

ITALIAN = LessonTree(
    "Italian Game", LINES, SECTIONS,
    intro="1.e4 e5 2.Nf3 Nc6 3.Bc4, played from White's side. Simple to learn: develop fast, castle, and use the bishop on c4 to pressure f7.",
    slug="italian", side="white", icon="🇮🇹", level="Beginner",
    blurb="Classic and easy to learn: quick development, a bishop aimed at f7, plus the Evans Gambit for attackers.")
