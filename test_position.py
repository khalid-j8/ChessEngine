import chess
from engine import get_best_move

fen = "r1b1r1k1/pppn1p2/6R1/4P3/3P3q/8/PBQ4P/1K4R1 b - - 0 23"

board = chess.Board(fen)

move, score = get_best_move(board)
print("Engine chose:", move, "score:", score)