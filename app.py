from flask import Flask, request, jsonify
from flask_cors import CORS
import chess

from engine import get_best_move

app = Flask(__name__)
CORS(app)  # allows your browser (a different origin) to call this server

# logging info on each move
def log_move(player, move_uci, fen):
    print(f"{player}: {move_uci} -> {fen}")


@app.route("/best-move", methods=["POST"])
def best_move():
    data = request.get_json()
    fen = data.get("fen") if data else None
    human_move = data.get("human_move") if data else None

    if not fen:
        return jsonify({"error": "no fen provided"}), 400

    board = chess.Board(fen)

    # log the human's move and the resulting position
    if human_move:
        log_move("Human", human_move, fen)

    result = get_best_move(board)

    if result is None:
        return jsonify({"move": None, "game_over": True})

    move, score = result

    board.push(move)

    # log the engine's move, its eval, and the resulting position
    log_move(f"Engine (eval: {score})", move.uci(), board.fen())

    return jsonify({"move": move.uci(), "game_over": False})


if __name__ == "__main__":
    app.run(debug=True, port=5001)