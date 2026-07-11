[README](../README.md) | [API](API.md) | [CLI](CLI.md) | [SPEC](../FUNCTIONAL_SPEC.md) | [CHANGELOG](../CHANGELOG.md)

# Vistab Command-Line Interface (CLI)

`vistab` includes a command-line utility for parsing, truncating, and styling `.csv` datasets directly in your terminal.

## Usage Overview
`vistab` tracks standard UNIX pipeline inputs and positional arguments:

```bash
# Process defined files
vistab data.csv

# Process multiple datasets sequentially
vistab file1.csv file2.csv logs.tsv

# Pipe standard stdout directly into vistab
echo -e "Name,Age\nGabriel,25" | vistab --theme forest-index
```
![Screenshot: Terminal output showing vistab successfully executing a parsed CSV structure displaying a table with colored columns.](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-CLI-basic.png)

## Formatting Configurations

The CLI lets you manage data layout, spacing, and wrapper constraints via standard flags.

### 1. Dimension Wrappers
- **`-w, --width`**: Limits global maximum table geometries (0 = infinite wraps).
- **`-W, --col-widths`**: Explicit comma-separated array of bounding integers (e.g., `--col-widths 10,20,5`).
- **`-r, --max-rows`**: Sets the maximum number of rows to print (e.g., `-r 50`).
- **`-c, --max-cols`**: Drops the right-most columns to fit within a specific limit.

### 2. Alignment Logic and Typing
*Provide a single character sequence to evaluate columns chronologically.*
- **`-a, --align`**: Target horizontal alignments (`l=left`, `c=center`, `r=right`). Example: `-a lrc`
- **`--valign`**: Target vertical alignments (`t=top`, `m=middle`, `b=bottom`). Example: `--valign ttb`
- **`--dtype`**: Force datatypes to ensure uniform output.
   * **Categories:** `a=auto`, `t=text`, `f=float`, `i=int`, `e=scientific`.
   * **Auto Inference (`a`)**: Applies uniform cascades resolving floating point formatting across unified columns.
   * **Inline Precisions (`f2`, `e5`)**: Apply exact numeric overlays directly without arrays. Example: `--dtype "i,f2,e4"`

### 3. Data Pipelines & Streaming
- **`--stream`**: Bypasses full array buffering, printing mapped iterations continuously.
- **`--stream-probe`**: Scans the first N rows computationally to align continuous widths upfront (default: 50).
- **`--sort-by INDEX`**: Sort arrays structurally based on a specified column index (0-indexed).
- **`--sort-reverse`**: Flip sorting logic mapped off `--sort-by`.
- **`--csv-dialect NAME`**: Enforce native Python CSV sniffer logic for specific structure parsing.
- **`--on-short ACTION`**: Set boundary routing for missing CSV columns (`pad`, `skip`, `raise`).
- **`--on-long ACTION`**: Route overflowing row alignments (`truncate`, `skip`, `raise`).
- **`--mark-abnormal COLOR`**: Apply rapid visual diagnostics highlighting data arrays that conflict with boundaries.

### 4. Aesthetics & Themes
- **`-t, --theme`**: Apply predefined dynamic Zebra-Striping matrix algorithms (`ocean-cols`, `forest`).
- **`-s, --style`**: Modify the table border characters (`light`, `round-header`, `markdown`).
- **`--style-def`**: Override standard styles using an explicit 15 or 4-character string configuring exact structural boundaries (e.g., `--style-def "═║╔╗╚╝╠╣╦╩╬═╠╣╬"`). To get a feel for which characters are used to draw which borders, try `vistab tests/data/test_5x11.csv --style-def "ABCDEFGHIJKLMNO"` or `vistab tests/data/test_5x11.csv --style-def "ABCD"`.
- **`-p, --padding`**: Expand the internal whitespace padding of cells by a standard integer.
- **`--title`**: Pass a title to center above the table header.
- **`--no-header`**: Ignore header styling logic and render the first dataset row as plain data.

![Screenshot: Terminal output displaying an execution block utilizing formatting constraints and showing --no-header flags.](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-CLI-formatting.png)

### 5. Granular Color Targeting
If predefined themes aren't enough, you can override coordinate elements using discrete color arguments (`red`, `blue`, `bright_black`, `none` to remove):
- **`--border-color` / `--border-bg-color`**: Surrounding frame color.
- **`--col0-bg-color`**: Target the first column data.
- **`-l, --last-row-color` / `-A, --last-row-bg-color`**: Target the dynamic bottom offset (`-1`).
- **`-x, --last-col-color` / `-y, --last-col-bg-color`**: Target the dynamic rightmost boundary.
- **`-g, --table-bg-color`**: Apply a global background wash uniformly across the layout.

## Command-Based Subcommands & Diagnostic Demos

Vistab supports a natural subject/verb/object CLI subcommand syntax:

### 1. The `show` Command
Visualize current capabilities and formatting styles. Flags remain supported as aliases (e.g. `vistab show themes` is identical to `vistab --demo themes`):
- **`vistab show themes`** (alias: `--demo themes`): Render a color matrix showcasing every pre-built Theme algorithm.
- **`vistab show styles`** (alias: `--demo styles`): Visualize structural framework limits parsing valid physical Table styles.
- **`vistab show colors`** (alias: `--demo colors`): Print the terminal execution dictionary displaying CLI colors.
- **`vistab show capabilities`** (alias: `show caps`, `show wrapping`, `--demo capabilities`): ANSI + CJK-safe word-wrapping and datatype-parsing conformance.
- **`vistab show anatomy`** (alias: `--demo anatomy`): Labeled diagram of a table's parts (borders, header, cells) and coordinate styling.
- **`vistab show span`** (alias: `show spans`, `demo span`, `--demo span`): Column-spanning demonstration with example code beneath each table.

Colors can be disabled globally with `--no-color` (or by setting the `NO_COLOR` environment variable); vistab then emits no styling escapes of its own, and a color-focused demo prints a `WARNING: colors turned off ...` notice to stderr so the monochrome output is not confusing.

### 2. The `demo` Command
Run interactive feature demonstrations:
- **`vistab demo span`** (alias: `demo colspan`, `demo rowspan`, `--demo span`): Render a comprehensive column spanning (colspan) demo in action, with the corresponding Python code printed directly to stdout.

### 3. The `help` Command
Show contextual help screens:
- **`vistab help colors`** (alias: `--help-colors`): Show advanced coordinate-based color parameters.
- **`vistab help advanced`** (alias: `help adv`, `--help-advanced`): Show advanced streaming, sorting, and jagged matrix behaviors.

### Unknown Subjects and Error Handling
If an unknown subject is passed (e.g. `vistab show invalid`), the CLI writes a list of valid subjects to **stderr** and exits with code **2**. A bare verb command (e.g. `vistab show` or `vistab demo`) prints the same list of valid subjects to **stdout** and exits cleanly with code **0**.

> [!IMPORTANT]
> **Reserved File Name Collisions**: Because `show`, `demo`, and `help` are reserved subcommand words, if you attempt to render a local file literally named `show`, `demo`, or `help`, Vistab will try to run the subcommand instead. To bypass this collision, specify the relative path to the file (e.g., `vistab ./show`) or pass it via the input flag (e.g., `vistab -i show`).

### 4. Configuration Diagnostics
- **`-K, --create-config TARGET`**: Generate a standard configuration file globally by default, or mapped to a passed target path (e.g. `vistab --create-config` creates `~/.config/vistab/config.toml`).
- **`-Q, --show-config`**: Print the paths mapping global dynamic configuration directories and exit.


### The Configuration Workflow (`--save-theme` & `--show-code`)
You can lock in CLI outputs saving configurations mapped to `~/.config/vistab/themes.json` using `--save-theme`:
```bash
# Bind global layout styles to a custom alias
vistab data.csv --theme graphite --table-bg-color bright_black --last-row-color magenta --save-theme my_custom_theme
```

Use `--show-code` to generate the literal Python dictionary reproducing your aesthetic layout. 
**Note:** Built-in Vistab configurations intentionally strip *rigid data modifiers* (like `--align` and `--width`) from the theme registry so styles can adapt modularly across arbitrary datasets without throwing boundary exceptions.

```bash
vistab data.csv --theme graphite --table-bg-color bright_black --align lrl --show-code
```

![Screenshot: a grid of vistab's built-in theme macros rendered in the terminal.](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-demo-themes-01.png)

---
[README](../README.md) | [API](API.md) | [CLI](CLI.md) | [SPEC](../FUNCTIONAL_SPEC.md) | [CHANGELOG](../CHANGELOG.md)
