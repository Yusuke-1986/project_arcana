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
    loop_depth: int = 0 # ループカウンタ
    max_loop_depth: int = 3 # 最大ループネスト深度
    warnings: List[str] = None  # type: ignore
    env: Dict[str, str] = None  # 比較用型環境

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []
        if self.env is None:
            self.env = {}


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
    """文の解釈"""
    # Control statements
    if isinstance(s, A.BreakStmt):
        """effigium;"""
        if ctx.loop_depth <= 0:
            raise semantic_error(
            ErrorCode.BREAK_OUTSIDE_LOOP,
            message="Nullus discessus est extra reditum.",
            span=s.span,
        )
        return

    if isinstance(s, A.ContinueStmt):
        """proximum;"""
        if ctx.loop_depth <= 0:
            raise semantic_error(
            ErrorCode.CONTINUE_OUTSIDE_LOOP,
            message="Nulla continuitas extra limites est.",
            span=s.span,
        )
        return

    if isinstance(s, A.NihilStmt):
        """nihil;"""
        return

    # VarDecl / Assign / Move / CallStmt / ExprStmt
    if isinstance(s, A.VarDecl):
        """VCON name:Type = expr;"""
        # 変数を型環境に登録（同名再宣言チェックは今は省略でOK）
        ctx.env[s.name] = s.typ

        if s.init is not None:
            _sem_expr(s.init, ctx)
            rhs_t = infer_expr_type(s.init, ctx.env) # 右辺の型チェック
            if rhs_t is not None and rhs_t != s.typ: # 型が合わなかったら
                raise semantic_error(
                    code=ErrorCode.TYPE_MISMATCH,   
                    message="Feretrum neque nimis magnum neque nimis parvum esse debet.",
                    span=s.span,
                )
        return

    if isinstance(s, A.Assign):
        """Identifier = expr;"""
        _sem_expr(s.value, ctx)

        lhs_t = ctx.env.get(s.name) # 左辺の型取得
        rhs_t = infer_expr_type(s.value, ctx.env) # 右辺の型取得
        if lhs_t is not None and rhs_t is not None and lhs_t != rhs_t: # 型が合わなかったら
            raise semantic_error(
                code=ErrorCode.TYPE_MISMATCH,
                message="Feretrum neque nimis magnum neque nimis parvum esse debet.",
                span=s.span,
            )
        return

    if isinstance(s, A.Move):
        """Identifier <- Identifier;"""
        # grammar already restricts src to Identifier; nothing else to check here
        return

    if isinstance(s, A.CallStmt):
        """call_expr;"""
        _sem_call_expr(s.call, ctx)
        return

    if isinstance(s, A.ExprStmt):
        """expr;"""
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
    """ループの解釈"""
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
    if qv is not None and qv < 0: # 正の整数でない場合
        raise semantic_error(
            ErrorCode.LOOP_QUOTA_INVALID,
            message="Rectus valor, recta via",
            span=loop.quota.span if hasattr(loop.quota, "span") else None,
        )

    sv = _num_value(loop.step)
    if sv is not None and sv <= 0: # 0以下の場合
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
        for st in loop.body: # ネストのカウント(再帰的に)
            _sem_stmt(st, ctx)
    finally:
        ctx.loop_depth = old_depth # ネストを初期に戻す


def _sem_expr(e: A.Expr, ctx: _SemContext) -> None:
    """式の解釈"""
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
        """Identifier () <- (args...)"""
        _sem_call_expr(e, ctx)
        return

    # unknown expr node: ignore for now

# builtin functions arity specs: name -> (min_args, max_args)
_BUILTIN_ARITY = {
    "accipere": (0, 1),
    "longitudo": (1, 1),
    "figura": (1, 1),
    "indicant": (0, None),  # or (1, None)
    "inte": (1, 1),
    "real": (1, 1),
    "filum": (1, 1),
    "ordinata": (0, None), # 可変長引数扱い
    "verum": (1, 1),
}

def _sem_call_expr(c: A.CallExpr, ctx: _SemContext) -> None:
    # Arg expressions are always valid expressions
    for a in c.args:
        _sem_expr(a, ctx)

    # Optional: built-in / function existence and arg counts
    # Keep it off for now; can be added later when you implement function_declare/builtins table.
    spec = _BUILTIN_ARITY.get(c.name)
    if spec is None:
        return
    
    mn, mx = spec # min/max args
    n = len(c.args) # actual arg count
    if n < mn:
        raise semantic_error(
            code=ErrorCode.ARG_COUNT_MISMATCH,
            message="Numeri non congruunt. Fortasse mus eos abstulit.",
            span=c.span,
        )
    if mx is not None and n > mx:
        raise semantic_error(
            code=ErrorCode.ARG_COUNT_MISMATCH,
            message="Numeri non congruunt. Fortasse mus eos abstulit.",
            span=c.span,
        )
    
    return

def infer_expr_type(e, env) -> str | None:
    """Infer the type of an expression, if possible."""
    if isinstance(e, A.IntLit):
        return "inte"
    if isinstance(e, A.RealLit):
        return "real"
    if isinstance(e, A.StringLit):
        return "filum"
    if isinstance(e, A.Name):
        return env.get(e.id)
    if isinstance(e, A.CallExpr):
        # builtin return types
        rt = {
            "accipere": "filum",
            "longitudo": "inte",
            "figura": "filum",
            "inte": "inte",
            "real": "real",
            "filum": "filum",
            "ordinata": "ordinata",
            "verum": "verum",
            "indicant": "nihil",
        }.get(e.name)
        return rt
    return None



