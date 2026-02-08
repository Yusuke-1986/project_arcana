# arcana.py
from __future__ import annotations

import argparse
import re
from typing import Any


# --- Arcana -> Python mappings ---
TYPE_MAP = {
    "inte": "int",
    "real": "float",
    "verum": "bool",
    "filum": "str",
    "nihil": "None",  # return type only
}

BUILTIN_MAP = {
    "indicant": "print",
    # optional future:
    # "accipio": "input",
    # "longitudo": "len",
}

CONST_MAP = {
    "VERUM": "True",
    "FALSUM": "False",
    "NIHIL": "None",
}

IDENT = r"[A-Za-z_]\w*"

TRACE = False
TRACE_INDENT = 0

# --- tracing ---
def tr(msg: str) -> None:
    if TRACE:
        print(f"[arcana:trace] {'  ' * TRACE_INDENT}{msg}")

def strip_inline_comment(line: str) -> str:
    """Strip Arcana inline comments introduced by '///' (only when outside string literals).

    Examples:
      - 'x <- 1; /// comment' -> 'x <- 1;'
      - "cantus'abc /// not comment'" stays intact
    """
    in_single = False
    in_double = False
    escaped = False

    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if ch == '\\':
            escaped = True
            i += 1
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            i += 1
            continue

        # Arcana comment starts with '///' when not inside a string
        if not in_single and not in_double and line.startswith('///', i):
            return line[:i].rstrip()
        i += 1

    return line.rstrip()


# --- helpers ---
def replace_consts(expr: str) -> str:
    for k, v in CONST_MAP.items():
        expr = re.sub(rf"\b{k}\b", v, expr)
    return expr


def normalize_expr(expr: str) -> str:
    """
    v0: operator sugar + const + cantus
    - ><  -> !=
    - !x  -> not x
    """
    expr = expr.strip()

    # 1) const
    expr = replace_consts(expr)

    # 2) operator sugar
    expr = expr.replace("><", "!=")  # must be first

    # 3) unary not
    # "!" but not "!="
    expr = re.sub(r"(?<![A-Za-z0-9_])!\s*(?!=)", "not ", expr)
    # 注意: "a!b" のようなケースはArcana文法的に不正なので無視

    # 4) cantus
    expr = transpile_cantus_in_expr(expr)

    return expr

def transpile_flow_expr(expr: str) -> str:
    """
    Arcana expression that may contain a flow call:
      potentia() <- (a, b)   -> potentia(a, b)
      indicant() <- x        -> print(x)   (式としては副作用だが、v0では許容)
    If not flow, returns expr (after cantus/const handling is done outside or inside).
    """
    expr = expr.strip()

    m = re.fullmatch(rf"({IDENT})\s*\(\s*\)\s*<-\s*(.+)", expr)
    if not m:
        return expr

    fname = m.group(1)
    rhs = m.group(2).strip()

    py_name = BUILTIN_MAP.get(fname, fname)

    rhs = replace_consts(rhs)
    rhs = transpile_cantus_in_expr(rhs)

    if rhs.startswith("(") and rhs.endswith(")"):
        inner = rhs[1:-1].strip()
        if not inner:
            return f"{py_name}()"
        parts = split_top_level_commas(inner)
        return f"{py_name}({', '.join(parts)})"

    return f"{py_name}({rhs})"


def transpile_cantus_in_expr(expr: str) -> str:
    """
    cantus'...${expr}...'  ->  f'...{expr}...'
    cantus"...${expr}..."  ->  f"...{expr}..."
    (最小実装: 文字列内の ${...} を {...} に置換)
    """
    expr = expr.strip()
    m = re.fullmatch(r"cantus\s*(['\"])(.*)\1", expr, flags=re.DOTALL)
    if not m:
        return expr

    quote = m.group(1)
    body = m.group(2)

    # ${ ... } -> { ... } (外側の空白は軽くトリム)
    def repl(match: re.Match) -> str:
        inner = match.group(1).strip()
        return "{" + inner + "}"

    body2 = re.sub(r"\$\{([^}]*)\}", repl, body)
    return f"f{quote}{body2}{quote}"


def split_top_level_commas(s: str) -> list[str]:
    """トップレベルのカンマで分割（括弧/文字列をざっくり考慮）"""
    out, buf = [], []
    depth = 0
    in_squote = False
    in_dquote = False
    esc = False

    for ch in s:
        if esc:
            buf.append(ch)
            esc = False
            continue
        if ch == "\\":
            buf.append(ch)
            esc = True
            continue

        if ch == "'" and not in_dquote:
            in_squote = not in_squote
        elif ch == '"' and not in_squote:
            in_dquote = not in_dquote
        elif not in_squote and not in_dquote:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append("".join(buf).strip())
                buf = []
                continue

        buf.append(ch)

    last = "".join(buf).strip()
    if last:
        out.append(last)
    return out


def indent(lines: list[str], n: int = 4) -> list[str]:
    pad = " " * n
    return [pad + ln if ln else ln for ln in lines]

def transpile_stmts(block_lines: list[str], need_any: dict) -> list[str]:
    """
    Parse a list of Arcana lines (already extracted from a { ... } block body),
    allowing nested blocks like si/repetitio/minst inside.
    """
    out: list[str] = []
    i = 0
    while i < len(block_lines):
        py, i2 = transpile_stmt(block_lines, i, need_any)
        out.extend(py)
        i = i2
    return out


# --- statement transpilers ---
def transpile_stmt(lines: list[str], i: int, need_any: dict) -> tuple[list[str], int]:
    """
    Returns (python_lines, next_index)
    Supports:
      - VINST name: type = expr;
      - name = expr;
      - flow call: fname() <- expr;  / fname() <- (a,b);
      - MINST ... -> { ... };
      - REPETITIO (...) { ... };
      - SI conditio: (expr){ verum{...} FALSUM{...} };
    """
    line = strip_inline_comment(lines[i]).strip()
    tr(f"stmt i={i}: {line}")

    if not line or line.startswith("///"):
        tr(f"match comment line={line}")
        return ([], i + 1)

    # <cmt> ... </cmt> block
    if line.startswith("<cmt>"):
        
        j = i + 1
        while j < len(lines) and "</cmt>" not in lines[j]:
            j += 1

        tr(f"match  <cmt> block from i={i} to j={j}")
        return ([], min(j + 1, len(lines)))

    # VINST a: inte = 10;
    m = re.fullmatch(rf"VINST\s+({IDENT})\s*:\s*({IDENT})\s*=\s*(.+)\s*;\s*", line)
    if m:
        tr(f"match VINST name={m.group(1)} type={m.group(2)} expr={m.group(3)}")
        name, ty, expr = m.group(1), m.group(2).lower(), m.group(3).strip()
        if ty not in TYPE_MAP:
            raise SyntaxError(f"unknown type: {ty}")

        py_ty = TYPE_MAP[ty]
        # expr transforms
        expr = normalize_expr(expr)
        expr = transpile_cantus_in_expr(expr)

        # None注釈は変数には微妙なのでAnyに逃がす（v0の保険）
        if py_ty == "None":
            need_any["need_any"] = True
            py_ty = "Any"

        if py_ty == "Any":
            need_any["need_any"] = True

        return ([f"{name}: {py_ty} = {expr}"], i + 1)

    # assignment: name = expr;
    m = re.fullmatch(rf"({IDENT})\s*=\s*(.+)\s*;\s*", line)
    if m:
        tr(f"match assignment name={m.group(1)} expr={m.group(2)}")
        name, expr = m.group(1), m.group(2).strip()
        expr = normalize_expr(expr)
        expr = transpile_cantus_in_expr(expr)

        # ここを追加：flow式なら展開してPython式へ
        expr = transpile_flow_expr(expr)

        return ([f"{name} = {expr}"], i + 1)

    # flow call: fname() <- expr;
    m = re.fullmatch(rf"({IDENT})\s*\(\s*\)\s*<-\s*(.+)\s*;\s*", line)
    if m:
        tr(f"match flow call fname={m.group(1)} rhs={m.group(2)}")
        fname = m.group(1)
        rhs = m.group(2).strip()

        py_name = BUILTIN_MAP.get(fname, fname)

        rhs = normalize_expr(rhs)
        rhs = transpile_cantus_in_expr(rhs)

        # tuple args: (a, b, c)
        if rhs.startswith("(") and rhs.endswith(")"):
            inner = rhs[1:-1].strip()
            if not inner:
                return ([f"{py_name}()"], i + 1)
            parts = split_top_level_commas(inner)
            return ([f"{py_name}({', '.join(parts)})"], i + 1)

        return ([f"{py_name}({rhs})"], i + 1)

    # function definition: MINST name: ret (params) -> { ... };
    if line.startswith("MINST "):
        tr(f"match MINST line={line}")
        py_lines, next_i = transpile_MINST(lines, i, need_any)
        return (py_lines, next_i)

    # loop: REPETITIO (...) { ... };
    if line.startswith("REPETITIO "):
        tr(f"match REPETITIO line={line}")
        py_lines, next_i = transpile_REPETITIO(lines, i, need_any)
        return (py_lines, next_i)

    # if: SI conditio: (expr){ VERUM{...} FALSUM{...} };
    if line.startswith("SI "):
        tr(f"match SI line={line}")
        py_lines, next_i = transpile_SI(lines, i, need_any)
        return (py_lines, next_i)

    raise SyntaxError(f"unsupported syntax: {line}")


def collect_block(lines: list[str], start_i: int) -> tuple[list[str], int]:
    """
    start_i: line index where an outer block starts (must contain '{')
    Returns:
      - body lines inside the outermost { ... } (keeping inner braces/closers intact)
      - next index after the outer block (and optional trailing ';' line)
    """
    if "{" not in lines[start_i]:
        raise SyntaxError("block must start with '{'")
    
    global TRACE_INDENT
    tr(f"collect_block start_i={start_i}: {strip_inline_comment(lines[start_i]).strip()}")
    TRACE_INDENT += 1

    depth = 0
    entered = False
    body: list[str] = []

    i = start_i
    while i < len(lines):
        raw = strip_inline_comment(lines[i])
        stripped = raw.strip()

        # まず深さを更新しつつ、外側ブロック終端を検知する
        for ch in raw:
            if ch == "{":
                depth += 1
                entered = True
            elif ch == "}":
                depth -= 1
                if entered and depth == 0:
                    # 外側ブロックが閉じた。閉じ行は本文に入れない。
                    i += 1
                    # 次の行が ';' 単独なら吸収
                    if i < len(lines) and strip_inline_comment(lines[i]).strip() == ";":
                        i += 1

                    tr(f"collect_block end at i={i}, next={i+1}, body_lines={len(body)}")
                    TRACE_INDENT -= 1
                    return (body, i)

        # start_i（外側の開始行）以外は、内側の構文を壊さないようそのまま保持
        if entered and i != start_i:
            if stripped != "":
                body.append(stripped)

        i += 1

    raise SyntaxError("unterminated block")




def transpile_MINST(lines: list[str], i: int, need_any: dict) -> tuple[list[str], int]:
    header = lines[i].strip()

    # Expect header like:
    # MINST potentia: inte (a: inte, b: inte ) -> {
    m = re.fullmatch(
        rf"MINST\s+({IDENT})\s*:\s*({IDENT})\s*\(\s*(.*?)\s*\)\s*->\s*\{{\s*",
        header
    )
    if not m:
        raise SyntaxError(f"invalid MINST header: {header}")

    name = m.group(1)
    ret_ty = m.group(2).lower()
    params_raw = m.group(3).strip()

    if ret_ty not in TYPE_MAP:
        raise SyntaxError(f"unknown return type: {ret_ty}")
    py_ret = TYPE_MAP[ret_ty]
    if py_ret == "Any":
        need_any["need_any"] = True

    # parse params: "a: inte, b: inte" or "*args: filum"
    py_params: list[str] = []
    if params_raw:
        parts = split_top_level_commas(params_raw)
        for p in parts:
            p = p.strip()
            pm = re.fullmatch(rf"(\*?{IDENT})\s*:\s*({IDENT})", p)
            if not pm:
                raise SyntaxError(f"invalid param: {p}")
            pname = pm.group(1)
            pty = pm.group(2).lower()
            if pty not in TYPE_MAP:
                raise SyntaxError(f"unknown param type: {pty}")
            py_ty = TYPE_MAP[pty]
            if py_ty == "Any":
                need_any["need_any"] = True
            if py_ty == "None":
                # param None型は変なのでAnyへ（v0保険）
                need_any["need_any"] = True
                py_ty = "Any"
            py_params.append(f"{pname}: {py_ty}")

    # collect block body lines until matching }
    body_lines, next_i = collect_block(lines, i)

    # reditus だけ先に python の return に置換してから、まとめて再帰パース
    normalized_body = []
    for bl in body_lines:
        bl = bl.strip()
        if not bl or bl.startswith("///"):
            continue
        rm = re.fullmatch(r"REDITUS\s+(.+)\s*;\s*", bl)
        if rm:
            expr = rm.group(1).strip()
            expr = normalize_expr(expr)  # もし normalize_expr を入れてるなら
            normalized_body.append(f"__ARCANA_RETURN__ {expr};")
        else:
            normalized_body.append(bl)

    py_body = []
    for bl in normalized_body:
        mret = re.fullmatch(r"__ARCANA_RETURN__\s+(.+)\s*;\s*", bl)
        if mret:
            py_body.append(f"return {mret.group(1)}")
        else:
            # ここは通常の stmt として再帰処理させたいので、一旦 list に入れる
            py_body.extend(transpile_stmts([bl], need_any))

    if not py_body:
        py_body = ["pass"]


    py = [f"def {name}({', '.join(py_params)}) -> {py_ret}:"]
    py.extend(indent(py_body))
    return (py, next_i)


def transpile_REPETITIO(lines: list[str], i: int, need_any: dict) -> tuple[list[str], int]:
    header = lines[i].strip()
    # REPETITIO (prima: i=1, conditio: i<10, gradu: +1) {
    m = re.fullmatch(r"REPETITIO\s*\(\s*(.+)\s*\)\s*\{\s*", header)
    if not m:
        raise SyntaxError(f"invalid REPETITIO header: {header}")

    inside = m.group(1).strip()
    items = split_top_level_commas(inside)

    prima = None
    conditio = None
    gradu = None
    varname = None

    for it in items:
        it = it.strip()
        if it.startswith("prima:"):
            val = it.split("prima:", 1)[1].strip()
            # i=1
            mm = re.fullmatch(rf"({IDENT})\s*=\s*(.+)", val)
            if not mm:
                raise SyntaxError("prima must be like i=1")
            varname = mm.group(1)
            prima = mm.group(2).strip()
        elif it.startswith("conditio:"):
            conditio = it.split("conditio:", 1)[1].strip()
        elif it.startswith("gradu:"):
            gradu = it.split("gradu:", 1)[1].strip()
        else:
            raise SyntaxError(f"unknown REPETITIO part: {it}")

    if varname is None or prima is None or conditio is None or gradu is None:
        raise SyntaxError("REPETITIO requires prima, conditio, gradu")

    prima = transpile_cantus_in_expr(normalize_expr(prima))
    conditio = transpile_cantus_in_expr(normalize_expr(conditio))

    # gradu: +1 / -2
    gm = re.fullmatch(r"([+-])\s*(\d+)", gradu)
    if not gm:
        raise SyntaxError("gradu must be like +1 or -2 (v0)")
    sign = gm.group(1)
    step = int(gm.group(2))
    if step == 0:
        raise SyntaxError("gradu step must be non-zero")
    op = "+=" if sign == "+" else "-="

    body_lines, next_i = collect_block(lines, i)

    # ネスト対応: ブロック全体を再帰的に解析
    py_body = transpile_stmts(body_lines, need_any)

    # increment at end
    py_body.append(f"{varname} {op} {step}")

    py = [
        f"{varname} = {prima}",
        f"while {conditio}:",
        *indent(py_body),
    ]
    return (py, next_i)


def transpile_SI(lines: list[str], i: int, need_any: dict) -> tuple[list[str], int]:
    header = lines[i].strip()
    # SI conditio: (1==1){
    m = re.fullmatch(r"SI\s+conditio:\s*\((.+)\)\s*\{\s*", header)
    if not m:
        raise SyntaxError(f"invalid SI header: {header}")

    cond = m.group(1).strip()
    cond = transpile_cantus_in_expr(normalize_expr(cond))

    # collect inside SI { ... } until matching }
    SI_body_lines, next_i = collect_block(lines, i)

    # Inside should contain:
    # VERUM{ ... }
    # FALSUM{ ... }
    # We'll parse them by scanning lines list with miniature block collectors.
    # We'll reconstruct a faux-lines list with braces for the collector to work:
    faux = []
    for bl in SI_body_lines:
        faux.append(bl)

    # The collector expects real braces in the same line. Our collect_block stripped braces.
    # So we implement a simple parser for VERUM{ ... } FALSUM{ ... } in the original lines instead.
    # We'll re-parse from original lines starting at i+1 until end of SI.
    # Easiest: find VERUM{ and FALSUM{ blocks within the original stream between i and next_i.
    segment = [ln.strip() for ln in lines[i:next_i]]

    def find_block(keyword: str) -> list[str]:
        # find line that starts with keyword{
        for idx, ln in enumerate(segment):
            if re.fullmatch(rf"{keyword}\s*\{{\s*", ln) or ln.startswith(f"{keyword}{{"):
                # build a temporary lines list from that point and use collect_block
                # ensure the line has '{'
                tmp = segment[idx:]
                # Need to map back to original 'lines' with braces; we can collect from original using index offset
                orig_start = i + idx
                body, _ = collect_block(lines, orig_start)
                return body
        return []

    VERUM_body = find_block("VERUM")
    FALSUM_body = find_block("FALSUM")

    if not VERUM_body and not FALSUM_body:
        raise SyntaxError("SI block must contain VERUM{...} and/or FALSUM{...}")

    def transpile_body(body: list[str]) -> list[str]:
        out: list[str] = []
        for bl in body:
            bl = bl.strip()
            if not bl or bl.startswith("///"):
                continue
            mini_py, _ = transpile_stmt([bl], 0, need_any)
            out.extend(mini_py)
        if not out:
            out = ["pass"]
        return out

    py_VERUM = transpile_body(VERUM_body) if VERUM_body else ["pass"]
    py_FALSUM = transpile_body(FALSUM_body) if FALSUM_body else ["pass"]

    py = [f"if {cond}:"]
    py.extend(indent(py_VERUM))
    py.append("else:")
    py.extend(indent(py_FALSUM))
    return (py, next_i)

def transpile_flow_expr(expr: str) -> str:
    """
    Arcana expression that may contain a flow call:
      potentia() <- (a, b)   -> potentia(a, b)
      indicant() <- x        -> print(x)   (式としては副作用だが、v0では許容)
    If not flow, returns expr (after cantus/const handling is done outside or inside).
    """
    expr = expr.strip()

    m = re.fullmatch(rf"({IDENT})\s*\(\s*\)\s*<-\s*(.+)", expr)
    if not m:
        return expr

    fname = m.group(1)
    rhs = m.group(2).strip()

    py_name = BUILTIN_MAP.get(fname, fname)

    rhs = normalize_expr(rhs)
    rhs = transpile_cantus_in_expr(rhs)

    if rhs.startswith("(") and rhs.endswith(")"):
        inner = rhs[1:-1].strip()
        if not inner:
            return f"{py_name}()"
        parts = split_top_level_commas(inner)
        return f"{py_name}({', '.join(parts)})"

    return f"{py_name}({rhs})"


def transpile(source: str) -> str:
    raw_lines = source.splitlines()

    need_any = {"need_any": False}
    out: list[str] = []

    i = 0
    while i < len(raw_lines):
        tr(f"top i={i}: {raw_lines[i].rstrip()}")
        py_lines, i = transpile_stmt(raw_lines, i, need_any)
        out.extend(py_lines)

    if need_any["need_any"]:
        out.insert(0, "from typing import Any")

    return "\n".join(out) + "\n"


def run_file(path: str, emit: bool=False, no_run: bool=False) -> None:
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    py_code = transpile(src)

    if emit:
        print("=== [arcana emit] transpiled python ===")
        print(py_code)
        print("=== [arcana emit] end ===")
    if no_run:
        return
    

    # Minimal execution environment
    env: dict[str, Any] = {}
    exec(py_code, env, env)


def main() -> None:
    ap = argparse.ArgumentParser(prog="arcana")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("exsecutio", help="run .arkhe source")
    p_run.add_argument("file", help="e.g. main.arkhe")
    p_run.add_argument("--emit", action="store_true", help="print transpiled python code")
    p_run.add_argument("--no-run", action="store_true", help="emit only, do not execute")
    p_run.add_argument("--trace", action="store_true", help="print parser/transpiler trace")



    args = ap.parse_args()
    if args.cmd == "exsecutio":
        global TRACE
        global TRACE_INDENT
        TRACE = args.trace
        run_file(args.file, emit=args.emit, no_run=args.no_run)


if __name__ == "__main__":
    main()