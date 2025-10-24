from dataclasses import dataclass

class InterpreterError(Exception):
    pass

class LexicalError(InterpreterError):
    pass

class ParseError(InterpreterError):
    pass

class ExecutionError(InterpreterError):
    pass

class UnknownDrugError(ExecutionError):
    def __init__(self, drug: str):
        super().__init__(f"Unknown drug: {drug}")
        self.drug = drug

class UnknownConditionError(ExecutionError):
    def __init__(self, condition: str):
        super().__init__(f"Unknown condition: {condition}")
        self.condition = condition

class SafetyLimitExceeded(ExecutionError):
    def __init__(self, message: str, computed: float, limit: float):
        super().__init__(message)
        self.computed = computed
        self.limit = limit

@dataclass
class ErrorReport:
    kind: str
    message: str
    position: int | None = None
