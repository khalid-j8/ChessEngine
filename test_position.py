import chess
from engine import get_best_move

fen = "r1b1r1k1/pppn4/6Q1/4P3/3P3q/8/PB5P/1K4R1 b - - 0 24"

board = chess.Board(fen)

move, score = get_best_move(board)
print("Engine chose:", move, "score:", score)