[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)

# vistab

`vistab` is a lightweight Python module for creating beautiful text-based ASCII/Unicode tables. It comes out-of-the-box with support for fluid terminal formatting (ANSI escape sequences), coordinate-based discrete cell styling, and guarantees consistent string lengths across dense color variations.

## Key Features

- **Lightweight Native Core**: Operates primarily off the Python standard library with `wcwidth` enabling accurate string geometry calculations.
- **Color-Aware Word Wrapping**: Dynamically measures and wraps table widths over embedded, invisible ANSI formatting sequences without breaking table geometry.
- **Coordinate-Based Styling API**: Colorize rows, columns, headers, or specific cells declaratively (e.g. `set_header_style(bg="red", bold=True)`).
- **Hierarchical TOML Configurations**: Persist your favorite table paddings and layout themes cross-project using a localized `.vistab.toml`.
- **Advanced Data Parsing**: Injects automatic text wrapping, infers scientific datatypes, and parses CSV files.

## Detailed Documentation
Looking for an exhaustive configuration breakdown or command-line parser bindings?

- **[Vistab Python API Reference](docs/API.md)** *(Covers all objects, data formatting algorithms, and properties)*
- **[Command-Line (CLI) Manual](docs/CLI.md)** *(Covers mapping raw CSV structures and terminal limits)*

## Installation

You can install `vistab` directly via pip:

```bash
pip install vistab
```

> **Note**: For complex Asian/CJK full-width character wrapping support, install the optional component using `pip install vistab[cjk]`.

## Quick Start

Getting started with `vistab` is simple. Initialize a `Vistab` instance, set up column alignments and paddings, and append your rows.

```python
from vistab import Vistab

table = Vistab(style="round2", padding=1)
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

> **Note on Web Rendering:** We display the raw output below as an image because some package registries (like PyPI) explicitly enforce code-block font stacks (e.g., `Source Code Pro`) that lack glyphs for Unicode Extended Box Drawing characters. When falling back to secondary system fonts for characters like `╭` or `╪`, the physical grid mathematically misaligns. On your local terminal—and on full-featured renderers like GitHub or BitBucket—the actual text output mathematically aligns perfectly!

![Screenshot: Terminal output displaying a formatted 3-column data matrix. The headers are 'Name', 'Age', and 'Nickname'. The table perfectly encapsulates complex multi-line text blocks across individual cells mapping 'Sarah Jones' directly alongside her age, wrapped inside exactly aligned rounded Unicode border geometries.](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-code-output-01.png)

## Cookbook Examples

While `Vistab` excels at rendering arrays, it's also a data-aware formatting engine. Because the API uses a **fluent** architecture, you can chain multiple logic mutations without intermediate variables.

### 1. Data Modification & Sorting

You can completely replace data sets or sequentially sort physical rows tracking exact coordinate values without needing `pandas` overhead: 
```python
table = Vistab(style="round", padding=1)

# Sort the array tracking the second column (col_idx=1) descending...
table.set_rows(my_messy_csv_data, header=True).sort_by(1, reverse=True)
```

### 2. Output Formatting & Safe Dimensional Windows

Sometimes querying SQL leaves us with extensive data dimensions. We can protect logging interfaces elegantly:
```python
# Force-limit outputs protecting CLI limits! 
table.set_max_rows(10).set_max_cols(5)
```

### 3. Shorthand Styling & Native Formatting

You don't need to pass massive syntax strings to evaluate layout injections:
```python
# Conditionally highlight physical elements:
for i, condition in enumerate(my_events):
    table.color_row(i, bg="red" if condition == 'CRITICAL' else None)

# Make the header globally bold instantly:
table.bold_header()
```

## Coordinate-Based Cell Styling

`vistab` supports a fluent, declarative API to inject background colors, foreground colors, and text styles (like bolding and underlining) targeting specific grids—ranging from individual cells, whole rows, columns, headers, or borders.

![Styling Demo](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-D-styling-demo.png)

## Coordinate-Based Word Wrapping (Nested Tables)

If you need absolute structural control over spatial layouts—for example, if you are embedding pre-rendered ASCII tables inside the cells of another `Vistab`—you can bypass the internal word-wrapping engine entirely using coordinate mapping. 

By setting `wrap=False` on specific axes, `Vistab` guarantees it will preserve your structural spacing verbatim without snapping or aggressively pruning layouts:

```python
# Globally bypass word-wrapping for the entire table
table.set_table_wrap(False)

# Or target specific structural coordinates
table.set_row_wrap(0, False)
table.set_col_wrap(2, False)
table.set_cell_wrap(0, 1, False)
```
If a cell bypassed with `wrap=False` exceeds `table.max_width`, `Vistab` uses a constraint router (`table.on_wrap_conflict = "warn"`) that securely drops trailing characters while reconstructing your internal ANSI styling sequences to prevent terminal boundary collapse.

## Streaming & Caveat Emptor Pipeline Constraints

For extremely large or infinitely generating files, you can stream data iteratively using the `--stream` flag to bypass native memory buffering constraints:

```bash
$ cat large_dataset.csv | vistab --stream
```

> [!WARNING]
> **Caveat Emptor System Limitations**: 
> When executing highly constrained pipeline commands requiring complete structured arrays logically (i.e. `--sort-by`), Vistab gracefully relies on the host OS executing standard mapping limits naturally. Pipelining infinite streams containing no explicitly terminated newlines (like `cat /dev/zero`) will unconditionally lock system buffers, triggering OS native Out-Of-Memory (OOM) failures natively similarly to standard POSIX `sort` behaviors. No artificial memory caps are injected structurally. 

## Hierarchical Configuration System
Stop re-typing your constructor arguments! `vistab` actively scans your execution environment for two distinct configuration architectures:

### 1. Default Fallbacks (`vistab.toml`)
It searches `[./.config/vistab.toml, ./.vistab.toml, ~/.config/vistab.toml, ~/.vistab.toml]` for generic table properties. 

You can generate a template configuration file to test using the CLI command:
```bash
vistab --create-config .vistab.toml
```

### 2. Custom Aesthetic Themes (`themes.json`)
You can lock in CLI layout arguments seamlessly by saving custom styles into `~/.config/vistab/themes.json` using the `--save-theme` directive. Once saved, these aesthetics become natively addressable on your machine using `--theme`.

```bash
# Safely capture a global background wash + custom last row colors 
vistab data.csv --table-bg-color bright_black --last-row-color magenta --save-theme my_custom_theme

# Execute the saved layout on another dataset modularly universally!
vistab another_data.csv --theme my_custom_theme
```

## Built-in Structural Themes

`vistab` comes with predefined structural themes including `light`, `bold`, `double`, `ascii`, `round2`, `markdown`, and others.

You can view a full structural geometry matrix printed on your terminal by executing:
```bash
vistab -L
```
![Available Styles](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-L-available-styles.png)

### The Curated Color Theme Matrix

In addition to ASCII-structural styles, `Vistab` dynamically computes 18 color layout themes utilizing Zebra-Striping. You can paint entire layouts instantly using `.apply_theme()`.

The library supports three base color palettes (`ocean`, `forest`, `minimalist`). Each color palette is distributed across six visual geometries matching the systematic format `<palette>-<striping>-<index>`. For example:

- `table.apply_theme("ocean")` *(Default Alternating Zebra Rows)*
- `table.apply_theme("ocean-index")` *(Alternating Rows + First Column Index Highlight applied)*
- `table.apply_theme("ocean-cols")` *(Alternating Column Striping)*
- `table.apply_theme("ocean-solid")` *(Static Background, No striping)*

If these 18 themes aren't enough, you can dynamically construct custom matrices by pushing a dictionary configuration directly into the global static boundary `Vistab.THEMES["my_blue_theme"] = {...}` in your own scripts.

View the curated themes rendered stacked by executing:
```bash
vistab -M
```
![Theme Output](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-M-themes-output.png)

#### Applying Themes via CLI
You can inject these structural formats directly onto raw CSVs leveraging the command line endpoints:
```bash
# Parsing files iteratively via positional bindings
vistab data.csv --theme ocean-cols-index --style round

# Routing pipes over STDIN straight from bash
echo -e "Value,Metric\n99,Speed" | vistab --theme minimalist
```

## Discovering Output Colors (CLI)

Because terminal color renderings vary across different user host profiles and color palettes, `vistab` comes packaged with a native matrix test exposing every foreground, background, and styling text option you can safely deploy. 

You can view the palette directly on the console by executing:
```bash
vistab -C
```
![Defined Colors](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-C-defined-colors.png)

## ANSI Color Layout Support

A major benchmark advantage of `vistab` is native, invisible terminal styling support. Common ASCII libraries frequently break their visual wrapper alignments when raw terminal colors are embedded because they incorrectly count invisible geometry bytes.

You can view a comprehensive color-wrapping conformance test demonstrating dynamic alignment across complex CJK blocks by executing:
```bash
vistab -T
```
![Test Output](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-T-test-output.png)

## Advanced Formatting (Datatypes)

`vistab` can infer and parse formatting rules strictly by passing data types, controlling precision dynamically for scientific floats and integers seamlessly.

```python
from vistab import Vistab

table = Vistab(style="ascii")
table.set_cols_dtype(['t', 'f', 'e', 'i', 'a']) 
table.set_cols_align(["l", "r", "r", "r", "l"])

table.add_rows([
    ["text", "float", "exp", "int", "auto"],
    ["alpha", "23.45", 543, 100, 45.67],
    ["beta", 3.1415, 1.23, 78, 56789012345.12],
    ["gamma", 2.718, 2e-3, 56.8, .0000000000128]
])
```

## Detailed API Reference

For the complete list of endpoints, configuration schemas, parameters, and wrapping constraints available in `vistab`:
**Please refer to the absolute granular [Vistab Core API Documentation](docs/API.md)**

## License

This project is licensed under the BSD 3-Clause License. See [LICENSE](LICENSE) for details.

---
[README](README.md) | [API](docs/API.md) | [CLI](docs/CLI.md) | [SPEC](FUNCTIONAL_SPEC.md) | [CHANGELOG](CHANGELOG.md)
