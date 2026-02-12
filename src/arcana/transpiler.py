# transpiler.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from . import ast as A
from .error import ArcanaRuntimeError, runtime_error, R_VERITATEM_NON_ATTIGI, E_LOOP_STEP_NOT_POSITIVE


# -----------------------------
# Public API
# -----------------------------
def transpile(program: A.Program) -> str:
    """
    Arcana AST(v2) -> Python source.

    Design goals:
    - Visitor-based emitter (extensible, no giant isinstance chain)
    - Minimal runtime helpers embedded (step validation, etc.)
    - Keep semantic meaning in semantic.py; this phase focuses on codegen.
    """
    t = _Transpiler()
    return t.transpile(program)


# -----------------------------
# Emitter / Visitor
# -----------------------------
@dataclass
class _EmitCtx:
    indent: int = 0

    def pad(self) -> str:
        return " " * self.indent


class _Transpiler:
    BUILTINS: Dict[str, str] = {
        "indicant": "print",
        "accipere": "input",
        "longitudo": "len",
        "figura": "__arcana_figura",
        # future:
        # "tempus": "...",
        # "chronos": "...",
        # casts (type-name call)
        "inte": "int",
        "real": "float",
        "filum": "str",
        "ordinata": "tuple",
        "catalogus": "dict",
        "verum": "__arcana_verum",
    }

    def __init__(self) -> None:
        self._lines: List[str] = []
        self._loop_id: int = 0

    # ---- main ----
    def transpile(self, program: A.Program) -> str:
        self._lines = []
        self._emit_prelude()

        # FONS: imports (currently empty placeholder)
        # INTRODUCTIO: module-level init
        self._emit_section_intro(program.introductio)

        # DOCTRINA: main function (subjecto)
        self._emit_section_doctrina(program.doctrina)

        # entry
        self._lines.append('if __name__ == "__main__":')
        self._lines.append("    subjecto()")
        self._lines.append("")
        return "\n".join(self._lines)

    # ---- prelude ----
    def _emit_prelude(self) -> None:
        self._lines.append("class ArcanaRuntimeError(RuntimeError):")
        self._lines.append("    def __init__(self, code, message):")
        self._lines.append("        self.code = code")
        self._lines.append("        self.message = message")
        self._lines.append("        super().__init__(f'[{code}] {message}')")
        self._lines.append("")
        self._lines.append("def __arcana_assert_positive(code, value):")
        self._lines.append("    if value <= 0:")
        self._lines.append("        raise ArcanaRuntimeError(code, 'stationarius accelerationis')")
        self._lines.append("")
        self._lines.append("")

        self._lines.append("def __arcana_figura(x):")
        self._lines.append("    if isinstance(x, bool):")
        self._lines.append("        return 'verum'")
        self._lines.append("    if x is None:")
        self._lines.append("        return 'nihil'")
        self._lines.append("    if isinstance(x, int):")
        self._lines.append("        return 'inte'")
        self._lines.append("    if isinstance(x, float):")
        self._lines.append("        return 'real'")
        self._lines.append("    if isinstance(x, str):")
        self._lines.append("        return 'filum'")
        self._lines.append("    if isinstance(x, dict):")
        self._lines.append("        return 'catalogus'")
        self._lines.append("    if isinstance(x, tuple):")
        self._lines.append("        return 'ordinata'")
        self._lines.append("    return f'{type(x).__name__}_python_originis'")
        self._lines.append("")

    # ---- sections ----
    def _emit_section_intro(self, intro: A.IntroSection) -> None:
        ctx = _EmitCtx(indent=0)
        for st in intro.stmts:
            self._emit_stmt(st, ctx)
        if intro.stmts:
            self._lines.append("")

    def _emit_section_doctrina(self, doctrina: A.DoctrinaSection) -> None:
        self._lines.append("def subjecto():")
        ctx = _EmitCtx(indent=4)
        for st in doctrina.main.body:
            self._emit_stmt(st, ctx)
        if not doctrina.main.body:
            self._lines.append("    pass")
        self._lines.append("")

    # ---- stmt dispatch ----
    def _emit_stmt(self, st: A.Stmt, ctx: _EmitCtx) -> None:
        # print(f"[arcana: transpiler] emitting stmt: {type(st).__name__}")
        fn = getattr(self, f"_stmt_{type(st).__name__}", None)
        if fn is None:
            raise NotImplementedError(f"Transpiler missing stmt handler for: {type(st).__name__}")
        fn(st, ctx)

    def _stmt_NihilStmt(self, st: A.NihilStmt, ctx: _EmitCtx) -> None:
        self._lines.append(ctx.pad() + "pass")

    def _stmt_RditusStmt(self, st: A.RditusStmt, ctx: _EmitCtx) -> None:
        self._lines.append(ctx.pad() + f"return {self._emit_expr(st.value)}")

    def _stmt_FuncDecl(self, st: A.FuncDecl, ctx: _EmitCtx) -> None:
        # print(st.name, st.args)
        self._lines.append(ctx.pad() + f"def {st.name}({', '.join([f'{arg.name}' for arg in st.args])}):")
        # print(self._lines)
        body_ctx = _EmitCtx(indent=ctx.indent + 4)
        for s in st.body:
            self._emit_stmt(s, body_ctx)
        if not st.body:
            self._lines.append(body_ctx.pad() + "    pass")
        self._lines.append("")

    def _stmt_VarDecl(self, st: A.VarDecl, ctx: _EmitCtx) -> None:
        if st.init is None:
            self._lines.append(ctx.pad() + f"{st.name} = None")
        else:
            self._lines.append(ctx.pad() + f"{st.name} = {self._emit_expr(st.init)}")

    def _stmt_Assign(self, st: A.Assign, ctx: _EmitCtx) -> None:
        self._lines.append(ctx.pad() + f"{st.name} = {self._emit_expr(st.value)}")

    def _stmt_Move(self, st: A.Move, ctx: _EmitCtx) -> None:
        # move semantics (Arcana idea): dst gets src, src cleared
        self._lines.append(ctx.pad() + f"{st.dst} = {st.src}")
        self._lines.append(ctx.pad() + f"{st.src} = None")

    def _stmt_CallStmt(self, st: A.CallStmt, ctx: _EmitCtx) -> None:
        self._lines.append(ctx.pad() + self._emit_call_expr(st.call))

    def _stmt_ExprStmt(self, st: A.ExprStmt, ctx: _EmitCtx) -> None:
        self._lines.append(ctx.pad() + self._emit_expr(st.expr))

    def _stmt_BreakStmt(self, st: A.BreakStmt, ctx: _EmitCtx) -> None:
        self._lines.append(ctx.pad() + "break")

    def _stmt_ContinueStmt(self, st: A.ContinueStmt, ctx: _EmitCtx) -> None:
        self._lines.append(ctx.pad() + "continue")

    def _stmt_IfStmt(self, st: A.IfStmt, ctx: _EmitCtx) -> None:
        self._lines.append(ctx.pad() + f"if {self._emit_expr(st.cond)}:")
        then_ctx = _EmitCtx(indent=ctx.indent + 4)
        if st.then_body:
            for s in st.then_body:
                self._emit_stmt(s, then_ctx)
        else:
            self._lines.append(then_ctx.pad() + "pass")

        self._lines.append(ctx.pad() + "else:")
        else_ctx = _EmitCtx(indent=ctx.indent + 4)
        if st.else_body:
            for s in st.else_body:
                self._emit_stmt(s, else_ctx)
        else:
            self._lines.append(else_ctx.pad() + "pass")

    def _stmt_LoopStmt(self, st: A.LoopStmt, ctx: _EmitCtx) -> None:
        self._loop_id += 1
        lid = self._loop_id
        ctr_var = f"__arc_ctr_{lid}"
        quota_var = f"__arc_quota_{lid}"
        step_var = f"__arc_step_{lid}"

        quota_expr = self._emit_expr(st.quota) if st.quota is not None else "100"
        step_expr = self._emit_expr(st.step) if st.step is not None else "1"

        self._lines.append(ctx.pad() + f"{ctr_var} = 0")
        self._lines.append(ctx.pad() + f"{quota_var} = {quota_expr}")
        self._lines.append(ctx.pad() + f"{step_var} = {step_expr}")

        # runtime validations (dynamic expr 対応)
        self._lines.append(ctx.pad() + f"if {quota_var} < 0:")
        self._lines.append(ctx.pad() + f"    raise ArcanaRuntimeError('{R_VERITATEM_NON_ATTIGI}', 'stationarius accelerationis')")
        self._lines.append(ctx.pad() + f"__arcana_assert_positive('{E_LOOP_STEP_NOT_POSITIVE}', {step_var})")

        self._lines.append(ctx.pad() + f"while ({self._emit_expr(st.cond)}):")
        body_ctx = _EmitCtx(indent=ctx.indent + 4)

        # guard + counter update at iteration start (cond True の反復に入った直後)
        self._lines.append(body_ctx.pad() + f"if {ctr_var} >= {quota_var}:")
        self._lines.append(body_ctx.pad() + f"    raise ArcanaRuntimeError('{R_VERITATEM_NON_ATTIGI}', 'Veritatem non attigi.')")
        self._lines.append(body_ctx.pad() + f"{ctr_var} += {step_var}")

        if st.body:
            for s in st.body:
                self._emit_stmt(s, body_ctx)
        else:
            self._lines.append(body_ctx.pad() + "pass")

    # ---- expr dispatch ----
    def _emit_expr(self, e: A.Expr) -> str:
        fn = getattr(self, f"_expr_{type(e).__name__}", None)
        if fn is None:
            raise NotImplementedError(f"Transpiler missing expr handler for: {type(e).__name__}")
        return fn(e)

    def _expr_Name(self, e: A.Name) -> str:
        return e.id

    def _expr_IntLit(self, e: A.IntLit) -> str:
        return str(e.value)

    def _expr_RealLit(self, e: A.RealLit) -> str:
        return repr(e.value)

    def _expr_StringLit(self, e: A.StringLit) -> str:
        # lexer strips quotes already; emit Python string literal safely
        return repr(e.value)

    def _expr_CantusLit(self, e: A.CantusLit) -> str:
        # Arcana cantus'...': emit as Python f-string.
        # lexer already stripped quotes, so e.template is raw content.
        # Use repr to safely quote, then prefix with f.
        return "f" + repr(e.template)
    
    def _expr_DictLit(self, e: A.DictLit) -> str:
        inner = ", ".join(f"{self._emit_expr(k)}: {self._emit_expr(v)}" for k, v in e.pairs)
        return "{" + inner + "}"

    def _expr_Paren(self, e: A.Paren) -> str:
        return f"({self._emit_expr(e.inner)})"
    
    def _expr_IndexExpr(self, e: A.IndexExpr) -> str:
        return f"{self._emit_expr(e.target)}[{self._emit_expr(e.key)}]"

    def _expr_UnaryOp(self, e: A.UnaryOp) -> str:
        if e.op == "non":
            return f"(not {self._emit_expr(e.expr)})"
        if e.op == "+":
            return f"(+{self._emit_expr(e.expr)})"
        if e.op == "-":
            return f"(-{self._emit_expr(e.expr)})"
        return f"({e.op}{self._emit_expr(e.expr)})"

    def _expr_BinaryOp(self, e: A.BinaryOp) -> str:
        # logical ops are in Arcana words
        if e.op == "et":
            return f"({self._emit_expr(e.left)} and {self._emit_expr(e.right)})"
        if e.op == "aut":
            return f"({self._emit_expr(e.left)} or {self._emit_expr(e.right)})"
        # NE token maps to "><" in parser; python is "!="
        if e.op == "><":
            op = "!="
        else:
            op = e.op
        return f"({self._emit_expr(e.left)} {op} {self._emit_expr(e.right)})"

    def _expr_CallExpr(self, e: A.CallExpr) -> str:
        return self._emit_call_expr(e)

    # ---- call ----
    def _emit_call_expr(self, c: A.CallExpr) -> str:
        # Special: ordinata(...) should become a Python tuple literal,
        # because tuple(a,b,c) is invalid (tuple takes 0 or 1 arg).
        if c.name == "ordinata":
            if len(c.args) == 0:
                return "()"
            if len(c.args) == 1:
                return f"({self._emit_expr(c.args[0])},)"
            inner = ", ".join(self._emit_expr(a) for a in c.args)
            return f"({inner})"
        
        fn = self.BUILTINS.get(c.name, c.name)
        args = ", ".join(self._emit_expr(a) for a in c.args)
        return f"{fn}({args})"

    def __arcana_verum(x):
        if isinstance(x, bool):
            return x
        if isinstance(x, (int, float)):
            return x != 0
        if isinstance(x, str):
            s = x.strip().lower()
            if s in ("verum", "true", "1", "yes", "y"):
                return True
            if s in ("falsum", "false", "0", "no", "n", ""):
                return False
        return bool(x)
