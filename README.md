# vistab

`vistab` is a simple Python module for creating ASCII tables, color-aware wrapping, and Unicode display width handling.

## Installation

You can install `vistab` directly via pip (once published):

```bash
pip install vistab
```

## Usage

```python
from vistab import Vistab

table = Vistab()
table.set_cols_align(["l", "r", "c"])
table.set_cols_valign(["t", "m", "b"])

table.add_rows([
    ["Name", "Age", "Nickname"],
    ["Ms\nSarah\nJones", 27, "Sarah"],
    ["Mr\nJohn\nDoe", 45, "Johnny"],
    ["Dr\nEmma\nBrown", 34, "Em"]
])

print(table.draw())
```

### With ASCII Colors

`vistab` is designed with ANSI escape sequences in mind and correctly wraps and aligns strings containing terminal colors:

```python
from vistab import Vistab

t1 = Vistab([
    ["Test 1", "Test 2", "Test 3", "Test 4"],
    [
        "This is some \033[1;31mRed text\033[0m to show the ability to wrap \033[38;5;226mcolored text\033[0m correctly.",
        "And this is some \033[1;32mGreen Text\033[0m",
        "Just short.",
        "Normal Table Behavior."
    ]
], max_width=40)

print(t1.draw())
```

## Built-in Styles

`vistab` comes with predefined rendering styles like `light`, `heavy`, `ascii`, `round`, `double`, and more.

```python
# Change the style of the table
table = Vistab(style="double")
```

## License

This project is licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.
