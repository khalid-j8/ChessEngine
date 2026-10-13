# imports
import random, time
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

#constants
MateScore = 100000
INF = 1000000

# search state shared by negamax and quiescence
class SearchTimeout(Exception):
    pass

deadline = None     # time.time() value when the search must stop; None means no limit
nodes = 0           # positions visited in the current search


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

# use bitboard for fast evaluation
PIECES = (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)

# material + table bonus for every piece on every square, built once when the file loads;
# White's tables are rank-flipped here so the search never needs `square ^ 56`
WHITE_VALUE = {
    piece: [material_value[piece] + piece_square_table[piece][square ^ 56] for square in range(64)]
    for piece in PIECES
}
BLACK_VALUE = {
    piece: [material_value[piece] + piece_square_table[piece][square] for square in range(64)]
    for piece in PIECES
}

# king tables, indexed by whether it's the endgame
WHITE_KING_VALUE = {
    False: [KING_MIDDLE_TABLE[square ^ 56] for square in range(64)],
    True: [KING_END_TABLE[square ^ 56] for square in range(64)],
}
BLACK_KING_VALUE = {
    False: KING_MIDDLE_TABLE,
    True: KING_END_TABLE,
}


def is_endgame(board: chess.Board) -> bool:
    # endgame if every side that still has a queen has no rooks and at most one minor piece
    for color in (chess.WHITE, chess.BLACK):
        own = board.occupied_co[color]
        if board.queens & own:
            if (board.rooks & own) or chess.popcount((board.knights | board.bishops) & own) > 1:
                return False
    return True


def evaluate_board(board: chess.Board) -> int:
    white = board.occupied_co[chess.WHITE]
    black = board.occupied_co[chess.BLACK]
    score = 0

    for piece, pieces in (
        (chess.PAWN, board.pawns),
        (chess.KNIGHT, board.knights),
        (chess.BISHOP, board.bishops),
        (chess.ROOK, board.rooks),
        (chess.QUEEN, board.queens),
    ):
        white_values = WHITE_VALUE[piece]
        black_values = BLACK_VALUE[piece]

        for square in chess.scan_forward(pieces & white):
            score += white_values[square]

        for square in chess.scan_forward(pieces & black):
            score -= black_values[square]

    endgame = is_endgame(board)
    score += WHITE_KING_VALUE[endgame][board.king(chess.WHITE)]
    score -= BLACK_KING_VALUE[endgame][board.king(chess.BLACK)]

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
def quiescence(board: chess.Board, alpha: int, beta: int) -> int:
    global nodes
    nodes += 1
    if deadline is not None and nodes % 1024 == 0 and time.time() > deadline:
        raise SearchTimeout

    if board.is_check():
        # in check: standing pat isn't allowed, so try every legal move
        moves = list(board.legal_moves)

        if not moves:
            return -MateScore            # no way out of check: checkmate

        bestValue = -INF
    else:
        bestValue = evaluate_board(board)

        if bestValue >= beta:
            return bestValue

        if bestValue > alpha:
            alpha = bestValue

        moves = [move for move in board.legal_moves if board.is_capture(move) or move.promotion]

    for move in order_moves(board, moves):
        board.push(move)
        score = -quiescence(board, -beta, -alpha)
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

    global nodes
    nodes += 1
    if deadline is not None and nodes % 1024 == 0 and time.time() > deadline:
        raise SearchTimeout
    
    # base cases
    if board.is_checkmate():
        return -(MateScore + depth)

    if board.is_game_over() or board.is_repetition(2):
        return 0

    if board.is_check():
        depth += 1

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


def search_root(board: chess.Board, depth: int) -> Tuple[list, int]:
    # one complete search at a fixed depth; returns every move tied for best, and its score
    best_moves = []
    best_score = -INF

    for move in list(board.legal_moves):
        board.push(move)
        score = -negamax(board, depth - 1, -INF, INF)
        board.pop()

        if score > best_score:
            best_moves = [move]
            best_score = score
        elif score == best_score:
            best_moves.append(move)

    return best_moves, best_score


def get_best_move(board: chess.Board, depth: int = 3, time_limit: Optional[float] = None,
                  verbose: bool = True) -> Optional[Tuple[chess.Move, int]]:
    global deadline, nodes

    if not any(board.legal_moves):
        return None

    start = time.time()
    nodes = 0
    best_move, best_score = None, None

    for current_depth in range(1, depth + 1):
        # depth 1 always runs without a clock, so there is always a move to play
        deadline = start + time_limit if (time_limit is not None and current_depth > 1) else None

        try:
            # search a copy: if the clock stops us mid-search, the copy is left with half-undone
            # moves on it, but the caller's board is untouched
            moves, score = search_root(board.copy(), current_depth)
        except SearchTimeout:
            break                   # this depth didn't finish: keep the last completed one

        best_move, best_score = random.choice(moves), score
        elapsed = time.time() - start

        if verbose:
            print(f"depth {current_depth}  score {score}  nodes {nodes}  time {elapsed:.2f}s  best {best_move}")

        if abs(score) >= MateScore:
            break                   # a forced mate was found (for either side): deeper won't change it
        if time_limit is not None and elapsed > time_limit / 2:
            break                   # the next depth would almost surely not finish in time

    deadline = None
    return best_move, best_score



if __name__ == "__main__":
    board = chess.Board()

    while not board.is_game_over():
        move, score = get_best_move(board)
        print(f"Move: {move}, Eval: {score}")
        board.push(move)

    print(board.outcome())
    print(board)