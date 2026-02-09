# parser.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .ast import (
    Program, FonsSection, IntroSection, DoctrinaSection, MainFunction,
    ImportStmt,
    Stmt, VarDecl, Assign, Move, CallStmt, ExprStmt,
    NihilStmt, BreakStmt, ContinueStmt,
    IfStmt, LoopStmt,
    Expr, Name, IntLit, RealLit, StringLit, UnaryOp, BinaryOp, CallExpr, Span,Paren
)

from .error import parse_error, ErrorCode

@dataclass
class Tok:
    kind: str
    value: str


class Parser:
    def __init__(self, toks: List[Tok]) -> None:
        self.toks = toks
        self.i = 0

    # ---------- helpers ----------
    def cur(self) -> Tok:
        return self.toks[self.i]

    def peek(self, n: int = 1) -> Tok:
        j = self.i + n
        return self.toks[j] if j < len(self.toks) else Tok("EOF", "")

    def match(self, kind: str, value: Optional[str] = None) -> bool:
        t = self.cur()
        if t.kind != kind:
            return False
        if value is not None and t.value != value:
            return False
        return True

    def eat(self, kind: str, value: Optional[str] = None) -> Tok:
        if not self.match(kind, value):
            t = self.cur()
            want = f"{kind}:{value}" if value is not None else kind
            got = f"{t.kind}:{t.value}"
            raise parse_error(
            ErrorCode.PARSE_EXPECTED_TOKEN,
            f"Accipe {got}, pro {want} apud indicem tesserae {self.i}.",
            self.span0(),
        )
        t = self.cur()
        self.i += 1
        return t

    def span0(self) -> Span:
        # lexer側で行列を持ってないなら固定でOK。後で拡張可
        return Span()

    # ---------- entry ----------
    def parse_program(self) -> Program:
        fons = self.parse_fons()
        intro = self.parse_introductio()
        doctrina = self.parse_doctrina()
        self.eat("EOF")
        return Program(fons=fons, introductio=intro, doctrina=doctrina)

    # ---------- sections ----------
    def parse_fons(self) -> FonsSection:
        self.eat("FONSST")
        imports: List[ImportStmt] = []
        # import grammar未確定なら、今は空でもOK。必要ならここで読み足す。
        self.eat("FONSED")
        return FonsSection(imports=imports)

    def parse_introductio(self) -> IntroSection:
        self.eat("INTROST")
        stmts: List[Stmt] = []
        while not self.match("INTROED"):
            stmts.append(self.parse_stmt())
        self.eat("INTROED")
        return IntroSection(stmts=stmts)

    def parse_doctrina(self) -> DoctrinaSection:
        self.eat("DOCTST")
        main = self.parse_main()
        self.eat("DOCTED")
        return DoctrinaSection(main=main)

    # ---------- main ----------
    def parse_main(self) -> MainFunction:
        # FCON subjecto: nihil () -> { ... };
        self.eat("KW", "FCON")
        name = self.eat("IDENT").value
        if name != "subjecto":
            raise parse_error(ErrorCode.PARSE_MAIN_SUBJECTO_REQUIRED, "Nulla scriptura sine themate est.", self.span0())

        self.eat("COLON")
        # nihil token is SP in your lexer output
        if self.match("SP", "nihil"):
            self.eat("SP", "nihil")
        else:
            raise parse_error(ErrorCode.PARSE_MAIN_NIHIL_REQUIRED, "Subiectum veritatem non dat.", self.span0())

        self.eat("LPAREN"); self.eat("RPAREN")
        self.eat("DEF")  # '->'
        self.eat("LBRACE")
        body: List[Stmt] = []
        while not self.match("RBRACE"):
            body.append(self.parse_stmt())
        self.eat("RBRACE")
        self.eat("SEMICOLON")
        return MainFunction(body=body)

    # ---------- statements ----------
    def parse_stmt(self) -> Stmt:
        # nihil;
        if self.match("SP", "nihil"):
            self.eat("SP", "nihil")
            self.eat("SEMICOLON")
            return NihilStmt(span=self.span0())

        # effigium; / proximum;
        if self.match("CTRL", "effigium"):
            self.eat("CTRL", "effigium")
            self.eat("SEMICOLON")
            return BreakStmt(span=self.span0())

        if self.match("CTRL", "proximum"):
            self.eat("CTRL", "proximum")
            self.eat("SEMICOLON")
            return ContinueStmt(span=self.span0())

        # VCON name:Type (= expr)?;
        if self.match("KW", "VCON"):
            return self.parse_vardecl()

        # SI ...
        if self.match("KW", "SI"):
            return self.parse_if()

        # RECURSIO ...
        if self.match("KW", "RECURSIO"):
            return self.parse_loop()

        # IDENT ...  (call / move / assign / expr_stmt)
        if self.match("IDENT"):
            # Guard against "+=" legacy pattern: IDENT PLUS ASSIGN ...
            if self.peek(1).kind == "PLUS" and self.peek(2).kind == "ASSIGN":
                raise parse_error(ErrorCode.PARSE_UNSUPPORTED_SYNTAX, "'+=' is not supported in v0.3. Use: i = i + 1;", self.span0())

            # call: IDENT ( ) FLOW ( args... ) ;
            if self.peek(1).kind == "LPAREN" and self.peek(2).kind == "RPAREN" and self.peek(3).kind == "FLOW":
                call = self.parse_call_expr()
                self.eat("SEMICOLON")
                return CallStmt(span=self.span0(), call=call)

            # move: IDENT FLOW IDENT ;
            if self.peek(1).kind == "FLOW":
                dst = self.eat("IDENT").value
                self.eat("FLOW")
                if not self.match("IDENT"):
                    raise parse_error(ErrorCode.PARSE_INVALID_MOVE, "Aquam sine vase infundere non potes", self.span0())
                src = self.eat("IDENT").value
                self.eat("SEMICOLON")
                return Move(span=self.span0(), dst=dst, src=src)

            # assign: IDENT ASSIGN expr ;
            if self.peek(1).kind == "ASSIGN":
                name = self.eat("IDENT").value
                self.eat("ASSIGN")
                value = self.parse_expr()
                self.eat("SEMICOLON")
                return Assign(span=self.span0(), name=name, value=value)

            # expr_stmt fallback: expr ;
            expr = self.parse_expr()
            self.eat("SEMICOLON")
            return ExprStmt(span=self.span0(), expr=expr)

        raise parse_error(ErrorCode.PARSE_UNEXPECTED_TOKEN, f"Quid est hoc! Quid faciam?: {self.cur()}", self.span0())

    def parse_vardecl(self) -> VarDecl:
        self.eat("KW", "VCON")
        name = self.eat("IDENT").value
        self.eat("COLON")
        t = self.eat("TYPE").value  # "inte" etc.
        init = None
        if self.match("ASSIGN"):
            self.eat("ASSIGN")
            init = self.parse_expr()
        self.eat("SEMICOLON")
        return VarDecl(span=self.span0(), name=name, typ=t, init=init)

    def parse_call_expr(self) -> CallExpr:
        name = self.eat("IDENT").value
        self.eat("LPAREN"); self.eat("RPAREN")
        self.eat("FLOW")  # '<-'
        args = self.parse_args_tuple_required()
        return CallExpr(span=self.span0(), name=name, args=args)

    def parse_args_tuple_required(self) -> List[Expr]:
        # v0.3: call RHS must be "( ... )" even for single arg: ("Fizz")
        self.eat("LPAREN")
        args: List[Expr] = []
        if not self.match("RPAREN"):
            args.append(self.parse_expr())
            while self.match("COMMA"):
                self.eat("COMMA")
                args.append(self.parse_expr())
        self.eat("RPAREN")
        return args

    def parse_if(self) -> IfStmt:
        # SI propositio:(cond) { VERUM{...} FALSUM{...} };
        self.eat("KW", "SI")
        cond = self.parse_propositio_clause()

        self.eat("LBRACE")
        # VERUM{...}
        self.eat("KW", "VERUM")
        then_body = self.parse_block_stmts()

        # FALSUM{...} (required)
        self.eat("KW", "FALSUM")
        else_body = self.parse_block_stmts()

        self.eat("RBRACE")
        self.eat("SEMICOLON")
        return IfStmt(span=self.span0(), cond=cond, then_body=then_body, else_body=else_body)

    def parse_block_stmts(self) -> List[Stmt]:
        self.eat("LBRACE")
        stmts: List[Stmt] = []
        while not self.match("RBRACE"):
            stmts.append(self.parse_stmt())
        self.eat("RBRACE")
        return stmts

    def parse_propositio_clause(self) -> Expr:
        # propositio : ( expr )
        self.eat("CTRL", "propositio")
        self.eat("COLON")
        self.eat("LPAREN")
        cond = self.parse_expr()
        self.eat("RPAREN")
        return cond

    def parse_loop(self) -> LoopStmt:
        # RECURSIO ( propositio:(cond) [, quota:expr] [, acceleratio:expr] ) -> { body } ;
        self.eat("KW", "RECURSIO")
        self.eat("LPAREN")

        cond: Optional[Expr] = None
        quota: Optional[Expr] = None
        step: Optional[Expr] = None

        first = True
        while not self.match("RPAREN"):
            if not first:
                self.eat("COMMA")
            first = False

            key = self.eat("CTRL").value  # propositio/quota/acceleratio
            self.eat("COLON")

            if key == "propositio":
                self.eat("LPAREN")
                cond = self.parse_expr()
                self.eat("RPAREN")
            elif key == "quota":
                quota = self.parse_expr()
            elif key == "acceleratio":
                step = self.parse_expr()
            else:
                raise parse_error(ErrorCode.PARSE_UNKNOWN_LOOP_HEADER, f"Quaslibet designationes falsas firmiter repudiabimus.: {key}", self.span0())

        self.eat("RPAREN")
        self.eat("DEF")  # '->' required
        self.eat("LBRACE")
        body: List[Stmt] = []
        while not self.match("RBRACE"):
            body.append(self.parse_stmt())
        self.eat("RBRACE")
        self.eat("SEMICOLON")

        if cond is None:
            raise parse_error(ErrorCode.PARSE_LOOP_PROPOSITIO_REQUIRED, "Propositiones in vita necessariae sunt.", self.span0())
        return LoopStmt(span=self.span0(), cond=cond, quota=quota, step=step, body=body)

    # ---------- expressions (precedence climbing) ----------
    # precedence: ** > */% > +- > comparisons > non > et > aut
    # We implement: aut -> et -> non -> comparison -> add -> mul -> pow -> primary

    def parse_expr(self) -> Expr:
        return self.parse_or()

    def parse_or(self) -> Expr:
        left = self.parse_and()
        while self.match("CTRL", "aut"):
            self.eat("CTRL", "aut")
            right = self.parse_and()
            left = BinaryOp(span=self.span0(), op="aut", left=left, right=right)
        return left

    def parse_and(self) -> Expr:
        left = self.parse_unary()
        while self.match("CTRL", "et"):
            self.eat("CTRL", "et")
            right = self.parse_unary()
            left = BinaryOp(span=self.span0(), op="et", left=left, right=right)
        return left

    def parse_unary(self) -> Expr:
        # { non } comparison
        if self.match("CTRL", "non"):
            self.eat("CTRL", "non")
            expr = self.parse_unary()
            return UnaryOp(span=self.span0(), op="non", expr=expr)
        return self.parse_comparison()

    def parse_comparison(self) -> Expr:
        left = self.parse_add()
        # allow at most one comparison (like your EBNF)
        if self.cur().kind in ("EQ", "NE", "LT", "GT", "LE", "GE"):
            op_tok = self.eat(self.cur().kind)
            op_map = {"EQ": "==", "NE": "><", "LT": "<", "GT": ">", "LE": "<=", "GE": ">="}
            op = op_map[op_tok.kind]
            right = self.parse_add()
            return BinaryOp(span=self.span0(), op=op, left=left, right=right)
        return left

    def parse_add(self) -> Expr:
        left = self.parse_mul()
        while self.cur().kind in ("PLUS", "MINUS"):
            op_tok = self.eat(self.cur().kind)
            op = "+" if op_tok.kind == "PLUS" else "-"
            right = self.parse_mul()
            left = BinaryOp(span=self.span0(), op=op, left=left, right=right)
        return left

    def parse_mul(self) -> Expr:
        left = self.parse_pow()
        while self.cur().kind in ("STAR", "SLASH", "PERCENT"):
            op_tok = self.eat(self.cur().kind)
            op = {"STAR": "*", "SLASH": "/", "PERCENT": "%"}[op_tok.kind]
            right = self.parse_pow()
            left = BinaryOp(span=self.span0(), op=op, left=left, right=right)
        return left

    def parse_pow(self) -> Expr:
        left = self.parse_primary()
        while self.match("POW"):
            self.eat("POW")
            right = self.parse_primary()
            left = BinaryOp(span=self.span0(), op="**", left=left, right=right)
        return left

    def parse_primary(self) -> Expr:
        # call_expr as expression: IDENT () <- (args_tuple)
        if self.match("IDENT") and self.peek(1).kind == "LPAREN" and self.peek(2).kind == "RPAREN" and self.peek(3).kind == "FLOW":
            return self.parse_call_expr()

        if self.match("IDENT"):
            return Name(span=self.span0(), id=self.eat("IDENT").value)

        if self.match("INT"):
            v = int(self.eat("INT").value)
            return IntLit(span=self.span0(), value=v)

        if self.match("REAL"):
            v = float(self.eat("REAL").value)
            return RealLit(span=self.span0(), value=v)

        if self.match("STRING"):
            s = self.eat("STRING").value
            return StringLit(span=self.span0(), value=s)

        if self.match("LPAREN"):
            self.eat("LPAREN")
            inner = self.parse_expr()
            self.eat("RPAREN")
            return Paren(span=self.span0(), inner=inner)

        # prevent using nihil as expression
        if self.match("SP", "nihil"):
            raise parse_error(ErrorCode.PARSE_NIHIL_NOT_EXPR, "nihil is not an expression in v0.3; use 'nihil;' as a statement", self.span0())

        raise parse_error(ErrorCode.PARSE_UNEXPECTED_TOKEN, f"Caerimoniae Sinice haberi non possunt.: {self.cur()}", self.span0())
