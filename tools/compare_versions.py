import importlib.util
import random
import sys
import time

import chess


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old = load(sys.argv[1], "old_engine")
new = load(sys.argv[2], "new_engine")

random.seed(1)
mismatches = 0
for _ in range(500):
    board = chess.Board()
    for _ in range(random.randint(0, 80)):
        if board.is_game_over():
            break
        board.push(random.choice(list(board.legal_moves)))
    if old.evaluate_board(board) != new.evaluate_board(board):
        mismatches += 1
print("evaluation mismatches out of 500:", mismatches)

for fen in ["rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"]:
    times = []
    for engine in (old, new):
        board = chess.Board(fen)
        start = time.time()
        _, score = engine.get_best_move(board, depth=3, verbose=False)
        times.append((time.time() - start, score))
    print(f"depth 3: old {times[0][0]:.2f}s score {times[0][1]} | new {times[1][0]:.2f}s score {times[1][1]}")