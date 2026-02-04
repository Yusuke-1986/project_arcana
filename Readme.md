# arcana programming language v0.1

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
key: VINST, MINST, CINST, PRINCIPIUM
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

| words | intent |
| ----- | ----- |
| VINST | variable declaration |
| MINST | function declaration |
| CINST | class declaration |
| PRINCIPIUM | constant declaration |
| REDITUS | return |
| REPETITIO | loop |
| prima | initial value |
| conditio | continuous condition |
| gradu | step value |
| SI | if |
| VERUM | true block |
| FALSUM | false block |
| cantus | f-string |
| CANTUS | 'CANTUS' syntax(Not implemented) |

### Type

| arcana | python |
| ----- | ----- |
| inte | int |
| real | float |
| verum | bool |
| filum | str |
| nihil | None |

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

### print

```bash
VINST a: inte = 10;
VINST b: inte = 20;
VINST veritas: inte = 0;

/// '->' is definition left is right(process has defined inside '{}')
MINST potentia: inte (a: inte, b: inte ) -> {
    REDITUS a ** b;
};

/// using function not need type annotation
indicant() <- a + b; /// '<-' is bridge right to left

/// When the number of arguments exceeds two, use tuples. When the argument is a tuple, use nested tuples. 
veritas = potentia() <- (a, b); 
indicant() <- veritas;
```

### loop

```bash
REPETITIO (prima: i=1, conditio: i<10, gradu: +1) {
    indicant() <- cantus'Current value: ${ i }';
};
```

### if

```bash
SI conditio: (1==1){
    VERUM { /// true
        indicant() <- 'verum';
    }
    FALSUM { /// false
        indicant() <- 'falsum';
    }
};
```
