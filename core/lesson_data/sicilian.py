"""The Sicilian Defence (1.e4 c5), from Black's side: the Najdorf, the Dragon, the Scheveningen set-up and the Sveshnikov."""
from ..lessons import LessonTree

OPEN = "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3"

LINES = [
    "e4{1.e4: White opens with the king's pawn.} "
    "c5{1...c5, the Sicilian Defence. Black fights for the centre from the side: the c-pawn attacks d4, so Black gets an unbalanced game "
    "where both sides have winning chances. It is the most popular and most successful reply to 1.e4.} "
    "Nf3{2.Nf3 prepares d4.} "
    "d6{2...d6 controls e5 and prepares ...Nf6 and ...cxd4. (Black can also play 2...Nc6 or 2...e6.)} "
    "d4{3.d4: White opens the centre, the 'Open Sicilian'.} "
    "cxd4{3...cxd4: Black gives up the c-pawn for White's d-pawn. Now White has an extra central pawn and Black has an extra open file, the c-file.} "
    "Nxd4{4.Nxd4: the knight is centralised.} "
    "Nf6{4...Nf6 attacks the e4 pawn and forces White to defend it.} "
    "Nc3{5.Nc3 defends e4. Black now chooses a system. 5...a6 is the Najdorf, 5...g6 the Dragon, and 5...e6 the Scheveningen set-up.}",

    # ==== Najdorf ============================================================================================================
    OPEN + " a6{5...a6, the Najdorf. A flexible waiting move: it stops Nb5 and Bb5+, and prepares ...e5 or ...e6 and the queenside expansion ...b5. "
    "It was the favourite of Fischer and Kasparov.} "
    "Be3{6.Be3, the English Attack. White plays f3, Qd2, O-O-O and then storms with g4-g5.} "
    "e5{6...e5 kicks the knight and fixes the pawn structure. The d5 square becomes a hole in Black's camp, but Black gets space and a healthy centre.} "
    "Nb3{7.Nb3: the knight retreats and keeps an eye on a5 and c5.} "
    "Be6{7...Be6 develops the bishop and eyes the a2-g8 diagonal.} "
    "f3{8.f3 protects e4 and prepares g4.} "
    "Be7{8...Be7.} "
    "Qd2{9.Qd2.} "
    "O-O{9...O-O: Black castles into the storm, because the counter on the queenside is fast.} "
    "O-O-O{10.O-O-O: opposite-side castling, so both sides race to attack the other king.} "
    "Nbd7{10...Nbd7.} "
    "g4{11.g4: the pawn storm begins.} "
    "b5{11...b5: Black counterattacks on the queenside at once. It is a pure race.} "
    "g5{12.g5 attacks the knight on f6.} "
    "b4{12...b4 attacks the c3 knight. Black gains time.} "
    "Ne2{13.Ne2.} "
    "Ne8{13...Ne8: the knight retreats, and covers g7 and d6.} "
    "f4{14.f4: White keeps attacking in the centre and on the kingside.} "
    "a5{14...a5: Black pushes on the queenside. A sharp, balanced fight.}",

    OPEN + " a6 Bg5{6.Bg5, the main alternative. White pins the f6 knight against the queen's side and prepares f4.} "
    "e6{6...e6.} "
    "f4{7.f4: a space-grabbing move, preparing Qf3 and O-O-O.} "
    "Be7{7...Be7: the solid choice (7...Qb6 is the Poisoned Pawn).} "
    "Qf3{8.Qf3.} "
    "Qc7{8...Qc7.} "
    "O-O-O{9.O-O-O.} "
    "Nbd7{9...Nbd7: Black is ready to break with ...b5 and ...Nc5. White has the initiative on the kingside.} "
    "g4{10.g4.} "
    "b5{10...b5.} "
    "Bxf6{11.Bxf6 removes a defender.} "
    "Nxf6{11...Nxf6.} "
    "g5{12.g5.} "
    "Nd7{12...Nd7.} "
    "f5{13.f5: White opens the lines against the king.} "
    "Ne5{13...Ne5: Black's knight is strong in the middle. A theoretical battle, very sharp.}",

    OPEN + " a6 Bg5 e6 f4 Qb6{7...Qb6, the Poisoned Pawn Variation. Black takes the b2 pawn with the queen and risks being cut off.} "
    "Qd2{8.Qd2.} "
    "Qxb2{8...Qxb2: the pawn is 'poisoned', but Black's queen is far from home.} "
    "Rb1{9.Rb1 attacks the queen.} "
    "Qa3{9...Qa3 is the only square that keeps the queen safe.} "
    "e5{10.e5: White opens the position and aims for the king. Extremely sharp theory, often well known to both sides.}",

    OPEN + " a6 Be2{6.Be2, the quiet main line. White develops simply and castles, without a direct attack.} "
    "e5{6...e5.} "
    "Nb3{7.Nb3.} "
    "Be7{7...Be7.} "
    "O-O{8.O-O.} "
    "O-O{8...O-O.} "
    "Be3{9.Be3.} "
    "Be6{9...Be6: Black develops and controls d5.} "
    "f4{10.f4: White opens the f-file.} "
    "Qc7{10...Qc7.} "
    "a4{11.a4: stops ...b5.} "
    "Nbd7{11...Nbd7.} "
    "Kh1{12.Kh1.} "
    "Rac8{12...Rac8: Black's pieces are well placed. Plans: ...exf4 and ...Ne5, or ...Nc5.}",

    # ==== Scheveningen set-up ==============================================================================================
    OPEN + " a6 Be2 e6{6...e6: the Scheveningen structure with pawns on d6 and e6. A compact, flexible set-up that keeps everything protected.} "
    "O-O{7.O-O.} "
    "Be7{7...Be7.} "
    "f4{8.f4: space in the centre.} "
    "Qc7{8...Qc7.} "
    "Kh1{9.Kh1 sidesteps tricks on the g1-a7 diagonal.} "
    "O-O{9...O-O.} "
    "a4{10.a4 stops ...b5.} "
    "Nc6{10...Nc6: Black challenges the knight on d4.} "
    "Be3{11.Be3.} "
    "Re8{11...Re8: Black keeps everything protected and waits for the right moment to strike with ...e5 or ...d5.}",

    # ==== Dragon ================================================================================================================
    OPEN + " g6{5...g6, the Dragon. The bishop on g7 shoots along the long diagonal and the pawn structure looks like a dragon's tail. "
    "Black gets fast development and attacking chances against White's king. Real sharp stuff.} "
    "Be3{6.Be3, preparing the Yugoslav Attack.} "
    "Bg7{6...Bg7.} "
    "f3{7.f3 protects e4 and prepares Qd2 and O-O-O.} "
    "O-O{7...O-O.} "
    "Qd2{8.Qd2.} "
    "Nc6{8...Nc6: Black pressures d4 and prepares ...d5 or ...Rc8.} "
    "Bc4{9.Bc4: the bishop aims at f7 and prepares to play Bb3.} "
    "Bd7{9...Bd7: Black prepares ...Rc8 and ...Ne5.} "
    "O-O-O{10.O-O-O: opposite-side castling. The h-pawn will soon push forward.} "
    "Rc8{10...Rc8: the rook enters the half-open c-file.} "
    "Bb3{11.Bb3.} "
    "Ne5{11...Ne5: Black's knight eyes c4 and wants to harass the bishop on b3.} "
    "h4{12.h4: White starts the attack on the h-file.} "
    "h5{12...h5: Black stops the h-pawn. The Dragon is a race: White attacks on the kingside, Black uses the c-file.}",

    OPEN + " g6 Be2{6.Be2, the Classical Dragon: calmer, with the bishop on e2.} "
    "Bg7{6...Bg7.} "
    "O-O{7.O-O.} "
    "O-O{7...O-O.} "
    "Be3{8.Be3.} "
    "Nc6{8...Nc6.} "
    "Nb3{9.Nb3.} "
    "Be6{9...Be6: Black develops and eyes the c4 square.} "
    "f4{10.f4.} "
    "Na5{10...Na5: Black attacks the knight on b3 and plans ...Bc4.}",

    # ==== Sveshnikov ============================================================================================================
    "e4 c5 Nf3 Nc6{2...Nc6 develops with pressure on d4.} "
    "d4{3.d4.} "
    "cxd4{3...cxd4.} "
    "Nxd4{4.Nxd4.} "
    "Nf6{4...Nf6.} "
    "Nc3{5.Nc3.} "
    "e5{5...e5! The Sveshnikov: Black kicks the knight with a central pawn, accepting the hole on d5 in return for space and activity.} "
    "Ndb5{6.Ndb5.} "
    "d6{6...d6.} "
    "Bg5{7.Bg5.} "
    "a6{7...a6 kicks the knight again.} "
    "Na3{8.Na3: the knight heads for the strong c4 and d5 squares.} "
    "b5{8...b5: Black gains space on the queenside.} "
    "Nd5{9.Nd5: White uses the hole at d5.} "
    "Be7{9...Be7: Black wants to remove White's best minor pieces.} "
    "Bxf6{10.Bxf6.} "
    "Bxf6{10...Bxf6.} "
    "c3{11.c3 supports the knight on d5.} "
    "O-O{11...O-O: a famous position. White has the d5 outpost, Black has the bishop pair and the plan ...Bg5, ...Rb8 and ...f5.}",

    "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Nf6 Nc3 e5 Ndb5 d6 Bg5 a6 Na3 b5 Bxf6{9.Bxf6, the Chelyabinsk Variation: White damages Black's pawns.} "
    "gxf6{9...gxf6.} "
    "Nd5{10.Nd5.} "
    "f5{10...f5: Black fights back with ...f5 to open the f-file and give the e5 pawn a supporter.} "
    "Bd3{11.Bd3.} "
    "Be6{11...Be6.} "
    "O-O{12.O-O.} "
    "Bxd5{12...Bxd5: Black removes the strong knight on d5. The position is about equal, and Black's bishop pair and open g-file give counterplay.}",
]

SECTIONS = [
    {"id": "najdorf", "title": "Najdorf (5…a6)", "start": OPEN + " a6", "icon": "👑",
     "summary": "The most flexible Sicilian. Against 6.Be3 play …e5 and castle short: both sides race with opposite plans (g4-g5 against …b5-b4). "
                "Against 6.Bg5 play …e6 and …Be7 and break with …b5. 6.Be2 is a quieter fight where Black plays …e5 and …Be6."},
    {"id": "scheveningen", "title": "Scheveningen (…e6)", "start": OPEN + " a6 Be2 e6", "icon": "🧱",
     "summary": "Pawns on d6 and e6 make a compact structure that is hard to crack. Black waits for White to commit and then hits back "
                "with …d5 or …e5."},
    {"id": "dragon", "title": "Dragon (5…g6)", "start": OPEN + " g6", "icon": "🐉",
     "summary": "Black fianchettoes the bishop on g7 and castles short. Against the Yugoslav Attack (Be3, f3, Qd2, O-O-O, h4) Black uses the c-file "
                "and the long diagonal. The classical 6.Be2 is calmer; Black aims for …Be6 and …Na5."},
    {"id": "sveshnikov", "title": "Sveshnikov (…e5)", "start": "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Nf6 Nc3 e5", "icon": "⚡",
     "summary": "After 2…Nc6 and 5…e5 Black kicks the knight and accepts a hole on d5 for space. Typical plans: …Bg5, …Rb8 and …f5. "
                "In the Chelyabinsk 9.Bxf6 gxf6 the …f5 break gives Black good counterplay."},
]

SICILIAN = LessonTree(
    "Sicilian Defence", LINES, SECTIONS,
    intro="1.e4 c5, played from Black's side. An ambitious reply to 1.e4: Black plays for a win with an unbalanced position, trading central pawns for a half-open c-file.",
    slug="sicilian", side="black", icon="🐉", level="Intermediate",
    blurb="The sharpest answer to 1.e4. The Najdorf, the Dragon, Scheveningen and Sveshnikov set-ups.")
