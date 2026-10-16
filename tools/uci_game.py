import sys
import time
import chess
import chess.engine

# usage: python3 uci_game.py 3     (the number is the search depth, default 2)
DEPTH = int(sys.argv[1]) if len(sys.argv) > 1 else 2
ENGINE_CMD = ["python3", "uci.py"]

# two separate copies of the engine, talking to us over UCI exactly like a GUI would
white = chess.engine.SimpleEngine.popen_uci(ENGINE_CMD)
black = chess.engine.SimpleEngine.popen_uci(ENGINE_CMD)

board = chess.Board()
san_moves = []
start = time.time()

while not board.is_game_over():
    engine = white if board.turn == chess.WHITE else black
    result = engine.play(board, chess.engine.Limit(depth=DEPTH))
    san_moves.append(board.san(result.move))
    board.push(result.move)

white.quit()
black.quit()

outcome = board.outcome()
print(f"depth {DEPTH} | plies: {len(san_moves)} | time: {time.time() - start:.1f}s")
print("result:", board.result(), "|", outcome.termination.name)
print("first 16 plies:", " ".join(san_moves[:16]))
print("last 8 plies:", " ".join(san_moves[-8:]))
print("final position:", board.fen())