# ========================
# Transpiler ver.1.0
# ========================

from DEF_AST import *
import re

BUILTINS={"indicant":"print", "accipere":"input", "longitudo":"len", "figura":"type"}

def emit_stmt(s,indent=0):
    """文の変換"""
    pad=" "*indent

    if isinstance(s, Fons):
        return []

    if isinstance(s, Introductio):
        return []

    # Through
    if isinstance(s, Through):
        return [pad + "pass"]

    # 関数(argsなし)
    if isinstance(s,FuncDecl):
        lines=[f"{pad}def {s.name}():"]
        for st in s.body:
            lines+=emit_stmt(st,indent+4)
        return lines+[""]

    # 変数
    if isinstance(s,VarDecl):
        return [f"{pad}{s.name} = {emit_expr(s.expr)}"]

    # 代入
    if isinstance(s,Assign):
        return [f"{pad}{s.name} = {emit_expr(s.expr)}"]

    # 式
    if isinstance(s,ExprStmt) and isinstance(s.expr,FlowCall):
        fn=BUILTINS.get(s.expr.call.name,s.expr.call.name)
        return [f"{pad}{fn}({emit_expr(s.expr.arg)})"]
    
    # if
    if isinstance(s, IfStmt):
        lines=[f"{pad}if {emit_expr(s.cond)}:"]
        for st in s.then_body:
            lines += emit_stmt(st, indent+4)
        lines.append(f"{pad}else:")
        for st in s.else_body:
            lines += emit_stmt(st, indent+4)
        return lines
    
    # loop
    if isinstance(s, RecurStmt):
        lines = []
        lines.append(f"{pad}__i = 0")
        lines.append(f"{pad}__prima = {emit_expr(s.prima)}")
        lines.append(f"{pad}while ({emit_expr(s.propositio)}) and (__i < __prima):")
        for st in s.body:
            lines += emit_stmt(st, indent+4)
        lines.append(f"{pad}    {emit_acceleratio_update(s.acceleratio)}")
        return lines
    
    # break
    if isinstance(s, BreakStmt):
        return [pad + "break"]

    # continue
    if isinstance(s, ContinueStmt):
        return [pad + "continue"]

    raise NotImplementedError(s)

def strip_line_comments(src: str) -> str:
    out = []
    i = 0
    in_s = False
    in_d = False
    while i < len(src):
        ch = src[i]

        # 文字列の開始/終了（エスケープは最小対応）
        if ch == "'" and not in_d:
            # \' を雑に回避
            if i == 0 or src[i-1] != "\\":
                in_s = not in_s
            out.append(ch)
            i += 1
            continue

        if ch == '"' and not in_s:
            if i == 0 or src[i-1] != "\\":
                in_d = not in_d
            out.append(ch)
            i += 1
            continue

        # 文字列の外だけコメント扱い
        if (not in_s and not in_d) and src.startswith("///", i):
            # 行末まで飛ばす
            while i < len(src) and src[i] != "\n":
                i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)

def emit_expr(e):
    if isinstance(e,Num):
        return e.value

    if isinstance(e,Str):
        return e.value

    if isinstance(e,Id):
        return BUILTINS.get(e.name,e.name)

    if isinstance(e, Binary) and e.op == "et":
        return f"({emit_expr(e.left)} and {emit_expr(e.right)})"
    
    if isinstance(e, Binary) and e.op == "aut":
        return f"({emit_expr(e.left)} or {emit_expr(e.right)})"
    
    if isinstance(e,Binary):
        return f"({emit_expr(e.left)} {e.op} {emit_expr(e.right)})"
    
    if isinstance(e, Unary) and e.op == "non":
        return f"(not {emit_expr(e.expr)})"

    if isinstance(e, Cantus):
        # e.raw は "'a=${a}'" みたいにクォート込み想定（今のtokenizerがそうなら）
        raw = e.raw
        if len(raw) >= 2 and raw[0] in ("'", '"') and raw[-1] == raw[0]:
            txt = raw[1:-1]
        else:
            txt = raw  # 念のため

        # ${expr} -> {expr} へ置換（最小実装：} までを1塊として扱う）
        txt = re.sub(r"\$\{([^}]+)\}", r"{\1}", txt)

        # f"..." を作る（reprで安全にクォート）
        return "f" + repr(txt)
    
    if isinstance(e, Compare):
        return f"({emit_expr(e.left)} {e.op.replace('><','!=')} {emit_expr(e.right)})"

    raise NotImplementedError(e)

def emit_acceleratio_update(g: acceleratioOpe) -> str:
    if g.op == "++":
        return "__i += 1"
    if g.op == "--":
        return "__i -= 1"
    if g.op == "+=":
        return f"__i += {g.value}"
    if g.op == "-=":
        return f"__i -= {g.value}"
    raise ValueError(g)

def has_effigum(stmts):
    for s in stmts:
        # 当該ループのbreak
        if isinstance(s, BreakStmt):
            return True

        # ifの中は同一ループなので探索OK
        if isinstance(s, IfStmt):
            if has_effigum(s.then_body):
                return True
            if has_effigum(s.else_body):
                return True

        #  内側RECURSIOは別ループなので無視
        if isinstance(s, RecurStmt):
            continue

    return False

def validate_recur_guard(stmts):
    for s in stmts:
        if isinstance(s, RecurStmt):
            # guardチェック（当該ループのみ）
            if not has_effigum(s.body):
                raise SyntaxError("RECURSIO requires effigum guard")

            # 内部探索
            validate_recur_guard(s.body)
            continue

        if isinstance(s, FuncDecl):
            validate_recur_guard(s.body)
            continue

        if isinstance(s, IfStmt):
            validate_recur_guard(s.then_body)
            validate_recur_guard(s.else_body)
            continue

def validate_types(stmts):
    for s in stmts:

        if isinstance(s, VarDecl):

            # propositio型チェック
            if s.type_name == "propositio" :
                
                if not is_propositio_expr(s.expr):
                    raise SyntaxError("propositio must be a boolean")

        if isinstance(s, FuncDecl):
            validate_types(s.body)

        if isinstance(s, IfStmt):
            validate_types(s.then_body)
            validate_types(s.else_body)

        if isinstance(s, RecurStmt):
            validate_types(s.body)

def is_propositio_expr(e) -> bool:
    if isinstance(e, Compare):
        return True
    if isinstance(e, Unary) and e.op == "non":
        return is_propositio_expr(e.expr)
    if isinstance(e, Binary) and e.op in ("et", "aut"):
        return is_propositio_expr(e.left) and is_propositio_expr(e.right)
    # bool変数を許可するなら
    if isinstance(e, Id):
        return True
    return False

def transpile(ast):
    out=[]
    for st in ast:
        out+=emit_stmt(st)

    out.append("if __name__==\"__main__\":")
    out.append("    subjecto()")
    return "\n".join(out)