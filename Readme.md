# arcana programming language v0.3.8

## feature

- concept: Strict grammar, emphasis on data flow, eternal recurrence and intention to leave, propositionalism
- python mystic wrapper
- latin base & PascalCase recommended, solemn and mysterious
  - constant & Main keywords: **UPPERCASE**
  - variables: **lowercase recommended**
- syntax: graphical data flow & type safety
- src:
  - original extends, '.arkhe' is main sourcecode
  - components,modules,defines sets '.dogma'

### Phrase

section-tag: all 3 sections are required.

| words | intent | 意味 |
| ----- | ----- | ----- |
| FONS | import section | インポート記述部 |
| INTRODUCTIO | define section | subjecto外部定義部 |
| DOCTRINA | main section | メイン処理記述部 |

Keywords

| words | intent | 意味 |
| ----- | ----- | ----- |
| VCON | Variabiles constituere(variable declaration) | 変数宣言 |
| FCON | Functiones constituere(function declaration) | 関数宣言 |
| CCON | Classes constituere(class declaration) | クラス宣言 |
| PRINCIPIUM | constant declaration | 定数宣言 |
| REDITUS | return | リターン |
| RECURSIO | loop | 再帰 |
| SI | if | 分岐 |
| VERUM | true | 真の場合 |
| FALSUM | false | 偽の場合 |

Control label

| words | intent | 意味 |
| ----- | ----- | ----- |
| propositio | continuous condition | (分岐するための)命題 |
| quota | loop limit | 指定ループ数(デフォルト:100) |
| acceleratio | step value | ステップ |
| effigium | break | 脱出 |
| proximum | continue, next | 次へ |
| non | not | ￢ |
| et | and | ∧ |
| aut | or | ∨ |

Special key: flexible use with context
*How to use will be explained later

words: **cantus**, **nihil**

### Type

| arcana | python | note |
| ----- | ----- | ----- |
| inte | int | ----- |
| real | float | ----- |
| filum | str | ----- |
| verum | bool | ----- |
| ordinata | tuple | tuple base, but ordinata has list-like behavior |
| catalogus | dict | ----- |

### Operands

| arcana | python |
| ----- | ----- |
| + | + |
| - | - |
| * | * |
| / | / |
| ** | ** |
| % | % |
| > | > |
| < | < |
| >= | >= |
| <= | <= |
| == | == |
| >< | != |

"><" is parsed as "!=" prior to ">" and "<".

### syntax

```ebnf
program = import_section, define_section, main_section ;

(* Section *)
import_section = "<FONS>", { import_statement }, "</FONS>" ;
define_section = "<INTRODUCTIO>", { statement }, "</INTRODUCTIO>" ;
main_section = "<DOCTRINA>", main_statement, "</DOCTRINA>" ;

(* Statement *)
statement = variable_declare
          | function_declare
          | class_declare
          | assign_statement
          | move_statement
          | call_statement
          | if_statement 
          | loop_statement 
          | expr_stmt
          | nihil_statement
          | break_statement
          | continue_statement ;

inner_statement = variable_declare 
                | assign_statement
                | move_statement
                | call_statement
                | if_statement 
                | loop_statement 
                | expr_stmt
                | nihil_statement
                | break_statement
                | continue_statement ;

nihil_statement    = "nihil", ";" ;
break_statement    = "effigium", ";" ;
continue_statement = "proximum", ";" ;

assign_statement = Identifier, "=", expr, ";" ;
move_statement = Identifier, "<-", Identifier, ";" ;

bool_expr = expr ; (* semantic: return boolean *)

call_statement = call_expr, ";" ;
call_expr = Identifier, "(", ")", "<-", args_tuple ;

args_tuple = "(" , [ expr , { "," , expr } ] , ")" ;

expr_stmt = expr, ";" ;

(* semantic: Looping maximum level = 3 *)
loop_statement = "RECURSIO", "(", 
                    propositio,
                     [",", quota], 
                     [",", acceleratio], 
                ")", "->",
                "{", { inner_statement }, "}", ";" ;

propositio = "propositio", ":", "(", bool_expr, ")" ;

quota = "quota", ":", init_expr ; (* budget loops, default = 100 *)
init_expr = assignment | expr ;
assignment = Identifier, "=", expr ;
acceleratio = "acceleratio", ":", step_expr ; (* step value, default = counter += 1 *)
step_expr = expr ; (* semantic: >0 *)

if_statement =
    "SI", propositio_clause,
    "{",
        verum_block,
        falsum_block,
    "}",
    ";" ;

propositio_clause = "propositio", ":", "(", bool_expr, ")" ;

verum_block  = "VERUM",  "{", { inner_statement }, "}" ;
falsum_block = "FALSUM", "{", { inner_statement }, "}" ;

(* Declare *)
main_statement = "FCON", "subjecto", ":", "nihil", "(", ")", "->", "{", { inner_statement }, "}", ";" ;
function_declare = "FCON", Identifier, ":", Type, "(", [ arg_list ], ")", "->", "{", { inner_statement }, "}", ";" ;
variable_declare = "VCON", Identifier, ":", Type, ["=", expr], ";" ;

(* expression *)
expr = or_expr ;

or_expr = and_expr, { "aut", and_expr } ;
and_expr = unary, { "et",  unary } ;

unary = { "non" }, comparison ; 

comparison = add, [ ( "==" | "><" | "<" | ">" | "<=" | ">=" ), add ] ;
add = mul, { ( "+" | "-" ), mul } ;
mul = pow, { ( "*" | "/" | "%" ), pow } ;
pow = primary, { "**", primary } ;
primary = dict_lit
        | call_expr
        | Identifier 
        | number 
        | string
        | "(" , expr , ")" ;

dict_lit = "{", [ dict_pair, { ",", dict_pair } ], "}" ;
dict_pair = expr, ":", expr ;

```

### commands

### Install(development)

```bash
cd arcana # project root
pip install -e .

# via module
py -m arcana exsecutio file.arkhe [options]
# or via installed command
arcana exsecutio file.arkhe [options]
```

- run code

```bash
> arcana exsecutio src.arkhe
```

- code validation(Not implemented)

```bash
> arcana inspectio src.arkhe
```

- build project(Not implemented)

```bash
> arcana aedificatio src.arkhe
```

- emit option

```bash
> arcana exsecutio src.arkhe --perscribere
=== [arcana perscribere] transpiled python ===
<transpiled python code>
=== [arcana perscribere] end ===
```

### example

```arcana
sample.arkhe
<FONS>
</FONS>

<INTRODUCTIO>
</INTRODUCTIO>

<DOCTRINA>
FCON subjecto: nihil () -> {
    VCON i:inte = 1;
    RECURSIO (propositio: (i < 51)) -> {
        SI propositio: (i % 15 == 0){
            VERUM{
                indicant () <- ("FizzBuzz");
            }
            FALSUM{
                SI propositio: (i % 3 == 0){
                    VERUM{
                        indicant () <- ("Fizz");
                    }
                    FALSUM{
                        SI propositio: (i % 5 == 0){
                            VERUM{
                                indicant () <- ("Buzz");
                            }
                            FALSUM{
                                indicant () <- (i);
                            }
                        };
                    }
                };   
            }
        };
        
        i = i + 1;
        
        SI propositio: (i > 100){
            VERUM{
                indicant () <- ("limit over.");
                effigium;
            }
            FALSUM{
                nihil;
            }
        };
    };
};
</DOCTRINA>
```

### built-ins

| arcana | python | definition |
| ----- | ----- | ----- |
| indicant | print | indicant: filum () <- (expr) |
| accipere | input | accipere: filum () <- (expr) |
| longitudo | len | longitude: inte () <- (expr) |
| figura | type | figure: arcana_type () <- (expr) |
| tempus | (pending)datetime.now | TBD |
| chronos | (pending)timedelta.total_seconds | TBD |

### Errors

| Code | Name | Msg(latin) | when |
| ----- | ----- | ----- | ----- |
| **Runtime**
| `R0100_VERITATEM_NON_ATTIGI` | `VERITATEM_NON_ATTIGI` | `Veritatem non attigi.` | `RECURSIO` の安全ガード quota 超過 |
| **Semantic**
| `E0101_BREAK_OUTSIDE_LOOP`     | `BREAK_OUTSIDE_LOOP`     | `Nullus discessus est extra reditum.`              | ループ外で `effigium;` |
| `E0102_CONTINUE_OUTSIDE_LOOP`  | `CONTINUE_OUTSIDE_LOOP`  | `Nulla continuitas extra limites est.`             | ループ外で `proximum;` |
| `E0103_LOOP_NEST_TOO_DEEP`     | `LOOP_NEST_TOO_DEEP`     | `Tres reincarnationes, si plures, maledictio est.` | `RECURSIO` のネスト > 3 |
| `E0110_LOOP_STEP_NOT_POSITIVE` | `LOOP_STEP_NOT_POSITIVE` | `stationarius accelerationis`                      | `acceleratio` が正でない |
| `E0111_LOOP_QUOTA_INVALID`     | `LOOP_QUOTA_INVALID`     | `Rectus valor, recta via`                          | `quota` が不正 |
| `E0202_NIHIL_NOT_EXPR`         | `NIHIL_NOT_EXPR`         | （必要ならMSGを付与） | `nihil` を式として扱った等 |
| `E0203_ARG_COUNT_MISMATCH` | `ARG_COUNT_MISMATCH` | `Numeri non congruunt. Fortasse mus eos abstulit.` | builtin / function の引数個数が仕様と一致しない |
| `E0204_TYPE_MISMATCH` | `TYPE_MISMATCH` | `Feretrum neque nimis magnum neque nimis parvum esse debet.` | 型の不一致 |
| **Parse**
| `P0001_EXPECTED_TOKEN` | `PARSE_EXPECTED_TOKEN` | `Accipe {got}, pro {want} apud indicem tesserae {i}.` | 期待したトークンと違う |
| `P0002_UNEXPECTED_TOKEN`         | `PARSE_UNEXPECTED_TOKEN`         | `Quid est hoc! Quid faciam?: {tok}` | 想定外トークン |
| `P0010_MAIN_SUBJECTO_REQUIRED`   | `PARSE_MAIN_SUBJECTO_REQUIRED`   | `Nulla scriptura sine themate est.` | `FCON subjecto ...` が必須 |
| `P0011_MAIN_NIHIL_REQUIRED`      | `PARSE_MAIN_NIHIL_REQUIRED`      | `Subiectum veritatem non dat` | `subjecto: nihil` 必須 |
| `P0020_UNSUPPORTED_SYNTAX`       | `PARSE_UNSUPPORTED_SYNTAX`       | `'+=' is not supported in v0.3. Use: i = i + 1;` | 非対応構文（例 `+=`） |
| `P0021_INVALID_MOVE`             | `PARSE_INVALID_MOVE`             | `Aquam sine vase infundere non potes`                             | `a <- b;` で RHS が Identifier でない等 |
| `P0030_UNKNOWN_LOOP_HEADER` | `PARSE_UNKNOWN_LOOP_HEADER` | `Quaslibet designationes falsas firmiter repudiabimus.: {key}` | `RECURSIO(...)` のヘッダキー不明 |
| `P0031_LOOP_PROPOSITIO_REQUIRED` | `PARSE_LOOP_PROPOSITIO_REQUIRED` | `Propositiones in vita necessariae sunt.`                         | `propositio:` 欠落 |
| `P0040_NIHIL_NOT_EXPR` | `PARSE_NIHIL_NOT_EXPR` | `nihil is not an expression in v0.3; use 'nihil;' as a statement` | `nihil` の式利用禁止 |
| `P0099_INTERNAL` | `PARSE_INTERNAL` | （任意）| 内部エラー/例外ラップ |

