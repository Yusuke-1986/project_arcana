# ========================
# AST nodes ver.1.0
# basic struct
# ========================
from dataclasses import dataclass

@dataclass
class Fons:
    pass

@dataclass
class Introductio:
    pass

@dataclass
class Stmt: 
    """文のブレースホルダー"""
    pass

@dataclass
class Expr: 
    """式のブレースホルダー"""
    pass

@dataclass
class Num(Expr):
    """数値"""
    value:str

@dataclass
class Str(Expr):
    """文字列"""
    value:str

@dataclass
class Id(Expr):
    """識別子"""
    name:str

@dataclass
class Binary(Expr):
    """
    演算定義
    left -> op <- right
    """
    op:str
    left:Expr
    right:Expr

@dataclass
class CallEmpty(Expr):
    """()定義"""
    name:str

@dataclass
class FlowCall(Expr):
    """() <- arg 定義"""
    call:CallEmpty
    arg:Expr

@dataclass
class VarDecl(Stmt):
    """変数"""
    name:str
    type_name: str
    expr:Expr

# = 定義
@dataclass
class Assign(Stmt):
    name:str
    expr:Expr

# 式ステートメント
@dataclass
class ExprStmt(Stmt):
    expr:Expr

# 関数ステートメント
@dataclass
class FuncDecl(Stmt):
    name:str
    body:list

# cuntusステートメント
@dataclass
class Cantus(Expr):
    raw: str  # 例: 'a=${a}'

# 比較
@dataclass
class Compare(Expr):
    op: str
    left: Expr
    right: Expr

# if文
@dataclass
class IfStmt(Stmt):
    cond: Expr
    then_body: list
    else_body: list

# step
@dataclass
class acceleratioOpe:
    op: str          # "++" | "--" | "+=" | "-="
    value: int = 1   # ++/-- は 1、+=/-= は指定値

# loop
@dataclass
class RecurStmt(Stmt):
    prima: Expr      # まずは Expr にしておく（INTだけでもOK）
    propositio: Expr
    acceleratio: acceleratioOpe
    body: list

# break
@dataclass
class BreakStmt(Stmt):
    pass

# continue
@dataclass
class ContinueStmt(Stmt):
    pass

# 単項演算
@dataclass
class Unary(Expr):
    op: str
    expr: Expr

# pass
@dataclass
class Through(Stmt):
    pass