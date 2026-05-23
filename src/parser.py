"""
Fase 3 — Analizador Sintáctico (Parser) para MathLite
Parser recursivo descendente LL(1) que construye el AST.
"""

from .lexer import Token, TokenType
from .ast_nodes import (
    ProgramNode, BlockNode, AssignNode, FuncDefNode, FuncCallNode,
    IfNode, WhileNode, ReturnNode, PrintNode,
    BinOpNode, UnaryOpNode, NumberNode, BoolNode, StringNode,
    VariableNode
)


class ParseError(Exception):
    def __init__(self, message: str, line: int, column: int = 0):
        super().__init__(message)
        self.line = line
        self.column = column

    def __str__(self):
        return f"[Error Sintáctico] Línea {self.line}: {self.args[0]}"


class Parser:
    def __init__(self, tokens: list[Token]):
        # Filtrar tokens de error para no confundir el parser
        self.tokens = [t for t in tokens if t.type != TokenType.ERROR]
        self.pos = 0
        self.errors: list[ParseError] = []

    # ── Helpers ────────────────────────────────────────────────────────────

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset=1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _check(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _match(self, *types: TokenType) -> bool:
        if self._check(*types):
            self._advance()
            return True
        return False

    def _expect(self, ttype: TokenType, msg: str = None) -> Token:
        if self._check(ttype):
            return self._advance()
        tok = self._current()
        message = msg or f"Se esperaba {ttype.name}, se encontró '{tok.lexeme}'"
        raise ParseError(message, tok.line, tok.column)

    # ── Sincronización de errores ──────────────────────────────────────────

    def _synchronize(self):
        """Avanza hasta un punto de sincronización conocido."""
        sync_types = {
            TokenType.LET, TokenType.DEF, TokenType.IF,
            TokenType.WHILE, TokenType.PRINT, TokenType.RETURN,
            TokenType.RBRACE, TokenType.EOF
        }
        self._advance()  # siempre avanzar al menos uno para evitar bucles infinitos
        while not self._check(TokenType.EOF):
            if self._current().type in sync_types:
                return
            self._advance()

    # ── Gramática ──────────────────────────────────────────────────────────

    def parse(self) -> ProgramNode:
        """Punto de entrada: analiza el programa completo."""
        stmts = []
        while not self._check(TokenType.EOF):
            try:
                stmts.append(self._parse_statement())
            except ParseError as e:
                self.errors.append(e)
                self._synchronize()
        return ProgramNode(stmts, line=1)

    def _parse_statement(self):
        tok = self._current()

        if tok.type == TokenType.LET:
            return self._parse_let()
        if tok.type == TokenType.DEF:
            return self._parse_funcdef()
        if tok.type == TokenType.IF:
            return self._parse_if()
        if tok.type == TokenType.WHILE:
            return self._parse_while()
        if tok.type == TokenType.RETURN:
            return self._parse_return()
        if tok.type == TokenType.PRINT:
            return self._parse_print()

        # Expresión standalone (p.ej. llamada a función)
        expr = self._parse_expression()
        self._match(TokenType.SEMICOLON)
        return expr

    def _parse_let(self) -> AssignNode:
        tok = self._expect(TokenType.LET)
        name_tok = self._expect(TokenType.IDENT, "Se esperaba nombre de variable después de 'let'")
        self._expect(TokenType.ASSIGN, "Se esperaba '=' después del nombre de variable")
        value = self._parse_expression()
        self._match(TokenType.SEMICOLON)
        return AssignNode(name_tok.lexeme, value, line=tok.line)

    def _parse_funcdef(self) -> FuncDefNode:
        tok = self._expect(TokenType.DEF)
        name_tok = self._expect(TokenType.IDENT, "Se esperaba nombre de función después de 'def'")
        self._expect(TokenType.LPAREN, "Se esperaba '(' después del nombre de función")
        params = self._parse_param_list()
        self._expect(TokenType.RPAREN, "Se esperaba ')' para cerrar parámetros")
        body = self._parse_block()
        return FuncDefNode(name_tok.lexeme, params, body, line=tok.line)

    def _parse_param_list(self) -> list[str]:
        params = []
        if self._check(TokenType.RPAREN):
            return params
        params.append(self._expect(TokenType.IDENT, "Se esperaba nombre de parámetro").lexeme)
        while self._match(TokenType.COMMA):
            params.append(self._expect(TokenType.IDENT, "Se esperaba nombre de parámetro").lexeme)
        return params

    def _parse_block(self) -> BlockNode:
        tok = self._expect(TokenType.LBRACE, "Se esperaba '{' para iniciar bloque")
        stmts = []
        while not self._check(TokenType.RBRACE) and not self._check(TokenType.EOF):
            try:
                stmts.append(self._parse_statement())
            except ParseError as e:
                self.errors.append(e)
                self._synchronize()
                if self._check(TokenType.RBRACE):
                    break
        self._expect(TokenType.RBRACE, "Se esperaba '}' para cerrar bloque")
        return BlockNode(stmts, line=tok.line)

    def _parse_if(self) -> IfNode:
        tok = self._expect(TokenType.IF)
        condition = self._parse_expression()
        then_branch = self._parse_block()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._parse_block()
        return IfNode(condition, then_branch, else_branch, line=tok.line)

    def _parse_while(self) -> WhileNode:
        tok = self._expect(TokenType.WHILE)
        condition = self._parse_expression()
        body = self._parse_block()
        return WhileNode(condition, body, line=tok.line)

    def _parse_return(self) -> ReturnNode:
        tok = self._expect(TokenType.RETURN)
        value = self._parse_expression()
        self._match(TokenType.SEMICOLON)
        return ReturnNode(value, line=tok.line)

    def _parse_print(self) -> PrintNode:
        tok = self._expect(TokenType.PRINT)
        self._expect(TokenType.LPAREN, "Se esperaba '(' después de 'print'")
        value = self._parse_expression()
        self._expect(TokenType.RPAREN, "Se esperaba ')' para cerrar 'print'")
        self._match(TokenType.SEMICOLON)
        return PrintNode(value, line=tok.line)

    # ── Expresiones (precedencia ascendente) ──────────────────────────────

    def _parse_expression(self):
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_and()
        while self._check(TokenType.OR):
            op = self._advance()
            right = self._parse_and()
            left = BinOpNode(left, op.lexeme, right, line=op.line)
        return left

    def _parse_and(self):
        left = self._parse_not()
        while self._check(TokenType.AND):
            op = self._advance()
            right = self._parse_not()
            left = BinOpNode(left, op.lexeme, right, line=op.line)
        return left

    def _parse_not(self):
        if self._check(TokenType.NOT):
            op = self._advance()
            operand = self._parse_not()
            return UnaryOpNode(op.lexeme, operand, line=op.line)
        return self._parse_comparison()

    def _parse_comparison(self):
        left = self._parse_addition()
        while self._check(TokenType.EQ, TokenType.NEQ,
                           TokenType.LT, TokenType.GT,
                           TokenType.LTE, TokenType.GTE):
            op = self._advance()
            right = self._parse_addition()
            left = BinOpNode(left, op.lexeme, right, line=op.line)
        return left

    def _parse_addition(self):
        left = self._parse_multiplication()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op = self._advance()
            right = self._parse_multiplication()
            left = BinOpNode(left, op.lexeme, right, line=op.line)
        return left

    def _parse_multiplication(self):
        left = self._parse_power()
        while self._check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._advance()
            right = self._parse_power()
            left = BinOpNode(left, op.lexeme, right, line=op.line)
        return left

    def _parse_power(self):
        base = self._parse_unary()
        if self._check(TokenType.CARET):
            op = self._advance()
            exp = self._parse_power()  # asociatividad derecha
            return BinOpNode(base, op.lexeme, exp, line=op.line)
        return base

    def _parse_unary(self):
        if self._check(TokenType.MINUS):
            op = self._advance()
            operand = self._parse_unary()
            return UnaryOpNode('-', operand, line=op.line)
        return self._parse_primary()

    # ── Primarios ─────────────────────────────────────────────────────────

    MATH_BUILTINS = {
        TokenType.SIN, TokenType.COS, TokenType.TAN,
        TokenType.SQRT, TokenType.LOG, TokenType.ABS,
        TokenType.FLOOR, TokenType.CEIL,
    }

    def _parse_primary(self):
        tok = self._current()

        # Literales
        if tok.type == TokenType.INT:
            self._advance()
            return NumberNode(int(tok.lexeme), line=tok.line)

        if tok.type == TokenType.REAL:
            self._advance()
            return NumberNode(float(tok.lexeme), line=tok.line)

        if tok.type in (TokenType.TRUE, TokenType.FALSE):
            self._advance()
            return BoolNode(tok.type == TokenType.TRUE, line=tok.line)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringNode(tok.lexeme, line=tok.line)

        # Funciones matemáticas integradas
        if tok.type in self.MATH_BUILTINS:
            self._advance()
            self._expect(TokenType.LPAREN, f"Se esperaba '(' después de '{tok.lexeme}'")
            arg = self._parse_expression()
            self._expect(TokenType.RPAREN, f"Se esperaba ')' para cerrar '{tok.lexeme}'")
            from .ast_nodes import FuncCallNode
            return FuncCallNode(tok.lexeme, [arg], line=tok.line)

        # print como expresión (sin return)
        if tok.type == TokenType.PRINT:
            return self._parse_print()

        # Identificador o llamada a función
        if tok.type == TokenType.IDENT:
            self._advance()
            if self._check(TokenType.LPAREN):
                return self._parse_func_call(tok)
            return VariableNode(tok.lexeme, line=tok.line)

        # Agrupación con paréntesis
        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Se esperaba ')' para cerrar expresión")
            return expr

        raise ParseError(
            f"Se encontró token inesperado: '{tok.lexeme}' ({tok.type.name})",
            tok.line, tok.column
        )

    def _parse_func_call(self, name_tok: Token):
        self._expect(TokenType.LPAREN)
        args = []
        if not self._check(TokenType.RPAREN):
            args.append(self._parse_expression())
            while self._match(TokenType.COMMA):
                args.append(self._parse_expression())
        self._expect(TokenType.RPAREN, f"Se esperaba ')' para cerrar llamada a '{name_tok.lexeme}'")
        return FuncCallNode(name_tok.lexeme, args, line=name_tok.line)
