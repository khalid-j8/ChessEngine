// Runs the Python engine (engine.py + the opening book) inside the browser with Pyodide.
// It lives in a Web Worker so the board stays responsive while the engine thinks.
//
// Messages in:  { id, moves: ["e2e4", ...], thinkTime: seconds }
// Messages out: { type: "ready" }
//               { type: "move", id, move: "e7e5" | null, score, book }
//               { type: "error", id, message }

const PYODIDE_VERSION = '0.26.4'
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`
const CHESS_WHEEL = 'lib/chess-1.11.2-py3-none-any.whl'          // python-chess, saved in the repo
const ENGINE_FILES = ['engine.py', 'tools/book.py', 'tools/book.txt']  // copied to engine/ by tools/build_site.sh

importScripts(PYODIDE_URL + 'pyodide.js')

async function fetchOk (url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`could not load ${url} (${response.status})`)
  return response
}

async function setup () {
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL })

  // install python-chess from the wheel
  const wheel = await (await fetchOk(CHESS_WHEEL)).arrayBuffer()
  pyodide.unpackArchive(wheel, 'wheel')

  // put the engine files into Pyodide's file system with the same layout as the repo
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

    result = get_best_move(board, depth=64, time_limit=think_time, verbose=False)
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
    const result = chooseMove(moves, thinkTime)
    const [move, score, book] = result.toJs()
    result.destroy()
    postMessage({ type: 'move', id, move, score, book })
  } catch (err) {
    postMessage({ type: 'error', id, message: String(err) })
  }
}
