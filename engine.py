# imports
import random
from typing import Optional
import chess

# define piece value for position eval
piece_value = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}

def evaluate_board(board: chess.Board) -> int:
    """
    Material-only evaluation of the position.
    Positive = better for White, negative = better for Black, 0 = balanced.
    Sums up each piece's value, adding for White's pieces and subtracting for Black's.
    """
    score = 0

    for piece_type, value in piece_value.items():
       score += len(board.pieces(piece_type, chess.WHITE)) * value 
       score -= len(board.pieces(piece_type, chess.BLACK)) * value

    return score


# function
def get_best_move(board: chess.Board) -> Optional[chess.Move]:
    legal_moves = list(board.legal_moves)

    # game over / no moves available
    if not legal_moves:
        return None

    # white or black's turn
    maximising = board.turn == chess.WHITE

    if maximising:
        best_score = -9999
    else:
        best_score = 9999

    # Current logic (eval function)
    best_moves = []

    for move in legal_moves:
        board.push(move)
        score = evaluate_board(board)
        if score == best_score:
            best_moves.append(move)

        elif maximising and score > best_score:
            best_moves.clear()
            best_moves.append(move)
            best_score = score

        elif not maximising and score < best_score:
            best_moves.clear()
            best_moves.append(move)
            best_score = score

        board.pop()


    # pick a random move from the best moves array
    return random.choice(best_moves)

# game setup
if __name__ == "__main__":
    # quick manual test: play a full random/capture-preferring game and print it
    board = chess.Board()

    while not board.is_game_over():
        move = get_best_move(board)
        board.push(move)

    print(board.outcome())
    print(board)