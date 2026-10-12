import chess

# well-known, roughly balanced openings, a few moves deep
OPENINGS = [
    "e4 e5 Nf3 Nc6 Bb5",          # Ruy Lopez
    "e4 e5 Nf3 Nc6 Bc4",          # Italian
    "e4 e5 Nf3 Nc6 d4 exd4 Nxd4", # Scotch
    "e4 e5 Nf3 Nf6",              # Petrov
    "e4 e5 Nc3",                  # Vienna
    "e4 e5 f4",                   # King's Gambit
    "e4 c5 Nf3 d6",               # Sicilian
    "e4 c5 Nf3 Nc6",              # Sicilian
    "e4 c5 Nc3",                  # Closed Sicilian
    "e4 c5 c3",                   # Alapin
    "e4 e6 d4 d5",                # French
    "e4 c6 d4 d5",                # Caro-Kann
    "e4 d6 d4 Nf6",               # Pirc
    "e4 d5 exd5 Qxd5",            # Scandinavian
    "e4 Nf6",                     # Alekhine
    "d4 d5 c4 e6",                # Queen's Gambit Declined
    "d4 d5 c4 c6",                # Slav
    "d4 d5 c4 dxc4",              # Queen's Gambit Accepted
    "d4 d5 Nf3 Nf6 Bf4",          # London
    "d4 Nf6 c4 g6",               # King's Indian / Grunfeld
    "d4 Nf6 c4 e6 Nc3 Bb4",       # Nimzo-Indian
    "d4 Nf6 c4 e6 Nf3 b6",        # Queen's Indian
    "d4 Nf6 c4 c5 d5",            # Benoni
    "d4 Nf6 Nf3 g6 g3 Bg7 Bg2",   # fianchetto
    "d4 f5",                      # Dutch
    "c4 e5",                      # English
    "c4 c5 Nc3 Nc6",              # Symmetrical English
    "Nf3 d5 g3",                  # Reti
    "g3 d5 Bg2",                  # King's fianchetto
]

with open("../openings.epd", "w") as f:
    for line in OPENINGS:
        board = chess.Board()
        for san in line.split():
            board.push_san(san)        # raises an error if a move is illegal
        f.write(" ".join(board.fen().split()[:4]) + "\n")

print(f"wrote {len(OPENINGS)} openings to ../openings.epd")