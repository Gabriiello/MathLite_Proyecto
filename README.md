# MathLite — Intérprete DSL Matemático

**Proyecto Final · Lenguajes Formales · 2026-1**  
Ingeniería de Sistemas y Computación

---

## Estructura del Proyecto

```
mathlite/
├── src/
│   ├── __init__.py        # Módulo principal
│   ├── lexer.py           # Fase 2 — Analizador Léxico
│   ├── ast_nodes.py       # Fase 3 — Nodos del AST
│   ├── parser.py          # Fase 3 — Parser Recursivo Descendente
│   ├── semantic.py        # Fase 4 — Análisis Semántico
│   ├── interpreter.py     # Fase 5 — Intérprete (patrón Visitor)
│   └── pipeline.py        # Coordinador de fases
├── tests/
│   └── test_suite.py      # Fase 6 — 27 casos de prueba
├── web/
│   └── app.py             # Fase 6 — Aplicación web Flask
└── README.md
```

---

## Instalación

```bash
pip install flask
```

---

## Ejecución

### Intérprete desde Python

```python
from src.pipeline import run, run_and_report

codigo = """
def fact(n) {
    if n <= 1 { return 1 }
    return n * fact(n - 1)
}
print(fact(10))
"""

resultado = run(codigo)
print(resultado.output)       # ['3628800']
print(resultado.lex_errors)   # []
print(resultado.ast_text)     # árbol AST en texto
```

### REPL Interactivo

```bash
python -m src.interpreter
```

### Suite de Pruebas

```bash
python tests/test_suite.py
```

### Aplicación Web

```bash
cd web
python app.py
# Abrir http://localhost:5000
```

---

## Especificación del Lenguaje MathLite

### Tipos de Datos
| Tipo    | Ejemplo       |
|---------|---------------|
| Int     | `42`, `-7`    |
| Real    | `3.14`, `-0.5`|
| Bool    | `true`, `false`|
| String  | `"hola"`      |

### Construcciones

```mathlite
-- Comentario de línea

-- Variables
let x = 5
let pi = 3.14159

-- Funciones
def area(b, h) {
    return (b * h) / 2
}

-- Condicional
if x > 0 {
    print("positivo")
} else {
    print("no positivo")
}

-- Ciclo
while x > 0 {
    print(x)
    let x = x - 1
}

-- Funciones integradas
print(sin(3.14))
print(sqrt(16.0))
print(abs(-5))
```

### Operadores (por precedencia)
| Nivel | Operadores               |
|-------|--------------------------|
| 1     | `or`                     |
| 2     | `and`                    |
| 3     | `not`                    |
| 4     | `== != < > <= >=`        |
| 5     | `+ -`                    |
| 6     | `* / %`                  |
| 7     | `^` (asociatividad dcha) |
| 8     | Unario `-`               |

---

## Fases Implementadas

| Fase | Descripción                          | Archivo           | Peso |
|------|--------------------------------------|-------------------|------|
| 1    | Especificación (ver README)          | —                 | 10%  |
| 2    | Analizador Léxico                    | `src/lexer.py`    | 15%  |
| 3    | Parser + AST                         | `src/parser.py`, `src/ast_nodes.py` | 25%  |
| 4    | Análisis Semántico                   | `src/semantic.py` | 20%  |
| 5    | Intérprete                           | `src/interpreter.py` | 20% |
| 6    | App Web + Pruebas                    | `web/app.py`, `tests/` | 10% |

---

## Errores Semánticos Detectados

1. Variable no declarada antes de su uso
2. Redeclaración en el mismo alcance
3. Función no definida
4. Número incorrecto de argumentos (aridad)
5. Tipos incompatibles en operación aritmética (e.g. `String + Int`)
6. `return` fuera del cuerpo de una función

## Errores de Ejecución

1. División por cero
2. Módulo por cero
3. Función no encontrada en tiempo de ejecución
4. Argumento inválido para función matemática
5. Límite de iteraciones excedido (ciclo infinito)
6. Variable no definida en entorno de ejecución

---

## Base de Datos NoSQL y Despliegue

La aplicacion web puede guardar cada ejecucion como caso de prueba en MongoDB
Atlas. Para activarlo, definir estas variables de entorno antes de iniciar la
app:

```bash
MATHLITE_MONGODB_URI="mongodb+srv://usuario:clave@cluster.mongodb.net/"
MATHLITE_MONGODB_DB="mathlite"
```

Si `MATHLITE_MONGODB_URI` no existe, la aplicacion sigue funcionando en modo
local sin almacenamiento externo.

Endpoints disponibles:

- `POST /run`: ejecuta codigo y guarda el caso si MongoDB esta configurado.
- `POST /tokens`: retorna el flujo de tokens.
- `GET /cases`: lista los ultimos casos guardados.

Para despliegue en Render se incluyen `Procfile` y `render.yaml`.

El informe tecnico base esta en `docs/INFORME_TECNICO.md`.
