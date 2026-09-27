var board = null
var game = new Chess()

// onDragStart helps keep the board in correct shape by denying the humans access to pick up black pieces or if the game is over
function onDragStart (source, piece, position, orientation) {
  // do not pick up pieces if the game is over
  if (game.game_over()) return false

  // only pick up pieces for White because human is playing white
  if (piece.search(/^b/) !== -1) return false
}

// makes a random move
function makeRandomMove () {
  var computer_move = '';
  var possibleMoves = game.moves()

  // game over
  if (possibleMoves.length === 0) return

  

  for (let i=0; i<(possibleMoves.length); i++) {
    if (possibleMoves[i].includes('x')) {
      computer_move = possibleMoves[i];
      break;
    }
  }


  if (computer_move == '') {
    var randomIdx = Math.floor(Math.random() * possibleMoves.length)
    game.move(possibleMoves[randomIdx]);
  }

  else {game.move(computer_move);}

  board.position(game.fen())
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

  // make random legal move for black
  window.setTimeout(makeRandomMove, 250)
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