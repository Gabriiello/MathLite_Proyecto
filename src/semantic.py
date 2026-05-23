"""
Fase 4 — Análisis Semántico para MathLite
Tabla de símbolos con alcances global/función.
Verificación de tipos, aridad de funciones y uso de return.
"""

from .ast_nodes import *


class SemanticError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(message)
        self.line = line

    def __str__(self):
        return f"[Error Semántico] Línea {self.line}: {self.args[0]}"


# Tipos del lenguaje
TYPE_INT    = 'Int'
TYPE_REAL   = 'Real'
TYPE_BOOL   = 'Bool'
TYPE_STRING = 'String'
TYPE_VOID   = 'Void'
TYPE_ANY    = 'Any'   # tipo de retorno de funciones definidas por el usuario


class SymbolTable:
    """Tabla de símbolos con soporte de alcances apilados."""

    def __init__(self):
        self._scopes: list[dict] = [{}]   # scope[0] = global

    def push_scope(self):
        self._scopes.append({})

    def pop_scope(self):
        self._scopes.pop()

    def declare(self, name: str, info: dict, line: int):
        current = self._scopes[-1]
        if name in current:
            raise SemanticError(f"Variable '{name}' ya declarada en este alcance", line)
        current[name] = info

    def lookup(self, name: str) -> dict | None:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_current(self, name: str) -> dict | None:
        return self._scopes[-1].get(name)

    def update(self, name: str, info: dict):
        for scope in reversed(self._scopes):
            if name in scope:
                scope[name] = info
                return


class SemanticAnalyzer:
    """Recorre el AST, anota tipos y valida reglas semánticas."""

    BUILTIN_FUNCTIONS = {
        'sin':   (1, TYPE_REAL),
        'cos':   (1, TYPE_REAL),
        'tan':   (1, TYPE_REAL),
        'sqrt':  (1, TYPE_REAL),
        'log':   (1, TYPE_REAL),
        'abs':   (1, TYPE_REAL),
        'floor': (1, TYPE_INT),
        'ceil':  (1, TYPE_INT),
    }

    def __init__(self):
        self.symbols = SymbolTable()
        self.errors: list[SemanticError] = []
        self._in_function = False

    def analyze(self, node: ASTNode) -> str:
        """Analiza un nodo y retorna su tipo inferido."""
        try:
            return node.accept(self)
        except SemanticError as e:
            self.errors.append(e)
            return TYPE_ANY

    # ── Visitantes ─────────────────────────────────────────────────────────

    def visit_ProgramNode(self, node: ProgramNode) -> str:
        for stmt in node.statements:
            self.analyze(stmt)
        return TYPE_VOID

    def visit_BlockNode(self, node: BlockNode) -> str:
        for stmt in node.statements:
            self.analyze(stmt)
        return TYPE_VOID

    def visit_AssignNode(self, node: AssignNode) -> str:
        val_type = self.analyze(node.value)
        if self.symbols.lookup_current(node.name) is not None:
            self.errors.append(SemanticError(
                f"Variable '{node.name}' ya declarada en este alcance",
                node.line
            ))
            node._inferred_type = val_type
            return TYPE_VOID

        # En bloques internos, 'let' puede actualizar una variable externa.
        existing = self.symbols.lookup(node.name)
        if existing is None:
            self.symbols.declare(node.name, {'type': val_type}, node.line)
        else:
            self.symbols.update(node.name, {'type': val_type})
        node._inferred_type = val_type
        return TYPE_VOID

    def visit_FuncDefNode(self, node: FuncDefNode) -> str:
        # Registrar en la tabla global antes de analizar el cuerpo
        # para permitir recursión
        self.symbols.declare(
            node.name,
            {'type': 'function', 'params': node.params, 'arity': len(node.params)},
            node.line
        )
        self.symbols.push_scope()
        prev = self._in_function
        self._in_function = True

        for param in node.params:
            self.symbols.declare(param, {'type': TYPE_ANY}, node.line)

        self.analyze(node.body)

        self._in_function = prev
        self.symbols.pop_scope()
        return TYPE_VOID

    def visit_FuncCallNode(self, node: FuncCallNode) -> str:
        # Funciones integradas
        if node.name in self.BUILTIN_FUNCTIONS:
            arity, ret_type = self.BUILTIN_FUNCTIONS[node.name]
            if len(node.args) != arity:
                self.errors.append(SemanticError(
                    f"'{node.name}' espera {arity} argumento(s), se dieron {len(node.args)}",
                    node.line
                ))
            for arg in node.args:
                self.analyze(arg)
            node._inferred_type = ret_type
            return ret_type

        # Funciones definidas por el usuario
        sym = self.symbols.lookup(node.name)
        if sym is None:
            self.errors.append(SemanticError(
                f"Función '{node.name}' no está definida", node.line
            ))
            return TYPE_ANY

        if sym.get('type') != 'function':
            self.errors.append(SemanticError(
                f"'{node.name}' no es una función", node.line
            ))
            return TYPE_ANY

        if len(node.args) != sym['arity']:
            self.errors.append(SemanticError(
                f"'{node.name}' espera {sym['arity']} argumento(s), se dieron {len(node.args)}",
                node.line
            ))

        for arg in node.args:
            self.analyze(arg)

        node._inferred_type = TYPE_ANY
        return TYPE_ANY

    def visit_IfNode(self, node: IfNode) -> str:
        cond_type = self.analyze(node.condition)
        if cond_type not in (TYPE_BOOL, TYPE_ANY):
            self.errors.append(SemanticError(
                f"La condición del 'if' debe ser Bool, se encontró {cond_type}",
                node.line
            ))
        self.symbols.push_scope()
        self.analyze(node.then_branch)
        self.symbols.pop_scope()
        if node.else_branch:
            self.symbols.push_scope()
            self.analyze(node.else_branch)
            self.symbols.pop_scope()
        return TYPE_VOID

    def visit_WhileNode(self, node: WhileNode) -> str:
        cond_type = self.analyze(node.condition)
        if cond_type not in (TYPE_BOOL, TYPE_ANY):
            self.errors.append(SemanticError(
                f"La condición del 'while' debe ser Bool, se encontró {cond_type}",
                node.line
            ))
        self.symbols.push_scope()
        self.analyze(node.body)
        self.symbols.pop_scope()
        return TYPE_VOID

    def visit_ReturnNode(self, node: ReturnNode) -> str:
        if not self._in_function:
            self.errors.append(SemanticError(
                "'return' usado fuera del cuerpo de una función", node.line
            ))
        self.analyze(node.value)
        return TYPE_VOID

    def visit_PrintNode(self, node: PrintNode) -> str:
        self.analyze(node.value)
        return TYPE_VOID

    def visit_BinOpNode(self, node: BinOpNode) -> str:
        left_type  = self.analyze(node.left)
        right_type = self.analyze(node.right)

        # Operadores lógicos
        if node.op in ('and', 'or'):
            node._inferred_type = TYPE_BOOL
            return TYPE_BOOL

        # Operadores de comparación
        if node.op in ('==', '!=', '<', '>', '<=', '>='):
            node._inferred_type = TYPE_BOOL
            return TYPE_BOOL

        # Operadores aritméticos
        if node.op in ('+', '-', '*', '/', '^', '%'):
            numeric = {TYPE_INT, TYPE_REAL, TYPE_ANY}
            if left_type not in numeric or right_type not in numeric:
                self.errors.append(SemanticError(
                    f"Operación '{node.op}' inválida entre tipos {left_type} y {right_type}",
                    node.line
                ))
                node._inferred_type = TYPE_ANY
                return TYPE_ANY
            # Int op Real → Real
            if TYPE_REAL in (left_type, right_type):
                node._inferred_type = TYPE_REAL
                return TYPE_REAL
            node._inferred_type = TYPE_INT
            return TYPE_INT

        node._inferred_type = TYPE_ANY
        return TYPE_ANY

    def visit_UnaryOpNode(self, node: UnaryOpNode) -> str:
        t = self.analyze(node.operand)
        if node.op == '-':
            node._inferred_type = t
            return t
        if node.op == 'not':
            node._inferred_type = TYPE_BOOL
            return TYPE_BOOL
        node._inferred_type = TYPE_ANY
        return TYPE_ANY

    def visit_NumberNode(self, node: NumberNode) -> str:
        t = TYPE_INT if isinstance(node.value, int) else TYPE_REAL
        node._inferred_type = t
        return t

    def visit_BoolNode(self, node: BoolNode) -> str:
        node._inferred_type = TYPE_BOOL
        return TYPE_BOOL

    def visit_StringNode(self, node: StringNode) -> str:
        node._inferred_type = TYPE_STRING
        return TYPE_STRING

    def visit_VariableNode(self, node: VariableNode) -> str:
        sym = self.symbols.lookup(node.name)
        if sym is None:
            self.errors.append(SemanticError(
                f"Variable '{node.name}' no está declarada", node.line
            ))
            node._inferred_type = TYPE_ANY
            return TYPE_ANY
        t = sym.get('type', TYPE_ANY)
        node._inferred_type = t
        return t
