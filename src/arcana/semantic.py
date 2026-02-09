# semantic.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, Dict, Set, cast

from . import ast as A
from .error import semantic_error, ErrorCode


# -----------------------------
# Public API
# -----------------------------
@dataclass
class SemanticResult:
    program: A.Program
    # optional: collected warnings later
    warnings: List[str]


def analyze(program: A.Program, *, max_loop_depth: int = 3) -> SemanticResult:
    """
    Runs semantic checks and normalizations.
    - Validates loop control placement
    - Validates RECURSIO nesting depth
    - Normalizes LoopStmt defaults (quota=100, step=+1)
    - Performs basic literal validations (quota >=0, step >0 if literal)
    """
    ctx = _SemContext(max_loop_depth=max_loop_depth)
    _sem_program(program, ctx)
    return SemanticResult(program=program, warnings=ctx.warnings)


# -----------------------------
# Internal context
# -----------------------------
@dataclass
class _SemContext:
    loop_depth: int = 0
    max_loop_depth: int = 3
    warnings: List[str] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


# -----------------------------
# Helpers
# -----------------------------
def _int_value(expr: A.Expr) -> Optional[int]:
    """Return int value if expr is IntLit, else None."""
    if isinstance(expr, A.IntLit):
        return expr.value
    return None


def _num_value(expr: A.Expr) -> Optional[float]:
    """Return numeric value if IntLit or RealLit, else None."""
    if isinstance(expr, A.IntLit):
        return float(expr.value)
    if isinstance(expr, A.RealLit):
        return float(expr.value)
    return None


def _default_int(span: A.Span, n: int) -> A.IntLit:
    return A.IntLit(span=span, value=n)


# -----------------------------
# Semantic traversal
# -----------------------------
def _sem_program(p: A.Program, ctx: _SemContext) -> None:
    # FONS imports: currently no rules
    # INTRODUCTIO
    for s in p.introductio.stmts:
        _sem_stmt(s, ctx)

    # DOCTRINA main
    for s in p.doctrina.main.body:
        _sem_stmt(s, ctx)


def _sem_stmt(s: A.Stmt, ctx: _SemContext) -> None:
    # Control statements
    if isinstance(s, A.BreakStmt):
        if ctx.loop_depth <= 0:
            raise semantic_error(
            ErrorCode.BREAK_OUTSIDE_LOOP,
            message="Nullus discessus est extra reditum.",
            span=s.span,
        )
        return

    if isinstance(s, A.ContinueStmt):
        if ctx.loop_depth <= 0:
            raise semantic_error(
            ErrorCode.CONTINUE_OUTSIDE_LOOP,
            message="Nulla continuitas extra limites est.",
            span=s.span,
        )
        return

    if isinstance(s, A.NihilStmt):
        return

    # VarDecl / Assign / Move / CallStmt / ExprStmt
    if isinstance(s, A.VarDecl):
        if s.init is not None:
            _sem_expr(s.init, ctx)
        return

    if isinstance(s, A.Assign):
        _sem_expr(s.value, ctx)
        return

    if isinstance(s, A.Move):
        # grammar already restricts src to Identifier; nothing else to check here
        return

    if isinstance(s, A.CallStmt):
        _sem_call_expr(s.call, ctx)
        return

    if isinstance(s, A.ExprStmt):
        _sem_expr(s.expr, ctx)
        return

    # If
    if isinstance(s, A.IfStmt):
        _sem_expr(s.cond, ctx)
        for st in s.then_body:
            _sem_stmt(st, ctx)
        for st in s.else_body:
            _sem_stmt(st, ctx)
        return

    # Loop
    if isinstance(s, A.LoopStmt):
        _sem_loop_stmt(s, ctx)
        return

    # ImportStmt (placeholder)
    if isinstance(s, A.ImportStmt):
        return

    # Unknown future statement type
    return


def _sem_loop_stmt(loop: A.LoopStmt, ctx: _SemContext) -> None:
    # nesting check
    next_depth = ctx.loop_depth + 1
    if next_depth > ctx.max_loop_depth:
        raise semantic_error(
            ErrorCode.LOOP_NEST_TOO_DEEP,
            message=f"Tres reincarnationes, si plures, maledictio est.",
            span=loop.span,
        )

    # condition must be semantic "boolean" (we can't fully type-check yet)
    _sem_expr(loop.cond, ctx)

    # Normalize defaults
    # quota default = 100
    if loop.quota is None:
        loop.quota = _default_int(loop.span, 100)
    else:
        _sem_expr(loop.quota, ctx)

    # step default = +1
    if loop.step is None:
        loop.step = _default_int(loop.span, 1)
    else:
        _sem_expr(loop.step, ctx)

    # Literal validations (compile-time when possible)
    qv = _int_value(loop.quota)
    if qv is not None and qv < 0:
        raise semantic_error(
            ErrorCode.LOOP_QUOTA_INVALID,
            message="Rectus valor, recta via",
            span=loop.quota.span if hasattr(loop.quota, "span") else None,
        )

    sv = _num_value(loop.step)
    if sv is not None and sv <= 0:
        raise semantic_error(
            ErrorCode.LOOP_STEP_NOT_POSITIVE,
            message="stationarius accelerationis",
            span=loop.step.span if hasattr(loop.step, "span") else None,
        )
    # If step is non-literal expression, let runtime enforce (>0) in codegen

    # Enter loop body context
    old_depth = ctx.loop_depth
    ctx.loop_depth = next_depth
    try:
        for st in loop.body:
            _sem_stmt(st, ctx)
    finally:
        ctx.loop_depth = old_depth


def _sem_expr(e: A.Expr, ctx: _SemContext) -> None:
    # Disallow nihil as expression (parser already blocks SP nihil in expr,
    # but keep this as a safety net in case AST is constructed elsewhere)
    # (In ast_v2, there is no NihilExpr node, so this is mostly defensive.)

    if isinstance(e, A.Name):
        return

    if isinstance(e, (A.IntLit, A.RealLit, A.StringLit)):
        return

    if isinstance(e, A.Paren):
        _sem_expr(e.inner, ctx)
        return

    if isinstance(e, A.UnaryOp):
        _sem_expr(e.expr, ctx)
        return

    if isinstance(e, A.BinaryOp):
        _sem_expr(e.left, ctx)
        _sem_expr(e.right, ctx)
        return

    if isinstance(e, A.CallExpr):
        _sem_call_expr(e, ctx)
        return

    # unknown expr node: ignore for now


def _sem_call_expr(c: A.CallExpr, ctx: _SemContext) -> None:
    # Arg expressions are always valid expressions
    for a in c.args:
        _sem_expr(a, ctx)

    # Optional: built-in / function existence and arg counts
    # Keep it off for now; can be added later when you implement function_declare/builtins table.
    return
