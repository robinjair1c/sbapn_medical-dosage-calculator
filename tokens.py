from dataclasses import dataclass
from enum import Enum, auto

class TokenType(Enum):
    EQUALS = auto()
    COMMA = auto()
    NUMBER = auto()
    UNIT = auto()
    IDENT = auto()
    KEYWORD = auto()
    AND = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str
    pos: int
