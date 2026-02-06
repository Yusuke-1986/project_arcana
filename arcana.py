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

# ========================
# Tokenizer
# ========================

@dataclass
class Token:
    kind: str
    value: str

KEYWORDS = {"FCON", "VCON", "SI", "VERUM", "FALSUM"}
TYPE_NAMES = {"nihil", "inte", "real", "filum"}

TOKEN_SPEC = [
    ("FLOW", r"<-"),
    ("ARROW", r"->"),

    ("NE", r"><"),
    ("GE", r">="),
    ("LE", r"<="),
    ("EQ", r"=="),

    ("POW", r"\*\*"),

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
        self.eat("TYPE")  # nihil
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
        # VCON
        if self.match("KW","VCON"):
            self.eat("KW","VCON")
            name=self.eat("IDENT").value
            self.eat("COLON")
            self.eat("TYPE")
            self.eat("ASSIGN")
            expr=self.parse_expr()
            self.eat("SEMICOLON")
            return VarDecl(name,expr)

        # assign
        if self.match("IDENT") and self.toks[self.i+1].kind=="ASSIGN":
            name=self.eat("IDENT").value
            self.eat("ASSIGN")
            expr=self.parse_expr()
            self.eat("SEMICOLON")
            return Assign(name,expr)

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

    # ----- expression (Pratt, stable) -----
    def parse_expr(self, min_bp: int = 0):
        PRECEDENCE = {
        "**": 70,                 # right-assoc
        "*": 60, "/": 60, "%": 60,
        "+": 50, "-": 50,
        "==": 40, "><": 40, ">": 40, "<": 40, ">=": 40, "<=": 40,
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
            "LE": "<=",
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

        else:
            raise SyntaxError(f"Bad expression (prefix) at token={t}")

        # infix
        while True:
            t = self.cur()
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
            left = Binary(op, left, right)

        return left


# ========================
# Transpile
# ========================

BUILTINS={"indicant":"print","incant":"print"}

def emit_expr(e):

    if isinstance(e,Num):
        return e.value

    if isinstance(e,Str):
        return e.value

    if isinstance(e,Id):
        return BUILTINS.get(e.name,e.name)

    if isinstance(e,Binary):
        return f"({emit_expr(e.left)} {e.op} {emit_expr(e.right)})"
    
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

def emit_stmt(s,indent=0):

    pad=" "*indent

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

    raise NotImplementedError(s)


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
        toks = tokenize(src)
        tr(f"TOKENS: {[(t.kind, t.value) for t in toks]}")
        ast = Parser(toks).parse()
        tr(f"PARSE: {ast}")
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
        import traceback
        print("[arcana] ERROR:", e)
        traceback.print_exc()

def main() -> None:
    ap = argparse.ArgumentParser(prog="arcana")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("exsecutio", help="run .arkhe source")
    p_run.add_argument("file", help="e.g. main.arkhe")
    p_run.add_argument("--emit", action="store_true", help="print transpiled python code")
    p_run.add_argument("--no-run", action="store_true", help="emit only, do not execute")
    p_run.add_argument("--trace", action="store_true", help="print parser/transpiler trace")
    p_run.add_argument("--version", action="store_true", help="current transpiler version")

    args = ap.parse_args()
    
    print(f"arcana: python transpiler ver v.{VERSION}")
    
    if args.cmd == "exsecutio": # exsecutioあれば実行
        global TRACE
        TRACE = args.trace
        run_file(args.file, emit=args.emit, no_run=args.no_run)


if __name__ == "__main__":
    main()