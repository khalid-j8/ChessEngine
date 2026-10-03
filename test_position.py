import chess
from engine import get_best_move

fen = "1r4nr/p1pkpp1p/bp6/n2BP1N1/2P5/1PN5/P1K2PPP/3R3R b - - 0 17"
board = chess.Board(fen)

move, score = get_best_move(board)
print("Engine chose:", move, "score:", score)