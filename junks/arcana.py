# arcana.py　ver.0.15
# Arcana minimal runner + calculations
import argparse
from dataclasses import dataclass
from typing import List, Optional, Any
import sys
import re

VERSION = 0.15

# --- tracing ---
TRACE = False

def tr(msg: str) -> None:
    if TRACE:
        print(f"[arcana: trace]> {msg}")


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


# ========================
# Tokenizer
# ========================

@dataclass
class Token:
    kind: str
    value: str

KEYWORDS = {
    "FCON", "VCON", 
    "SI", "VERUM", "FALSUM", 
    "RECURSIO", "effigum", "proximum",
    "et", "aut", "non", "nihil"}
TYPE_NAMES = {"inte", "real", "verum", "filum"}
SPECIAL_KEY = {"nihil"}

TOKEN_SPEC = [
    ("FLOW", r"<-"),
    ("ARROW", r"->"),

    ("NE", r"><"),
    ("GE", r">="),
    ("LE", r"<="),
    ("EQ", r"=="),

    ("POW", r"\*\*"),

    ("INCR", r"\+\+"),
    ("DECR", r"--"),
    ("PLUSEQ", r"\+="),
    ("MINUSEQ", r"-="),

    ("GT", r">"),
    ("LT", r"<"),

    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("STAR", r"\*"),
    ("SLASH", r"/"),
    ("PERCENT", r"%"),

    ("ASSIGN", r"="),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("COLON", r":"),
    ("COMMA", r","),  
    ("SEMICOLON", r";"),

    ("REAL", r"\d+\.\d+"),
    ("INT", r"\d+"),

    ("STRING", r'"[^"]*"|\'[^\']*\''),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("SKIP", r"[ \t\n]+"),
]


MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n,p in TOKEN_SPEC))

def tokenize(src: str):
    tokens=[]
    for m in MASTER.finditer(src):
        kind=m.lastgroup
        val=m.group()
        if kind=="SKIP":
            continue
        if kind == "IDENT":
            if val in KEYWORDS:
                kind = "KW"
            elif val in TYPE_NAMES:
                kind = "TYPE"
            elif val == "cantus":
                kind = "CANTUS"
        tokens.append(Token(kind,val))
    tokens.append(Token("EOF",""))
    return tokens


# ========================
# AST
# ========================

@dataclass
class Expr: pass

@dataclass
class Num(Expr):
    value:str

@dataclass
class Str(Expr):
    value:str

@dataclass
class Id(Expr):
    name:str

@dataclass
class Binary(Expr):
    op:str
    left:Expr
    right:Expr

@dataclass
class CallEmpty(Expr):
    name:str

@dataclass
class FlowCall(Expr):
    call:CallEmpty
    arg:Expr

@dataclass
class Stmt: pass

@dataclass
class VarDecl(Stmt):
    name:str
    type_name: str
    expr:Expr

@dataclass
class Assign(Stmt):
    name:str
    expr:Expr

@dataclass
class ExprStmt(Stmt):
    expr:Expr

@dataclass
class FuncDecl(Stmt):
    name:str
    body:list

@dataclass
class Cantus(Expr):
    raw: str  # 例: 'a=${a}'

@dataclass
class Compare(Expr):
    op: str
    left: Expr
    right: Expr

@dataclass
class IfStmt(Stmt):
    cond: Expr
    then_body: list
    else_body: list

@dataclass
class GraduOpe:
    op: str          # "++" | "--" | "+=" | "-="
    value: int = 1   # ++/-- は 1、+=/-= は指定値

@dataclass
class RecurStmt(Stmt):
    prima: Expr      # まずは Expr にしておく（INTだけでもOK）
    propositio: Expr
    gradu: GraduOpe
    body: list

@dataclass
class BreakStmt(Stmt):
    pass

@dataclass
class ContinueStmt(Stmt):
    pass

@dataclass
class Unary(Expr):
    op: str
    expr: Expr

@dataclass
class Through(Stmt):
    pass


# ========================
# Parser (minimal Pratt)
# ========================

class Parser:
    def __init__(self,toks):
        self.toks=toks
        self.i=0

    def cur(self):
        return self.toks[self.i]

    def eat(self,kind,val=None):
        t=self.cur()
        if t.kind!=kind or (val and t.value!=val):
            raise SyntaxError(f"Unexpected token {t}")
        self.i+=1
        return t

    def match(self,kind,val=None):
        t=self.cur()
        if t.kind!=kind:
            return False
        if val and t.value!=val:
            return False
        return True

    # ----- program -----

    def parse(self):
        body=[]
        while not self.match("EOF"):
            if self.match("KW","FCON"):
                body.append(self.parse_func())
            else:
                self.i+=1
        return body

    def parse_func(self):
        # FCON IDENT: type () -> { の判定
        self.eat("KW","FCON")
        name=self.eat("IDENT").value
        self.eat("COLON")
        t = self.cur()
        if t.kind == "TYPE":
            self.i += 1
        elif t.kind == "KW" and t.value == "nihil":
            self.i += 1
        else:
            raise SyntaxError("Expected return type")
        self.eat("LPAREN")
        self.eat("RPAREN")
        self.eat("ARROW")
        self.eat("LBRACE")

        stmts=[]
        # }閉じてない場合
        while not self.match("RBRACE"):
            stmts.append(self.parse_stmt())

        # };でちゃんと閉じたか
        self.eat("RBRACE")
        if self.match("SEMICOLON"):
            self.eat("SEMICOLON")

        return FuncDecl(name,stmts)

    def parse_stmt(self):
        # nihil;
        if self.match("KW", "nihil"):
            self.eat("KW", "nihil")
            self.eat("SEMICOLON")
            return Through()
        
        # VCON
        if self.match("KW","VCON"):
            self.eat("KW","VCON")
            name=self.eat("IDENT").value
            self.eat("COLON")
            # self.eat("TYPE")
            t = self.cur()
            if t.kind not in ("TYPE", "KW"):
                raise SyntaxError("Expected type name")
            type_name = t.value
            self.i += 1
            self.eat("ASSIGN")
            expr=self.parse_expr()
            self.eat("SEMICOLON")
            return VarDecl(name,type_name, expr)
        
        if self.match("KW","effigum"):
            self.eat("KW","effigum")
            self.eat("SEMICOLON")
            return BreakStmt()

        if self.match("KW","proximum"):
            self.eat("KW","proximum")
            self.eat("SEMICOLON")
            return ContinueStmt()

        # assign
        if self.match("IDENT") and self.toks[self.i+1].kind in ("ASSIGN","PLUSEQ","MINUSEQ"):
            name=self.eat("IDENT").value
            op=self.cur().kind
            self.i+=1
            expr=self.parse_expr()
            self.eat("SEMICOLON")

            if op=="ASSIGN":
                return Assign(name,expr)
            if op=="PLUSEQ":
                return Assign(name, Binary("+", Id(name), expr))
            if op=="MINUSEQ":
                return Assign(name, Binary("-", Id(name), expr))

        if self.match("KW","SI"):
            self.eat("KW","SI")
            self.eat("IDENT","propositio")  # 固定語
            self.eat("COLON")
            self.eat("LPAREN")
            cond = self.parse_expr()
            self.eat("RPAREN")
            self.eat("LBRACE")

            self.eat("KW","VERUM")
            self.eat("LBRACE")
            then_body=[]
            while not self.match("RBRACE"):
                then_body.append(self.parse_stmt())
            self.eat("RBRACE")

            self.eat("KW","FALSUM")
            self.eat("LBRACE")
            else_body=[]
            while not self.match("RBRACE"):
                else_body.append(self.parse_stmt())
            self.eat("RBRACE")

            self.eat("RBRACE")
            self.eat("SEMICOLON")
            return IfStmt(cond, then_body, else_body)
        
        if self.match("KW","RECURSIO"):
            self.eat("KW","RECURSIO")
            self.eat("LPAREN")

            # defaults
            prima = Num("100")              # デフォルト上限
            propositio = Num("1")             # 1==True扱い（簡易）
            gradu = GraduOpe("++", 1)

            # header: prima / propositio / gradu (order-free)
            while not self.match("RPAREN"):
                key = self.eat("IDENT").value   # "prima" | "propositio" | "gradu"
                self.eat("COLON")

                if key == "prima":
                    prima = self.parse_expr()
                elif key == "propositio":
                    propositio = self.parse_expr()
                    if self.contains_call(propositio):
                        raise SyntaxError("RECURSIO propositio: function call is not allowed")

                elif key == "gradu":
                    gradu = self.parse_gradu_ope()
                else:
                    raise SyntaxError(f"Unknown RECURSIO header key: {key}")

                if self.match("COMMA"):
                    self.eat("COMMA")

            self.eat("RPAREN")
            self.eat("LBRACE")

            body=[]
            while not self.match("RBRACE"):
                body.append(self.parse_stmt())

            self.eat("RBRACE")
            self.eat("SEMICOLON")
            return RecurStmt(prima, propositio, gradu, body)

        # flowcall
        call=self.parse_call_empty()
        self.eat("FLOW")

        arg=self.parse_expr()
        self.eat("SEMICOLON")
        return ExprStmt(FlowCall(call,arg))
    
    def parse_call_empty(self):
        name=self.eat("IDENT").value
        self.eat("LPAREN")
        self.eat("RPAREN")
        return CallEmpty(name)
    
    def parse_gradu_ope(self) -> GraduOpe:
        t = self.cur()
        if t.kind == "INCR":
            self.i += 1
            return GraduOpe("++", 1)
        if t.kind == "DECR":
            self.i += 1
            return GraduOpe("--", 1)
        if t.kind == "PLUSEQ":
            self.i += 1
            n = int(self.eat("INT").value)
            return GraduOpe("+=", n)
        if t.kind == "MINUSEQ":
            self.i += 1
            n = int(self.eat("INT").value)
            return GraduOpe("-=", n)
        raise SyntaxError(f"Bad gradu ope token={t}")

    def contains_call(self, expr):
        if isinstance(expr, CallEmpty):
            return True

        if isinstance(expr, Binary):
            return self.contains_call(expr.left) or self.contains_call(expr.right)

        if isinstance(expr, Compare):
            return self.contains_call(expr.left) or self.contains_call(expr.right)

        return False

    # ----- expression (Pratt, stable) -----
    def parse_expr(self, min_bp: int = 0):
        PRECEDENCE = {
        "**": 70,                 # right-assoc
        "*": 60, "/": 60, "%": 60,
        "+": 50, "-": 50,
        "==": 40, "><": 40, ">": 40, "<": 40, ">=": 40, "<=": 40,
        "et": 30, "aut": 20,
        }

        OP_MAP = {
            "PLUS": "+",
            "MINUS": "-",
            "STAR": "*",
            "SLASH": "/",
            "PERCENT": "%",
            "POW": "**",
            "EQ": "==",
            "NE": "><",
            "GT": ">",
            "LT": "<",
            "GE": ">=",
            "LE": "<="
        }
        t = self.cur()

        # prefix
        if t.kind in ("INT", "REAL"):
            self.i += 1
            left = Num(t.value)

        elif t.kind == "STRING":
            self.i += 1
            left = Str(t.value)

        elif t.kind == "IDENT":
            self.i += 1
            left = Id(t.value)

        elif t.kind == "CANTUS":
            self.i += 1
            s = self.eat("STRING").value
            left = Cantus(s)

        elif t.kind == "LPAREN":
            self.eat("LPAREN")
            left = self.parse_expr(0)
            self.eat("RPAREN")

        elif t.kind == "KW" and t.value == "non":
            self.i += 1
            inner = self.parse_expr(65)   # non の優先度(適当に強め)
            left = Unary("non", inner)

        else:
            raise SyntaxError(f"Bad expression (prefix) at token={t}")

        # infix
        while True:
            t = self.cur()

            # KW infix: et / aut
            if t.kind == "KW" and t.value in ("et", "aut"):
                op = t.value
                prec = PRECEDENCE[op]
                if prec < min_bp:
                    break
                self.i += 1
                right = self.parse_expr(prec + 1)
                left = Binary(op, left, right)
                continue

            if t.kind not in OP_MAP:
                break

            op = OP_MAP[t.kind]
            prec = PRECEDENCE[op]
            if prec < min_bp:
                break

            # consume operator
            self.i += 1

            # binding power:
            # right-assoc only for **
            next_min_bp = prec if op == "**" else prec + 1

            right = self.parse_expr(next_min_bp)
            if op in ("==", "><", ">", "<", ">=", "<="):
                left = Compare(op, left, right)
            else:
                left = Binary(op, left, right)

            

        return left

# ========================
# Transpile
# ========================

BUILTINS={"indicant":"print"}

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

def emit_gradu_update(g: GraduOpe) -> str:
    if g.op == "++":
        return "__i += 1"
    if g.op == "--":
        return "__i -= 1"
    if g.op == "+=":
        return f"__i += {g.value}"
    if g.op == "-=":
        return f"__i -= {g.value}"
    raise ValueError(g)

def emit_stmt(s,indent=0):

    pad=" "*indent

    if isinstance(s, Through):
        return [pad + "pass"]

    if isinstance(s,FuncDecl):
        lines=[f"{pad}def {s.name}():"]
        for st in s.body:
            lines+=emit_stmt(st,indent+4)
        return lines+[""]

    if isinstance(s,VarDecl):
        return [f"{pad}{s.name} = {emit_expr(s.expr)}"]

    if isinstance(s,Assign):
        return [f"{pad}{s.name} = {emit_expr(s.expr)}"]

    if isinstance(s,ExprStmt) and isinstance(s.expr,FlowCall):
        fn=BUILTINS.get(s.expr.call.name,s.expr.call.name)
        return [f"{pad}{fn}({emit_expr(s.expr.arg)})"]
    
    if isinstance(s, IfStmt):
        lines=[f"{pad}if {emit_expr(s.cond)}:"]
        for st in s.then_body:
            lines += emit_stmt(st, indent+4)
        lines.append(f"{pad}else:")
        for st in s.else_body:
            lines += emit_stmt(st, indent+4)
        return lines
    
    if isinstance(s, RecurStmt):
        lines = []
        lines.append(f"{pad}__i = 0")
        lines.append(f"{pad}__prima = {emit_expr(s.prima)}")
        lines.append(f"{pad}while ({emit_expr(s.propositio)}) and (__i < __prima):")
        for st in s.body:
            lines += emit_stmt(st, indent+4)
        lines.append(f"{pad}    {emit_gradu_update(s.gradu)}")
        return lines
    
    if isinstance(s, BreakStmt):
        return [pad + "break"]

    if isinstance(s, ContinueStmt):
        return [pad + "continue"]


    raise NotImplementedError(s)

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
    out=["# transpiled Arcana\n"]
    for st in ast:
        out+=emit_stmt(st)
        tr(f"{st} -- transpile --> {out}")
    out.append("if __name__==\"__main__\":")
    out.append("    subjecto()")
    return "\n".join(out)


# ========================
# Runner
# ========================

def run_file(path: str, emit: bool=False, no_run: bool=False) -> None:
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    try:
        src = strip_line_comments(src)
        toks = tokenize(src)
        tr(f"TOKENS: {[(t.kind, t.value) for t in toks]}")
        ast = Parser(toks).parse()
        tr(f"PARSE: {ast}")
        validate_recur_guard(ast)
        validate_types(ast)
        py = transpile(ast)
        
        if emit:
            print("=== [arcana emit] transpiled python ===")
            print(py)
            print("=== [arcana emit] end ===")
        if no_run:
            return
        
        # Minimal execution environment
        print("=== [arcana: oraculum] ===")
        env = {"__name__": "__main__"}
        exec(compile(py, "<arcana>", "exec"), env, env)

    except Exception as e:
        if PYTRACE:
            import traceback
            print("[arcana] ERROR:", e)
            traceback.print_exc()
        else:
            print("[arcana] ERROR:", e)

def main() -> None:
    ap = argparse.ArgumentParser(prog="arcana")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("exsecutio", help="run .arkhe source")
    p_run.add_argument("file", help="e.g. main.arkhe")
    p_run.add_argument("--emit", action="store_true", help="print transpiled python code")
    p_run.add_argument("--no-run", action="store_true", help="emit only, do not execute")
    p_run.add_argument("--trace", action="store_true", help="print parser/transpiler trace")
    p_run.add_argument("--no-pytrace", action="store_false", help="do not print python traceback")

    args = ap.parse_args()
    print(args)
    
    print(f"arcana: python transpiler ver v.{VERSION}")
    
    if args.cmd == "exsecutio": # exsecutioあれば実行
        global TRACE
        TRACE = args.trace
        global PYTRACE
        PYTRACE = args.no_pytrace
        run_file(args.file, emit=args.emit, no_run=args.no_run)


if __name__ == "__main__":
    main()