[README](../README.md) | [API](API.md) | [CLI](CLI.md) | [SPEC](../FUNCTIONAL_SPEC.md) | [CHANGELOG](../CHANGELOG.md)

# Vistab Command-Line Interface (CLI)

`vistab` includes a command-line utility for parsing, truncating, and styling `.csv` datasets directly in your terminal.

## Usage Overview
`vistab` tracks standard UNIX pipeline inputs and positional arguments:

```bash
# Process explicitly defined files
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
- **`--dtype`**: Force datatypes to ensure consistent output formatting (`a=auto`, `t=text`, `f=float`, `i=int`, `e=exp`).

### 3. Aesthetics & Themes
- **`-t, --theme`**: Apply predefined dynamic Zebra-Striping matrix algorithms (`ocean-cols`, `forest`).
- **`-s, --style`**: Modify the table border characters (`light`, `round2`, `markdown`).
- **`-p, --padding`**: Expand the internal whitespace padding of cells by a standard integer.
- **`--title`**: Pass a title to center above the table header.
- **`--no-header`**: Ignore header styling logic and render the first dataset row as plain data.

![Screenshot: Terminal output displaying an execution block utilizing formatting constraints and showing --no-header flags.](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-CLI-formatting.png)

### 4. Granular Color Targeting
If predefined themes aren't enough, you can explicitly override coordinate elements using discrete color arguments (`red`, `blue`, `bright_black`, `none` to remove):
- **`--border-color` / `--border-bg-color`**: Surrounding frame color.
- **`--col0-bg-color`**: Target the first column data explicitly.
- **`-l, --last-row-color` / `-A, --last-row-bg-color`**: Auto-resolves targeting the dynamic bottom offset (`-1`) natively.
- **`-x, --last-col-color` / `-y, --last-col-bg-color`**: Auto-resolves targeting the dynamic rightmost boundary.
- **`-g, --table-bg-color`**: Safely injects a global fallback background wash uniformly across the layout.

## Diagnostic Endpoints & Theme Customization

The CLI provides visual evaluation matrices to verify layouts locally:
- **`--create-config TARGET`**: Generate a standard configuration file for the current local directory (e.g., `vistab --create-config .vistab.toml`).
- **`vistab -M`**: Render a color matrix showcasing every pre-built Theme algorithm.
- **`vistab -L`**: Visualize structural framework limits parsing valid physical Table styles.
- **`vistab -C`**: Print the terminal execution dictionary safely displaying CLI colors.

### The Configuration Workflow (`--save-theme` & `--show-code`)
You can lock in CLI outputs saving configurations mapped to `~/.config/vistab/themes.json` using `--save-theme`:
```bash
# Safely bind complex global bounds preventing dictionary bleed natively
vistab data.csv --theme minimalist --table-bg-color bright_black --last-row-color magenta --save-theme my_custom_theme
```

Use `--show-code` to generate the literal Python initialization dictionary reproducing your aesthetic layout. 
**Note:** Built-in Vistab configurations intentionally strictly strip *rigid data modifiers* (like `--align` and `--width`) from the global dictionary registry so styles can adapt modularly across arbitrary datasets safely without throwing boundary exceptions.

```bash
vistab data.csv --theme minimalist --table-bg-color bright_black --align lrl --show-code
```

![Screenshot: Massive colorful logical matrix block structurally displaying 15 different theme executions mapped perfectly across distinct visual borders sequentially rendering dynamic zebra-striping.](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-M-themes-output.png)

---
[README](../README.md) | [API](API.md) | [CLI](CLI.md) | [SPEC](../FUNCTIONAL_SPEC.md) | [CHANGELOG](../CHANGELOG.md)
