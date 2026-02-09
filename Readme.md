# arcana programming language v0.2

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

words: **CANTUS**, **cantus**, **nihil**

### Type

| arcana | python | note |
| ----- | ----- | ----- |
| inte | int | ----- |
| real | float | ----- |
| filum | str | ----- |
| verum | bool | ----- |
| ordinata | tuple | taple base, but ordinata has list-like behavior |

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
primary = call_expr
        | Identifier 
        | number 
        | string
        | "(" , expr , ")" ;

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

### built-ins

| arcana | python | definition |
| ----- | ----- | ----- |
| indicant | print | indicant: filum (*objects, sep=' ', end='\n', file=sys.stdout, flush=False) <- expr |
| accipere | input | accipere: filum (*args) <- expr |
| longitudo | len | longitude: inte (*args) <- expr |
| figura | type | figure: filum (*args) <- expr |
| tempus | datetime.now | *** |
| chronos | timedelta.total_seconds | *** |
