# arcana.py
from __future__ import annotations

import argparse
import re
from typing import Any
from dataclasses import dataclass

@dataclass
class ScanState:
    in_single: bool = False
    in_double: bool = False
    escaped: bool = False

def scan_braces_and_update_state(raw: str, state: ScanState) -> tuple[int, ScanState]:
    delta = 0
    k = 0
    while k < len(raw):
        ch = raw[k]

        if state.escaped:
            state.escaped = False
            k += 1
            continue
        if ch == "\\":
            state.escaped = True
            k += 1
            continue
        if ch == "'" and not state.in_double:
            state.in_single = not state.in_single
            k += 1
            continue
        if ch == '"' and not state.in_single:
            state.in_double = not state.in_double
            k += 1
            continue

        if not state.in_single and not state.in_double:
            if ch == "{":
                delta += 1
            elif ch == "}":
                delta -= 1

        k += 1

    # 行末で escaped を持ち越すと事故りやすいので、ここで落としてもいい（好み）
    state.escaped = False
    return delta, state


MAX_NESTING_DEPTH = 3  # Arcana block nesting limit


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
    """Convert Arcana cantus string literals into Python f-strings inside an expression.

    - Transforms: cantus'${x} ...'  -> f'{x} ...'
                 cantus"${x}"     -> f"{x}"
    - Works when cantus literal appears inside larger expressions.
    - Only transforms 'cantus' occurrences that appear outside of existing string literals.
    """
    out: list[str] = []
    i = 0
    n = len(expr)

    in_single = False
    in_double = False
    escaped = False

    def is_ident_char(c: str) -> bool:
        return c.isalnum() or c == "_"

    def starts_ident_at(pos: int, word: str) -> bool:
        if not expr.startswith(word, pos):
            return False
        before = expr[pos - 1] if pos > 0 else ""
        after_pos = pos + len(word)
        after = expr[after_pos] if after_pos < n else ""
        if before and is_ident_char(before):
            return False
        if after and is_ident_char(after):
            return False
        return True

    def read_string_literal(pos: int) -> tuple[str, int]:
        """Read a quoted string starting at pos (quote char at pos)."""
        quote = expr[pos]
        j = pos + 1
        buf: list[str] = []
        esc = False
        while j < n:
            ch = expr[j]
            if esc:
                buf.append(ch)
                esc = False
                j += 1
                continue
            if ch == "\\":  # escape
                buf.append(ch)
                esc = True
                j += 1
                continue
            if ch == quote:
                return (quote + "".join(buf) + quote, j + 1)
            buf.append(ch)
            j += 1
        return (expr[pos:], n)

    def transform_dollar_braces(quoted: str) -> str:
        """Inside a quoted string, convert ${...} -> {...} (simple, non-nested)."""
        if len(quoted) < 2:
            return quoted
        quote = quoted[0]
        inner = quoted[1:-1]
        inner = re.sub(r"\$\{([^}]+)\}", r"{\1}", inner)
        return quote + inner + quote

    while i < n:
        ch = expr[i]

        if escaped:
            out.append(ch)
            escaped = False
            i += 1
            continue

        if ch == "\\":  # escape
            out.append(ch)
            escaped = True
            i += 1
            continue

        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
            i += 1
            continue

        if not in_single and not in_double and starts_ident_at(i, "cantus"):
            j = i + len("cantus")
            while j < n and expr[j].isspace():
                j += 1
            if j < n and expr[j] in ("'", '"'):
                lit, k = read_string_literal(j)
                lit2 = transform_dollar_braces(lit)
                out.append("f")
                out.append(lit2)
                i = k
                continue

        out.append(ch)
        i += 1

    return "".join(out)


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

def transpile_stmts(block_lines: list[str], need_any: dict, depth: int = 0) -> list[str]:
    """
    Parse a list of Arcana lines (already extracted from a { ... } block body),
    allowing nested blocks like si/repetitio/minst inside.
    """
    out: list[str] = []
    i = 0
    while i < len(block_lines):
        py, i2 = transpile_stmt(block_lines, i, need_any, depth)
        out.extend(py)
        i = i2
    return out


# --- statement transpilers ---
def transpile_stmt(lines: list[str], i: int, need_any: dict, depth: int = 0) -> tuple[list[str], int]:
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

        # nihil is return-only in Arcana
        if ty == "nihil" or py_ty == "None":
            raise SyntaxError("nihil is return-only and cannot be used as a variable type")

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
        if depth + 1 > MAX_NESTING_DEPTH:
            raise SyntaxError(
                f"Nesting too deep: depth {depth + 1} exceeds MAX_NESTING_DEPTH={MAX_NESTING_DEPTH}. "
                "Arcana supports up to 3 nested blocks; refactor into separate functions/modules."
            )
        py_lines, next_i = transpile_MINST(lines, i, need_any, depth + 1)
        return (py_lines, next_i)

    # loop: REPETITIO (...) { ... };
    if line.startswith("REPETITIO "):
        tr(f"match REPETITIO line={line}")
        if depth + 1 > MAX_NESTING_DEPTH:
            raise SyntaxError(
                f"Nesting too deep: depth {depth + 1} exceeds MAX_NESTING_DEPTH={MAX_NESTING_DEPTH}. "
                "Arcana supports up to 3 nested blocks; refactor into separate functions/modules."
            )
        py_lines, next_i = transpile_REPETITIO(lines, i, need_any, depth + 1)
        return (py_lines, next_i)

    # if: SI conditio: (expr){ VERUM{...} FALSUM{...} };
    if line.startswith("SI "):
        tr(f"match SI line={line}")
        if depth + 1 > MAX_NESTING_DEPTH:
            raise SyntaxError(
                f"Nesting too deep: depth {depth + 1} exceeds MAX_NESTING_DEPTH={MAX_NESTING_DEPTH}. "
                "Arcana supports up to 3 nested blocks; refactor into separate functions/modules."
            )
        py_lines, next_i = transpile_SI(lines, i, need_any, depth + 1)
        return (py_lines, next_i)

    raise SyntaxError(f"unsupported syntax: {line}")


def collect_block(lines: list[str], start_i: int, nesting_depth: int) -> tuple[list[str], int]:
    if "{" not in lines[start_i]:
        raise SyntaxError("block must start with '{'")

    body: list[str] = []

    state = ScanState()

    # start_i 行で開始ブレースを確定
    raw0 = strip_inline_comment(lines[start_i])
    d0, state = scan_braces_and_update_state(raw0, state)
    if d0 <= 0:
        raise SyntaxError("block must start with '{' (unbalanced start line)")
    brace_depth = d0

    i = start_i + 1
    while i < len(lines):
        raw = strip_inline_comment(lines[i])
        stripped = raw.strip()

        d, state = scan_braces_and_update_state(raw, state)
        brace_depth += d

        if brace_depth == 0:
            i += 1
            if i < len(lines) and strip_inline_comment(lines[i]).strip() == ";":
                i += 1
            return (body, i)

        if stripped != "":
            body.append(stripped)

        i += 1

    raise SyntaxError(f"unterminated block at start_i={start_i}, last_i={i}, brace_depth={brace_depth}")


def transpile_MINST(lines: list[str], i: int, need_any: dict, depth: int = 0) -> tuple[list[str], int]:
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
    body_lines, next_i = collect_block(lines, i, depth)

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
            py_body.extend(transpile_stmts([bl], need_any, depth))

    if not py_body:
        py_body = ["pass"]


    py = [f"def {name}({', '.join(py_params)}) -> {py_ret}:"]
    py.extend(indent(py_body))
    return (py, next_i)


def transpile_REPETITIO(lines: list[str], i: int, need_any: dict, depth: int = 0) -> tuple[list[str], int]:
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

    body_lines, next_i = collect_block(lines, i, depth)

    # ネスト対応: ブロック全体を再帰的に解析
    py_body = transpile_stmts(body_lines, need_any, depth)

    # increment at end
    py_body.append(f"{varname} {op} {step}")

    py = [
        f"{varname} = {prima}",
        f"while {conditio}:",
        *indent(py_body),
    ]
    return (py, next_i)


def transpile_SI(lines: list[str], i: int, need_any: dict, depth: int = 0) -> tuple[list[str], int]:
    header = lines[i].strip()
    m = re.fullmatch(r"SI\s+conditio:\s*\((.+)\)\s*\{\s*", header)
    if not m:
        raise SyntaxError(f"invalid SI header: {header}")

    cond = transpile_cantus_in_expr(normalize_expr(m.group(1).strip()))

    # collect inside SI { ... }
    _, next_i = collect_block(lines, i, depth)

    segment = [ln.strip() for ln in lines[i:next_i]]

    def find_block(keyword: str) -> list[str]:
        for idx, ln in enumerate(segment):
            if re.fullmatch(rf"{keyword}\s*\{{\s*", ln) or ln.startswith(f"{keyword}{{") or ln.startswith(f"{keyword} {{"):
                orig_start = i + idx
                # VERUM/FALSUM は SI の「枝」なのでネスト段数を増やさない
                body, _ = collect_block(lines, orig_start, depth) 
                return body
        return []

    VERUM_body = find_block("VERUM")
    FALSUM_body = find_block("FALSUM")

    if not VERUM_body and not FALSUM_body:
        raise SyntaxError("SI block must contain VERUM{...} and/or FALSUM{...}")

    # ★ ここが重要：1行ずつ transpile_stmt しない。まとめて transpile_stmts する
    py_VERUM = transpile_stmts(VERUM_body, need_any, depth) if VERUM_body else ["pass"]
    py_FALSUM = transpile_stmts(FALSUM_body, need_any, depth) if FALSUM_body else ["pass"]

    if not py_VERUM:
        py_VERUM = ["pass"]
    if not py_FALSUM:
        py_FALSUM = ["pass"]

    py = [f"if {cond}:"]
    py.extend(indent(py_VERUM))
    py.append("else:")
    py.extend(indent(py_FALSUM))
    return (py, next_i)


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