import math
import sys
import chess.pgn

import chess
import chess.engine

# usage: python3 vs_stockfish.py GAMES DEPTH SETTING
#   GAMES    how many games to play (colours alternate every game)
#   DEPTH    search depth for your engine
#   SETTING  an Elo such as 1320 (UCI_Elo, Stockfish's minimum), or "skill0" .. "skill20"
GAMES = int(sys.argv[1]) if len(sys.argv) > 1 else 4
DEPTH = int(sys.argv[2]) if len(sys.argv) > 2 else 3
SF_SETTING = sys.argv[3] if len(sys.argv) > 3 else "1320"

STOCKFISH_PATH = "stockfish"       # or a full path, e.g. "/opt/homebrew/bin/stockfish"
SF_MOVE_TIME = 0.1                 # seconds Stockfish thinks per move
MAX_PLIES = 300                    # adjudicate very long games as draws

mine = chess.engine.SimpleEngine.popen_uci(["python3", "uci.py"])
sf = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

if SF_SETTING.startswith("skill"):
    sf.configure({"Skill Level": int(SF_SETTING[5:])})
    sf_label = f"Skill Level {SF_SETTING[5:]}"
else:
    sf.configure({"UCI_LimitStrength": True, "UCI_Elo": int(SF_SETTING)})
    sf_label = f"UCI_Elo {SF_SETTING}"

points = 0.0
wins = draws = losses = 0

for game in range(GAMES):
    board = chess.Board()
    mine_is_white = (game % 2 == 0)       # alternate colours every game

    while not board.is_game_over(claim_draw=True) and board.ply() < MAX_PLIES:
        my_turn = (board.turn == chess.WHITE) == mine_is_white
        if my_turn:
            move = mine.play(board, chess.engine.Limit(depth=DEPTH)).move
        else:
            move = sf.play(board, chess.engine.Limit(time=SF_MOVE_TIME)).move
        board.push(move)

    if board.is_game_over(claim_draw=True):
        result = board.result(claim_draw=True)
    else:
        result = "1/2-1/2"                # hit the ply cap

    if result == "1/2-1/2":
        points += 0.5
        draws += 1
        text = "draw"
    elif (result == "1-0") == mine_is_white:
        points += 1
        wins += 1
        text = "win"
    else:
        losses += 1
        text = "loss"

    colour = "White" if mine_is_white else "Black"
    print(f"game {game + 1}: I was {colour} | {text} | {board.ply()} plies", flush=True)
    pgn = chess.pgn.Game.from_board(board)
    pgn.headers["White"] = "InsaneEngine" if mine_is_white else f"Stockfish {sf_label}"
    pgn.headers["Black"] = f"Stockfish {sf_label}" if mine_is_white else "InsaneEngine"
    pgn.headers["Result"] = result
    print(pgn)
    print("final FEN:", board.fen())
    print(board)
    print()

mine.quit()
sf.quit()

fraction = points / GAMES
print(f"\nscore: {points}/{GAMES} (+{wins} ={draws} -{losses}) vs Stockfish at {sf_label}")
if 0 < fraction < 1:
    diff = -400 * math.log10(1 / fraction - 1)
    print(f"rough Elo difference: {diff:+.0f}  (very uncertain with only {GAMES} games)")
else:
    print("score was 0% or 100%, so the Elo difference is too large to estimate from this match")