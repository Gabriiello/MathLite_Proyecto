"""
Nodos del Árbol de Sintaxis Abstracta (AST) para MathLite
Fase 3 — Definición de estructuras de nodos
"""

from dataclasses import dataclass, field
from typing import Optional, Any


class ASTNode:
    """Clase base para todos los nodos del AST."""
    line: int = 0

    def accept(self, visitor):
        method = f'visit_{type(self).__name__}'
        return getattr(visitor, method)(self)


@dataclass
class NumberNode(ASTNode):
    """Literal numérico: entero o real."""
    value: Any   # int o float
    line: int = 0


@dataclass
class BoolNode(ASTNode):
    """Literal booleano: true o false."""
    value: bool
    line: int = 0


@dataclass
class StringNode(ASTNode):
    """Literal cadena de texto."""
    value: str
    line: int = 0


@dataclass
class VariableNode(ASTNode):
    """Referencia a una variable por nombre."""
    name: str
    line: int = 0


@dataclass
class BinOpNode(ASTNode):
    """Operación binaria: izquierda op derecha."""
    left: ASTNode
    op: str
    right: ASTNode
    line: int = 0


@dataclass
class UnaryOpNode(ASTNode):
    """Operación unaria: op operand."""
    op: str
    operand: ASTNode
    line: int = 0


@dataclass
class AssignNode(ASTNode):
    """Declaración/asignación: let name = expr."""
    name: str
    value: ASTNode
    line: int = 0


@dataclass
class BlockNode(ASTNode):
    """Bloque de sentencias entre { }."""
    statements: list
    line: int = 0


@dataclass
class IfNode(ASTNode):
    """Condicional: if cond { then } else { else_branch }."""
    condition: ASTNode
    then_branch: BlockNode
    else_branch: Optional[BlockNode]
    line: int = 0


@dataclass
class WhileNode(ASTNode):
    """Ciclo while: while cond { body }."""
    condition: ASTNode
    body: BlockNode
    line: int = 0


@dataclass
class FuncDefNode(ASTNode):
    """Definición de función: def name(params) { body }."""
    name: str
    params: list[str]
    body: BlockNode
    line: int = 0


@dataclass
class FuncCallNode(ASTNode):
    """Llamada a función: name(args)."""
    name: str
    args: list
    line: int = 0


@dataclass
class ReturnNode(ASTNode):
    """Sentencia return dentro de una función."""
    value: ASTNode
    line: int = 0


@dataclass
class PrintNode(ASTNode):
    """Sentencia print(expr)."""
    value: ASTNode
    line: int = 0


@dataclass
class ProgramNode(ASTNode):
    """Nodo raíz que contiene todas las sentencias."""
    statements: list
    line: int = 0


# ── Utilidad: visualización en texto indentado ──────────────────────────────

def ast_to_string(node: ASTNode, indent: int = 0) -> str:
    """Convierte el AST a una representación de texto indentada."""
    pad = '  ' * indent
    if node is None:
        return f"{pad}None"

    if isinstance(node, ProgramNode):
        children = '\n'.join(ast_to_string(s, indent + 1) for s in node.statements)
        return f"{pad}Program\n{children}"

    if isinstance(node, NumberNode):
        return f"{pad}Number({node.value})"

    if isinstance(node, BoolNode):
        return f"{pad}Bool({node.value})"

    if isinstance(node, StringNode):
        return f'{pad}String("{node.value}")'

    if isinstance(node, VariableNode):
        return f"{pad}Var({node.name})"

    if isinstance(node, BinOpNode):
        left  = ast_to_string(node.left,  indent + 1)
        right = ast_to_string(node.right, indent + 1)
        return f"{pad}BinOp({node.op})\n{left}\n{right}"

    if isinstance(node, UnaryOpNode):
        operand = ast_to_string(node.operand, indent + 1)
        return f"{pad}UnaryOp({node.op})\n{operand}"

    if isinstance(node, AssignNode):
        val = ast_to_string(node.value, indent + 1)
        return f"{pad}Assign({node.name})\n{val}"

    if isinstance(node, BlockNode):
        children = '\n'.join(ast_to_string(s, indent + 1) for s in node.statements)
        return f"{pad}Block\n{children}"

    if isinstance(node, IfNode):
        cond = ast_to_string(node.condition, indent + 1)
        then = ast_to_string(node.then_branch, indent + 1)
        else_str = ''
        if node.else_branch:
            else_str = f"\n{pad}Else\n{ast_to_string(node.else_branch, indent + 1)}"
        return f"{pad}If\n{pad}Condition\n{cond}\n{pad}Then\n{then}{else_str}"

    if isinstance(node, WhileNode):
        cond = ast_to_string(node.condition, indent + 1)
        body = ast_to_string(node.body, indent + 1)
        return f"{pad}While\n{pad}Condition\n{cond}\n{pad}Body\n{body}"

    if isinstance(node, FuncDefNode):
        params = ', '.join(node.params)
        body   = ast_to_string(node.body, indent + 1)
        return f"{pad}FuncDef({node.name})  params=[{params}]\n{body}"

    if isinstance(node, FuncCallNode):
        args = '\n'.join(ast_to_string(a, indent + 1) for a in node.args)
        return f"{pad}FuncCall({node.name})\n{args}"

    if isinstance(node, ReturnNode):
        val = ast_to_string(node.value, indent + 1)
        return f"{pad}Return\n{val}"

    if isinstance(node, PrintNode):
        val = ast_to_string(node.value, indent + 1)
        return f"{pad}Print\n{val}"

    return f"{pad}Unknown({type(node).__name__})"
