# ChessEngine

A chess engine written from scratch in Python, built as a project to learn algorithms and game-tree optimization.

You can play a chess game against the engine using the browser. The engine also speaks the UCI protocol, so it works with chess GUIs and testing tools.

Move generation and board rules come from [python-chess](https://python-chess.readthedocs.io/). Everything about *choosing* a move (search, evaluation, move ordering, time management) is implemented in [`engine.py`](engine.py).

## How it thinks

### Search
- **Negamax with alpha-beta pruning**: a minimax search written from the side to move's point of view, cutting off branches that can't change the result, which makes the search much faster.
- **Iterative deepening**: searches depth 1, 2, 3, … until time runs out, always keeping the best move from the last completed depth. The previous best move is searched first at each new depth.
- **Quiescence search**: at the end of the main search, keeps searching captures and promotions until the position is quiet, so the engine doesn't stop in the middle of an exchange (the horizon effect). When in check, it searches every legal evasion instead of "standing pat".
- **Check extension**: positions where the side to move is in check are searched one ply deeper, so the engine doesn't miss what happens right after a check, such as a forced mate or a piece won.
- **Transposition table**: positions are identified using Zobrist hashing. Stored results are reused when the same position is reached by a different move order, with exact, lower-bound and upper-bound entries. This makes the search faster, since a position that was already searched doesn't need to be searched again, and its best move is tried first.
- **Draws and mates**: repetitions score as draws, and mates are scored by distance, so the engine prefers the fastest mate and the slowest loss.

### Move ordering
Alpha-beta is only as fast as its move ordering, so moves are tried in this order:
1. the move stored in the transposition table
2. captures, by **MVV-LVA** (most valuable victim, least valuable attacker)
3. **killer moves**: quiet moves that caused a cutoff at the same depth in a sibling position (two per ply)
4. remaining quiet moves, by the **history heuristic** (how often a move has caused cutoffs, weighted by depth²)

### Evaluation
Material plus piece-square tables, based on Tomasz Michniewski's [Simplified Evaluation Function](https://www.chessprogramming.org/Simplified_Evaluation_Function), with separate middlegame and endgame tables for the king.

### Time management
Each move gets about 1/30 of the remaining clock plus half the increment, capped at half the clock, with a small reserve for communication overhead. The search checks the clock every 256 nodes and returns the best move from the last finished depth.

### Opening book
A small hand-written book ([`tools/book.txt`](tools/book.txt)) of about 40 mainline openings in standard notation, covering about 400 positions. The engine picks between book moves at random, weighted by how often each line should be played, so its games vary. It can be turned off with the UCI option `OwnBook` for testing purposes.

## Project layout

```
engine.py      search, evaluation, move ordering, time control
app.py         Flask server behind the browser board
web/           browser board (chessboard.js + chess.js)
tests/         regression tests and test positions
tools/         UCI wrapper, opening book, testing and analysis scripts
```

## Running it

Requires Python 3.9+.

```
pip3 install -r requirements.txt
```

**Play in the browser:**
```
python3 app.py
```
Then open `web/main_page.html` with a local web server (for example VS Code's Live Server). The engine runs on `http://127.0.0.1:5001`.

**Use it in a chess GUI** (Cute Chess, Arena, Banksia, …): add a UCI engine with the command
```
python3 /path/to/ChessEngine/tools/uci.py
```

## Testing

Every engine change is checked in two ways:

- **Regression tests** (`python3 -m tests.regression_tests`): known positions with known answers, such as finding mate in one, recognizing stalemate and repetition, evaluation symmetry, and not falling for tactics at the search horizon. A separate test (`tests/kq_test.py`) checks that the engine can actually convert king and queen vs king.
- **SPRT matches** with [fastchess](https://github.com/Disservin/fastchess): the new version plays hundreds of games against the previous one from a set of opening positions, and the change is kept only if the sequential probability ratio test shows it gains Elo. Each tested version is tagged in git.

## Possible next steps

- null-move pruning and late move reductions
- principal variation search and aspiration windows
- pawn structure and king safety in the evaluation
- playing online as a Lichess bot