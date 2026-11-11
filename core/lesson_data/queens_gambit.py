"""The Queen's Gambit (1.d4 d5 2.c4), from White's side: Declined, Accepted and the Slav."""
from ..lessons import LessonTree

LINES = [
    "d4{1.d4.} "
    "d5{1...d5.} "
    "c4{2.c4, the Queen's Gambit. It is not a real gambit: if Black takes on c4, White gets the pawn back easily. White attacks d5 with a wing pawn so that "
    "the centre can be undermined. Black has three main ways to answer: decline with 2...e6, accept with 2...dxc4, or defend with 2...c6 (the Slav).}",

    # ==== Declined ==============================================================================================================
    "d4 d5 c4 e6{2...e6, the Queen's Gambit Declined. Black keeps the d5 pawn and builds a rock-solid centre. The price: the bishop on c8 is a bit locked in.} "
    "Nc3{3.Nc3.} "
    "Nf6{3...Nf6.} "
    "Bg5{4.Bg5: the classic pin that pressures d5 by pinning the defender.} "
    "Be7{4...Be7.} "
    "e3{5.e3.} "
    "O-O{5...O-O.} "
    "Nf3{6.Nf3.} "
    "Nbd7{6...Nbd7.} "
    "Rc1{7.Rc1: the rook supports c4 and prepares cxd5 and the queenside pressure.} "
    "c6{7...c6: Black solidifies d5.} "
    "Bd3{8.Bd3.} "
    "dxc4{8...dxc4: Black takes only now, once the bishop has committed.} "
    "Bxc4{9.Bxc4.} "
    "Nd5{9...Nd5: Black trades pieces to free the position.} "
    "Bxe7{10.Bxe7.} "
    "Qxe7{10...Qxe7.} "
    "O-O{11.O-O.} "
    "Nxc3{11...Nxc3.} "
    "Rxc3{12.Rxc3: a balanced position.} "
    "e5{12...e5: Black frees the position with the central break. This is the main line of the Orthodox Defence.}",

    "d4 d5 c4 e6 Nc3 Nf6 cxd5{4.cxd5, the Exchange Variation. White gets a clear plan, the minority attack with b4-b5, or a kingside plan with e4.} "
    "exd5{4...exd5.} "
    "Bg5{5.Bg5.} "
    "Be7{5...Be7.} "
    "e3{6.e3.} "
    "O-O{6...O-O.} "
    "Bd3{7.Bd3.} "
    "Nbd7{7...Nbd7.} "
    "Qc2{8.Qc2: the queen supports the minority attack and the e4 break.} "
    "Re8{8...Re8.} "
    "Nge2{9.Nge2: the knight goes to e2 so that the f-pawn can advance.} "
    "Nf8{9...Nf8: Black defends the kingside.} "
    "O-O{10.O-O.} "
    "c6{10...c6: the Carlsbad structure. White has a clear plan: Rab1 and b4-b5 to damage Black's queenside.} "
    "Rab1{11.Rab1: the minority attack is coming.} "
    "Ne6{11...Ne6.}",

    # ==== Accepted ==============================================================================================================
    "d4 d5 c4 dxc4{2...dxc4, the Queen's Gambit Accepted. Black takes the pawn and gives the centre back later.} "
    "Nf3{3.Nf3: the bishop will get the pawn back on c4.} "
    "Nf6{3...Nf6.} "
    "e3{4.e3.} "
    "e6{4...e6.} "
    "Bxc4{5.Bxc4: material is level, and White has the lead in the centre and in space.} "
    "c5{5...c5: Black attacks d4.} "
    "O-O{6.O-O.} "
    "a6{6...a6.} "
    "Qe2{7.Qe2: the queen prepares Rd1 and keeps the centre flexible.} "
    "b5{7...b5.} "
    "Bb3{8.Bb3.} "
    "Bb7{8...Bb7.} "
    "Rd1{9.Rd1.} "
    "Nbd7{9...Nbd7.} "
    "Nc3{10.Nc3.} "
    "Qb6{10...Qb6.} "
    "a4{11.a4: you challenge the queenside pawns. A rich strategic game.}",

    # ==== Slav ==================================================================================================================
    "d4 d5 c4 c6{2...c6, the Slav Defence. Black supports d5 and keeps the bishop on c8 free to leave the pawn chain.} "
    "Nf3{3.Nf3.} "
    "Nf6{3...Nf6.} "
    "Nc3{4.Nc3.} "
    "dxc4{4...dxc4: the Slav proper. Black plans to hold the pawn with ...b5.} "
    "a4{5.a4: stops ...b5, so Black cannot hold the extra pawn.} "
    "Bf5{5...Bf5.} "
    "e3{6.e3.} "
    "e6{6...e6.} "
    "Bxc4{7.Bxc4: you have regained the pawn.} "
    "Bb4{7...Bb4.} "
    "O-O{8.O-O.} "
    "Nbd7{8...Nbd7.} "
    "Qe2{9.Qe2.} "
    "Bg6{9...Bg6.} "
    "e4{10.e4: the centre pawn takes space. White has the better centre.} "
    "O-O{10...O-O.} "
    "Bd3{11.Bd3: offers a bishop trade to remove Black's most active piece.} "
    "Bh5{11...Bh5.}",

    "d4 d5 c4 c6 Nf3 Nf6 Nc3 e6{4...e6, the Semi-Slav. Black locks the bishop in but builds a very solid centre.} "
    "e3{5.e3.} "
    "Nbd7{5...Nbd7.} "
    "Bd3{6.Bd3: you set a trap by allowing ...dxc4.} "
    "dxc4{6...dxc4.} "
    "Bxc4{7.Bxc4.} "
    "b5{7...b5: the Meran Variation. Black gains queenside space.} "
    "Bd3{8.Bd3.} "
    "a6{8...a6.} "
    "e4{9.e4: the centre breaks open.} "
    "c5{9...c5.} "
    "e5{10.e5: White grabs space and attacks the f6 knight.} "
    "cxd4{10...cxd4.} "
    "Nxb5{11.Nxb5: a tactic that opens the position. Sharp and complicated theory.} "
    "axb5{11...axb5.}",
]

SECTIONS = [
    {"id": "declined", "title": "Declined (2…e6)", "start": "d4 d5 c4 e6", "icon": "🧱",
     "summary": "Black keeps a solid centre. With the classical pin Bg5 you keep the pressure on d5. The Exchange Variation (cxd5) gives White an easy plan: "
                "the minority attack with Rab1 and b4-b5 against Black's queenside."},
    {"id": "accepted", "title": "Accepted (2…dxc4)", "start": "d4 d5 c4 dxc4", "icon": "🎁",
     "summary": "Black takes the pawn, you take it back with Bxc4 and get a nice centre. Develop with Nf3, e3, O-O and Qe2, and be ready for ...c5 and ...b5 by Black."},
    {"id": "slav", "title": "Slav / Semi-Slav (2…c6)", "start": "d4 d5 c4 c6", "icon": "🏔️",
     "summary": "Black supports d5 with a pawn but leaves the bishop free. Stop ...b5 with a4, win back the c4 pawn, and build a strong e4 centre. "
                "In the Semi-Slav Meran (…b5), the e4-e5 break leads to sharp play."},
]

QUEENS_GAMBIT = LessonTree(
    "Queen's Gambit", LINES, SECTIONS,
    intro="1.d4 d5 2.c4, played from White's side. A classic: White fights for the centre with a wing pawn, and the pawn structures decide the plans.",
    slug="queens-gambit", side="white", icon="♕", level="Intermediate",
    blurb="The classic 1.d4 opening: understand pawn structures like the Carlsbad and the Slav.")
