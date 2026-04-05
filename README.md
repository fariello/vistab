# vistab

`vistab` is a lightweight, zero-dependency Python module for creating beautiful text-based ASCII/Unicode tables. It comes out-of-the-box with support for terminal formatting (ANSI escape sequences) and guarantees consistent string lengths across color variations.

## Installation

You can install `vistab` directly via pip:

```bash
pip install vistab
```

## Basic Usage

Getting started with `vistab` is simple. Initialize a `Vistab` instance, set up alignment if desired, and add your rows!

```python
from vistab import Vistab

table = Vistab()
# Left, Right, Center alignment
table.set_cols_align(["l", "r", "c"])
# Top, Middle, Bottom vertical alignment
table.set_cols_valign(["t", "m", "b"])

table.add_rows([
    ["Name", "Age", "Nickname"],
    ["Ms\nSarah\nJones", 27, "Sarah"],
    ["Mr\nJohn\nDoe", 45, "Johnny"],
    ["Dr\nEmma\nBrown", 34, "Em"]
])

print(table.draw())
```

**Output:**
```
┌───────┬─────┬──────────┐
│ Name  │ Age │ Nickname │
├───────┼─────┼──────────┤
│ Ms    │     │          │
│ Sarah │  27 │          │
│ Jones │     │  Sarah   │
├───────┼─────┼──────────┤
│ Mr    │     │          │
│ John  │  45 │          │
│ Doe   │     │  Johnny  │
├───────┼─────┼──────────┤
│ Dr    │     │          │
│ Emma  │  34 │          │
│ Brown │     │    Em    │
└───────┴─────┴──────────┘
```

## Advanced Formatting (Datatypes & Scientific Formatting)

`vistab` can infer and parse formatting rules strictly by passing data types, controlling precision dynamically for scientific floats and integers.

```python
from vistab import Vistab

table = Vistab(style="ascii")
table.set_decorations(Vistab.HEADER)
table.set_cols_dtype(['t', 'f', 'e', 'i', 'a']) 
table.set_cols_align(["l", "r", "r", "r", "l"])

table.add_rows([
    ["text", "float", "exp", "int", "auto"],
    ["alpha", "23.45", 543, 100, 45.67],
    ["beta", 3.1415, 1.23, 78, 56789012345.12],
    ["gamma", 2.718, 2e-3, 56.8, .0000000000128],
    ["delta", .045, 1e+10, 92, 89000000000000.9]
])

print(table.draw())
```

**Output:**
```
text    float       exp       int         auto  
==============================================
alpha   23.450    5.430e+02   100       45.670  
beta    3.142     1.230e+00   78        5.679e+10
gamma   2.718     2.000e-03   57        1.280e-11
delta   0.045     1.000e+10   92        8.900e+13
```

## Built-in Theme Styles

`vistab` comes with predefined rendering styles like `light`, `bold`, `double`, `ascii`, and `round`. 

```python
table = Vistab(style="double")
table.header(["Name", "Age"])
table.add_row(["Alice", 30])
table.add_row(["Bob", 28])
```

**Output:**
```
╔═══════╦═════╗
║ Name  ║ Age ║
╠═══════╬═════╣
║ Alice ║ 30  ║
╠═══════╬═════╣
║ Bob   ║ 28  ║
╚═══════╩═════╝
```

## ANSI Color Support

A major advantage of `vistab` is native, invisible terminal styling support. It successfully measures invisible ANSI color codes and dynamically resizes your table width correctly underneath color escape formatting (e.g. `\033[1;31m`). Other common ASCII libraries will typically break their visual alignment when terminal colors are embedded.

```python
from vistab import Vistab

colored_table = Vistab(max_width=40)
colored_table.add_rows([
    ["Test 1", "Test 2"],
    ["\033[1;31mRed Alert!\033[0m", "\033[1;32mSystem Stable\033[0m"]
])

print(colored_table.draw())
```

## License

This project is licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.
