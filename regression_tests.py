import random
import time

import chess

from engine import evaluate_board, negamax, MateScore, INF


def root_scores(fen, depth):
    # score every legal move the same way get_best_move does, but keep all of them
    board = chess.Board(fen)
    scores = {}
    for move in list(board.legal_moves):
        board.push(move)
        scores[move.uci()] = -negamax(board, depth - 1, -INF, INF)
        board.pop()
    return scores


def best_moves(scores):
    best = max(scores.values())
    return {move for move, score in scores.items() if score == best}, best


def test_start_position_is_balanced():
    assert evaluate_board(chess.Board()) == 0


def test_evaluation_is_symmetric():
    # a position and its colour-flipped mirror must look the same to the side to move
    random.seed(1)
    for _ in range(300):
        board = chess.Board()
        for _ in range(random.randint(0, 80)):
            if board.is_game_over():
                break
            board.push(random.choice(list(board.legal_moves)))
        assert evaluate_board(board) == evaluate_board(board.mirror()), board.fen()


def test_finds_mate_in_one():
    # fool's mate: 1.f3 e5 2.g4, Black plays Qh4#
    scores = root_scores("rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2", 3)
    moves, best = best_moves(scores)
    assert moves == {"d8h4"}, moves
    assert best >= MateScore


def test_mates_instead_of_stalemating():
    # exd4 and Bxd4 both stalemate Black; the engine must find a mate instead
    scores = root_scores("7B/8/8/1Q4P1/P2p3N/k3PKPP/7R/8 w - - 0 66", 3)
    moves, best = best_moves(scores)
    assert best >= MateScore, best
    assert "e3d4" not in moves and "h8d4" not in moves, moves


def test_avoids_walking_into_mate():
    # after Bxg6 hxg6 Rxg6+, fxg6 loses to Qxg6+ Kh8 Qg7#; the engine must see it (check extension)
    scores = root_scores("r1b1r1k1/pppn1p2/6R1/4P3/3P3q/8/PBQ4P/1K4R1 b - - 0 23", 3)
    moves, _ = best_moves(scores)
    assert scores["f7g6"] <= -MateScore, scores["f7g6"]
    assert moves == {"g8h8"}, moves


def test_takes_rook_before_recapture():
    # Nxg8 wins the rook; ignoring it loses to c8=Q then Qxg8 (quiescence)
    scores = root_scores("6R1/2P5/R4p1n/1P2k3/6pp/8/5PPP/6K1 b - - 0 35", 3)
    moves, _ = best_moves(scores)
    assert moves == {"h6g8"}, moves


def test_repetition_scores_as_draw():
    # both knights go out and back, so the start position appears for the second time
    board = chess.Board()
    for uci in ["g1f3", "g8f6", "f3g1", "f6g8"]:
        board.push_uci(uci)
    assert board.is_repetition(2)
    assert negamax(board, 2, -INF, INF) == 0


if __name__ == "__main__":
    tests = [value for name, value in list(globals().items()) if name.startswith("test_")]
    failed = 0
    for test in tests:
        start = time.time()
        try:
            test()
            print(f"PASS  {test.__name__}  ({time.time() - start:.1f}s)")
        except Exception as error:
            failed += 1
            print(f"FAIL  {test.__name__}: {error}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")