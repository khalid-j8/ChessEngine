import sys
import chess

from engine import get_best_move
from book import book_move

ENGINE_NAME = "InsaneEngine"
DEFAULT_DEPTH = 4
MOVE_OVERHEAD_MS = 50     # time lost to Python start-up and passing messages, per move
MIN_THINK_MS = 10


def send(message: str) -> None:
    # UCI talks over stdout, and Python buffers stdout when it's a pipe,
    # so every message must be flushed or the GUI never sees it
    print(message, flush=True)


def parse_position(tokens: list) -> chess.Board:
    # tokens look like: ["startpos", "moves", "e2e4", "e7e5"]
    #               or: ["fen", <6 FEN fields>, "moves", "e2e4", ...]
    if tokens[0] == "startpos":
        board = chess.Board()
        rest = tokens[1:]
    else:
        board = chess.Board(" ".join(tokens[1:7]))
        rest = tokens[7:]

    if rest and rest[0] == "moves":
        for uci in rest[1:]:
            board.push_uci(uci)

    return board


def parse_go(tokens: list, board: chess.Board, default_depth: int):
    # turns e.g. "go wtime 60000 btime 58000 winc 1000 binc 1000" into (max_depth, time_limit in seconds)
    params = {}
    for name in ("wtime", "btime", "winc", "binc", "movetime", "depth"):
        if name in tokens:
            params[name] = int(tokens[tokens.index(name) + 1])

    if "depth" in params:
        return params["depth"], None

    if "movetime" in params:
        return 64, max(params["movetime"] - MOVE_OVERHEAD_MS, MIN_THINK_MS) / 1000

    my_time = params.get("wtime" if board.turn == chess.WHITE else "btime")
    my_inc = params.get("winc" if board.turn == chess.WHITE else "binc", 0)

    if my_time is not None:
        # spend about 1/30 of the remaining time plus half the increment, never more than half the clock,
        # and keep MOVE_OVERHEAD_MS in reserve for the time spent outside the search
        budget = min(my_time / 30 + my_inc / 2, my_time / 2) - MOVE_OVERHEAD_MS
        return 64, max(budget, MIN_THINK_MS) / 1000

    return default_depth, None      # plain "go" with no limits: fixed depth


def main() -> None:
    board = chess.Board()
    depth = DEFAULT_DEPTH
    use_book = True

    while True:
        line = sys.stdin.readline()
        if line == "":          # stdin closed, GUI is gone
            break

        tokens = line.split()
        if not tokens:
            continue
        command = tokens[0]

        if command == "uci":
            send(f"id name {ENGINE_NAME}")
            send("id author Khalid")
            send("option name Depth type spin default 4 min 1 max 8")
            send("option name OwnBook type check default true")
            send("uciok")

        elif command == "isready":
            send("readyok")

        elif command == "ucinewgame":
            board = chess.Board()

        elif command == "setoption":
            # setoption name Depth value 5
            if "name" in tokens and "value" in tokens:
                name = tokens[tokens.index("name") + 1]
                value = tokens[tokens.index("value") + 1]
                if name.lower() == "depth":
                    depth = int(value)
                elif name.lower() == "ownbook":
                    use_book = value.lower() == "true"

        elif command == "position":
            board = parse_position(tokens[1:])

        elif command == "go":
            # play straight from the opening book while the position is in it
            move = book_move(board) if use_book else None
            if move is not None:
                send("info string book move")
                send(f"bestmove {move.uci()}")
                continue

            max_depth, time_limit = parse_go(tokens, board, depth)
            result = get_best_move(board, depth=max_depth, time_limit=time_limit, verbose=False)

            if result is None:
                send("bestmove 0000")
            else:
                move, score = result
                send(f"info score cp {score}")
                send(f"bestmove {move.uci()}")

        elif command == "quit":
            break


if __name__ == "__main__":
    main()