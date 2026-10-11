import sys
import chess

from engine import get_best_move

ENGINE_NAME = "InsaneEngine"
DEFAULT_DEPTH = 4


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


def main() -> None:
    board = chess.Board()
    depth = DEFAULT_DEPTH

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

        elif command == "position":
            board = parse_position(tokens[1:])

        elif command == "go":
            search_depth = depth
            if "depth" in tokens:
                search_depth = int(tokens[tokens.index("depth") + 1])

            result = get_best_move(board, depth=search_depth, verbose=False)

            if result is None:
                send("bestmove 0000")
            else:
                move, score = result
                send(f"info depth {search_depth} score cp {score}")
                send(f"bestmove {move.uci()}")

        elif command == "quit":
            break


if __name__ == "__main__":
    main()