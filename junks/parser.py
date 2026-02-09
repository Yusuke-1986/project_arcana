# ========================
# Parser (minimal Pratt) ver.1.0
# ========================
from .ast_v2 import *
# from types import int


class Parser:
    def __init__(self, toks: list):
        self.toks=toks
        self.i=0

    def cur(self) -> tuple:
        """現在位置のトークンを返す"""
        return self.toks[self.i]

    def eat(self,kind: str, val: str = None) -> tuple:
        """トークンを返して次のインデックスを指定する"""
        t=self.cur()
        if t.kind!=kind or (val and t.value!=val):
            raise SyntaxError(f"Unexpected token {t}")
        self.i+=1
        return t

    def match(self,kind: str ,val: str = None) -> bool:
        """該当するトークンか判別する"""
        t=self.cur()
        if t.kind!=kind:
            return False
        if val and t.value!=val:
            return False
        return True

    # ----- program -----

    def parse(self) -> list:
        body=[]
        while not self.match("EOF"):
            if self.match("FONSST"):
                body.append(self.pars_fons())
            elif self.match("INTROST"):
                body.append(self.pars_intro())
            elif self.match("DOCTST"):
                self.eat("DOCTST", "<DOCTRINA>")
                if self.match("KW","FCON"): # Topレベルからのパース
                    body.append(self.parse_func()) # 関数定義構文の解釈
            else:
                self.i+=1
        return body
    
    def pars_fons(self):
        while not self.match("FONSED") and self.i<=len(self.toks):
            t = self.cur()
            self.i += 1
            if self.match("FONSED"):
                return Fons()
            elif self.i > len(self.toks):
                raise SyntaxError("open section error. not find \"</FONSED>\"")

    def pars_intro(self):
        while not self.match("INTROED") and self.i<=len(self.toks):
            t = self.cur()
            self.i += 1
            if self.match("INTROED"):
                return Introductio()
            elif self.i > len(self.toks):
                raise SyntaxError("open section error. not find \"</INTRODUCTIO>\"")

    def parse_func(self) -> FuncDecl:
        """FCON IDENT: type () -> { の判定"""
        self.eat("KW","FCON")
        name=self.eat("IDENT").value
        self.eat("COLON")
        t = self.cur()
        if t.kind == "TYPE":
            self.i += 1
        elif t.kind == "SP" and t.value == "nihil":
            self.i += 1
        else:
            raise SyntaxError("Expected return type")
        self.eat("LPAREN")
        self.eat("RPAREN")
        self.eat("DEF")
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
        if self.match("SP", "nihil"):
            self.eat("SP", "nihil")
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
        
        if self.match("CTRL","effigum"):
            self.eat("CTRL","effigum")
            self.eat("SEMICOLON")
            return BreakStmt()

        if self.match("CTRL","proximum"):
            self.eat("CTRL","proximum")
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
            self.eat("CTRL","propositio")  # 固定語
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
            quota = Num("100")              # デフォルト上限
            propositio = Num("1")             # 1==True扱い（簡易）
            acceleratio = acceleratioOpe("++", 1)

            # header: quota / propositio / acceleratio (order-free)
            while not self.match("RPAREN"):
                key = self.eat("CTRL").value   # "quota" | "propositio" | "acceleratio"
                self.eat("COLON")

                if key == "quota":
                    quota = self.parse_expr()
                elif key == "propositio":
                    propositio = self.parse_expr()
                    if self.contains_call(propositio):
                        raise SyntaxError("RECURSIO propositio: function call is not allowed")

                elif key == "acceleratio":
                    acceleratio = self.parse_acceleratio_ope()
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
            return RecurStmt(quota, propositio, acceleratio, body)

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
    
    def parse_acceleratio_ope(self) -> acceleratioOpe:
        t = self.cur()
        if t.kind == "INCR":
            self.i += 1
            return acceleratioOpe("++", 1)
        if t.kind == "DECR":
            self.i += 1
            return acceleratioOpe("--", 1)
        if t.kind == "PLUSEQ":
            self.i += 1
            n = int(self.eat("INT").value)
            return acceleratioOpe("+=", n)
        if t.kind == "MINUSEQ":
            self.i += 1
            n = int(self.eat("INT").value)
            return acceleratioOpe("-=", n)
        raise SyntaxError(f"Bad acceleratio ope token={t}")

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