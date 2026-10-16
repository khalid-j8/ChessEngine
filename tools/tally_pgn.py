import math
import sys
import chess.pgn

# usage: python3 tally_pgn.py FILE.pgn ENGINE_NAME
path = sys.argv[1]
me = sys.argv[2]

wins = draws = losses = 0
with open(path) as f:
    while True:
        game = chess.pgn.read_game(f)
        if game is None:
            break
        result = game.headers["Result"]
        if result == "1/2-1/2":
            draws += 1
        elif (result == "1-0") == (game.headers["White"] == me):
            wins += 1
        else:
            losses += 1

n = wins + draws + losses
score = (wins + draws / 2) / n


def elo(p):
    return -400 * math.log10(1 / p - 1) if 0 < p < 1 else float("nan")


# standard error of the average score per game
variance = (wins * (1 - score) ** 2 + draws * (0.5 - score) ** 2 + losses * score ** 2) / n
se = math.sqrt(variance / n)
low, high = max(score - 1.96 * se, 1e-6), min(score + 1.96 * se, 1 - 1e-6)

# likelihood of superiority: how likely it is that the engine is really the stronger one
los = 0.5 * (1 + math.erf((wins - losses) / math.sqrt(2 * (wins + losses)))) if wins + losses else 0.5

print(f"{me}: {n} games | +{wins} ={draws} -{losses} | score {score:.1%}")
print(f"Elo difference: {elo(score):+.0f}  (95% range {elo(low):+.0f} to {elo(high):+.0f})")
print(f"likelihood of superiority: {los:.1%}")