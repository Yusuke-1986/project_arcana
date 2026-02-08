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
| quota | loop limit | ループ回数(デフォルト:100) |
| acceleratio | step value | ステップ |
| effgium | break | 脱出 |
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
          | if_statement 
          | loop_statement 
          | expr_stmt ;

inner_statement = variable_declare 
                | if_statement 
                | loop_statement 
                | expr_stmt ;

expr_stmt = expr, ";" ;

loop_statement = "RECURSIO", "(", 
                    propositio,
                     [",", quota], 
                     [",", acceleratio], 
                ")", "->",
                "{", { inner_statement }, "}", ";" ;

propositio = "propositio", ":", "(", bool_expr, ")" ;
bool_expr = expr ; (* semantic: return boolean *)
quota = "quota", ":", init_expr ; (* Max loop, default = 100 *)
init_expr = assignment | expr ;
assignment = Identifier, "=", expr ;
acceleratio = "acceleratio", ":", step_expr ; (* step value, default = counter += 1 *)
step_expr = expr ; (* semantic: >0 *)

(* Declare *)
main_statement = "FCON", "subjecto", ":", "nihil", "(", ")", "->", "{", { inner_statement }, "}", ";" ;
function_declare = "FCON", Identifier, ":", Type, "(", [ arg_list ], ")", "->", "{", { inner_statement }, "}", ";" ;
variable_declare = "VCON", Identifier, ":", Type, ["=", expr], ";" ;

(* expression *)
expr = comparison ;

comparison = add, [ ( "==" | "><" | "<" | ">" | "<=" | ">=" ), add ] ;
add = mul, { ( "+" | "-" ), mul } ;
mul = pow, { ( "*" | "/" | "%" ), pow } ;
pow = postfix, { "**", postfix } ;
postfix = primary, { "(", [ expr_list ], ")" } ;
primary = Identifier 
        | number 
        | "(" , expr , ")" ;

```

### commands

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
