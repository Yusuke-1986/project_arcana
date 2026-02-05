# arcana programming language v0.15

## feature

- python mystic wrapper
- latin base & PascalCase recommended, solemn and mysterious
  - constant & Main keywords: **UPPERCASE**
  - variables: **lowercase recommended**
- syntax: graphical data flow & type safety
- src:
  - original extends, '.arkhe' is main sourcecode
  - components,modules,defines sets '.dogma'

## example

### sample code

sample.arkhe

```arcana
<FONS>
VOCARE dogma elementum /// import type(dogma/arkhe/src) file_name(only filename) this sample does not use this dogma.
</FONS>

<INTRODUCTIO>
VCON a: inte = 1;
VCON b: inte = 10;
VCON c: inte = 2;
VCON msg: filum = cantus'a: ${a}, b: ${b}, c: ${c} a + b: ${a + b}';
VCON var_1: inte = 0;
VCON var_2: real = 0;

FCON Potentia: inte (a: inte, b: inte) -> {
    REDITUS a ** b;
};

FCON MsgIndicant: nihil () -> {
    indicant () <- msg;
    REDITUS NIHIL;
};
</INTRODUCTIO>

<DOCTRINA>
FCON subjecto: nihil () -> {
/// entry point: subjecto only in <DOCTRINA> section.

    MsgIndicant () <- ();

    var_1 = Potentia () <- (b, c);
    var_2 = a / c;

    indicant () <- var_1;
    indicant () <- var_2;

    RECURSIO (prima: i=1, conditio: i<11, gradu: +1) {
        indicant () <- "count 1";
        SI conditio: (i % 2 == 0){
            VERUM {
                indicant () <- cantus'${i} = even. count 2';
            }
            FALSUM {
                indicant () <- cantus'${i} = odd. count 2';
                SI propositio: (i == 1){
                    VERUM {
                        indicant () <- "count 3 one.";
                    }
                    FALSUM {
                        indicant () <- "not under two";
                    }
                };
            }
        };
    };
};
</DOCTRINA>
```

output:

```bash
a: 1, b: 10, c: 2 a + b: 11
100
0.5
count 1
1 = odd. count 2
count 3 one.
count 1
2 = even. count 2
count 1
3 = odd. count 2
not under three
count 1
4 = even. count 2
count 1
5 = odd. count 2
not under three
count 1
6 = even. count 2
count 1
7 = odd. count 2
not under three
count 1
8 = even. count 2
count 1
9 = odd. count 2
not under three
count 1
10 = even. count 2
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
> arcana exsecutio src.arkhe --emit
=== [arcana emit] transpiled python ===
<transpiled python code>
=== [arcana emit] end ===
```

### syntax

```bash
/// inline comment section
<cmt>
document section
- use variables, define function, define classes, must be initialize at first
key: VCON, MINST, CINST, PRINCIPIUM
- necessary data type explicitly 
</cmt>

/// termination: ';'
/// specific string: '...' or "..."
/// f-string like: cantus'...${expr}...';
/// use function: func () <- args;
/// declare function: 
MINST func: filum (*args: filum) -> { 
    detail

    REDITUS response;
};
* indicator is 'any name'
example, *args means any variables as args  

nested requirement = MAX_LEVEL: 3
recommended: use another logic(another function, class...)
```

### Keywords

| words | intent | 意味 |
| ----- | ----- | ----- |
| VCON | Variabiles constituere(variable declaration) | 変数宣言 |
| FCON | Functiones constituere(function declaration) | 関数宣言 |
| CCON | Classes constituere(class declaration) | クラス宣言 |
| PRINCIPIUM | constant declaration | 定数宣言 |
| REDITUS | return | リターン |
| RECURSIO | loop | 再帰 |
| prima | initial value | 初期値 |
| conditio | continuous condition | (ループの)継続条件 |
| gradu | step value | ステップ |
| SI | if | 分岐 |
| propositio | continuous condition | (分岐するための)命題 |
| VERUM | true block | 真の場合 |
| FALSUM | false block | 偽の場合 |
| cantus | f-string | 文字列構文 |
| CANTUS | chant syntax(Not implemented) | "詠唱構文" |
| effgium | break | 脱出 |
| proximum | continue, next | 次へ |
| nihil | pass | 何もしない |

### Type

| arcana | python | note |
| ----- | ----- | ----- |
| inte | int | ----- |
| real | float | ----- |
| verum | bool | ----- |
| filum | str | ----- |
| nihil | None | only return type(Can not use define types) |
| ordinata | tuple | taple base, but ordinata has list-like behavior |

### operator

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
| ! | not |

"><" is parsed as "!=" prior to ">" and "<".

### built-ins

| arcana | python | definition |
| ----- | ----- | ----- |
| indicant | print | indicant: filum (*objects, sep=' ', end='\n', file=sys.stdout, flush=False) <- expr |
| accipere | input | accipere: filum (*args) <- expr |
| longitude | len | longitude: inte (*args) <- expr |
| figura | type | figure: filum (*args) <- expr |

```arcana
VCON a: inte = 10;
VCON b: inte = 20;
VCON veritas: inte = 0;

/// '->' is definition left is right(process has defined inside '{}')
FCON Potentia: inte (a: inte, b: inte ) -> {
    REDITUS a ** b;
};

/// using function not need type annotation
indicant() <- a + b; /// '<-' is bridge right to left

/// When the number of arguments exceeds two, use tuples. When the argument is a tuple, use nested tuples. 
veritas = Potentia() <- (a, b); 
indicant() <- veritas;
```

### loop

```arcana
RECURSIO (prima: i=1, conditio: i<10, gradu: +1) {
    indicant() <- cantus'Current value: ${ i }';
};
```

### if

```arcana
SI propositio: (1 == 1){
    VERUM { /// true
        indicant() <- 'verum';
    }
    FALSUM { /// false
        indicant() <- 'falsum';
    }
};
```
