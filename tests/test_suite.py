"""
Fase 6 — Suite de Pruebas Automatizadas para MathLite
Cubre: casos positivos, errores léxicos, sintácticos, semánticos y de ejecución.
Mínimo: 25 casos de prueba.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pipeline import run


# ── Colores para la terminal ──────────────────────────────────────────────

GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
RESET  = '\033[0m'
BOLD   = '\033[1m'

passed = 0
failed = 0


def test(name: str, source: str, *,
         expect_output: list[str] = None,
         expect_lex_error: bool = False,
         expect_parse_error: bool = False,
         expect_semantic_error: bool = False,
         expect_runtime_error: bool = False):
    global passed, failed
    r = run(source)

    ok = True
    msg_parts = []

    if expect_lex_error and not r.lex_errors:
        ok = False
        msg_parts.append("esperaba error léxico")
    if expect_parse_error and not r.parse_errors:
        ok = False
        msg_parts.append("esperaba error sintáctico")
    if expect_semantic_error and not r.semantic_errors:
        ok = False
        msg_parts.append("esperaba error semántico")
    if expect_runtime_error and not r.runtime_errors:
        ok = False
        msg_parts.append("esperaba error de ejecución")

    if expect_output is not None:
        if r.output != expect_output:
            ok = False
            msg_parts.append(f"salida esperada {expect_output}, obtenida {r.output}")

    if ok:
        passed += 1
        print(f"  {GREEN}✓{RESET} {name}")
    else:
        failed += 1
        print(f"  {RED}✗{RESET} {name}: {'; '.join(msg_parts)}")

    return ok


# ══════════════════════════════════════════════════════════════════════════
# CASOS POSITIVOS
# ══════════════════════════════════════════════════════════════════════════

def test_positive_cases():
    print(f"\n{BOLD}── Programas Válidos ──{RESET}")

    # T01: (3+4*2)/(1-5)^2 = 11/16 = 0.6875
    test("T01 Aritmética con precedencia",
         "print((3 + 4 * 2) / (1 - 5) ^ 2)",
         expect_output=["0.6875"])

    # T02: Declaración y uso de variables
    test("T02 Variables enteras y reales",
         "let x = 10\nlet y = 3.5\nprint(x + y)",
         expect_output=["13.5"])

    # T03: Función simple con retorno
    test("T03 Función suma",
         "def suma(a, b) { return a + b }\nprint(suma(3, 7))",
         expect_output=["10"])

    # T04: Factorial recursivo
    test("T04 Factorial recursivo",
         """
def fact(n) {
    if n <= 1 { return 1 }
    return n * fact(n - 1)
}
print(fact(5))
         """,
         expect_output=["120"])

    # T05: Ciclo while acumulando suma
    test("T05 While — suma de 1 a 5",
         """
let i = 1
let s = 0
while i <= 5 {
    let s = s + i
    let i = i + 1
}
print(s)
         """,
         expect_output=["15"])

    # T06: Área de triángulo (ejemplo del enunciado)
    test("T06 Área de triángulo",
         """
let base = 5
let altura = 3.0
def area(b, h) { return (b * h) / 2 }
let resultado = area(base, altura)
print(resultado)
         """,
         expect_output=["7.5"])

    # T07: Funciones trigonométricas
    test("T07 sin, cos, sqrt",
         "print(sin(0) + cos(0) + sqrt(4.0))",
         expect_output=["3"])

    # T08: Booleanos y lógica
    test("T08 Expresiones lógicas",
         "print(3 > 2 and not false)",
         expect_output=["true"])

    # T09: Cadena de texto
    test("T09 Print de cadena",
         'print("hola mundo")',
         expect_output=["hola mundo"])

    # T10: Condicional if/else
    test("T10 if-else",
         """
let x = 10
if x > 5 { print("mayor") } else { print("menor") }
         """,
         expect_output=["mayor"])

    # T11: Función que llama a otra función
    test("T11 Funciones encadenadas",
         """
def doble(n) { return n * 2 }
def cuadruple(n) { return doble(doble(n)) }
print(cuadruple(3))
         """,
         expect_output=["12"])

    # T12: Operador módulo y potencia
    test("T12 Módulo y potencia",
         "print(2 ^ 10)\nprint(17 % 5)",
         expect_output=["1024", "2"])

    # T13: Múltiples prints en secuencia
    test("T13 Cuadrados del 1 al 5 (while)",
         """
let i = 1
while i <= 5 {
    print(i * i)
    let i = i + 1
}
         """,
         expect_output=["1", "4", "9", "16", "25"])

    # T14: Comparación de igualdad
    test("T14 Comparación ==",
         "let a = 5\nlet b = 5\nprint(a == b)",
         expect_output=["true"])

    # T15: Funciones floor y ceil
    test("T15 floor y ceil",
         "print(floor(3.7))\nprint(ceil(3.2))",
         expect_output=["3", "4"])


# ══════════════════════════════════════════════════════════════════════════
# ERRORES LÉXICOS
# ══════════════════════════════════════════════════════════════════════════

def test_lexical_errors():
    print(f"\n{BOLD}── Errores Léxicos ──{RESET}")

    # T16: Carácter inválido @
    test("T16 Carácter inválido '@'",
         "let x = @5",
         expect_lex_error=True)

    # T17: Carácter inválido #
    test("T17 Carácter inválido '#'",
         "# esto no es un comentario",
         expect_lex_error=True)

    # T18: Cadena sin comilla de cierre
    test("T18 Cadena sin cerrar",
         'print("sin cerrar)',
         expect_lex_error=True)


# ══════════════════════════════════════════════════════════════════════════
# ERRORES SINTÁCTICOS
# ══════════════════════════════════════════════════════════════════════════

def test_parse_errors():
    print(f"\n{BOLD}── Errores Sintácticos ──{RESET}")

    # T19: Paréntesis sin cerrar
    test("T19 Paréntesis sin cerrar",
         "print((3 + 4 * 2)",
         expect_parse_error=True)

    # T20: Función sin llaves de bloque
    test("T20 def sin llaves",
         "def f(x) return x",
         expect_parse_error=True)

    # T21: if sin condición (cuerpo directamente sin expresión de condición válida)
    test("T21 if con token inválido como condición",
         "if { } { print(1) }",
         expect_parse_error=True)


# ══════════════════════════════════════════════════════════════════════════
# ERRORES SEMÁNTICOS
# ══════════════════════════════════════════════════════════════════════════

def test_semantic_errors():
    print(f"\n{BOLD}── Errores Semánticos ──{RESET}")

    # T22: Variable no declarada
    test("T22 Variable no declarada",
         "print(x)",
         expect_semantic_error=True)

    # T28: Redeclaracion en el mismo alcance
    test("T28 Redeclaracion de variable",
         "let x = 1\nlet x = 2",
         expect_semantic_error=True)

    # T23: Aridad incorrecta en llamada a función
    test("T23 Aridad incorrecta",
         "def f(a, b) { return a + b }\nprint(f(1))",
         expect_semantic_error=True)

    # T24: Tipos incompatibles
    test('T24 String + Int',
         'let r = "hola" + 5',
         expect_semantic_error=True)

    # T25: return fuera de función
    test("T25 return fuera de función",
         "return 42",
         expect_semantic_error=True)


# ══════════════════════════════════════════════════════════════════════════
# ERRORES EN TIEMPO DE EJECUCIÓN
# ══════════════════════════════════════════════════════════════════════════

def test_runtime_errors():
    print(f"\n{BOLD}── Errores de Ejecución ──{RESET}")

    # T26: División por cero
    test("T26 División por cero",
         "let r = 10 / 0",
         expect_runtime_error=True)

    # T27: Función no definida en tiempo de ejecución
    test("T27 Función indefinida en ejecución",
         "print(funcionQueNoExiste(1))",
         expect_runtime_error=True)


# ══════════════════════════════════════════════════════════════════════════
# RESUMEN
# ══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print(f"\n{BOLD}╔══════════════════════════════════════╗")
    print(f"║    Suite de Pruebas MathLite          ║")
    print(f"╚══════════════════════════════════════╝{RESET}")

    test_positive_cases()
    test_lexical_errors()
    test_parse_errors()
    test_semantic_errors()
    test_runtime_errors()

    total = passed + failed
    color = GREEN if failed == 0 else RED
    print(f"\n{color}{BOLD}Resultado: {passed}/{total} pruebas pasaron{RESET}")
    if failed > 0:
        print(f"{RED}  {failed} prueba(s) fallaron{RESET}")
    sys.exit(0 if failed == 0 else 1)
