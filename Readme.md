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
| prima | initial value | 初期値 |
| gradu | step value | ステップ |
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
statement = variable_declare | function_declare | class_declare | if_statement | loop_statement | expr_stmt ;
inner_statement = variable_declare | if_statement | loop_statement | expr_stmt ;
expr_stmt = expr, ";" ;

(* Declare *)
main_statement = "FCON", "subjecto", ":", "nihil", "(", ")", "->", "{", { inner_statement }, "}", ";" ;
function_declare = "FCON", Identifier, ":", Type, "(", [ arg_list ], ")", "->", "{", { inner_statement }, "}", ";" ;
variable_declare = "VCON", Identifier, ":", Type, ["=", expr], ";" ;

(* expression *)
expr = aut_expr | et_expr | non_expr ;
aut_expr = "aut", "(", expr, ",", expr, ")" ;
et_expr = "et",  "(", expr, ",", expr, ")" ;
non_expr = [ "non" ], comparison ;

comparison = add, [ ( "==" | "><" | "<" | ">" | "<=" | ">=" ), add ] ;
add = mltp, { ( "+" | "-" ), mltp } ;
mltp = primary, { ( "*" | "/" | "**" | "%" ), primary } ;
primary = Identifier | number | "(" , expr , ")" | func_call ;

func_call = Identifier, "(", [ expr_list ], ")" ;

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
