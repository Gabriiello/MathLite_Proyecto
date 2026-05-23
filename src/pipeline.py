"""
Pipeline principal de MathLite
Coordina las fases: Léxico → Sintáctico → Semántico → Interpretación
"""

from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticAnalyzer
from .interpreter import Interpreter
from .ast_nodes import ast_to_string


class MathLiteResult:
    """Resultado de ejecutar un programa MathLite."""
    def __init__(self):
        self.tokens = []
        self.lex_errors = []
        self.parse_errors = []
        self.semantic_errors = []
        self.runtime_errors = []
        self.output: list[str] = []
        self.ast_text: str = ''
        self.success = False


def run(source_code: str) -> MathLiteResult:
    """
    Ejecuta un programa MathLite completo.

    Retorna un MathLiteResult con:
    - tokens generados
    - errores por fase
    - salida del programa
    - representación textual del AST
    """
    result = MathLiteResult()

    # ── Fase 2: Análisis Léxico ───────────────────────────────────────────
    lexer = Lexer(source_code)
    tokens, lex_errors = lexer.tokenize()
    result.tokens = tokens
    result.lex_errors = lex_errors

    # ── Fase 3: Análisis Sintáctico ───────────────────────────────────────
    parser = Parser(tokens)
    ast = parser.parse()
    result.parse_errors = parser.errors

    # AST como texto indentado
    result.ast_text = ast_to_string(ast)

    if result.parse_errors:
        return result  # Sin AST válido no podemos continuar

    # ── Fase 4: Análisis Semántico ────────────────────────────────────────
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    result.semantic_errors = analyzer.errors

    # No abortamos en errores semánticos: intentamos ejecutar de todos modos
    # (comportamiento configurable según preferencia del docente)

    # ── Fase 5: Interpretación ────────────────────────────────────────────
    try:
        interpreter = Interpreter()
        output = interpreter.execute(ast)
        result.output = output
        result.success = True
    except Exception as e:
        result.runtime_errors.append(e)

    return result


def run_and_report(source_code: str) -> str:
    """Ejecuta y devuelve un reporte legible de todos los resultados."""
    r = run(source_code)
    lines = []

    if r.lex_errors:
        lines.append("── Errores Léxicos ──")
        for e in r.lex_errors:
            lines.append(str(e))
        lines.append("")

    if r.parse_errors:
        lines.append("── Errores Sintácticos ──")
        for e in r.parse_errors:
            lines.append(str(e))
        lines.append("")

    if r.semantic_errors:
        lines.append("── Errores Semánticos ──")
        for e in r.semantic_errors:
            lines.append(str(e))
        lines.append("")

    if r.runtime_errors:
        lines.append("── Errores de Ejecución ──")
        for e in r.runtime_errors:
            lines.append(str(e))
        lines.append("")

    if r.output:
        lines.append("── Salida ──")
        lines.extend(r.output)

    return '\n'.join(lines)
