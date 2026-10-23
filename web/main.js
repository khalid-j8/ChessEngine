// seconds the engine thinks per move, for each difficulty
const THINK_TIMES = { easy: 0.5, medium: 2, hard: 5 }

// the engine normally runs in the browser (engine_worker.js);
// open the page with ?server at the end of the URL to use the local Flask server (python3 app.py) instead
const USE_SERVER = new URLSearchParams(window.location.search).has('server')
const SERVER_URL = 'http://127.0.0.1:5001/best-move'

let board = null
const game = new Chess()
let humanColor = 'w'          // 'w' or 'b'
let engineReady = USE_SERVER  // the in-browser engine needs a few seconds to load
let engineThinking = false
let engineError = null
let gameId = 0                // bumped on every new game, so a late reply from an old game is ignored

const statusEl = document.getElementById('status')
const difficultyEl = document.getElementById('difficulty')
const colorEl = document.getElementById('color')


// ---------------------------------------------------------------------------
// talking to the engine
// ---------------------------------------------------------------------------

let worker = null
let nextRequestId = 0
const pendingRequests = new Map()   // request id -> { resolve, reject }

if (!USE_SERVER) {
  worker = new Worker('engine_worker.js')

  worker.onmessage = (event) => {
    const msg = event.data

    if (msg.type === 'ready') {
      engineReady = true
      updateStatus()
      makeEngineMove()
      return
    }

    const request = pendingRequests.get(msg.id)
    pendingRequests.delete(msg.id)

    if (msg.type === 'move' && request) {
      request.resolve(msg)
    } else if (msg.type === 'error') {
      console.error('Engine error:', msg.message)
      if (request) {
        request.reject(new Error(msg.message))
      } else {
        engineError = 'The engine failed to load. Try reloading the page.'
        updateStatus()
      }
    }
  }
}

// every move played so far, in UCI format ("e2e4", "e7e8q"), so the engine knows the full history
function moveList () {
  return game.history({ verbose: true }).map(m => m.from + m.to + (m.promotion || ''))
}

// asks the engine for a move; resolves to { move: "e7e5" } (move is null if the game is over)
function askEngine (moves) {
  if (USE_SERVER) {
    return fetch(SERVER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fen: game.fen(), human_move: moves[moves.length - 1], moves: moves })
    }).then(response => response.json())
  }

  return new Promise((resolve, reject) => {
    const id = nextRequestId++
    pendingRequests.set(id, { resolve, reject })
    worker.postMessage({ id, moves, thinkTime: THINK_TIMES[difficultyEl.value] })
  })
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

// the engine moves whenever it's not the human's turn; checking the turn here also stops the
// delayed call from onDrop from moving for the human if a new game was started in the meantime
async function makeEngineMove () {
  if (game.game_over() || !engineReady || engineThinking || game.turn() === humanColor) return

  const thisGame = gameId
  engineThinking = true
  updateStatus()

  try {
    const reply = await askEngine(moveList())
    if (thisGame !== gameId) return      // a new game was started while the engine was thinking

    if (reply.move) {
      game.move(uciToMoveObject(reply.move))
      board.position(game.fen())
    }
  } catch (err) {
    console.error('Engine request failed:', err)
    if (thisGame === gameId) engineError = 'The engine had an error. Start a new game to try again.'
  }

  if (thisGame === gameId) {
    engineThinking = false
    updateStatus()
  }
}


// ---------------------------------------------------------------------------
// status line and game controls
// ---------------------------------------------------------------------------

function updateStatus () {
  let text
  if (engineError) {
    text = engineError
  } else if (!engineReady) {
    text = 'Loading engine…'
  } else if (game.in_checkmate()) {
    text = game.turn() === humanColor ? 'Checkmate. The engine wins.' : 'Checkmate. You win!'
  } else if (game.in_draw()) {
    text = 'Draw.'
  } else if (engineThinking || game.turn() !== humanColor) {
    text = 'Thinking…'
  } else {
    text = game.in_check() ? 'Your move (you are in check)' : 'Your move'
  }
  statusEl.textContent = text
}

function newGame () {
  gameId++
  engineThinking = false
  if (engineReady) engineError = null   // a failed engine load stays on screen: only a reload can fix it
  humanColor = colorEl.value
  game.reset()
  board.orientation(humanColor === 'w' ? 'white' : 'black')
  board.position('start')
  updateStatus()
  makeEngineMove()   // when the human plays Black, the engine opens
}


// ---------------------------------------------------------------------------
// chessboard.js callbacks
// ---------------------------------------------------------------------------

// only let the human pick up their own pieces, on their own turn, while the engine isn't busy
function onDragStart (source, piece) {
  if (game.game_over() || !engineReady || engineThinking || engineError) return false
  if (game.turn() !== humanColor) return false
  if (piece[0] !== humanColor) return false
}

// checks the human's move is legal, then lets the engine reply
function onDrop (source, target) {
  const move = game.move({
    from: source,
    to: target,
    promotion: 'q' // always promote to a queen for simplicity
  })

  if (move === null) return 'snapback'

  updateStatus()
  window.setTimeout(makeEngineMove, 250)
}

// update the board position after the piece snap
// for castling, en passant, pawn promotion
function onSnapEnd () {
  board.position(game.fen())
}

board = Chessboard('myBoard', {
  draggable: true,
  position: 'start',
  onDragStart: onDragStart,
  onDrop: onDrop,
  onSnapEnd: onSnapEnd
})

document.getElementById('newGame').addEventListener('click', newGame)
colorEl.addEventListener('change', newGame)
window.addEventListener('resize', () => board.resize())

updateStatus()
