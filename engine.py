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


# Zobrist hashing
_rng = random.Random(2026)                      

ZOBRIST_PIECE = {
    (piece, color): [_rng.getrandbits(64) for _ in range(64)]
    for piece in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING)
    for color in (chess.WHITE, chess.BLACK)
}
ZOBRIST_BLACK_TO_MOVE = _rng.getrandbits(64)
ZOBRIST_CASTLING = {square: _rng.getrandbits(64) for square in (chess.A1, chess.H1, chess.A8, chess.H8)}
ZOBRIST_EP_FILE = [_rng.getrandbits(64) for _ in range(8)]


def zobrist_hash(board: chess.Board) -> int:
    key = 0

    for piece, pieces in (
        (chess.PAWN, board.pawns),
        (chess.KNIGHT, board.knights),
        (chess.BISHOP, board.bishops),
        (chess.ROOK, board.rooks),
        (chess.QUEEN, board.queens),
        (chess.KING, board.kings),
    ):
        for color in (chess.WHITE, chess.BLACK):
            table = ZOBRIST_PIECE[(piece, color)]
            for square in chess.scan_forward(pieces & board.occupied_co[color]):
                key ^= table[square]

    if board.turn == chess.BLACK:
        key ^= ZOBRIST_BLACK_TO_MOVE

    for square in chess.scan_forward(board.castling_rights):
        key ^= ZOBRIST_CASTLING[square]

    if board.ep_square is not None and board.has_legal_en_passant():
        key ^= ZOBRIST_EP_FILE[chess.square_file(board.ep_square)]

    return key


# ---------------------------------------------------------------------------
# Transposition table: zobrist key -> (depth, score, flag, best move)
# ---------------------------------------------------------------------------
EXACT, LOWER_BOUND, UPPER_BOUND = 0, 1, 2
TT_MAX_ENTRIES = 1_000_000
tt = {}


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
    if deadline is not None and nodes % 256 == 0 and time.time() > deadline:
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


def negamax(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    global nodes
    nodes += 1
    if deadline is not None and nodes % 256 == 0 and time.time() > deadline:
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

    # transposition table lookup
    key = zobrist_hash(board)
    entry = tt.get(key)
    tt_move = None

    if entry is not None:
        entry_depth, entry_score, entry_flag, tt_move = entry

        if entry_depth >= depth:
            if entry_flag == EXACT:
                return entry_score
            if entry_flag == LOWER_BOUND and entry_score >= beta:
                return entry_score
            if entry_flag == UPPER_BOUND and entry_score <= alpha:
                return entry_score

    original_alpha = alpha
    legal_moves = order_moves(board, board.legal_moves)

    # search the best move from an earlier search first
    if tt_move is not None and tt_move in legal_moves:
        legal_moves.remove(tt_move)
        legal_moves.insert(0, tt_move)

    best_score = -INF
    best_move = None

    for move in legal_moves:
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha)
        board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        if best_score > alpha:
            alpha = best_score

        if alpha >= beta:
            break

    # transposition table store
    if best_score <= original_alpha:
        flag = UPPER_BOUND          # nothing beat alpha: the true score is at most best_score
    elif best_score >= beta:
        flag = LOWER_BOUND          # cut off early: the true score is at least best_score
    else:
        flag = EXACT

    if len(tt) >= TT_MAX_ENTRIES:
        tt.clear()
    tt[key] = (depth, best_score, flag, best_move)

    return best_score


def search_root(board: chess.Board, depth: int, first_move: Optional[chess.Move] = None) -> Tuple[list, int]:
    # one complete search at a fixed depth; returns every move tied for best, and its score
    moves = order_moves(board, board.legal_moves)
    if first_move in moves:
        moves.remove(first_move)
        moves.insert(0, first_move)     # last depth's best move first: it is usually best again

    best_moves = []
    best_score = -INF

    for move in moves:
        board.push(move)
        # alpha = best_score - 1: anything worse than the best so far is cut off quickly,
        # but a move that exactly ties the best still gets its exact score, so ties are kept
        score = -negamax(board, depth - 1, -INF, -(best_score - 1))
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
    tt.clear()                      # fresh table for every move

    # fallback in case even depth 1 runs out of time: the first move in our usual ordering
    best_move = order_moves(board, board.legal_moves)[0]
    best_score = 0

    # the clock now applies from depth 1 onward, so a nearly empty clock can't be overrun
    deadline = start + time_limit if time_limit is not None else None

    for current_depth in range(1, depth + 1):
        try:
            # search a copy: if the clock stops us mid-search, the copy is left with half-undone
            # moves on it, but the caller's board is untouched
            moves, score = search_root(board.copy(), current_depth, best_move if current_depth > 1 else None)
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