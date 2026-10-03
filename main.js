var board = null
var game = new Chess()

// onDragStart helps keep the board in correct shape by denying the humans access to pick up black pieces or if the game is over
function onDragStart (source, piece, position, orientation) {
  // do not pick up pieces if the game is over
  if (game.game_over()) return false

  // only pick up pieces for White because human is playing white
  if (piece.search(/^b/) !== -1) return false
}

// converts a UCI move string like "e7e5" (or "e7e8q" for promotion)
// into the {from, to, promotion} object chess.js expects
function uciToMoveObject (uci) {
  return {
    from: uci.slice(0, 2),
    to: uci.slice(2, 4),
    promotion: uci.length > 4 ? uci.slice(4, 5) : 'q'
  }
}

// asks the Python engine (running via Flask) for its move, then plays it
async function makeComputerMove (humanMoveUci) {
  if (game.game_over()) return

  try {
    const response = await fetch('http://127.0.0.1:5000/best-move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fen: game.fen(), human_move: humanMoveUci })
    })

    const data = await response.json()

    if (data.move) {
      game.move(uciToMoveObject(data.move))
      board.position(game.fen())
    }
  } catch (err) {
    console.error('Engine request failed:', err)
  }
}


// checks if human move is legal, then calls function for computer's move
function onDrop (source, target) {
  // see if the move is legal
  var move = game.move({
    from: source,
    to: target,
    promotion: 'q' // NOTE: always promote to a queen for example simplicity
  })

  // illegal move
  if (move === null) return 'snapback'

  // build the UCI string for what the human just played, to send to the server for logging
  var humanMoveUci = move.from + move.to + (move.promotion || '')

  // ask the Python engine for its move
  window.setTimeout(() => makeComputerMove(humanMoveUci), 250)
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd () {
  board.position(game.fen())
}


// end of functions
// config on chessboard.js
var config = {
  draggable: true,
  position: 'start',
  onDragStart: onDragStart,
  onDrop: onDrop,
  onSnapEnd: onSnapEnd
}

// chessboard.js html board representation with ability for human to play white, chess.js functions called inside config
board = Chessboard('myBoard', config)