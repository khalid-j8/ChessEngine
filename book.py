import os
import random
from typing import Optional

import chess

BOOK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "book.txt")


def position_key(board: chess.Board) -> str:
    # pieces, side to move, castling and en passant: the move counters don't matter for the book
    return " ".join(board.fen().split()[:4])


def load_book(path: str = BOOK_PATH) -> dict:
    # builds {position key: {move: total weight}} by replaying every line of the text file
    book = {}
    if not os.path.exists(path):
        return book

    with open(path) as f:
        for line_number, raw in enumerate(f, start=1):
            line = raw.split("#", 1)[0].strip()      # drop comments
            if not line:
                continue

            weight = 1
            if "|" in line:
                weight_text, line = line.split("|", 1)
                weight = int(weight_text.strip())

            board = chess.Board()
            for san in line.split():
                try:
                    move = board.parse_san(san)
                except ValueError:
                    raise ValueError(f"book.txt line {line_number}: illegal move {san!r} in {board.fen()}")

                moves = book.setdefault(position_key(board), {})
                moves[move] = moves.get(move, 0) + weight
                board.push(move)

    return book


BOOK = load_book()


def book_move(board: chess.Board) -> Optional[chess.Move]:
    # a weighted random book move for this position, or None if we're out of book
    moves = BOOK.get(position_key(board))
    if not moves:
        return None
    choices = list(moves.keys())
    weights = list(moves.values())
    return random.choices(choices, weights=weights, k=1)[0]