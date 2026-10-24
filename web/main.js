import { Chessground } from './lib/chessground/chessground.min.js'
import { Chess } from './lib/chess.js/chess.js'

// seconds the engine thinks per move, for each strength
const THINK_TIMES = { easy: 0.5, medium: 2, hard: 5 }
const MATE_SCORE = 100000          // engine.py scores mates as MateScore (+ depth) or more

// the engine normally runs in the browser (engine_worker.js);
// open the page with ?server at the end of the URL to use the local Flask server (python3 app.py) instead
const USE_SERVER = new URLSearchParams(window.location.search).has('server')
const SERVER_URL = 'http://127.0.0.1:5001/best-move'

const $ = (id) => document.getElementById(id)
const COLOR_NAME = { w: 'white', b: 'black' }
const PIECE_NAME = { q: 'queen', r: 'rook', b: 'bishop', n: 'knight' }

const game = new Chess()
const state = {
  humanColor: 'w',
  engineReady: USE_SERVER,
  engineThinking: false,
  engineError: null,
  resigned: false,
  token: 0,            // bumped by new game and take back, so a late engine reply is ignored
  pendingPromotion: null
}


// ---------------------------------------------------------------------------
// the board
// ---------------------------------------------------------------------------

const cg = Chessground($('board'), {
  fen: game.fen(),
  orientation: 'white',
  coordinates: true,
  animation: { enabled: true, duration: 220 },
  highlight: { lastMove: true, check: true },
  premovable: { enabled: false },
  draggable: { showGhost: true },
  movable: {
    free: false,
    color: undefined,
    showDests: true,
    events: { after: onHumanMove }
  }
})

function legalDests () {
  const dests = new Map()
  for (const m of game.moves({ verbose: true })) {
    if (!dests.has(m.from)) dests.set(m.from, [])
    dests.get(m.from).push(m.to)
  }
  return dests
}

function humanCanMove () {
  return state.engineReady && !state.engineError && !state.engineThinking && !state.resigned &&
    !state.pendingPromotion && !game.isGameOver() && game.turn() === state.humanColor
}

// redraws everything from the chess.js game: board, move list, status, buttons
function sync () {
  const history = game.history({ verbose: true })
  const last = history[history.length - 1]
  const canMove = humanCanMove()

  cg.set({
    fen: game.fen(),
    orientation: COLOR_NAME[state.humanColor],
    turnColor: COLOR_NAME[game.turn()],
    lastMove: last ? [last.from, last.to] : undefined,
    check: game.inCheck() ? COLOR_NAME[game.turn()] : false,
    movable: { color: canMove ? COLOR_NAME[state.humanColor] : undefined, dests: canMove ? legalDests() : new Map() }
  })

  renderMoveList(history)
  renderStatus()
  renderButtons()
}


// ---------------------------------------------------------------------------
// human moves (and promotion)
// ---------------------------------------------------------------------------

function onHumanMove (from, to) {
  const piece = game.get(from)
  const lastRank = state.humanColor === 'w' ? '8' : '1'
  if (piece && piece.type === 'p' && to[1] === lastRank) {
    askPromotion(from, to)
    return
  }
  playHumanMove({ from, to })
}

function playHumanMove (move) {
  game.move(move)
  sync()
  if (game.isGameOver()) return showResult()
  window.setTimeout(makeEngineMove, 150)
}

function askPromotion (from, to) {
  state.pendingPromotion = { from, to }
  const box = $('promotionChoices')
  box.innerHTML = ''
  for (const p of ['q', 'r', 'b', 'n']) {
    const button = document.createElement('button')
    button.className = 'promotion-choice'
    button.setAttribute('aria-label', PIECE_NAME[p])
    button.innerHTML = `<piece class="${PIECE_NAME[p]} ${COLOR_NAME[state.humanColor]}"></piece>`
    button.addEventListener('click', () => {
      state.pendingPromotion = null
      $('promotionOverlay').hidden = true
      playHumanMove({ from, to, promotion: p })
    })
    box.appendChild(button)
  }
  $('promotionOverlay').hidden = false
  box.querySelector('button').focus()
  renderStatus()
  renderButtons()
}

$('promotionCancel').addEventListener('click', () => {
  state.pendingPromotion = null
  $('promotionOverlay').hidden = true
  sync()   // puts the pawn back
})


// ---------------------------------------------------------------------------
// the engine
// ---------------------------------------------------------------------------

let worker = null
let nextRequestId = 0
const pendingRequests = new Map()   // request id -> { resolve, reject, token }

if (USE_SERVER) {
  $('loadingOverlay').hidden = true
  $('engineNote').textContent = 'Search details aren\'t shown when playing against the local Flask server.'
  $('engineNote').hidden = false
} else {
  worker = new Worker('engine_worker.js')
  worker.onmessage = onWorkerMessage
}

function onWorkerMessage (event) {
  const msg = event.data

  if (msg.type === 'loading') {
    $('loadingStage').textContent = msg.stage
    return
  }
  if (msg.type === 'ready') {
    state.engineReady = true
    $('loadingOverlay').hidden = true
    sync()
    makeEngineMove()
    return
  }

  const request = pendingRequests.get(msg.id)

  if (msg.type === 'info') {
    if (request && request.token === state.token) addDepthRow(msg)
    return
  }

  pendingRequests.delete(msg.id)
  if (msg.type === 'move' && request) {
    request.resolve(msg)
  } else if (msg.type === 'error') {
    console.error('Engine error:', msg.message)
    if (request) {
      request.reject(new Error(msg.message))
    } else {
      state.engineError = 'The engine failed to load. Reload the page to try again.'
      $('loadingStage').textContent = state.engineError
      $('loadingOverlay').querySelector('.spinner').hidden = true
      sync()
    }
  }
}

// every move played so far, in UCI format ("e2e4", "e7e8q"), so the engine knows the full history
function uciMoves () {
  return game.history({ verbose: true }).map(m => m.from + m.to + (m.promotion || ''))
}

function selectedLevel () {
  return document.querySelector('input[name="level"]:checked').value
}

function askEngine (moves) {
  if (USE_SERVER) {
    return fetch(SERVER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fen: game.fen(), human_move: moves[moves.length - 1], moves })
    }).then(response => response.json())
  }

  return new Promise((resolve, reject) => {
    const id = nextRequestId++
    pendingRequests.set(id, { resolve, reject, token: state.token })
    worker.postMessage({ id, moves, thinkTime: THINK_TIMES[selectedLevel()] })
  })
}

async function makeEngineMove () {
  if (!state.engineReady || state.engineError || state.engineThinking || state.resigned) return
  if (game.isGameOver() || game.turn() === state.humanColor) return

  const token = state.token
  state.engineThinking = true
  clearDepthRows()
  sync()

  try {
    const reply = await askEngine(uciMoves())
    if (token !== state.token) return       // new game or take back while the engine was thinking

    if (reply.move) {
      game.move({ from: reply.move.slice(0, 2), to: reply.move.slice(2, 4), promotion: reply.move[4] })
    }
    if (reply.book) showBookMove()
    else if (reply.score !== undefined && reply.score !== null) showEval(reply.score)
  } catch (err) {
    console.error('Engine request failed:', err)
    if (token === state.token) state.engineError = 'The engine hit an error. Start a new game to try again.'
  }

  if (token === state.token) {
    state.engineThinking = false
    sync()
    if (game.isGameOver()) showResult()
  }
}


// ---------------------------------------------------------------------------
// engine readout: evaluation and the depth-by-depth search
// ---------------------------------------------------------------------------

// the engine reports scores from the side to move (itself); the readout uses White's view
function whiteScore (engineScore) {
  return state.humanColor === 'w' ? -engineScore : engineScore
}

function formatScore (score) {   // score in centipawns, White's view
  if (Math.abs(score) >= MATE_SCORE) return 'Mate'
  const pawns = score / 100
  return (pawns > 0 ? '+' : pawns < 0 ? '−' : '') + Math.abs(pawns).toFixed(1)
}

function showEval (engineScore) {
  $('evalNumber').textContent = formatScore(whiteScore(engineScore))
}

function showBookMove () {
  $('evalNumber').textContent = 'Book'
  clearDepthRows()
  $('depthRows').innerHTML = '<tr class="book-row"><td colspan="5">Opening book move</td></tr>'
}

function clearDepthRows () {
  $('depthRows').innerHTML = ''
}

// one row per completed depth; uses a scratch board to turn "b8c6" into "Nc6"
function addDepthRow (info) {
  let san = info.best
  try {
    const scratch = new Chess(game.fen())
    san = scratch.move({ from: info.best.slice(0, 2), to: info.best.slice(2, 4), promotion: info.best[4] }).san
  } catch (e) { /* keep the UCI text */ }

  const row = document.createElement('tr')
  row.innerHTML = `<td>${info.depth}</td><td>${san}</td><td>${formatScore(whiteScore(info.score))}</td>` +
    `<td>${info.nodes.toLocaleString()}</td><td>${info.time.toFixed(2)} s</td>`
  $('depthRows').appendChild(row)
  $('depthScroll').scrollTop = $('depthScroll').scrollHeight   // keep the newest depth in view
  $('evalNumber').textContent = formatScore(whiteScore(info.score))
}

function resetReadout () {
  clearDepthRows()
  $('evalNumber').textContent = '0.0'
}


// ---------------------------------------------------------------------------
// move list, status line, buttons
// ---------------------------------------------------------------------------

function renderMoveList (history) {
  const list = $('moveList')
  list.innerHTML = ''
  for (let i = 0; i < history.length; i += 2) {
    const li = document.createElement('li')
    const number = document.createElement('b')
    number.textContent = i / 2 + 1 + '.'
    li.appendChild(number)
    for (const move of history.slice(i, i + 2)) {
      const span = document.createElement('span')
      span.textContent = move.san
      li.appendChild(span)
    }
    list.appendChild(li)
  }
  const spans = list.querySelectorAll('span')
  if (spans.length) spans[spans.length - 1].classList.add('latest')
  $('movesEmpty').hidden = history.length > 0
  list.scrollTop = list.scrollHeight
}

function renderStatus () {
  let text
  if (state.engineError) text = state.engineError
  else if (!state.engineReady) text = 'Loading the engine…'
  else if (state.resigned || game.isGameOver()) text = 'Game over.'
  else if (state.pendingPromotion) text = 'Choose a piece to promote to.'
  else if (game.turn() !== state.humanColor) text = 'The engine is thinking…'
  else text = game.inCheck() ? 'Your move. You\'re in check.' : 'Your move.'

  $('statusText').textContent = text
  $('turnDot').className = 'turn-dot ' + COLOR_NAME[game.turn()]
}

function humanMovesPlayed () {
  return game.history({ verbose: true }).filter(m => m.color === state.humanColor).length
}

function renderButtons () {
  const over = state.resigned || game.isGameOver()
  $('takeBack').disabled = !state.engineReady || !!state.engineError || humanMovesPlayed() === 0 || !!state.pendingPromotion
  $('resign').disabled = !state.engineReady || !!state.engineError || over || humanMovesPlayed() === 0
}


// ---------------------------------------------------------------------------
// game over
// ---------------------------------------------------------------------------

function resultFor () {
  if (state.resigned) return { winner: oppositeColor(state.humanColor), title: 'The engine wins', reason: 'You resigned.' }
  if (game.isCheckmate()) {
    const winner = oppositeColor(game.turn())
    return winner === state.humanColor
      ? { winner, title: 'You win!', reason: 'Checkmate. You beat the engine.' }
      : { winner, title: 'The engine wins', reason: 'Checkmate.' }
  }
  let reason = 'Draw by the fifty-move rule.'
  if (game.isStalemate()) reason = 'Stalemate: the side to move has no legal moves but isn\'t in check.'
  else if (game.isThreefoldRepetition()) reason = 'The same position came up three times.'
  else if (game.isInsufficientMaterial()) reason = 'Neither side has enough pieces left to checkmate.'
  return { winner: null, title: 'Draw', reason }
}

function oppositeColor (c) { return c === 'w' ? 'b' : 'w' }

function showResult () {
  const result = resultFor()
  const kings = $('resultKings')
  // the winner's king stands, the loser's king is knocked over; both stand for a draw
  kings.innerHTML = ['w', 'b'].map(c => {
    const fallen = result.winner && result.winner !== c
    return `<piece class="king ${COLOR_NAME[c]}${fallen ? ' fallen' : ''}"></piece>`
  }).join('')
  const overlay = $('resultOverlay')
  overlay.dataset.outcome = !result.winner ? 'draw' : result.winner === state.humanColor ? 'win' : 'loss'
  $('resultTitle').textContent = result.title
  $('resultReason').textContent = result.reason
  overlay.hidden = false
  $('playAgain').focus()
  sync()
}

$('viewBoard').addEventListener('click', () => { $('resultOverlay').hidden = true })
$('playAgain').addEventListener('click', newGame)


// ---------------------------------------------------------------------------
// controls
// ---------------------------------------------------------------------------

function newGame () {
  state.token++
  state.engineThinking = false
  state.resigned = false
  state.pendingPromotion = null
  if (state.engineReady) state.engineError = null   // a failed engine load needs a page reload
  state.humanColor = document.querySelector('input[name="color"]:checked').value
  game.reset()
  $('resultOverlay').hidden = true
  $('promotionOverlay').hidden = true
  resetReadout()
  sync()
  makeEngineMove()   // when the human plays Black, the engine opens
}

// undo back to the human's previous turn; cancels the engine if it's thinking
function takeBack () {
  state.token++
  state.engineThinking = false
  state.resigned = false
  state.pendingPromotion = null
  if (state.engineReady) state.engineError = null
  game.undo()
  if (game.turn() !== state.humanColor && game.history().length > 0) game.undo()
  $('resultOverlay').hidden = true
  $('promotionOverlay').hidden = true
  resetReadout()
  sync()
  makeEngineMove()   // only moves if it's the engine's turn (playing Black with every move taken back)
}

let resignArmed = null
function resign () {
  const button = $('resign')
  if (!resignArmed) {
    button.textContent = 'Confirm resign'
    button.classList.add('danger')
    resignArmed = window.setTimeout(disarmResign, 3000)
    return
  }
  disarmResign()
  state.token++
  state.engineThinking = false
  state.resigned = true
  showResult()
}
function disarmResign () {
  window.clearTimeout(resignArmed)
  resignArmed = null
  $('resign').textContent = 'Resign'
  $('resign').classList.remove('danger')
}

$('newGame').addEventListener('click', newGame)
$('takeBack').addEventListener('click', takeBack)
$('resign').addEventListener('click', resign)
for (const input of document.querySelectorAll('input[name="color"]')) input.addEventListener('change', newGame)

window.addEventListener('resize', () => cg.redrawAll())
// chessground remembers where the board is on the page; when the layout above it shifts without a
// window resize (e.g. the web font loading and rewrapping the header), clicks and taps would land
// on the wrong squares, so redraw whenever the page's size changes
new ResizeObserver(() => cg.redrawAll()).observe(document.body)
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !$('resultOverlay').hidden) $('resultOverlay').hidden = true
})

resetReadout()
sync()
