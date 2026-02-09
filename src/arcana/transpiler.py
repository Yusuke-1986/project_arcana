# ========================
# Transpiler ver.2.0 (AST v2 compatible)
# ========================
from __future__ import annotations

import re
from typing import List, Optional, Any

from . import ast as A


# Arcana built-ins -> Python built-ins
BUILTINS = {
    "indicant": "print",
    "accipere": "input",
    "longitudo": "len",
    "figura": "type",
}


def transpile(program: A.Program) -> str:
    """
    Transpile Arcana AST (ast_v2) into Python source code.

    Layout:
      - (optional) INTRODUCTIO statements are emitted at module level
      - DOCTRINA main becomes: def subjecto(): ...
      - __main__ calls subjecto()
    """
    out: List[str] = []

    # --- INTRODUCTIO: module-level initializations (VCON, etc.) ---
    for st in program.introductio.stmts:
        out += _emit_stmt(st, indent=0)

    if out and out[-1] != "":
        out.append("")  # blank line between global and function

    # --- DOCTRINA: subjecto() ---
    out.append("def subjecto():")
    body = program.doctrina.main.body
    if not body:
        out.append("    pass")
    else:
        for st in body:
            out += _emit_stmt(st, indent=4)

    out.append("")
    out.append('if __name__ == "__main__":')
    out.append("    subjecto()")
    return "\n".join(out)


# -----------------------------
# Statements
# -----------------------------
def _emit_stmt(s: A.Stmt, indent: int = 0) -> List[str]:
    pad = " " * indent

    # nihil;
    if isinstance(s, A.NihilStmt):
        return [pad + "pass"]

    # VCON name:typ (= init)?;
    if isinstance(s, A.VarDecl):
        if s.init is None:
            return [f"{pad}{s.name} = None"]
        return [f"{pad}{s.name} = {_emit_expr(s.init)}"]

    # name = expr;
    if isinstance(s, A.Assign):
        return [f"{pad}{s.name} = {_emit_expr(s.value)}"]

    # move: dst <- src;  (Arcana move semantics: dst gets src, src cleared)
    if isinstance(s, A.Move):
        return [
            f"{pad}{s.dst} = {s.src}",
            f"{pad}{s.src} = None",
        ]

    # call statement: name() <- (args...);
    if isinstance(s, A.CallStmt):
        return [pad + _emit_call(s.call)]

    # expr statement: expr;
    if isinstance(s, A.ExprStmt):
        return [pad + _emit_expr(s.expr)]

    # if statement
    if isinstance(s, A.IfStmt):
        lines: List[str] = []
        lines.append(f"{pad}if {_emit_expr(s.cond)}:")
        then_body = s.then_body or []
        if not then_body:
            lines.append(pad + " " * 4 + "pass")
        else:
            for st in then_body:
                lines += _emit_stmt(st, indent + 4)

        lines.append(f"{pad}else:")
        else_body = s.else_body or []
        if not else_body:
            lines.append(pad + " " * 4 + "pass")
        else:
            for st in else_body:
                lines += _emit_stmt(st, indent + 4)

        return lines

    # loop: RECURSIO(propositio:(cond), quota:..., acceleratio:...) -> { body };
    if isinstance(s, A.LoopStmt):
        return _emit_loop(s, indent)

    # break/continue
    if isinstance(s, A.BreakStmt):
        return [pad + "break"]

    if isinstance(s, A.ContinueStmt):
        return [pad + "continue"]

    # ImportStmt placeholder (if added later)
    if hasattr(A, "ImportStmt") and isinstance(s, A.ImportStmt):  # type: ignore[attr-defined]
        # not implemented yet; safe no-op
        return []

    raise NotImplementedError(f"Transpiler: unsupported stmt node: {type(s).__name__}")


def _emit_loop(loop: A.LoopStmt, indent: int) -> List[str]:
    pad = " " * indent
    lines: List[str] = []

    # We use a synthetic counter __arc_i to enforce quota, independent of user vars.
    lines.append(f"{pad}__arc_i = 0")

    quota_expr = _emit_expr(loop.quota) if loop.quota is not None else "100"
    step_expr = _emit_expr(loop.step) if loop.step is not None else "1"
    cond_expr = _emit_expr(loop.cond)

    lines.append(f"{pad}while ({cond_expr}) and (__arc_i < ({quota_expr})):")

    if not loop.body:
        lines.append(pad + " " * 4 + "pass")
    else:
        for st in loop.body:
            lines += _emit_stmt(st, indent + 4)

    # Increment counter at loop end
    lines.append(f"{pad}    __arc_i += ({step_expr})")
    return lines


def _emit_call(c: A.CallExpr) -> str:
    fn = BUILTINS.get(c.name, c.name)
    args = ", ".join(_emit_expr(a) for a in c.args)
    return f"{fn}({args})"


# -----------------------------
# Expressions
# -----------------------------
def _emit_expr(e: A.Expr) -> str:
    # names / literals
    if isinstance(e, A.Name):
        return BUILTINS.get(e.id, e.id)

    if isinstance(e, A.IntLit):
        return str(e.value)

    if isinstance(e, A.RealLit):
        # keep python-friendly repr
        return repr(e.value)

    if isinstance(e, A.StringLit):
        # safe quoting
        return repr(e.value)

    if isinstance(e, A.Paren):
        return f"({_emit_expr(e.inner)})"

    if isinstance(e, A.UnaryOp):
        if e.op == "non":
            return f"(not {_emit_expr(e.expr)})"
        # fallback
        return f"({e.op}{_emit_expr(e.expr)})"

    if isinstance(e, A.BinaryOp):
        op = _map_binop(e.op)
        left = _emit_expr(e.left)
        right = _emit_expr(e.right)
        return f"({left} {op} {right})"

    if isinstance(e, A.CallExpr):
        return _emit_call(e)

    # Optional future: Cantus (f-string-ish)
    # Support both class name and attribute-based detection to avoid tight coupling.
    if type(e).__name__ == "Cantus" or hasattr(e, "raw"):
        raw = getattr(e, "raw", None) or getattr(e, "value", "")
        if isinstance(raw, str):
            txt = raw
            # If raw already contains quotes, strip them
            if len(txt) >= 2 and txt[0] in ("'", '"') and txt[-1] == txt[0]:
                txt = txt[1:-1]
            txt = re.sub(r"\$\{([^}]+)\}", r"{\1}", txt)
            return "f" + repr(txt)

    raise NotImplementedError(f"Transpiler: unsupported expr node: {type(e).__name__}")


def _map_binop(op: str) -> str:
    # Arcana logical ops
    if op == "et":
        return "and"
    if op == "aut":
        return "or"
    if op == "><":
        return "!="
    return op
