"""
Fase 6 — Aplicación Web para MathLite
Backend Flask con API REST para el intérprete.
"""

import sys
import os
from datetime import datetime, timezone

# Asegurar que el directorio padre esté en el path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, request, jsonify, render_template_string
from src.pipeline import run
from src.lexer import Lexer

app = Flask(__name__)


def _get_cases_collection():
    uri = os.getenv('MATHLITE_MONGODB_URI') or os.getenv('MONGODB_URI')
    if not uri:
        return None
    try:
        from pymongo import MongoClient
    except ImportError:
        return None

    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    db_name = os.getenv('MATHLITE_MONGODB_DB', 'mathlite')
    return client[db_name]['test_cases']


CASES_COLLECTION = _get_cases_collection()


def save_case(code: str, result) -> str | None:
    if CASES_COLLECTION is None:
        return None

    try:
        document = {
            'source': code,
            'output': result.output,
            'lex_errors': [str(e) for e in result.lex_errors],
            'parse_errors': [str(e) for e in result.parse_errors],
            'semantic_errors': [str(e) for e in result.semantic_errors],
            'runtime_errors': [str(e) for e in result.runtime_errors],
            'ast': result.ast_text,
            'success': result.success,
            'created_at': datetime.now(timezone.utc),
        }
        inserted = CASES_COLLECTION.insert_one(document)
        return str(inserted.inserted_id)
    except Exception:
        return None


def list_cases(limit: int = 20) -> list[dict]:
    if CASES_COLLECTION is None:
        return []

    try:
        docs = CASES_COLLECTION.find({}, {'ast': 0}).sort('created_at', -1).limit(limit)
    except Exception:
        return []
    cases = []
    for doc in docs:
        doc['_id'] = str(doc['_id'])
        if isinstance(doc.get('created_at'), datetime):
            doc['created_at'] = doc['created_at'].isoformat()
        cases.append(doc)
    return cases

# ── Plantilla HTML de la aplicación ──────────────────────────────────────

HTML = r"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MathLite — Intérprete DSL</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@300;500;700&display=swap');

  :root {
    --bg:       #0d1117;
    --surface:  #161b22;
    --border:   #30363d;
    --accent:   #58a6ff;
    --accent2:  #3fb950;
    --error:    #f85149;
    --warn:     #e3b341;
    --text:     #e6edf3;
    --muted:    #8b949e;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Grotesk', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  header {
    padding: 18px 32px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 14px;
  }
  header .logo {
    font-size: 22px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -.5px;
  }
  header .sub {
    font-size: 13px;
    color: var(--muted);
  }

  .container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto 1fr 1fr;
    gap: 0;
    flex: 1;
    height: calc(100vh - 61px);
  }

  .panel {
    border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
  }
  .panel:nth-child(2) { border-right: none; }
  .panel:nth-child(3) { border-right: 1px solid var(--border); }
  .panel:nth-child(4) { border-right: none; }

  .panel-header {
    padding: 10px 16px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--surface);
  }

  textarea, .output-box {
    flex: 1;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    line-height: 1.6;
    background: transparent;
    color: var(--text);
    border: none;
    outline: none;
    resize: none;
    white-space: pre-wrap;
    overflow: auto;
  }

  .toolbar {
    grid-column: 1 / -1;
    padding: 10px 20px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    display: flex;
    gap: 10px;
    align-items: center;
  }

  button {
    padding: 7px 18px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 600;
    transition: opacity .15s;
  }
  button:hover { opacity: .85; }

  #btn-run   { background: var(--accent2); color: #0d1117; }
  #btn-clear { background: var(--border);  color: var(--text); }
  #btn-tokens { background: #6e40c9; color: #fff; }
  #btn-ast   { background: #388bfd22; color: var(--accent); border: 1px solid var(--accent); }

  .badge {
    margin-left: auto;
    font-size: 12px;
    color: var(--muted);
  }

  .error   { color: var(--error); }
  .success { color: var(--accent2); }
  .warn    { color: var(--warn); }
  .info    { color: var(--accent); }

  /* Numeración de líneas del editor */
  .editor-wrap {
    flex: 1;
    display: flex;
    overflow: auto;
  }
  .line-nums {
    padding: 16px 8px 16px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--muted);
    user-select: none;
    text-align: right;
    min-width: 40px;
    border-right: 1px solid var(--border);
    background: var(--surface);
  }
</style>
</head>
<body>

<header>
  <div class="logo">⟨ MathLite ⟩</div>
  <div class="sub">Intérprete DSL — Lenguajes Formales 2026-1</div>
</header>

<div class="container">
  <div class="toolbar">
    <button id="btn-run"    onclick="ejecutar()">▶ Ejecutar</button>
    <button id="btn-clear"  onclick="limpiar()">✕ Limpiar</button>
    <button id="btn-tokens" onclick="verTokens()">{ } Tokens</button>
    <button id="btn-ast"    onclick="verAST()">⌥ Ver AST</button>
    <span class="badge" id="status">listo</span>
  </div>

  <!-- Editor -->
  <div class="panel">
    <div class="panel-header">
      Código Fuente
    </div>
    <div class="editor-wrap">
      <div class="line-nums" id="line-nums">1</div>
      <textarea id="editor" spellcheck="false"
        placeholder="-- Escribe tu programa MathLite aquí&#10;let x = 10&#10;print(x * x)"
        oninput="updateLines()"></textarea>
    </div>
  </div>

  <!-- Salida -->
  <div class="panel">
    <div class="panel-header">Salida</div>
    <div class="output-box" id="output"></div>
  </div>

  <!-- Diagnósticos -->
  <div class="panel">
    <div class="panel-header">Diagnósticos</div>
    <div class="output-box" id="diagnostics"></div>
  </div>

  <!-- AST / Tokens -->
  <div class="panel">
    <div class="panel-header" id="panel4-title">AST / Tokens</div>
    <div class="output-box" id="ast-view"></div>
  </div>
</div>

<script>
const EXAMPLES = {
  default: `-- Declaración de variables
let base = 5
let altura = 3.0

-- Función que calcula el área de un triángulo
def area(b, h) {
    return (b * h) / 2
}

-- Uso de la función y salida
let resultado = area(base, altura)
print(resultado)

-- Ciclo while
let i = 1
while i <= 5 {
    print(i * i)
    let i = i + 1
}`
};

document.getElementById('editor').value = EXAMPLES.default;
updateLines();

function updateLines() {
  const lines = document.getElementById('editor').value.split('\n').length;
  document.getElementById('line-nums').textContent =
    Array.from({length: lines}, (_, i) => i + 1).join('\n');
}

async function ejecutar() {
  const code = document.getElementById('editor').value;
  setStatus('ejecutando...', 'info');

  try {
    const res  = await fetch('/run', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({code})
    });
    const data = await res.json();

    // Salida
    const out = document.getElementById('output');
    out.innerHTML = data.output.length
      ? data.output.map(l => escHtml(l)).join('\n')
      : '<span class="muted">— sin salida —</span>';

    // Diagnósticos
    const diag = document.getElementById('diagnostics');
    let diagHtml = '';
    for (const e of data.lex_errors)      diagHtml += `<span class="error">⚡ [Léxico]    ${escHtml(e)}</span>\n`;
    for (const e of data.parse_errors)    diagHtml += `<span class="error">⚡ [Sintáctico] ${escHtml(e)}</span>\n`;
    for (const e of data.semantic_errors) diagHtml += `<span class="warn">⚠ [Semántico]  ${escHtml(e)}</span>\n`;
    for (const e of data.runtime_errors)  diagHtml += `<span class="error">💥 [Ejecución]  ${escHtml(e)}</span>\n`;
    if (!diagHtml) diagHtml = '<span class="success">✓ Sin errores</span>';
    diag.innerHTML = diagHtml;

    // AST
    document.getElementById('ast-view').textContent = data.ast || '';
    document.getElementById('panel4-title').textContent = 'AST';

    const total = data.lex_errors.length + data.parse_errors.length +
                  data.semantic_errors.length + data.runtime_errors.length;
    setStatus(total === 0 ? '✓ OK' : `${total} error(es)`, total === 0 ? 'success' : 'error');

  } catch(e) {
    setStatus('error de red', 'error');
    console.error(e);
  }
}

async function verTokens() {
  const code = document.getElementById('editor').value;
  const res  = await fetch('/tokens', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({code})
  });
  const data = await res.json();
  const box  = document.getElementById('ast-view');
  document.getElementById('panel4-title').textContent = 'Tokens';
  box.innerHTML = data.tokens
    .map(t => `<span class="info">${t.type.padEnd(12)}</span>  ${escHtml(t.lexeme).padEnd(16)}  <span class="muted">${t.line}:${t.col}</span>`)
    .join('\n');
}

function verAST() {
  document.getElementById('panel4-title').textContent = 'AST';
}

function limpiar() {
  document.getElementById('editor').value = '';
  document.getElementById('output').textContent = '';
  document.getElementById('diagnostics').textContent = '';
  document.getElementById('ast-view').textContent = '';
  updateLines();
  setStatus('listo', '');
}

function setStatus(msg, cls) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = `badge ${cls}`;
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;');
}

// Ctrl+Enter para ejecutar
document.getElementById('editor').addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    ejecutar();
  }
});
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/run', methods=['POST'])
def api_run():
    data = request.get_json()
    code = data.get('code', '')
    r = run(code)
    case_id = save_case(code, r)

    return jsonify({
        'output':          r.output,
        'lex_errors':      [str(e) for e in r.lex_errors],
        'parse_errors':    [str(e) for e in r.parse_errors],
        'semantic_errors': [str(e) for e in r.semantic_errors],
        'runtime_errors':  [str(e) for e in r.runtime_errors],
        'ast':             r.ast_text,
        'success':         r.success,
        'case_id':         case_id,
        'storage':         'mongodb' if case_id else 'disabled',
    })


@app.route('/cases', methods=['GET'])
def api_cases():
    limit = request.args.get('limit', 20, type=int)
    limit = max(1, min(limit, 100))
    return jsonify({
        'cases': list_cases(limit),
        'storage': 'mongodb' if CASES_COLLECTION is not None else 'disabled',
    })


@app.route('/tokens', methods=['POST'])
def api_tokens():
    data = request.get_json()
    code = data.get('code', '')
    lexer = Lexer(code)
    tokens, errors = lexer.tokenize()
    token_list = [
        {'type': t.type.name, 'lexeme': t.lexeme, 'line': t.line, 'col': t.column}
        for t in tokens
    ]
    return jsonify({
        'tokens': token_list,
        'errors': [str(e) for e in errors],
    })


if __name__ == '__main__':
    print("MathLite Web — http://localhost:5000")
    app.run(debug=True, port=5000)
