# error.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union


class ErrorCode(str, Enum):
    # -----------------------------
    # Runtime error codes
    # -----------------------------
    VERITATEM_NON_ATTIGI = "R0100_VERITATEM_NON_ATTIGI"

    # -----------------------------
    # Semantic error codes
    # -----------------------------
    BREAK_OUTSIDE_LOOP = "E0101_BREAK_OUTSIDE_LOOP"
    CONTINUE_OUTSIDE_LOOP = "E0102_CONTINUE_OUTSIDE_LOOP"
    LOOP_NEST_TOO_DEEP = "E0103_LOOP_NEST_TOO_DEEP"
    LOOP_STEP_NOT_POSITIVE = "E0110_LOOP_STEP_NOT_POSITIVE"
    LOOP_QUOTA_INVALID = "E0111_LOOP_QUOTA_INVALID"
    NIHIL_NOT_EXPR = "E0202_NIHIL_NOT_EXPR"

    # -----------------------------
    # Parse error codes
    # -----------------------------
    PARSE_EXPECTED_TOKEN = "P0001_EXPECTED_TOKEN"
    PARSE_UNEXPECTED_TOKEN = "P0002_UNEXPECTED_TOKEN"
    PARSE_MAIN_SUBJECTO_REQUIRED = "P0010_MAIN_SUBJECTO_REQUIRED"
    PARSE_MAIN_NIHIL_REQUIRED = "P0011_MAIN_NIHIL_REQUIRED"
    PARSE_UNSUPPORTED_SYNTAX = "P0020_UNSUPPORTED_SYNTAX"
    PARSE_INVALID_MOVE = "P0021_INVALID_MOVE"
    PARSE_UNKNOWN_LOOP_HEADER = "P0030_UNKNOWN_LOOP_HEADER"
    PARSE_LOOP_PROPOSITIO_REQUIRED = "P0031_LOOP_PROPOSITIO_REQUIRED"
    PARSE_NIHIL_NOT_EXPR = "P0040_NIHIL_NOT_EXPR"
    PARSE_INTERNAL = "P0099_INTERNAL"


CodeLike = Union[str, ErrorCode]


def _code_str(code: CodeLike) -> str:
    return code.value if isinstance(code, ErrorCode) else code


# -----------------------------
# Base Arcana Error
# -----------------------------
@dataclass
class ArcanaError(Exception):
    """
    Base class for all Arcana-related errors.

    Notes:
      - span is Optional[Any] to avoid import cycles with AST/Span.
      - If span has .line/.col, __str__ will include it.
    """
    code: str
    message: str
    span: Optional[Any] = None

    def __str__(self) -> str:
        if self.span and (getattr(self.span, "line", 0) or getattr(self.span, "col", 0)):
            return f"[{self.code}] {self.message} (at {self.span.line}:{self.span.col})"
        return f"[{self.code}] {self.message}"


# -----------------------------
# Compile-time Errors
# -----------------------------
class ArcanaParseError(ArcanaError):
    """Syntax / grammar errors (parser phase)."""
    pass


class ArcanaSemanticError(ArcanaError):
    """Semantic errors (semantic analysis phase)."""
    pass


# -----------------------------
# Runtime Errors
# -----------------------------
class ArcanaRuntimeError(RuntimeError):
    """
    Runtime error raised by transpiled Python code.
    (This one intentionally does NOT inherit ArcanaError,
     so Python traceback stays natural.)
    """
    def __init__(self, code: CodeLike, message: str) -> None:
        self.code = _code_str(code)
        self.message = message
        super().__init__(f"[{self.code}] {message}")

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


# -----------------------------
# Helper constructors
# -----------------------------
def semantic_error(code: CodeLike, message: str, span=None) -> ArcanaSemanticError:
    return ArcanaSemanticError(code=_code_str(code), message=message, span=span)


def parse_error(code: CodeLike, message: str, span=None) -> ArcanaParseError:
    return ArcanaParseError(code=_code_str(code), message=message, span=span)


def runtime_error(code: CodeLike, message: str) -> ArcanaRuntimeError:
    return ArcanaRuntimeError(code=code, message=message)


# -----------------------------
# Backward compatible constants
# -----------------------------
# Runtime
R_VERITATEM_NON_ATTIGI = ErrorCode.VERITATEM_NON_ATTIGI.value

# Semantic
E_BREAK_OUTSIDE_LOOP = ErrorCode.BREAK_OUTSIDE_LOOP.value
E_CONTINUE_OUTSIDE_LOOP = ErrorCode.CONTINUE_OUTSIDE_LOOP.value
E_LOOP_NEST_TOO_DEEP = ErrorCode.LOOP_NEST_TOO_DEEP.value
E_LOOP_STEP_NOT_POSITIVE = ErrorCode.LOOP_STEP_NOT_POSITIVE.value
E_LOOP_QUOTA_INVALID = ErrorCode.LOOP_QUOTA_INVALID.value
E_NIHIL_NOT_EXPR = ErrorCode.NIHIL_NOT_EXPR.value
