// Runs the Python engine (engine.py + the opening book) inside the browser with Pyodide.
// It lives in a Web Worker so the board stays responsive while the engine thinks.
//
// Messages in:  { id, moves: ["e2e4", ...], thinkTime: seconds }
// Messages out: { type: "loading", stage }                       while starting up
//               { type: "ready" }
//               { type: "info", id, depth, score, nodes, time, best }   after each completed search depth
//               { type: "move", id, move: "e7e5" | null, score, book }
//               { type: "error", id, message }

const PYODIDE_VERSION = '0.26.4'
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`
const CHESS_WHEEL = 'lib/chess-1.11.2-py3-none-any.whl'          // python-chess, saved in the repo
const ENGINE_FILES = ['engine.py', 'tools/book.py', 'tools/book.txt']  // copied to engine/ by tools/build_site.sh

// get_best_move(verbose=True) prints one line per completed depth, e.g.
// "depth 5  score 40  nodes 24795  time 1.81s  best b8c6"
const DEPTH_LINE = /depth (\d+)\s+score (-?\d+)\s+nodes (\d+)\s+time ([\d.]+)s\s+best (\S+)/

let currentId = null   // the request being searched, so search info can be tagged with it

async function fetchOk (url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`could not load ${url} (${response.status})`)
  return response
}

async function setup () {
  postMessage({ type: 'loading', stage: 'Downloading Python' })
  importScripts(PYODIDE_URL + 'pyodide.js')
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL })

  // turn the engine's printed search progress into messages for the page
  pyodide.setStdout({
    batched: (line) => {
      const m = DEPTH_LINE.exec(line)
      if (m) {
        postMessage({
          type: 'info',
          id: currentId,
          depth: Number(m[1]),
          score: Number(m[2]),
          nodes: Number(m[3]),
          time: Number(m[4]),
          best: m[5]
        })
      }
    }
  })

  postMessage({ type: 'loading', stage: 'Installing python-chess' })
  const wheel = await (await fetchOk(CHESS_WHEEL)).arrayBuffer()
  pyodide.unpackArchive(wheel, 'wheel')

  // put the engine files into Pyodide's file system with the same layout as the repo
  postMessage({ type: 'loading', stage: 'Loading the engine' })
  pyodide.FS.mkdirTree('/engine/tools')
  for (const file of ENGINE_FILES) {
    const text = await (await fetchOk('engine/' + file)).text()
    pyodide.FS.writeFile('/engine/' + file, text)
  }

  await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/engine")

import chess
from engine import get_best_move
from tools.book import book_move

def choose_move(moves, think_time):
    board = chess.Board()
    for uci in moves:
        board.push_uci(uci)

    move = book_move(board)
    if move is not None:
        return move.uci(), None, True

    result = get_best_move(board, depth=64, time_limit=think_time, verbose=True)
    if result is None:
        return None, None, False
    move, score = result
    return move.uci(), score, False
`)
  return pyodide.globals.get('choose_move')
}

const ready = setup()
ready.then(
  () => postMessage({ type: 'ready' }),
  (err) => postMessage({ type: 'error', id: null, message: String(err) })
)

onmessage = async (event) => {
  const { id, moves, thinkTime } = event.data
  try {
    const chooseMove = await ready
    currentId = id
    const result = chooseMove(moves, thinkTime)
    const [move, score, book] = result.toJs()
    result.destroy()
    postMessage({ type: 'move', id, move, score, book })
  } catch (err) {
    postMessage({ type: 'error', id, message: String(err) })
  }
}
