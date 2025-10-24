from __future__ import annotations
from typing import List, Dict
from tokens import Token, TokenType
from errors import ParseError
from ast_nodes import *

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def advance(self) -> Token:
        t = self.tokens[self.i]
        self.i += 1
        return t

    def match_keyword(self, *keys: str) -> bool:
        if self.peek().type == TokenType.KEYWORD and self.peek().lexeme in keys:
            self.advance()
            return True
        return False

    def require_keyword(self, key: str):
        if not self.match_keyword(key):
            t = self.peek()
            raise ParseError(f"Expected keyword '{key}' at {t.pos} but found '{t.lexeme}'")

    def expect(self, ttype: TokenType) -> Token:
        t = self.peek()
        if t.type != ttype:
            raise ParseError(f"Expected {ttype.name} at {t.pos} but found {t.lexeme!r}")
        return self.advance()

    def parse(self) -> Command:
        if self.match_keyword("CALCULATE"):
            self.require_keyword("DOSE")
            self.require_keyword("FOR")
            params = self.parse_kv_list()
            return CalculateDose("CALCULATE", params)
        if self.match_keyword("CHECK"):
            self.require_keyword("INTERACTION")
            self.require_keyword("BETWEEN")
            a = self.expect_ident_value()
            self.expect(TokenType.AND)
            b = self.expect_ident_value()
            return CheckInteraction("CHECK", {"drug_a": a, "drug_b": b})
        if self.match_keyword("ADJUST"):
            self.require_keyword("DOSE")
            self.require_keyword("FOR")
            params = self.parse_kv_list()
            return AdjustDose("ADJUST", params)
        if self.match_keyword("VALIDATE"):
            self.require_keyword("PRESCRIPTION")
            params = self.parse_kv_list()
            return ValidatePrescription("VALIDATE", params)
        if self.match_keyword("REPORT"):
            self.require_keyword("REGIMEN")
            params = self.parse_kv_list()
            return ReportRegimen("REPORT", params)
        if self.match_keyword("ALERT"):
            self.require_keyword("WHEN")
            self.require_keyword("DOSE")
            self.require_keyword("EXCEEDS")
            self.require_keyword("SAFETY_LIMIT")
            return AlertThreshold("ALERT", {"rule": "dose_exceeds_safety_limit"})
        t = self.peek()
        raise ParseError(f"Unknown command starting at {t.pos}: {t.lexeme!r}")

    def parse_kv_list(self) -> Dict[str, str]:
        params: Dict[str, str] = {}
        while self.peek().type != TokenType.EOF:
            key = self.expect_ident_value()
            self.expect(TokenType.EQUALS)
            val = self.expect_value_with_optional_unit()
            params[key] = val
            if self.peek().type == TokenType.COMMA:
                self.advance()
            if self.peek().type == TokenType.EOF:
                break
        return params

    def expect_ident_value(self) -> str:
        t = self.peek()
        if t.type in (TokenType.IDENT, TokenType.KEYWORD):
            return self.advance().lexeme
        raise ParseError(f"Expected identifier at {t.pos} but found {t.lexeme!r}")

    def expect_value_with_optional_unit(self) -> str:
        t = self.peek()
        if t.type == TokenType.NUMBER:
            num = self.advance().lexeme
            if self.peek().type == TokenType.UNIT:
                unit = self.advance().lexeme
                return f"{num}{unit}"
            return num
        if t.type in (TokenType.IDENT,):
            return self.advance().lexeme
        if t.type == TokenType.KEYWORD:
            return self.advance().lexeme.lower()
        if t.type == TokenType.UNIT:
            u = self.advance().lexeme
            return u
        raise ParseError(f"Expected value at {t.pos} but found {t.lexeme!r}")
