import chess
from engine import get_best_move

fen = "rn3knr/pp3pp1/2p5/q1b1P2p/2P1N1b1/P2B1N2/1BQ2PPP/3RR1K1 b - - 4 17"

board = chess.Board(fen)

move, score = get_best_move(board, depth=64, time_limit=10.0)
print("Engine chose:", move, "score:", score)