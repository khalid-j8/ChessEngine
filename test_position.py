import chess
from engine import get_best_move

fen = "7B/8/8/6P1/P1Q4N/k2pPKPP/7R/8 w - - 0 67"
board = chess.Board(fen)

move, score = get_best_move(board)
print("Engine chose:", move, "score:", score)