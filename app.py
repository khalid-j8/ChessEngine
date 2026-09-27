from flask import Flask, request, jsonify
from flask_cors import CORS
import chess

from engine import get_best_move

app = Flask(__name__)
CORS(app)  # allows your browser (a different origin) to call this server


@app.route("/best-move", methods=["POST"])
def best_move():
    data = request.get_json()
    fen = data.get("fen") if data else None

    if not fen:
        return jsonify({"error": "no fen provided"}), 400

    board = chess.Board(fen)
    move = get_best_move(board)

    if move is None:
        # no legal moves left, game is over
        return jsonify({"move": None, "game_over": True})

    return jsonify({"move": move.uci(), "game_over": False})


if __name__ == "__main__":
    app.run(debug=True, port=5000)