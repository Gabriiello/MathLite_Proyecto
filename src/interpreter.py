"""
Fase 5 — Intérprete para MathLite
Evalúa el AST mediante el patrón Visitor.
Mantiene entornos separados por función (scope stack).
"""

import math
from .ast_nodes import *


class RuntimeError(Exception):
    def __init__(self, message: str, line: int = 0):
        super().__init__(message)
        self.line = line

    def __str__(self):
        loc = f" (línea {self.line})" if self.line else ""
        return f"[Error de Ejecución]{loc}: {self.args[0]}"


class ReturnSignal(Exception):
    """Señal interna para implementar 'return' dentro de funciones."""
    def __init__(self, value):
        self.value = value


class Environment:
    """Entorno de ejecución: pila de diccionarios de variables."""

    def __init__(self, parent=None):
        self._vars: dict = {}
        self.parent: Environment | None = parent

    def get(self, name: str, line: int = 0):
        if name in self._vars:
            return self._vars[name]
        if self.parent:
            return self.parent.get(name, line)
        raise RuntimeError(f"Variable '{name}' no definida", line)

    def set(self, name: str, value):
        """Actualiza si existe en algún scope; si no, crea en el actual."""
        if name in self._vars:
            self._vars[name] = value
            return
        if self.parent and self.parent._has(name):
            self.parent.set(name, value)
            return
        self._vars[name] = value

    def _has(self, name: str) -> bool:
        if name in self._vars:
            return True
        if self.parent:
            return self.parent._has(name)
        return False

    def define(self, name: str, value):
        self._vars[name] = value


MATH_BUILTINS = {
    'sin':   (math.sin,   1),
    'cos':   (math.cos,   1),
    'tan':   (math.tan,   1),
    'sqrt':  (math.sqrt,  1),
    'log':   (math.log,   1),
    'abs':   (abs,         1),
    'floor': (math.floor, 1),
    'ceil':  (math.ceil,  1),
}


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self._functions: dict[str, FuncDefNode] = {}
        self.output: list[str] = []          # captura de print()

    def run(self, node: ASTNode, env: Environment = None) -> any:
        if env is None:
            env = self.global_env
        return node.accept(self)

    def _exec(self, node: ASTNode, env: Environment):
        # Visitor manual con entorno
        return self._dispatch(node, env)

    def _dispatch(self, node: ASTNode, env: Environment):
        name = type(node).__name__
        method = getattr(self, f'visit_{name}', None)
        if method is None:
            raise RuntimeError(f"Nodo desconocido: {name}")
        return method(node, env)

    # ── Punto de entrada público ──────────────────────────────────────────

    def execute(self, node: ASTNode) -> list[str]:
        """Ejecuta el AST completo y retorna las líneas de salida."""
        self.output = []
        self._dispatch(node, self.global_env)
        return self.output

    # ── Visitantes ────────────────────────────────────────────────────────

    def visit_ProgramNode(self, node: ProgramNode, env: Environment):
        for stmt in node.statements:
            self._dispatch(stmt, env)

    def visit_BlockNode(self, node: BlockNode, env: Environment):
        for stmt in node.statements:
            self._dispatch(stmt, env)

    def visit_AssignNode(self, node: AssignNode, env: Environment):
        value = self._dispatch(node.value, env)
        env.set(node.name, value)

    def visit_FuncDefNode(self, node: FuncDefNode, env: Environment):
        self._functions[node.name] = node
        env.define(node.name, node)   # también en el entorno global

    def visit_FuncCallNode(self, node: FuncCallNode, env: Environment):
        # Funciones matemáticas integradas
        if node.name in MATH_BUILTINS:
            func, arity = MATH_BUILTINS[node.name]
            args = [self._dispatch(a, env) for a in node.args]
            if len(args) != arity:
                raise RuntimeError(
                    f"'{node.name}' espera {arity} argumento(s), se dieron {len(args)}",
                    node.line
                )
            try:
                result = func(float(args[0]))
                # floor y ceil retornan entero
                if node.name in ('floor', 'ceil'):
                    return int(result)
                return result
            except (ValueError, ZeroDivisionError) as e:
                raise RuntimeError(f"Error en '{node.name}': {e}", node.line)

        # Función definida por el usuario
        func_def = self._functions.get(node.name)
        if func_def is None:
            raise RuntimeError(f"Función '{node.name}' no encontrada", node.line)

        args = [self._dispatch(a, env) for a in node.args]
        if len(args) != len(func_def.params):
            raise RuntimeError(
                f"'{node.name}' espera {len(func_def.params)} argumento(s), se dieron {len(args)}",
                node.line
            )

        # Crear entorno local con los parámetros
        local_env = Environment(parent=self.global_env)
        for param, arg in zip(func_def.params, args):
            local_env.define(param, arg)

        try:
            self._dispatch(func_def.body, local_env)
        except ReturnSignal as ret:
            return ret.value

        return None

    def visit_IfNode(self, node: IfNode, env: Environment):
        condition = self._dispatch(node.condition, env)
        if condition:
            child_env = Environment(parent=env)
            self._dispatch(node.then_branch, child_env)
        elif node.else_branch:
            child_env = Environment(parent=env)
            self._dispatch(node.else_branch, child_env)

    def visit_WhileNode(self, node: WhileNode, env: Environment):
        MAX_ITER = 100_000
        count = 0
        while self._dispatch(node.condition, env):
            count += 1
            if count > MAX_ITER:
                raise RuntimeError("Límite de iteraciones excedido (posible ciclo infinito)", node.line)
            child_env = Environment(parent=env)
            self._dispatch(node.body, child_env)

    def visit_ReturnNode(self, node: ReturnNode, env: Environment):
        value = self._dispatch(node.value, env)
        raise ReturnSignal(value)

    def visit_PrintNode(self, node: PrintNode, env: Environment):
        value = self._dispatch(node.value, env)
        line = self._format_value(value)
        self.output.append(line)
        print(line)  # también imprime en consola

    def visit_BinOpNode(self, node: BinOpNode, env: Environment):
        left = self._dispatch(node.left, env)
        right = self._dispatch(node.right, env)
        op = node.op

        try:
            if op == '+':  return left + right
            if op == '-':  return left - right
            if op == '*':  return left * right
            if op == '/':
                if right == 0:
                    raise RuntimeError("División por cero", node.line)
                result = left / right
                # Si ambos son enteros y la división es exacta, retorna entero
                if isinstance(left, int) and isinstance(right, int) and left % right == 0:
                    return left // right
                return result
            if op == '^':  return left ** right
            if op == '%':
                if right == 0:
                    raise RuntimeError("Módulo por cero", node.line)
                return left % right
            if op == '==': return left == right
            if op == '!=': return left != right
            if op == '<':  return left < right
            if op == '>':  return left > right
            if op == '<=': return left <= right
            if op == '>=': return left >= right
            if op == 'and': return bool(left) and bool(right)
            if op == 'or':  return bool(left) or bool(right)
        except TypeError as e:
            raise RuntimeError(f"Operación inválida '{op}' entre {type(left).__name__} y {type(right).__name__}", node.line)

        raise RuntimeError(f"Operador desconocido: '{op}'", node.line)

    def visit_UnaryOpNode(self, node: UnaryOpNode, env: Environment):
        val = self._dispatch(node.operand, env)
        if node.op == '-':
            return -val
        if node.op == 'not':
            return not val
        raise RuntimeError(f"Operador unario desconocido: '{node.op}'", node.line)

    def visit_NumberNode(self, node: NumberNode, env: Environment):
        return node.value

    def visit_BoolNode(self, node: BoolNode, env: Environment):
        return node.value

    def visit_StringNode(self, node: StringNode, env: Environment):
        return node.value

    def visit_VariableNode(self, node: VariableNode, env: Environment):
        return env.get(node.name, node.line)

    # ── Utilidad ──────────────────────────────────────────────────────────

    def _format_value(self, val) -> str:
        if isinstance(val, bool):
            return 'true' if val else 'false'
        if isinstance(val, float):
            # Evitar notación científica para valores pequeños
            return f"{val:.10g}"
        return str(val)

    # ── Modo REPL ─────────────────────────────────────────────────────────

    def repl(self):
        """Inicia un REPL interactivo para MathLite."""
        from .lexer import Lexer
        from .parser import Parser

        print("MathLite REPL — escribe 'salir' para terminar")
        while True:
            try:
                line = input(">>> ").strip()
                if line in ('salir', 'exit', 'quit'):
                    break
                if not line:
                    continue

                lexer = Lexer(line)
                tokens, lex_errors = lexer.tokenize()
                for e in lex_errors:
                    print(e)

                parser = Parser(tokens)
                ast = parser.parse()
                for e in parser.errors:
                    print(e)

                if not lex_errors and not parser.errors:
                    self.output = []
                    if len(ast.statements) == 1 and not isinstance(
                        ast.statements[0],
                        (AssignNode, BlockNode, IfNode, WhileNode,
                         FuncDefNode, ReturnNode, PrintNode)
                    ):
                        value = self._dispatch(ast.statements[0], self.global_env)
                        if value is not None:
                            print(self._format_value(value))
                    else:
                        self._dispatch(ast, self.global_env)
                    if not self.output:
                        # Si la expresión produce un valor, mostrarlo
                        pass

            except (RuntimeError, KeyboardInterrupt) as e:
                print(e)
            except EOFError:
                break
        print("¡Hasta luego!")
 
if __name__ == '__main__':
    Interpreter().repl()
