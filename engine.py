# imports
import random
from typing import Optional,Tuple
import chess


# define piece value for position eval
piece_value = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}

MateScore = 1000

# function to help with move ordering
def move_score(board: chess.Board, move: chess.Move) -> int:
    score = 0

    if move.promotion:
        score += 100 + 10 * piece_value[move.promotion]

    if board.is_capture(move):
        victim = chess.PAWN if board.is_en_passant(move) else board.piece_type_at(move.to_square)
        attacker = board.piece_type_at(move.from_square)
        score += 100 + 10 * piece_value[victim] - piece_value.get(attacker, 100)

    return score


def order_moves(board: chess.Board, moves) -> list:
    return sorted(moves, key=lambda move: move_score(board, move), reverse=True)


def evaluate_board(board: chess.Board) -> int:
    """
    Material-only evaluation of the position.
    Sums up each piece's value, adding for White's pieces and subtracting for Black's.
    higher score is better no matter whos turn it is to move since that is already factored in to code
    """
    score = 0

    for piece_type, value in piece_value.items():
       score += len(board.pieces(piece_type, chess.WHITE)) * value 
       score -= len(board.pieces(piece_type, chess.BLACK)) * value

    who_to_move = 1 if board.turn == chess.WHITE else -1

    return score * who_to_move


# minmax function using recursion
def negamax(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    # base cases

    if board.is_checkmate():
        return -(MateScore + depth)

    if board.is_game_over():
        return 0

    if depth == 0: 
        return evaluate_board(board)

    legal_moves = order_moves(board, board.legal_moves)
    best_score = -9999

    for move in legal_moves:
        board.push(move)
        score = -negamax(board,depth-1,-beta,-alpha)
        board.pop()

        if score > best_score:
            best_score = score

        if best_score > alpha:
            alpha = best_score

        if alpha >= beta:
            break

    return best_score

def get_best_move(board: chess.Board, depth: int = 6, verbose: bool = True) -> Optional[Tuple[chess.Move, int]]:
    legal_moves = list(board.legal_moves)

    if not legal_moves:
        return None

    best_moves = []
    best_score = -9999

    for move in legal_moves:
        board.push(move)
        score = -negamax(board, depth-1,-10000,10000)
        if verbose:
            print(f"  {move}: {score}")
        board.pop()

        if score > best_score:
            best_moves.clear()
            best_score = score
            best_moves.append(move)

        elif score == best_score:
            best_moves.append(move)

    if verbose:
        print(f"Best score: {best_score}, candidates: {best_moves}")

    return random.choice(best_moves), best_score



if __name__ == "__main__":
    board = chess.Board()

    while not board.is_game_over():
        move, score = get_best_move(board)
        print(f"Move: {move}, Eval: {score}")
        board.push(move)

    print(board.outcome())
    print(board)