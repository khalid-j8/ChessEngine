# imports
import random
from typing import Optional
import chess


# function
def get_best_move(board: chess.Board) -> Optional[chess.Move]:
    legal_moves = list(board.legal_moves)

    # game over / no moves available
    if not legal_moves:
        return None

    # Current logic (look for the first available capture move)
    for move in legal_moves:
        if board.is_capture(move):
            return move

    # if no captures found, pick randomly
    return random.choice(legal_moves)







# game setup
if __name__ == "__main__":
    # quick manual test: play a full random/capture-preferring game and print it
    board = chess.Board()

    while not board.is_game_over():
        move = get_best_move(board)
        board.push(move)

    print(board.outcome())
    print(board)