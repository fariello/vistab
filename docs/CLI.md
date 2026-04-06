# Vistab Command-Line Interface (CLI)

`vistab` natively acts as a vastly powerful command-line utility for parsing, truncating, and beautifully styling `.csv` datasets physically entirely within your terminal without touching Python logic.

## Usage Overview
To seamlessly render a raw delimited file securely structurally:
```bash
vistab --input data.csv
```
![Basic CLI Execution](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-CLI-basic.png)


## Formatting Configs & Structure Limits

The CLI naturally captures all data layout, spacing, and wrapper restrictions tracking parameters gracefully!

### 1. Dimension Wrappers
- **`-w, --width`**: Limits global maximum table geometries natively bounding sequences safely (0 = infinite wraps).
- **`-W, --col-widths`**: Explicit array of bounding integers statically forcing geometry cleanly (e.g., `--col-widths 10,20,5`).
- **`-r, --max-rows`**: Maps boundaries tracking row execution bounds limits (e.g., `-r 50`).
- **`-c, --max-cols`**: Aggressively drops right-most bounds physically protecting visual interfaces smoothly.

### 2. Alignment Logic and Typing
*Provide one character chronologically evaluating your specific CSV geometries sequence!*
- **`-a, --align`**: Target horizontal tracking alignments seamlessly (`l=left`, `c=center`, `r=right`). Example: `-a lrc`
- **`--valign`**: Maps cell internal evaluations vertically natively (`t=top`, `m=middle`, `b=bottom`). Example: `--valign ttb`
- **`--dtype`**: Force datatypes actively ensuring outputs format consistently (`a=auto`, `t=text`, `f=float`, `i=int`, `e=exp`).

### 3. Aesthetics & Themes
- **`-t, --theme`**: Statically map beautiful dynamic Zebra-Striping matrix algorithms dynamically parsing data (`ocean-cols`, `forest`).
- **`-s, --style`**: Modifies the boundary rendering strings cleanly (`light`, `round2`, `markdown`).
- **`-p, --padding`**: Expands visual footprint integers pushing whitespace internally smoothly.
- **`--title`**: Passes a centered string elegantly displaying over the header organically.
- **`--no-header`**: Tracks boolean variables silently injecting plain data structures (prevents treating the top `.csv` line globally as formal column headers).

![Terminal Formatting Configuration](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-CLI-formatting.png)

## Diagnostic Endpoints

The CLI natively provides visual evaluation matrices allowing you to verify rendering structures locally gracefully tracking outputs!
- **`vistab -M`**: Render a massive color matrix showcasing every single pre-built Theme algorithm physically globally.
- **`vistab -L`**: Visualize structural framework limits parsing valid physical Table styles mapped explicitly natively.
- **`vistab -C`**: Prints the native execution dictionary safely displaying CLI colors organically (`fg="red"`, etc.).

![Diagnostic Endpoints](https://raw.githubusercontent.com/fariello/vistab/main/docs/assets/vistab-CLI-diagnostics.png)
