import random
import sys

import chess

from engine import get_best_move

# usage: python3 kq_test.py [GAMES] [DEPTH]
GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DEPTH = int(sys.argv[2]) if len(sys.argv) > 2 else 3
START = "8/8/8/4k3/8/8/4Q3/4K3 w - - 0 1"   # White: king + queen, Black: lone king
MAX_PLIES = 200

results = {}
for seed in range(GAMES):
    random.seed(seed)                     # Black's random moves are the same every run
    board = chess.Board(START)

    while not board.is_game_over(claim_draw=True) and board.ply() < MAX_PLIES:
        if board.turn == chess.WHITE:
            move, _ = get_best_move(board, depth=DEPTH, verbose=False)
        else:
            move = random.choice(list(board.legal_moves))
        board.push(move)

    if board.is_checkmate():
        outcome = "checkmate"
    elif board.is_stalemate():
        outcome = "stalemate"
    elif board.can_claim_threefold_repetition():
        outcome = "threefold repetition"
    elif board.can_claim_fifty_moves():
        outcome = "fifty-move rule"
    else:
        outcome = "move limit"

    results[outcome] = results.get(outcome, 0) + 1
    print(f"game {seed + 1:>2}: {outcome:<21} after {board.ply() // 2} White moves", flush=True)

print(f"\n{results.get('checkmate', 0)}/{GAMES} checkmates | {results}")