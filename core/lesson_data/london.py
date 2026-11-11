"""The London System (1.d4 and 2.Bf4), from White's side."""
from ..lessons import LessonTree

LINES = [
    "d4{1.d4: take the centre with the queen's pawn.} "
    "d5{1...d5.} "
    "Bf4{2.Bf4, the London System. The bishop comes out before the pawn on e3 closes the diagonal. It is a system, not a set of memorised moves: the same "
    "set-up (Bf4, e3, Nf3, Bd3, c3, Nbd2) works against almost everything. Black has many ways to respond, and the buttons above show the most important ones.} "
    "Nf6{2...Nf6.} "
    "e3{3.e3: the bishop is now safe behind the pawn chain and the f1 bishop is free.} "
    "e6{3...e6.} "
    "Nf3{4.Nf3.} "
    "Bd6{4...Bd6: Black challenges the London bishop directly.} "
    "Bg3{5.Bg3: you keep the bishop pair potential and prepare to take on d6 with a pawn if needed.} "
    "O-O{5...O-O.} "
    "Nbd2{6.Nbd2: this knight supports e4 and keeps the c-pawn free.} "
    "c5{6...c5.} "
    "c3{7.c3: solid, protects d4 and the b4 square.} "
    "Nc6{7...Nc6.} "
    "Bd3{8.Bd3: the bishop eyes h7 and supports e4.} "
    "Qe7{8...Qe7.} "
    "O-O{9.O-O.} "
    "Bxg3{9...Bxg3.} "
    "hxg3{10.hxg3: the recapture opens the h-file for your rook, and the structure is healthy. A very typical London position.}",

    "d4 d5 Bf4 Nf6 e3 e6 Nf3 c5{4...c5: Black strikes at d4.} "
    "c3{5.c3: you are solid and keep the centre.} "
    "Nc6{5...Nc6.} "
    "Nbd2{6.Nbd2.} "
    "Bd6{6...Bd6.} "
    "Bg3{7.Bg3.} "
    "O-O{7...O-O.} "
    "Bd3{8.Bd3: now e4 is coming. Black has equal chances, but you have a pleasant set-up where it is easy to find plans.} "
    "b6{8...b6.}",

    # ==== against ...c5 =========================================================================================================
    "d4 d5 Bf4 c5{2...c5 hits d4 immediately. White must not defend with c3 only; develop with e3.} "
    "e3{3.e3.} "
    "Nc6{3...Nc6.} "
    "c3{4.c3: a very solid pawn on c3 protects d4.} "
    "Nf6{4...Nf6.} "
    "Nd2{5.Nd2: the knight goes to d2 first so that Ngf3 can follow without blocking the c-pawn.} "
    "e6{5...e6.} "
    "Ngf3{6.Ngf3.} "
    "Bd6{6...Bd6.} "
    "Bg3{7.Bg3.} "
    "O-O{7...O-O.} "
    "Bd3{8.Bd3: your pieces are ideally placed. Plans: O-O, Ne5 and f4, or Qe2 and e4.} "
    "Nh5{8...Nh5: Black tries to eliminate your bishop.}",

    # ==== against ...Bf5 ========================================================================================================
    "d4 d5 Bf4 Bf5{2...Bf5: Black copies you.} "
    "e3{3.e3.} "
    "e6{3...e6.} "
    "Nf3{4.Nf3.} "
    "Nf6{4...Nf6.} "
    "Bd3{5.Bd3: offers to trade the light-squared bishops before Black can take the pressure off your centre.} "
    "Bxd3{5...Bxd3.} "
    "Qxd3{6.Qxd3: your queen is active and eyes the b5 and a6 squares.} "
    "Bd6{6...Bd6.} "
    "Bxd6{7.Bxd6: you trade the dark-squared bishops too, which leaves a calm position.} "
    "Qxd6{7...Qxd6.} "
    "Nbd2{8.Nbd2: a harmonious set-up. The c-pawn is free to go to c4 or c3.} "
    "Nbd7{8...Nbd7.} "
    "O-O{9.O-O.} "
    "O-O{9...O-O.} "
    "e4{10.e4: now you take the centre, with a small but safe plus.} "
    "dxe4{10...dxe4.} "
    "Nxe4{11.Nxe4: the knights trade off and White is slightly more comfortable.} "
    "Nxe4{11...Nxe4.}",

    # ==== against the King's Indian set-up =====================================================================================
    "d4 Nf6{1...Nf6.} "
    "Nf3{2.Nf3: the knight comes out first to avoid ...Ne4 hitting the bishop.} "
    "g6{2...g6: the King's Indian / Grunfeld set-up.} "
    "Bf4{3.Bf4.} "
    "Bg7{3...Bg7.} "
    "e3{4.e3.} "
    "O-O{4...O-O.} "
    "Be2{5.Be2: against the fianchetto, the bishop belongs on e2.} "
    "d6{5...d6.} "
    "h3{6.h3: a useful waiting move that gives the bishop on f4 an escape square on h2.} "
    "Nbd7{6...Nbd7.} "
    "O-O{7.O-O.} "
    "Re8{7...Re8.} "
    "c3{8.c3.} "
    "e5{8...e5: Black attacks the bishop and the centre.} "
    "Bh2{9.Bh2: the bishop is safe on h2 and keeps an eye on the diagonal. A solid position: you can now play Nbd2 and Qc2.} "
    "exd4{9...exd4.}",
]

SECTIONS = [
    {"id": "main", "title": "vs …d5 …e6 (main)", "start": "d4 d5 Bf4 Nf6", "icon": "🏙️",
     "summary": "The standard London position: pawns on d4, e3 and c3, bishops on f4 and d3, knights on f3 and d2. If Black plays …Bd6 offer the trade with Bg3; "
                "after …c5 stay solid with c3 and develop the pieces."},
    {"id": "c5", "title": "vs …c5", "start": "d4 d5 Bf4 c5", "icon": "🎯",
     "summary": "Black hits d4 at once. Play e3 and c3, and develop the queenside knight to d2 so that the g1 knight can come to f3 without blocking the c-pawn."},
    {"id": "bf5", "title": "vs …Bf5", "start": "d4 d5 Bf4 Bf5", "icon": "🪞",
     "summary": "Black mirrors your bishop. Develop normally and offer a trade of light-squared bishops with Bd3. After Qxd3 your queen is active and h-file ideas appear."},
    {"id": "kid", "title": "vs the King's Indian set-up", "start": "d4 Nf6 Nf3 g6", "icon": "👑",
     "summary": "Against …g6 play Bf4, e3, Be2, h3, O-O and c3. Keep the bishop safe with h3 and Bh2 when Black plays …e5, and keep a solid pawn structure."},
]

LONDON = LessonTree(
    "London System", LINES, SECTIONS,
    intro="1.d4 and 2.Bf4, played from White's side. A system opening: learn one set-up (Bf4, e3, Nf3, Bd3, c3, Nbd2) and play it against almost anything.",
    slug="london", side="white", icon="🌉", level="Beginner",
    blurb="A low-theory system for White: one set-up that works against almost everything.")
