# ast_v02.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union, List, Literal


# -----------------------------
# Source location (optional)
# -----------------------------
@dataclass(frozen=True)
class Span:
    line: int = 0
    col: int = 0

@dataclass
class Token:
    span: Span
    kind: str
    value: str

# -----------------------------
# Types
# -----------------------------
TypeName = Literal["inte", "real", "verum", "filum", "ordinata", "catalogus"]


# -----------------------------
# Expressions
# -----------------------------
@dataclass
class Expr:
    span: Span


@dataclass
class Name(Expr):
    id: str


@dataclass
class IntLit(Expr):
    value: int


@dataclass
class RealLit(Expr):
    value: float

@dataclass
class StringLit(Expr):
    value: str

@dataclass
class CantusLit(Expr):
    template: str

@dataclass
class DictLit(Expr):
    pairs: list[tuple[Expr, Expr]]

@dataclass
class NihilType(Expr):
    pass

@dataclass
class Paren(Expr):
    inner: Expr

@dataclass
class IndexExpr(Expr):
    target: Expr
    key: Expr

BinaryOpKind = Literal[
    "aut", "et",
    "==", "><", "<", ">", "<=", ">=",
    "+", "-", "*", "/", "%", "**"
]

@dataclass
class BinaryOp(Expr):
    op: BinaryOpKind
    left: Expr
    right: Expr


@dataclass
class UnaryOp(Expr):
    op: Literal["non"]
    expr: Expr


@dataclass
class CallExpr(Expr):
    """
    Surface: Identifier () <- (args_tuple)
    Meaning: Identifier(args...)
    """
    name: str
    args: List[Expr]


# -----------------------------
# Statements
# -----------------------------
@dataclass
class Stmt:
    span: Span


@dataclass
class NihilStmt(Stmt):
    """nihil;  -> semantic: pass"""
    pass

@dataclass
class FuncDecl(Stmt):
    """FCON name:Type (arg1:Type, arg2:Type, ...) { REDITUS expr; }"""
    name: str
    type: TypeName
    args: List[Args]
    body: List[Stmt]

@dataclass
class BreakStmt(Stmt):
    """effigium;  (only inside RECURSIO)"""
    pass


@dataclass
class ContinueStmt(Stmt):
    """proximum;  (only inside RECURSIO)"""
    pass

@dataclass
class RditusStmt(Stmt):
    """REDITUS expr;"""
    value: Expr


@dataclass
class VarDecl(Stmt):
    """VCON name:Type = expr;"""
    name: str
    typ: TypeName
    init: Optional[Expr] = None

@dataclass
class Args:
    name: str
    type: TypeName

@dataclass
class Assign(Stmt):
    """name = expr;"""
    name: str
    value: Expr


@dataclass
class Move(Stmt):
    """dst <- src;  (src must be Identifier)"""
    dst: str
    src: str


@dataclass
class CallStmt(Stmt):
    """call_expr;"""
    call: CallExpr


@dataclass
class ExprStmt(Stmt):
    """expr;  (keep if you want, or drop later)"""
    expr: Expr


@dataclass
class IfStmt(Stmt):
    """
    SI propositio:(cond) { VERUM{...} FALSUM{...} };
    FALSUM is required; do nothing => nihil;
    """
    cond: Expr
    then_body: List[Stmt]
    else_body: List[Stmt]


@dataclass
class LoopStmt(Stmt):
    """
    RECURSIO (propositio:(cond) [, quota:init_expr] [, acceleratio:step_expr]) -> { ... };
    - quota default: 100 (semantic)
    - step  default: +1  (semantic), step_expr must be >0 (semantic)
    - guard exceed => runtime error "Veritatem non attigi."
    - counter update at iteration start (after cond true, before body)
    """
    cond: Expr
    quota: Optional[Expr]
    step: Optional[Expr]
    body: List[Stmt]


# -----------------------------
# Sections / Program
# -----------------------------
@dataclass
class ImportStmt(Stmt):
    raw: str


@dataclass
class FonsSection:
    imports: List[ImportStmt]


@dataclass
class IntroSection:
    stmts: List[Stmt]


@dataclass
class MainFunction:
    body: List[Stmt]


@dataclass
class DoctrinaSection:
    main: MainFunction


@dataclass
class Program:
    fons: FonsSection
    introductio: IntroSection
    doctrina: DoctrinaSection
