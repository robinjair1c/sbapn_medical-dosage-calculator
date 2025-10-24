import re
from tokens import Token, TokenType
from errors import LexicalError

KEYWORDS = {
    "CALCULATE","DOSE","FOR","PATIENT","DRUG","CONDITION","WEIGHT","AGE","KIDNEY_FUNCTION",
    "CHECK","INTERACTION","BETWEEN","AND",
    "ADJUST",
    "VALIDATE","PRESCRIPTION",
    "REPORT","REGIMEN","PATIENT_ID",
    "ALERT","WHEN","EXCEEDS","SAFETY_LIMIT",
}

UNITS = {"kg","mg","mcg","g","ml","mg/kg/day","mg/kg/dose","mg/day","mcg/day","mg/dose"}

_token_spec = [
    ("SKIP",   r"[ \t]+"),
    ("COMMA",  r","),
    ("EQUALS", r"="),
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("UNIT",   r"(?:mg/kg/day|mg/kg/dose|mg/day|mcg/day|mg/dose|kg|mg|mcg|g|ml)\b"),
    ("WORD",   r"[A-Za-z_][A-Za-z0-9_\-]*"),
    ("MISMATCH", r"."),
]
_tok_re = re.compile("|".join(f"(?P<{n}>{r})" for n,r in _token_spec))

def is_keyword(word: str) -> bool:
    return word in KEYWORDS

def lex(source: str):
    tokens = []
    for m in _tok_re.finditer(source):
        kind = m.lastgroup
        lexeme = m.group()
        pos = m.start()
        if kind == "SKIP":
            continue
        if kind == "COMMA":
            tokens.append(Token(TokenType.COMMA, lexeme, pos))
        elif kind == "EQUALS":
            tokens.append(Token(TokenType.EQUALS, lexeme, pos))
        elif kind == "NUMBER":
            tokens.append(Token(TokenType.NUMBER, lexeme, pos))
        elif kind == "UNIT":
            tokens.append(Token(TokenType.UNIT, lexeme, pos))
        elif kind == "WORD":
            if lexeme.upper() in KEYWORDS:
                t = Token(TokenType.KEYWORD, lexeme.upper(), pos)
                if lexeme.upper() == "AND":
                    t = Token(TokenType.AND, lexeme.upper(), pos)
                tokens.append(t)
            else:
                tokens.append(Token(TokenType.IDENT, lexeme.lower(), pos))
        elif kind == "MISMATCH":
            raise LexicalError(f"Unexpected character {lexeme!r} at {pos}")
    tokens.append(Token(TokenType.EOF, "", len(source)))
    return tokens
