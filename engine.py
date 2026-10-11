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


MateScore = 100000
INF = 1000000


# material values in centipawns, from the Simplified Evaluation Function
material_value = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
}
 
# piece-square tables, written the way you'd see the board from White's side:
# the first row is rank 8 and the last row is rank 1
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]
 
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
 
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
 
ROOK_TABLE = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0,
]
 
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
 
KING_MIDDLE_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]
 
KING_END_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]
 
piece_square_table = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
}

def is_endgame(board: chess.Board) -> bool:
    # endgame if every side that still has a queen has no rooks and at most one minor piece
    for color in (chess.WHITE, chess.BLACK):
        if board.pieces(chess.QUEEN, color):
            minors = len(board.pieces(chess.KNIGHT, color)) + len(board.pieces(chess.BISHOP, color))
            if board.pieces(chess.ROOK, color) or minors > 1:
                return False
    return True 

def evaluate_board(board: chess.Board) -> int:
    """
    Material plus piece-square bonuses, from the side to move's point of view.
    """
    endgame = is_endgame(board)
    score = 0
 
    for square, piece in board.piece_map().items():
        if piece.piece_type == chess.KING:
            table = KING_END_TABLE if endgame else KING_MIDDLE_TABLE
            value = 0
        else:
            table = piece_square_table[piece.piece_type]
            value = material_value[piece.piece_type]
 
        if piece.color == chess.WHITE:
            score += value + table[square ^ 56]     # flip the rank: the tables start at rank 8
        else:
            score -= value + table[square]          # Black reads the table as written
 
    return score if board.turn == chess.WHITE else -score 


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


# quiescence search
def quiescence(board: chess.Board, alpha: int, beta: int, evasions_left: int = 2) -> int:
    if board.is_check() and evasions_left > 0:
        # in check: standing pat isn't allowed, so try every legal move
        moves = list(board.legal_moves)

        if not moves:
            return -MateScore            # no way out of check: checkmate

        bestValue = -INF
        evasions_left -= 1
    else:
        bestValue = evaluate_board(board)

        if bestValue >= beta:
            return bestValue

        if bestValue > alpha:
            alpha = bestValue

        moves = [move for move in board.legal_moves if board.is_capture(move) or move.promotion]

    for move in order_moves(board, moves):
        board.push(move)
        score = -quiescence(board, -beta, -alpha, evasions_left)
        board.pop()

        if score > bestValue:
            bestValue = score

        if bestValue > alpha:
            alpha = bestValue

        if alpha >= beta:
            break

    return bestValue


# minmax function using recursion
def negamax(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    # base cases

    if board.is_checkmate():
        return -(MateScore + depth)

    #if board.is_game_over() or board.is_repetition(2):
        #return 0

    if board.is_game_over():
        return 0

    if depth == 0: 
        return quiescence(board, alpha, beta)

    legal_moves = order_moves(board, board.legal_moves)
    best_score = -INF

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


def get_best_move(board: chess.Board, depth: int = 3, verbose: bool = True) -> Optional[Tuple[chess.Move, int]]:
    legal_moves = list(board.legal_moves)

    if not legal_moves:
        return None

    best_moves = []
    best_score = -INF

    for move in legal_moves:
        board.push(move)
        score = -negamax(board, depth-1, -INF, INF)
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