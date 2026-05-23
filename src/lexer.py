"""
Fase 2 — Analizador Léxico (Lexer) para MathLite
Reconoce todos los tokens del lenguaje y reporta errores sin abortar.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Literales
    INT       = auto()
    REAL      = auto()
    BOOL      = auto()
    STRING    = auto()

    # Palabras reservadas
    LET       = auto()
    DEF       = auto()
    RETURN    = auto()
    IF        = auto()
    ELSE      = auto()
    WHILE     = auto()
    PRINT     = auto()
    AND       = auto()
    OR        = auto()
    NOT       = auto()
    TRUE      = auto()
    FALSE     = auto()

    # Funciones matemáticas integradas
    SIN       = auto()
    COS       = auto()
    TAN       = auto()
    SQRT      = auto()
    LOG       = auto()
    ABS       = auto()
    FLOOR     = auto()
    CEIL      = auto()

    # Identificadores
    IDENT     = auto()

    # Operadores aritméticos
    PLUS      = auto()   # +
    MINUS     = auto()   # -
    STAR      = auto()   # *
    SLASH     = auto()   # /
    CARET     = auto()   # ^
    PERCENT   = auto()   # %

    # Operadores relacionales
    EQ        = auto()   # ==
    NEQ       = auto()   # !=
    LT        = auto()   # <
    GT        = auto()   # >
    LTE       = auto()   # <=
    GTE       = auto()   # >=

    # Asignación
    ASSIGN    = auto()   # =

    # Delimitadores
    LPAREN    = auto()   # (
    RPAREN    = auto()   # )
    LBRACE    = auto()   # {
    RBRACE    = auto()   # }
    COMMA     = auto()   # ,
    SEMICOLON = auto()   # ;

    # Especiales
    EOF       = auto()
    ERROR     = auto()


KEYWORDS = {
    'let':   TokenType.LET,
    'def':   TokenType.DEF,
    'return':TokenType.RETURN,
    'if':    TokenType.IF,
    'else':  TokenType.ELSE,
    'while': TokenType.WHILE,
    'print': TokenType.PRINT,
    'and':   TokenType.AND,
    'or':    TokenType.OR,
    'not':   TokenType.NOT,
    'true':  TokenType.TRUE,
    'false': TokenType.FALSE,
    'sin':   TokenType.SIN,
    'cos':   TokenType.COS,
    'tan':   TokenType.TAN,
    'sqrt':  TokenType.SQRT,
    'log':   TokenType.LOG,
    'abs':   TokenType.ABS,
    'floor': TokenType.FLOOR,
    'ceil':  TokenType.CEIL,
}


@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.lexeme!r}, {self.line}:{self.column})"


class LexerError:
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column

    def __str__(self):
        return f"[Error Léxico] Línea {self.line}, Columna {self.column}: {self.message}"


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.errors: list[LexerError] = []

    def _current(self):
        if self.pos < len(self.source):
            return self.source[self.pos]
        return '\0'

    def _peek(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return '\0'

    def _advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _match(self, expected):
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self._advance()
            return True
        return False

    def tokenize(self) -> tuple[list[Token], list[LexerError]]:
        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens, self.errors

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self._current()
            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
            elif ch == '-' and self._peek() == '-':
                # Comentario de línea
                while self.pos < len(self.source) and self._current() != '\n':
                    self._advance()
            else:
                break

    def _scan_token(self):
        start_line = self.line
        start_col = self.column
        ch = self._advance()

        # Número: real o entero
        if ch.isdigit():
            return self._scan_number(ch, start_line, start_col)

        # Cadena
        if ch == '"':
            return self._scan_string(start_line, start_col)

        # Identificador / palabra reservada
        if ch.isalpha() or ch == '_':
            return self._scan_ident(ch, start_line, start_col)

        # Operadores y delimitadores
        simple = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '^': TokenType.CARET,
            '%': TokenType.PERCENT,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            ',': TokenType.COMMA,
            ';': TokenType.SEMICOLON,
        }
        if ch in simple:
            self.tokens.append(Token(simple[ch], ch, start_line, start_col))
            return

        if ch == '=':
            if self._match('='):
                self.tokens.append(Token(TokenType.EQ, '==', start_line, start_col))
            else:
                self.tokens.append(Token(TokenType.ASSIGN, '=', start_line, start_col))
            return

        if ch == '!':
            if self._match('='):
                self.tokens.append(Token(TokenType.NEQ, '!=', start_line, start_col))
            else:
                self.errors.append(LexerError(f"Carácter inesperado '!' sin '='", start_line, start_col))
                self.tokens.append(Token(TokenType.ERROR, ch, start_line, start_col))
            return

        if ch == '<':
            if self._match('='):
                self.tokens.append(Token(TokenType.LTE, '<=', start_line, start_col))
            else:
                self.tokens.append(Token(TokenType.LT, '<', start_line, start_col))
            return

        if ch == '>':
            if self._match('='):
                self.tokens.append(Token(TokenType.GTE, '>=', start_line, start_col))
            else:
                self.tokens.append(Token(TokenType.GT, '>', start_line, start_col))
            return

        # Carácter inválido — reportar error, continuar
        self.errors.append(LexerError(f"Carácter inválido: '{ch}'", start_line, start_col))
        self.tokens.append(Token(TokenType.ERROR, ch, start_line, start_col))

    def _scan_number(self, first: str, line: int, col: int):
        lexeme = first
        while self._current().isdigit():
            lexeme += self._advance()

        if self._current() == '.' and self._peek().isdigit():
            lexeme += self._advance()  # consume '.'
            while self._current().isdigit():
                lexeme += self._advance()
            self.tokens.append(Token(TokenType.REAL, lexeme, line, col))
        else:
            self.tokens.append(Token(TokenType.INT, lexeme, line, col))

    def _scan_string(self, line: int, col: int):
        lexeme = ''
        while self.pos < len(self.source) and self._current() != '"':
            if self._current() == '\n':
                self.errors.append(LexerError("Cadena sin cerrar (salto de línea antes del cierre)", line, col))
                self.tokens.append(Token(TokenType.ERROR, '"' + lexeme, line, col))
                return
            lexeme += self._advance()

        if self.pos >= len(self.source):
            self.errors.append(LexerError("Cadena sin comilla de cierre", line, col))
            self.tokens.append(Token(TokenType.ERROR, '"' + lexeme, line, col))
            return

        self._advance()  # consume '"' de cierre
        self.tokens.append(Token(TokenType.STRING, lexeme, line, col))

    def _scan_ident(self, first: str, line: int, col: int):
        lexeme = first
        while self._current().isalnum() or self._current() == '_':
            lexeme += self._advance()

        token_type = KEYWORDS.get(lexeme, TokenType.IDENT)
        self.tokens.append(Token(token_type, lexeme, line, col))


if __name__ == '__main__':
    code = """
-- Ejemplo básico
let x = 10
let y = 3.14
def suma(a, b) {
    return a + b
}
print(suma(x, y))
"""
    lexer = Lexer(code)
    tokens, errors = lexer.tokenize()

    print("=== TOKENS ===")
    for t in tokens:
        print(t)

    if errors:
        print("\n=== ERRORES LÉXICOS ===")
        for e in errors:
            print(e)
