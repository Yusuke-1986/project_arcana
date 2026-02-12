from .ast import Token, Span
import re
# ========================
# Lexer(Tokenizer) ver.1.0
# ========================

# セクション名
SECTION_TAG = {"FONS", "INTRODUCTIO", "DOCTRINA"}

# 予約語(制御指示語)
KEYWORDS = {
    "FCON", "VCON", "CCON", "PRINCIPIUM",
    "SI", "VERUM", "FALSUM", 
    "RECURSIO","REDITUS"
}

# 制御用ラベル
CONTROL_LABEL = {
    "effigium", "proximum",
    "et", "aut", "non", 
    "propositio", "quota", "acceleratio",
}

TYPE_LIST = {    
    "inte", "real", "verum", "filum", "ordinata", "catalogus"
}

SPECIAL_KEY = { "nihil" }

TOKEN_SPEC = [
    ("FONSST", r"<FONS>"),
    ("FONSED", r"</FONS>"),
    ("INTROST", r"<INTRODUCTIO>"),
    ("INTROED", r"</INTRODUCTIO>"),
    ("DOCTST", r"<DOCTRINA>"),
    ("DOCTED", r"</DOCTRINA>"),
    ("CMTBLKST", r"<cmt>"),
    ("CMTBLKED", r"</cmt>"),
    ("LINECMT", r"///[^\n]*"),  # line comment (Arcana: /// ... endline)

    ("STRING", r'"[^"]*"|\'[^\']*\''), # ""か''のチャンク
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"), # チャンクで取る
    ("SKIP", r"[ \t\n]+"), # 要らないもの(スペース、タブ、改行)スキップ用

    ("FLOW", r"<-"),
    ("DEF", r"->"),

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
    ("LBRACK", r"\["),
    ("RBRACK", r"\]"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("COLON", r":"),
    ("COMMA", r","),  
    ("SEMICOLON", r";"),

    ("REAL", r"\d+\.\d+"),
    ("INT", r"\d+"),
    ("MISMATCH", r"."),
]

# トークン検索対象一覧の作成
MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n,p in TOKEN_SPEC))

def tokenize(src: str) -> list[Token]:
    src = src.replace("\r\n", "\n").replace("\r", "\n")

    """Tokenize source code into a list of Tokens."""
    line, col = 0, 0
    tokens: list[Token] = []

    # 検索対象から一致するものを探して順番に取り出す
    for m in MASTER.finditer(src):
        kind=m.lastgroup
        val=m.group()
        start_span = Span(line, col)
        # print(f"[arcana: lexer] matched {kind} -> {val} at {start_span}")

        nl = val.count("\n")
        if nl:
            line += nl
            col = 1 + len(val.rsplit("\n", 1)[-1])
        else:
            col += len(val)

        # Normalize string literals: strip surrounding quotes
        if kind == "STRING" and len(val) >= 2 and val[0] == val[-1] and val[0] in ("\"", "\'"):
            val = val[1:-1]

        if kind in ("SKIP", "LINECMT"):
            continue
            
        if kind == "IDENT":
            if val in KEYWORDS:
                kind = "KW"

            elif val in SPECIAL_KEY:
                kind = "SP"

            elif val in SECTION_TAG:
                kind = "SECTION"

            elif val in TYPE_LIST:
                kind = "TYPE"

            elif val in CONTROL_LABEL:
                kind = "CTRL"

            elif val == "cantus":
                kind = "CANTUS"

        

        tokens.append(Token(start_span, kind, val))

    tokens.append(Token(start_span, "EOF", ""))

    
    return tokens