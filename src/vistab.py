#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This was inspired by texttable, an excellent lightweight module for creating simple ASCII tables by Gerome Fournier <jef(at)foutaise.org>. Thank you for your inspiration.
# Copyright (C) 2018-2026 Gabriele Fariello where applicable.

r"""vistab: a Python LIBRARY for building aligned, color-aware text tables.

Import it and call the API; do not shell out to the CLI for programmatic use:

    from vistab import Vistab
    t = Vistab(header=["Name", "Age"])
    t.add_row(["Sarah", 27])
    t.set_cols_align(["l", "r"])
    print(t.draw())

A command-line entry point also exists for ad-hoc CSV/terminal use (see docs/CLI.md),
but in Python code prefer `from vistab import Vistab`.

Example:

    table = Vistab()
    table.set_cols_align(["l", "r", "c"])
    table.set_cols_valign(["t", "m", "b"])
    table.add_rows([["Name", "Age", "Nickname"],
                    ["Ms\\nSarah\\nJones", 27, "Sarah"],
                    ["Mr\\nJohn\\nDoe", 45, "Johnny"],
                    ["Dr\\nEmma\\nBrown", 34, "Em"]])
    print(table.draw() + "\\n")

    table = Vistab()
    table.set_decorations(Vistab.HEADER)
    table.set_cols_dtype(['t',  # text
                          'f',  # float (decimal)
                          'e',  # float (exponent)
                          'i',  # integer
                          'a']) # automatic
    table.set_cols_align(["l", "r", "r", "r", "l"])
    table.add_rows([["text",    "float", "exp", "int", "auto"],
                    ["alpha",    "23.45", 543,   100,    45.67],
                    ["beta",     3.1415,  1.23,  78,    56789012345.12],
                    ["gamma",    2.718,   2e-3,  56.8,  .0000000000128],
                    ["delta",    .045,    1e+10, 92,    89000000000000.9]])
    print(table.draw())

Result:

    +--------+-----+---------+
    |  Name  | Age | Nickname|
    +========+=====+=========+
    | Ms     |     |         |
    | Sarah  |  27 |         |
    | Jones  |     |  Sarah  |
    +--------+-----+---------+
    | Mr     |     |         |
    | John   |  45 |         |
    | Doe    |     | Johnny  |
    +--------+-----+---------+
    | Dr     |     |         |
    | Emma   |  34 |         |
    | Brown  |     |    Em   |
    +--------+-----+---------+

    text    float       exp       int         auto
    ==============================================
    alpha   23.450    5.430e+02   100       45.670
    beta    3.142     1.230e+00   78        5.679e+10
    gamma   2.718     2.000e-03   57        1.280e-11
    delta   0.045     1.000e+10   92        8.900e+13
"""

import os
import sys

# Ensure Windows legacy cmd.exe supports ANSI formatting
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass

from typing import Union

try:
    from wcwidth import wcswidth  # For calculating the display width of unicode characters
except ImportError:
    sys.stderr.write("[\033[1;33mWARN\033[0m] For accurate terminal rendering alignment with wide characters, the wcwidth library is needed. Please use `pip install wcwidth` to fix this issue.\n")

    def wcswidth(text):
        return sum(1 for _ in text)
import re  # Regular expressions for text processing
import sys  # System-specific parameters and functions
from typing import List, Optional, Iterable, Any, Iterator, Set  # Type hints for better code clarity
from functools import reduce, lru_cache  # Higher-order function for performing cumulative operations
from decimal import Decimal, ROUND_HALF_UP  # symmetric round-half-away-from-zero for integer formatting


def _round_half_up(value: float) -> int:
    """Round to the nearest integer, ties away from zero (2.5 -> 3, -2.5 -> -3).

    Python's built-in round() uses banker's rounding (round-half-to-even), which surprises
    users formatting numbers as integers. Decimal(str(value)) avoids binary float artifacts.
    """
    return int(Decimal(str(value)).quantize(Decimal(0), rounding=ROUND_HALF_UP))

__all__ = ["Vistab", "ArraySizeError", "StringLengthCalculator", "ColSpan"]

__author__ = 'Gabriele Fariello <gfariello@fariel.com>'
__license__ = 'BSD 3-Clause 2026'
__version__ = '1.2.1'

# Column data-type codes: the single source of truth. Each entry is (code, short label,
# explanation). Used by set_cols_dtype validation/errors, the CLI --dtype help, and the CLI
# format-error tip so the valid types are enumerated and explained in exactly one place.
COLUMN_DTYPES = [
    ("a", "auto",     "automatic: pick the most appropriate type per column (the default)"),
    ("t", "text",     "treat the value as plain text (no numeric coercion)"),
    ("i", "int",      "integer"),
    ("I", "int,",     "integer with thousands separators (e.g. 1,234,567)"),
    ("f", "float",    "fixed-point decimal (e.g. 3.14)"),
    ("F", "float,",   "float with thousands separators (e.g. 123,456.79)"),
    ("e", "exp",      "scientific/exponential notation (e.g. 3.14e+00)"),
    ("E", "exp,",     "scientific/exponential with thousands separators"),
]
# Numeric codes (i, I, f, e) accept an optional precision suffix, e.g. 'f2' = 2 decimals.
_DTYPE_CODES = tuple(code for code, _, _ in COLUMN_DTYPES)


def _dtype_help(oneline: bool = False) -> str:
    """Human-readable enumeration of every valid column data-type code."""
    if oneline:
        return ", ".join(f"'{c}' ({label})" for c, label, _ in COLUMN_DTYPES)
    lines = [f"  {c}  {label:<6} {desc}" for c, label, desc in COLUMN_DTYPES]
    lines.append("  numeric codes (i, I, f, F, e, E) accept an optional precision suffix, e.g. 'F2'")
    lines.append("  for CURRENCY (e.g. $123,456.79) use the library API with a callable:")
    lines.append("  set_cols_dtype([lambda v: f\"${float(v):,.2f}\"])")
    return "\n".join(lines)


# CLI color state for the built-in demos. Set by main() from --no-color / NO_COLOR.
# _CLI_COLOR_TRIGGER records WHY color was suppressed, for an honest warning.
_CLI_COLOR = True
_CLI_COLOR_TRIGGER = None  # one of: None, "--no-color", "NO_COLOR"

# CLI bidi state. Set by main() from --no-bidi. See Vistab.set_bidi.
_CLI_BIDI = True

# Unicode LTR isolate wrappers (UAX #9). Zero-width; wrapping a cell's content in these
# makes the terminal treat the cell as a self-contained bidi island, so RTL (Arabic/Hebrew)
# content no longer reorders the whole table line. See Vistab.set_bidi.
_LRI = "\u2066"  # LEFT-TO-RIGHT ISOLATE
_PDI = "\u2069"  # POP DIRECTIONAL ISOLATE

# Strong right-to-left script blocks. If a cell contains any of these, the terminal will
# flip the physical line unless we isolate cells. We detect the scripts, not the invisible
# RTL control characters.
_RTL_RE = re.compile(
    "[\u0590-\u05FF"   # Hebrew
    "\u0600-\u06FF"    # Arabic
    "\u0700-\u074F"    # Syriac
    "\u0750-\u077F"    # Arabic Supplement
    "\u0780-\u07BF"    # Thaana
    "\u08A0-\u08FF"    # Arabic Extended-A
    "\uFB1D-\uFB4F"    # Hebrew presentation forms
    "\uFB50-\uFDFF"    # Arabic Presentation Forms-A
    "\uFE70-\uFEFF]"   # Arabic Presentation Forms-B
)


def _contains_rtl(text: str) -> bool:
    """True if the string contains any strong right-to-left script character."""
    return bool(_RTL_RE.search(text))


def _demo_text(s: str) -> str:
    """Pass demo text through unchanged when CLI color is on; strip ANSI escapes when off.

    The built-in demos embed literal escape sequences (titles, color swatches) that do not
    flow through Vistab's styling helpers, so this helper enforces --no-color for them too.
    """
    if _CLI_COLOR:
        return s
    return StringLengthCalculator._ANSI_ESCAPE.sub('', s)


def _maybe_warn_color_off():
    """Print an honest 'colors turned off' warning after a color-dependent demo.

    No-op when color is on. Names the actual trigger (--no-color or NO_COLOR).
    Goes to stderr so it stays out of the primary (captured) stdout payload.
    """
    if _CLI_COLOR:
        return
    trigger = _CLI_COLOR_TRIGGER or "--no-color"
    sys.stderr.write(f"WARNING: colors turned off by {trigger}\n")

__credits__ = """\
Gabriele Fariello <gfariello@fariel.com>
    - Wrote this module adding robust handling for unicode characters and ANSI escape sequences
    - Added support for CJK characters
    - Added support for right-to-left languages
    - Added support for right-to-left languages
    - Added color support
    - Added unicode table border support
    - Added ability to limit large tables
    - Added ability to format rows and columns
    - Added copious other features
    - Fixed a few bugs in the original code having to do with edge cases
Gerome Fournier <jef(at)foutaise.org>
    - Inspiration from his TextTable Python module from which
      this takes a LOT.
Others who contributed to Gerome's work and therefore mine, so I'm including them
from when I copied the file around 2018 or so:

Jeff Kowalczyk:
    - textwrap improved import
    - comment concerning header output

Anonymous:
    - add_rows method, for adding rows in one go

Sergey Simonenko:
    - redefined len() function to deal with non-ASCII characters

Roger Lew:
    - columns datatype specifications

Brian Peterson:
    - better handling of unicode errors

Frank Sachsenheim:
    - add Python 2/3-compatibility

Maximilian Hils:
    - fix minor bug for Python 3 compatibility

frinkelpi:
    - preserve empty lines
"""

# Attempt to define a text wrapping function to wrap text to a specific width
# - Use cjkwrap if available (provides better support for CJK characters)
# - Fallback to textwrap if cjkwrap is not available
_cjkwrap_available = None


def textwrapper(txt, width):
    """
    Wrap text to a specified width. If cjkwrap is available, it handles Asian characters properly.
    Otherwise, it warns the user (once) and falls back to textwrap.

    Args:
        txt (str): The text to wrap.
        width (int): The maximum width of each line.

    Returns:
        List[str]: A list of wrapped lines.
    """
    global _cjkwrap_available
    if _cjkwrap_available is None:
        try:
            import cjkwrap
            _cjkwrap_available = True
        except ImportError:
            _cjkwrap_available = False
            import sys
            sys.stderr.write("[\033[1;33mWARN\033[0m] For correct Asian/CJK characters wrapping, the cjkwrap library is needed. Please use `pip install vistab[cjk]` to fix this issue.\n")

    if _cjkwrap_available:
        import cjkwrap
        return cjkwrap.wrap(txt, width)
    else:
        import textwrap
        return textwrap.wrap(txt, width)


class ArraySizeError(Exception):
    """Exception raised when adding a row with a different number of columns than initialized."""
    pass


class VistabOverflowError(ValueError):
    """Exception raised when an explicit `wrap=False` literal violates `max_width` dimensions under strict `on_wrap_conflict`."""
    pass


class ColSpan:
    """Public wrapper to define column spanning inline during data initialization."""
    def __init__(self, value: Any, colspan: Optional[int] = None, span: Optional[int] = None):
        if colspan is not None and span is not None:
            if colspan != span:
                raise ValueError("Conflicting values for colspan and span.")
            resolved_colspan = colspan
        elif colspan is not None:
            resolved_colspan = colspan
        elif span is not None:
            resolved_colspan = span
        else:
            resolved_colspan = 2

        if not isinstance(resolved_colspan, int) or resolved_colspan < 1:
            raise ValueError("Colspan must be an integer >= 1")
        self.value = value
        self.colspan = resolved_colspan

    @property
    def span(self) -> int:
        """Alias for colspan for backward-compatibility."""
        return self.colspan

    @span.setter
    def span(self, value: int):
        if not isinstance(value, int) or value < 1:
            raise ValueError("Colspan must be an integer >= 1")
        self.colspan = value


class VistabCell:
    """Internal cell representation holding span metadata."""
    def __init__(self, value: Any, colspan: int = 1, rowspan: int = 1):
        self.value = value
        self.colspan = colspan
        self.rowspan = rowspan
        self.is_placeholder = False
        self.source_cell = None

    def __str__(self):
        return "" if self.value is None else str(self.value)


class VistabPlaceholderCell(VistabCell):
    """Sentinel placeholder occupying coordinates covered by a spanned cell."""
    def __init__(self, source_cell: VistabCell):
        super().__init__(value="")
        self.is_placeholder = True
        self.source_cell = source_cell
        self.colspan = source_cell.colspan
        self.rowspan = source_cell.rowspan


class StringLengthCalculator:
    """
    A class to calculate the visible length of a string, excluding ANSI escape sequences.

    This class is designed to handle strings containing ANSI escape sequences (used for text formatting) and
    accurately calculate their visible length. ANSI escape sequences are ignored in the length calculation,
    ensuring the actual displayed length of the text is returned.

    Attributes:
    -----------
    ansi_escape : re.Pattern
        A compiled regular expression pattern to match ANSI escape sequences.

    Methods:
    --------
    len(string: str) -> int
        Calculates the visible length of a string, excluding ANSI escape sequences.

    Example:
    --------
    ```
    calculator = StringLengthCalculator()
    colored_string = "\033[1;31mRed text\033[0m"
    length = calculator.len(colored_string)
    print(length)  # Outputs: 8
    ```

    The above example demonstrates how to use the `StringLengthCalculator` to get the length of a string
    without counting the ANSI escape sequences.
    """

    # Regular expression to match ANSI escape sequences
    # ANSI escape sequences are used for text formatting (e.g., colors)
    _ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def __init__(self):
        self.ansi_escape = self._ANSI_ESCAPE
        pass  # for auto-indentation

    @staticmethod
    @lru_cache(maxsize=8192)
    def len(string: str) -> int:
        """
        Calculate the visible length of a string, excluding ANSI escape sequences.

        Args:
        -----
        string : str
            The string whose visible length should be calculated.

        Returns:
        --------
        int
            The visible length of the string.

        Example:
        --------
        ```
        calculator = StringLengthCalculator()
        colored_string = "\033[1;31mRed text\033[0m"
        length = calculator.len(colored_string)
        print(length)  # Outputs: 8
        ```

        The above example shows how to use the `len` method to calculate the visible length of a string with ANSI escape sequences.
        """
        # Remove ANSI escape sequences from the string
        visible_string = StringLengthCalculator._ANSI_ESCAPE.sub('', string)

        # Return the length of the visible string
        # wcswidth returns the number of cells the string occupies when printed
        return wcswidth(visible_string)

    pass  # for auto-indentation


def _strip_ansi(text: str) -> str:
    """
    Remove all ANSI color and style escape sequences from a string.

    Args:
    -----
    text : str
        The string containing ANSI escape sequences to process.

    Returns:
    --------
    str
        The cleaned string containing textual characters.

    Important Behavior:
    -------------------
    This targets the standard terminal \\x1B escape mappings that define structural and foreground elements.
    It leverages the compiled regex globally cached in `StringLengthCalculator` to process replacements.

    Example:
    --------
    ```python
    clean_text = _strip_ansi("\\033[1;31mRed text\\033[0m")
    print(clean_text)  # "Red text"
    ```
    """
    if type(text) == str:
        return StringLengthCalculator._ANSI_ESCAPE.sub('', text)
    return text

class ColorAwareWrapper:
    """
    Class to wrap text to a specified width, excluding ANSI escape sequences.

    This class ensures that text containing ANSI escape sequences (used for text formatting) is wrapped correctly
    without disrupting the formatting. It calculates the visible length of text by excluding these sequences
    and wraps the text to the specified width.

    Attributes:
    -----------
    calculator : StringLengthCalculator
        An instance of StringLengthCalculator to handle the calculation of string lengths excluding ANSI escape sequences.

    Methods:
    --------
    wrap(text: str, width: int) -> str
        Wraps text to the specified width, ignoring ANSI escape sequences.

    Example:
    --------
    ```
    wrapper = ColorAwareWrapper()
    colored_text = "This is \033[1;31mred\033[0m and this is \033[1;32mgreen\033[0m."
    wrapped_text = wrapper.wrap(colored_text, 20)
    print(wrapped_text)
    ```

    The above example would produce:
    ```
    This is \033[1;31mred\033[0m
    and this is
    \033[1;32mgreen\033[0m.
    ```
    """
    def __init__(self):
        # Initialize an instance of StringLengthCalculator to handle ANSI escape sequences
        self.calculator = StringLengthCalculator()
        pass  # for auto-indentation

    def _break_word(self, word: str, width: int) -> List[str]:
        """
        Chunks a continuously contiguous string mathematically over width
        preserving ANSI nested styles.
        """
        if width <= 0:
            return [word]

        chunks = []
        parts = re.split(StringLengthCalculator._ANSI_ESCAPE, word)
        codes = StringLengthCalculator._ANSI_ESCAPE.findall(word)

        current_chunk = ''
        current_vis_len = 0
        active_codes = []

        for i, part in enumerate(parts):
            for char in part:
                char_vis_len = self.calculator.len(char)
                if current_vis_len + char_vis_len > width:
                    if current_vis_len > 0:
                        if active_codes:
                            chunks.append(current_chunk + "\033[0m")
                            current_chunk = "".join(active_codes) + char
                        else:
                            chunks.append(current_chunk)
                            current_chunk = char
                        current_vis_len = char_vis_len
                    else:
                        current_chunk += char
                        current_vis_len += char_vis_len
                else:
                    current_chunk += char
                    current_vis_len += char_vis_len

            if i < len(codes):
                code = codes[i]
                if code == "\033[0m":
                    active_codes = []
                else:
                    active_codes.append(code)
                current_chunk += code

        if current_chunk:
            if active_codes and StringLengthCalculator._ANSI_ESCAPE.sub('', current_chunk) != '':
                chunks.append(current_chunk + "\033[0m")
            elif current_vis_len > 0 or not chunks:
                chunks.append(current_chunk)

        return chunks

    def wrap_list(self, text: str, width: int) -> List[str]:
        """Core wrapping logic returning a list of lines."""
        words = text.split()
        line, result = [], []

        for word in words:
            line_length = self.calculator.len(' '.join(line))
            word_length = self.calculator.len(word)

            # space length accounting
            space_length = 1 if line else 0

            if line_length + space_length + word_length > width:
                if line:
                    result.append(' '.join(line))
                    line = []

                if word_length > width:
                    # Individual word is larger than column width constraint. Break it intelligently spanning ANSI.
                    broken_chunks = self._break_word(word, width)
                    result.extend(broken_chunks[:-1])
                    line = [broken_chunks[-1]] if broken_chunks else []
                else:
                    line = [word]
            else:
                line.append(word)

        if line:
            result.append(' '.join(line))

        return result

    def wrap(self, text: str, width: int) -> str:
        """
        Wraps text to the specified width, ignoring ANSI escape sequences.
        ...
        """
        return '\n'.join(self.wrap_list(text, width))

    pass  # for auto-indentation


def obj2unicode(obj: Any) -> str:
    """
    Return a unicode representation of a Python object.

    This function converts a given Python object to its unicode string representation.
    It handles strings, bytes, and other types by converting them appropriately.

    Args:
    -----
    obj : Any
        The Python object to convert to a unicode string.

    Returns:
    --------
    str
        The unicode string representation of the input object.

    Example:
    --------
    ```
    print(obj2unicode("test"))  # Outputs: 'test'
    print(obj2unicode(b'test'))  # Outputs: 'test'
    print(obj2unicode(123))  # Outputs: '123'
    ```
    """
    if isinstance(obj, str):
        return obj  # Return the string as it is
    elif isinstance(obj, bytes):
        return obj.decode()  # Decode bytes to string
    return str(obj)  # Convert other types to string


class ArraySizeError(Exception):
    """
    Exception raised when specified rows don't fit the required size.

    This custom exception is used to indicate that an operation involving rows in
    a table or array has failed because the specified rows do not match the expected size.

    Attributes:
    -----------
    msg : str
        The error message describing the reason for the exception.

    Methods:
    --------
    __str__() -> str
        Returns the error message as a string.
    """

    def __init__(self, msg: str):
        """
        Initialize the ArraySizeError with an error message.

        Args:
        -----
        msg : str
            The error message describing the reason for the exception.

        Example:
        --------
        ```
        raise ArraySizeError("Row size mismatch")
        ```
        """
        self.msg = msg  # Store the error message
        Exception.__init__(self, msg, '')  # Initialize the base Exception class
        pass  # for auto-indentation

    def __str__(self) -> str:
        """
        Return the error message as a string.

        Returns:
        --------
        str
            The error message describing the reason for the exception.

        Example:
        --------
        ```
        error = ArraySizeError("Row size mismatch")
        print(str(error))  # Outputs: 'Row size mismatch'
        ```
        """
        return self.msg  # Return the stored error message

    pass  # for auto-indentation


class FallbackToText(Exception):
    """
    Exception used for failed conversion to float.

    This custom exception indicates that a conversion to a float has failed and
    the operation should fallback to handling the value as text.

    Example:
    --------
    ```
    try:
        value = float(some_value)
    except ValueError:
        raise FallbackToText()
    ```
    """
    pass  # for auto-indentation


class Vistab:
    """Build aligned, color-aware text tables (ASCII/Unicode) for the terminal.

    Quick start:

        from vistab import Vistab
        t = Vistab(header=["Name", "Age"])
        t.add_row(["Sarah", 27])
        t.set_cols_align(["l", "r"])
        print(t.draw())

    Add rows/headers, choose a style or theme, set per-column alignment/data types, and call
    `draw()` to get the rendered string. Supports styles, borders, headers, decorations, column
    spanning, CJK/RTL-correct widths, and color-aware word wrapping.

    Attributes:
    -----------
    BORDER : int
        A constant for enabling border decoration.
    HEADER : int
        A constant for enabling header decoration.
    HLINES : int
        A constant for enabling horizontal lines between rows.
    VLINES : int
        A constant for enabling vertical lines between columns.
    TOP : int
        A constant representing the top border position.
    MIDDLE : int
        A constant representing the middle position for lines.
    BOTTOM : int
        A constant representing the bottom border position.
    STYLES : dict
        A dictionary mapping style names to their corresponding border characters.
    STYLE_MAPPER : dict
        A dictionary mapping complex style patterns to their corresponding characters.

    Example usage:
    --------------
    ```
    table = Vistab()
    table.set_cols_align(["l", "r", "c"])
    table.add_rows([["Name", "Age"], ["Alice", 25], ["Bob", 30]])
    print(table.draw())
    ```
    """

    # Constants for table decorations
    BORDER = 1  # Border around the table
    HEADER = 1 << 1  # Header line below the header
    HLINES = 1 << 2  # Horizontal lines between rows
    VLINES = 1 << 3  # Vertical lines between columns

    # Constants for line positions
    TOP = 0  # Top border position
    MIDDLE = 1  # Middle position for lines
    BOTTOM = 2  # Bottom border position

    _ANSI_DESTRUCTIVE_RE = __import__('re').compile(r'\x1b\[[0-9;]*[A-DEFGHJKST]')
    _ANSI_RESET_RE_INTERCEPT = __import__('re').compile(r'(\x1b\[[0-9;]*m)')

    # ANSI Formatting Constants
    COLORS = {
        "black": "30", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "magenta": "35", "cyan": "36", "white": "37",
        "bright_black": "90", "bright_red": "91", "bright_green": "92", "bright_yellow": "93",
        "bright_blue": "94", "bright_magenta": "95", "bright_cyan": "96", "bright_white": "97"
    }
    BG_COLORS = {
        "black": "40", "red": "41", "green": "42", "yellow": "43",
        "blue": "44", "magenta": "45", "cyan": "46", "white": "47",
        "bright_black": "100", "bright_red": "101", "bright_green": "102", "bright_yellow": "103",
        "bright_blue": "104", "bright_magenta": "105", "bright_cyan": "106", "bright_white": "107"
    }
    TEXT_STYLES = {
        "bold": "1", "faint": "2", "italic": "3", "underline": "4",
        "blink": "5", "reverse": "7", "strike": "9"
    }

    # Dictionary defining various table styles and their corresponding border characters
    STYLES = {
        "ascii": "-|+-",  # Basic ASCII style
        "ascii-header": "-|+=",  # ASCII style with different header separators
        "double": "═║╔╗╚╝╠╣╦╩╬═╠╣╬",  # Double line style
        "double-horizontal": "═│╒╕╘╛╞╡╤╧╪═╞╡╪", # Double horizontal lines.
        "double-vertical": "─║╓╖╙╜╟╢╥╨╫─╟╢╫", # Double vertical lines.
        "light": "─│┌┐└┘├┤┬┴┼─├┤┼",  # Light line style
        "light-header": "─│┌┐└┘├┤┬┴┼═╞╡╪",  # Light line style with double headers
        "round": "─│╭╮╰╯├┤┬┴┼─├┤┼",  # Round corners style
        "round-header": "─│╭╮╰╯├┤┬┴┼═╞╡╪",  # Round corners style with double headers
        "heavy": "━┃┏┓┗┛┣┫┳┻╋━┣┫╋",  # Heavy style
        "dashed": "┄┆┌┐└┘├┤┬┴┼┄├┤┼", # Dashed lines
        "dots": "┈┊┌┐└┘├┤┬┴┼┈├┤┼",   # Dotted dashed lines
        "markdown": " |         -|||", # GitHub Flavored Markdown
        "booktabs": ["━", "", "", "", "", "", "", "", "", "", "", "─", "", "", ""], # Academic horizontal rules
        "none": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],  # No lines style
    }

    # Dictionary mapping complex style patterns to specific characters
    STYLE_MAPPER = {
        "heavy": {
            "---w": " ", "--e-": " ", "--ew": "━", "-s--": " ", "-s-w": "┓", "-se-": "┏", "-sew": "┳",
            "n---": " ", "n--w": "┛", "n-e-": "┗", "n-ew": "┻", "ns--": "┃", "ns-w": "┫", "nse-": "┣", "nsew": "╋",
        },
        "light-header": {
            "---w": " ", "--e-": " ", "--ew": "-", "-s--": " ", "-s-w": "┐", "-se-": "┌", "-sew": "┬",
            "n---": " ", "n--w": "┘", "n-e-": "└", "n-ew": "┴", "ns--": "│", "ns-w": "┤", "nse-": "├", "nsew": "┼",
        },
        "round": {
            "---w": " ", "--e-": " ", "--ew": "-", "-s--": " ", "-s-w": "╮", "-se-": "╭", "-sew": "┬",
            "n---": " ", "n--w": "╯", "n-e-": "╰", "n-ew": "┴", "ns--": "│", "ns-w": "┤", "nse-": "├", "nsew": "┼",
        },
        "double": {
            "---w": " ", "--e-": " ", "--ew": "═", "-s--": " ", "-s-w": "╗", "-se-": "╔", "-sew": "╦",
            "n---": " ", "n--w": "╝", "n-e-": "╚", "n-ew": "╩", "ns--": "║", "ns-w": "╣", "nse-": "╠", "nsew": "╬",
        },
        "heavy:light": {
            "---w:--e-": "╾", "---w:-s--": "┑", "---w:-se-": "┲", "---w:n---": "┙", "---w:n-e-": "┺", "---w:ns--": "┥", "---w:nse-": "┽",
            "--e-:---w": "╼", "--e-:-s--": "┍", "--e-:-s-w": "┮", "--e-:n---": "┙", "--e-:n--w": "┶", "--e-:ns--": "┝", "--e-:ns-w": "┾",
            "--ew:-s--": "┰", "--ew:n---": "┸", "--ew:ns--": "┿", "-s--:---w": "┒", "-s--:--e-": "┎", "-s--:--ew": "┰", "-s--:n---": "╽",
            "-s--:n--w": "┧", "-s--:n-e-": "┟", "-s--:n-ew": "╁", "-s-w:--e-": "┱", "-s-w:n---": "┧", "-s-w:n-e-": "╅", "-se-:---w": "┲",
            "-se-:n---": "┢", "-se-:n--w": "╆", "-sew:n---": "╈", "n---:---w": "┖", "n---:--e-": "┚", "n---:--ew": "┸", "n---:-s--": "╿",
            "n---:-s-w": "┦", "n---:-se-": "┞", "n---:-sew": "╀", "n--w:--e-": "┹", "n--w:-s--": "┩", "n--w:-se-": "╃", "n-e-:---w": "┺",
            "n-e-:-s--": "┡", "n-e-:-s-w": "╄", "n-ew:-s--": "╇", "ns--:---w": "┨", "ns--:--e-": "┠", "ns--:--ew": "╂", "ns-w:--e-": "╉",
            "nse-:---w": "╊",
        }
    }

    # High-level color/style base palettes
    _BASE_PALETTES = {
        "ocean": {
            "style": "round-header",
            "header": {"fg": "bright_white", "bg": "blue", "bold": True},
            "border": {"fg": "bright_blue"},
            "col_0": {"fg": "bright_white", "bg": "blue", "bold": True},
            "fg2": "bright_white"
        },
        "forest": {
            "style": "round",
            "header": {"fg": "bright_white", "bg": "green", "bold": True},
            "border": {"fg": "bright_green"},
            "col_0": {"fg": "bright_white", "bg": "green", "bold": True},
            "fg2": "white"
        },
        "graphite": {
            "style": "light",
            "header": {"fg": "black", "bg": "bright_white", "bold": True},
            "border": {"fg": "bright_black"},
            "col_0": {"fg": "black", "bg": "bright_white", "bold": True},
            "fg2": "bright_white"
        },
        "orchid": {
            "style": "round-header",
            "header": {"fg": "bright_white", "bg": "magenta", "bold": True},
            "border": {"fg": "bright_magenta"},
            "col_0": {"fg": "bright_white", "bg": "magenta", "bold": True},
            "fg2": "bright_white"
        },
        "sunflower": {
            "style": "round",
            "header": {"fg": "black", "bg": "yellow", "bold": True},
            "border": {"fg": "bright_yellow"},
            "col_0": {"fg": "black", "bg": "yellow", "bold": True},
            "fg2": "white"
        }
    }

    THEMES = {}
    for _name, _config in _BASE_PALETTES.items():
        _base = {"style": _config["style"], "header": _config["header"], "border": _config["border"]}
        _alt_sequence = [{"bg": "black", "fg": "white"}, {"bg": "bright_black", "fg": _config["fg2"]}]

        # 1. Solid (Default)
        _solid_base = {"bg": "black", "fg": "white"}
        THEMES[f"{_name}"] = {**_base, "alt_rows": [_solid_base, _solid_base]}
        THEMES[f"{_name}-index"] = {**_base, "alt_rows": [_solid_base, _solid_base], "col_0": _config["col_0"]}
        THEMES[f"{_name}-slim"] = {**_base, "alt_rows": [_solid_base, _solid_base], "decorations": 3}
        THEMES[f"{_name}-slim-index"] = {**_base, "alt_rows": [_solid_base, _solid_base], "col_0": _config["col_0"], "decorations": 3}

        # 2. Alternating Rows (-rows)
        THEMES[f"{_name}-rows"] = {**_base, "alt_rows": _alt_sequence}
        THEMES[f"{_name}-rows-index"] = {**_base, "alt_rows": _alt_sequence, "col_0": _config["col_0"]}
        THEMES[f"{_name}-rows-slim"] = {**_base, "alt_rows": _alt_sequence, "decorations": 3}
        THEMES[f"{_name}-rows-slim-index"] = {**_base, "alt_rows": _alt_sequence, "col_0": _config["col_0"], "decorations": 3}

        # 3. Alternating Columns (-cols)
        THEMES[f"{_name}-cols"] = {**_base, "alt_cols": _alt_sequence}
        THEMES[f"{_name}-cols-index"] = {**_base, "alt_cols": _alt_sequence, "col_0": _config["col_0"]}
        THEMES[f"{_name}-cols-slim"] = {**_base, "alt_cols": _alt_sequence, "decorations": 3}
        THEMES[f"{_name}-cols-slim-index"] = {**_base, "alt_cols": _alt_sequence, "col_0": _config["col_0"], "decorations": 3}

    def __init__(self, rows: Optional[Iterable[Iterable[Any]]] = None, header: Optional[Iterable[Any]] = None, max_width: int = 0, alignment: Optional[str] = None, style: Optional[str] = None, padding: Optional[int] = None, title: Optional[str] = None, max_rows: int = 0, max_cols: int = 0, theme: Optional[Union[str, dict]] = None) -> None:
        """
        Initializes a new instance of the Vistab styling rendering class.

        This constructor sets up the initial default state of the table, compiling configuration files
        and initiating decorators to allow optional parameters.

        Args:
        -----
        rows : Optional[Iterable[Iterable[Any]]]
            An iterable containing grouped row sequences to be added immediately. Default is None.
        header : Union[bool, Iterable[Any], str, None]
            If True (default), extracts the first row as the top-most table header.
            If False, "" or None, bypasses extraction mapping structurally rows naturally.
            If an Iterable is passed, maps directly into `self.set_header()`.
        max_width : int
            The hard terminal rendering width limit enforced via color-aware wrapping. Default is 0.
        alignment : Optional[str]
            Layout sequences mapped column by column using characters defined in `set_cols_align("lrc")`.
        style : Optional[str]
            Default table box drawing parameters mapped against built-in themes.
        padding : Optional[int]
            The amount of numerical spaces injected padding left and right uniformly inside box cells.

        Returns:
        --------
        None

        Example:
        --------
        ```python
        table = Vistab(style="round-header", padding=1, max_width=100)
        ```

        Args:
        -----
        rows : Optional[Iterable[Iterable]]
            An iterable containing rows to be added to the table. Each row should be an iterable of cell values. Default is None.
        header : Optional[Iterable]
            The header definition for the table.
        max_width : int, optional
            The maximum width of the table. Default is 0.
        alignment : Optional[str], optional
            The alignment of columns. See set_cols_align().
        style : str, optional
            The style of the table. Default is 'light' or whatever is in .config/vistab.toml.
        theme : Union[str, dict], optional
            A named theme (e.g. ``"ocean-rows"``) or a custom theme dict applied after all other
            settings. Equivalent to calling ``set_theme()`` immediately after construction.
        padding : int, optional
            The amount of padding (left and right) for the cells. Default is 1 or whatever is in .config/vistab.toml.
        title : str, optional
            Optional title printed above the table.
        max_rows : int, optional
            Maximum rows to render (0 = infinite).
        max_cols : int, optional
            Maximum columns to render (0 = infinite).

        Example:
        --------
        ```
        # Creates a new Vistab instance with initial rows and a maximum width of 100
        table = Vistab(rows=[["Name", "Age"], ["Alice", 25], ["Bob", 30]], max_width=100)
        print(table.draw())
        ```

        If no rows are provided during initialization, they can be added later using the `add_row` or `add_rows` methods.
        """
        # Initialize table properties with default values
        self._has_border = True  # Whether the table has a border
        self._has_header = True  # Whether the table has a header
        self._has_hline_between_headers = True  # Whether there is a horizontal line between headers
        self._has_hline_header_2_cell = True  # Whether there is a horizontal line between header and cells
        self._has_hline_between_cells = True  # Whether there are horizontal lines between cells
        self._has_vline_between_headers = True  # Whether there are vertical lines between headers
        self._has_vline_header_2_cell = True  # Whether there are vertical lines between header and cells
        self._has_vline_between_cells = True  # Whether there are vertical lines between cells

        # Initialize helper classes for string length calculation and color-aware wrapping
        self._vislen = StringLengthCalculator()  # For calculating visible string length excluding ANSI sequences
        self._cwrap = ColorAwareWrapper()  # For wrapping text with ANSI sequences

        # Set default table decorations (border, header, horizontal and vertical lines)
        self._deco = Vistab.VLINES | Vistab.HLINES | Vistab.BORDER | Vistab.HEADER

        # Reset table properties
        self.reset()

        # Ingest configuration
        self._load_config()

        self._precision = 3  # Default precision for numeric values

        # Added to support rows arg (i.e., adding entire table definition in initialization).
        is_header = True
        if header is False or header == "":
            is_header = False
        elif getattr(header, '__iter__', False) and not isinstance(header, (str, bytes, bool)):
            self.set_header(header)
            is_header = False  # The explicit header was added, don't consume the first row structurally

        if rows is not None:
            self.add_rows(rows, header=is_header)  # Add initial rows to the table if provided

        if max_width > 0:
            self.set_max_width(max_width)  # Set the maximum width of the table

        # Regular expressions for handling ANSI escape sequences in table content
        self.no_end_reset = re.compile(r'\033\[0m(?!.*\033\[((?!0m)[0-?]*[ -/]*[@-~]))')
        self.non_reset_sequence = re.compile(r'\033\[((?!0m)[0-?]*[ -/]*[@-~])')
        self.non_reset_not_followed_by_reset = re.compile(r'(\033\[(?:(?!0m)[0-?]*[ -/]*[@-~]))(?!.*\033\[0m)')
        self.ansi_norm = "\033[0m"  # ANSI reset sequence

        # Apply explicit user configurations overriding TOML defaults
        if style is not None:
            self.set_style(style)  # Set the table style
        else:
            self.set_style(self._style) # Ensure char boundaries map out

        if padding is not None:
            self.set_padding(padding)  # Set the cell padding
        if alignment is not None:
            self.set_cols_align(alignment)  # Set the column alignment if provided
            pass  # for auto-indentation

        if title is not None:
            self.set_title(title)
        if max_rows > 0:
            self.set_max_rows(max_rows)
        if max_cols > 0:
            self.set_max_cols(max_cols)
        if theme is not None:
            self.set_theme(theme)  # Apply high-level color/style theme last so it can override other settings

        pass  # for auto-indentation

    def _sep_width(self) -> int:
        """Width, in characters, of one inter-column gap that a span absorbs."""
        return 2 * self._pad + (1 if self.has_vlines() else 0)

    def _span_block_width(self, start_col: int, colspan: int) -> int:
        """Total interior render width of a spanned block covering [start_col, start_col + colspan) physical columns."""
        interior = sum(self._width[start_col:start_col + colspan])
        interior += (colspan - 1) * self._sep_width()
        return interior

    def _expand_spans_in_row(self, row: List[Any]) -> List[VistabCell]:
        expanded = []
        i = 0
        while i < len(row):
            item = row[i]
            if isinstance(item, ColSpan):
                cell = VistabCell(item.value, colspan=item.colspan)
                expanded.append(cell)
                for _ in range(item.colspan - 1):
                    expanded.append(VistabPlaceholderCell(cell))
            elif isinstance(item, VistabCell):
                expanded.append(item)
                if item.colspan > 1:
                    for _ in range(item.colspan - 1):
                        expanded.append(VistabPlaceholderCell(item))
            else:
                expanded.append(VistabCell(item))
            i += 1
        return expanded

    def _load_config(self):
        """Internal routine loading default attributes from vistab.toml settings"""
        import sys
        # Attempt to import built-in TOML parser based on python version constraint
        try:
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                import tomli as tomllib
        except ImportError:
            sys.stderr.write("[\033[1;33mWARN\033[0m] For .toml configuration support on Python < 3.11, the 'tomli' library is needed. Please `pip install tomli`.\n")
            return

        from pathlib import Path

        # Standard recursive application configurations directory map
        search_paths = [
            Path(__file__).parent / "vistab.toml",
            Path.home() / ".vistab.toml",
            Path.home() / ".config" / "vistab.toml",
            Path.home() / ".config" / "vistab" / "config.toml",
            Path.cwd() / "vistab.toml",
            Path.cwd() / ".vistab.toml",
            Path.cwd() / ".config" / "vistab.toml",
        ]

        # Ingest latest relevant TOML config
        for p in reversed(search_paths):
            if p.exists():
                try:
                    with open(p, "rb") as f:
                        data = tomllib.load(f)
                        if "vistab" in data:
                            v = data["vistab"]
                            if "style" in v: self.set_style(v["style"])
                            if "padding" in v: self.set_padding(v["padding"])
                            if "align" in v: self.set_cols_align(v["align"])
                            if "max_width" in v: self.set_max_width(v["max_width"])
                            if "max_rows" in v: self.set_max_rows(v["max_rows"])
                            if "max_cols" in v: self.set_max_cols(v["max_cols"])
                    break # Halt after applying the active directory config!
                except Exception as e:
                    print(f"\033[33m[WARN] Failed to parse {p}: {e}\033[0m")
    def vislen(self, iterable: Iterable) -> int:
        """Calculate the visible legnth of strings or the length for anythine else."""
        if isinstance(iterable, bytes) or isinstance(iterable, str):
            return self._vislen.len(iterable)
        return iterable.__len__()

    @property
    def has_border(self) -> bool:
        """
        Gets whether the current table is configured to draw an external boundary border.

        Returns:
        --------
        bool
            True if the table is set to draw a visible border around its perimeter, False otherwise.

        Example:
        --------
        ```python
        border_status = table.has_border
        ```
        """
        return self._has_border and ((self._deco & Vistab.BORDER) > 0)

    @has_border.setter
    def has_border(self, value: bool) -> None:
        """
        Sets whether the table will draw an external boundary border.

        Args:
        -----
        value : bool
            Configuration boolean defining whether the table draws border decorators.

        Example:
        --------
        ```
        table.has_border = False
        ```
        """
        self._has_border = value

    @property
    def has_header(self) -> bool:
        """
        Gets whether the table is currently configured to format the first row as a structural header.

        Returns:
        --------
        bool
            True if the first array row is ingested as a header, False otherwise.

        Example:
        --------
        ```python
        header_status = table.has_header
        ```
        """
        return self._has_header

    @has_header.setter
    def has_header(self, value: bool) -> None:
        """
        Sets whether the table will force convert the first inserted row into a table header.

        Important Behavior:
        -------------------
        By default, Vistab initializes with `has_header=True`. Building a table via
        `Vistab(rows)` (with no explicit `header=`) consumes the first row as the header.
        Setting `has_header = False` afterward turns that consumed row back into an ordinary
        data row: the row is moved from the header slot to the front of the data rows, so it
        renders with the body column alignment (not centered header alignment) and no header
        divider is drawn. Setting it back to `True` re-consumes the current first data row as
        the header. The move preserves the row's cells verbatim (including any column spans).

        Args:
        -----
        value : bool
            Boolean indicating whether the top-most row is treated as a table header.

        Example:
        --------
        ```python
        table.has_header = False
        ```
        """
        value = bool(value)
        if value == self._has_header:
            self._has_header = value
            return

        if not value:
            # Turning the header off: demote a consumed header row back into the data rows.
            if self._header:
                self._rows.insert(0, self._header)
                self._header = []
        else:
            # Turning the header on: promote the current first data row into the header slot.
            if not self._header and self._rows:
                self._header = self._rows.pop(0)

        self._has_header = value

    def reset(self) -> 'Vistab':
        """
        Reset the Vistab instance safely to its default state.

        Clears all row data, header data, and restores styling logic configurations back to standard initialization values (such as reinstating 'light' mode lines, and purging coordinate-based coloring injections).

        Returns:
        --------
        Vistab
            The instance for method chaining.

        Important Behavior:
        -------------------
        Does not mutate the `None` fallbacks. Resets layout decorators.

        Example:
        --------
        ```python
        table.reset()
        ```
        """
        self._hline_string = None
        self._row_size = None
        self._header = []
        self._rows = []
        self._style = "light"
        self._pad = 1
        self._max_width = False
        self._max_rows = 0
        self._max_cols = 0
        self._col_styles = {}
        self._row_styles = {}
        self._cell_styles = {}
        self._alt_row_styles = {}
        self._alt_col_styles = {}
        self._table_wrap = True
        self._col_wraps = {}
        self._row_wraps = {}
        self._cell_wraps = {}
        self._table_style = {}
        self._header_style = {}
        self._border_style = {}
        self._color_enabled = True  # When False, no vistab styling ANSI is emitted (see set_color).
        self._bidi = True  # When True, RTL cells are LTR-isolated so they don't flip the grid (see set_bidi).
        self._bidi_active = False  # Recomputed per draw(): isolate cells only if the table has RTL content.
        self._title = None
        self.on_wrap_conflict = "warn"
        self.on_short_row = "pad"
        self._sanitize_ansi = True
        self.on_long_row = "truncate"
        self._metrics = {"padded": 0, "truncated": 0, "skipped": 0}
        self._abnormal_style = None  # Tuple of (fg, bg) injected directly into flawed row lines.
        self._sort_col = None
        self._sort_reverse = False
        return self

    def set_abnormal_row_style(self, fg: Optional[str] = None, bg: Optional[str] = None) -> 'Vistab':
        """
        Sets an explicit ANSI color override for rows that were structurally jagged (padded or truncated).

        Args:
            fg (Optional[str]): Foreground color (e.g. 'red', 'bright_yellow').
            bg (Optional[str]): Background color.
        """
        self._abnormal_style = (fg, bg)
        return self

    def get_structural_metrics(self) -> dict:
        """
        Returns a dictionary containing tallies of how many matrix rows bypassed pure structure.

        Returns:
            dict: `{"padded": X, "truncated": Y, "skipped": Z}`
        """
        return dict(self._metrics)


    def set_max_rows(self, max_rows: int) -> 'Vistab':
        """Set the maximum number of rows to render.

        Args:
            max_rows (int): The maximum rows. 0 means infinite.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_max_rows(100)
        """
        self._max_rows = max_rows if max_rows > 0 else 0
        return self

    def set_max_cols(self, max_cols: int) -> 'Vistab':
        """Set the maximum number of columns to render.

        Args:
            max_cols (int): The maximum columns. 0 means infinite.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_max_cols(5)
        """
        self._max_cols = max_cols if max_cols > 0 else 0
        return self

    def _compile_style_dict(self, fg=None, bg=None, **kwargs):
        """Helper to safely compile dicts."""
        d = {}
        if fg and fg in Vistab.COLORS: d["fg"] = Vistab.COLORS[fg]
        if bg and bg in Vistab.BG_COLORS: d["bg"] = Vistab.BG_COLORS[bg]
        for style, val in kwargs.items():
            if val and style in Vistab.TEXT_STYLES:
                d[style] = Vistab.TEXT_STYLES[style]
        return d

    def set_border_style(self, fg=None, bg=None, bold: bool=None, faint: bool=None, italic: bool=None, underline: bool=None, blink: bool=None, reverse: bool=None, strike: bool=None, **kwargs) -> 'Vistab':
        """Apply colors/styles to the table border and intersection characters."""
        self._border_style = self._compile_style_dict(fg, bg, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        return self


    @property
    def sanitize_ansi(self) -> bool:
        """Gets whether grid values strip layout-destructive positional mapping."""
        return self._sanitize_ansi

    @sanitize_ansi.setter
    def sanitize_ansi(self, value: bool) -> None:
        """Sets boolean state restricting destructive grid layout mappings."""
        self._sanitize_ansi = value

    def _sanitize_destructive_ansi(self, cell_text: str) -> str:
        """Purges absolute positional cursor modifiers that warp row rendering."""
        if not self._sanitize_ansi:
            return cell_text
        return self._ANSI_DESTRUCTIVE_RE.sub('', cell_text)

    def _reassert_ansi_context(self, cell_text: str, ansi_on: str) -> str:
        """Scans for embedded inner graphics resets and re-wraps their trailing values identically to bounding context."""
        if not ansi_on or not cell_text:
            return cell_text
        import re
        def replacer(m):
            code = m.group(1)
            nums = re.findall(r'\d+', code)
            if not nums or any(n in ['0', '22', '23', '24', '25', '27', '29', '39', '49'] for n in nums):
                return code + ansi_on
            return code
        return self._ANSI_RESET_RE_INTERCEPT.sub(replacer, cell_text)

    def set_title(self, title: str) -> 'Vistab':
        """Set a title string to be rendered centered above the table."""
        self._title = title
        return self

    def sort_by(self, col_idx: int, reverse: bool = False) -> 'Vistab':
        """Enable structured row caching and apply physical grid sort iterations."""
        self._sort_col = col_idx
        self._sort_reverse = reverse
        return self

    def _apply_sorting(self):
        """Evaluate structural sort flags converting accurately."""
        if hasattr(self, '_sort_col') and self._sort_col is not None:
            col_idx = self._sort_col
            dt = self._dtype[col_idx] if hasattr(self, '_dtype') and col_idx < len(self._dtype) else 't'

            def parse_val(row):
                if col_idx >= len(row): return ""
                val = str(row[col_idx]).strip()
                if dt in ('i', 'f', 'e'):
                    try: return float(val)
                    except ValueError: return float('-inf') if getattr(self, '_sort_reverse', False) else float('inf')
                return val

            self._rows.sort(key=parse_val, reverse=getattr(self, '_sort_reverse', False))

    # --- Shorthand UX Stylers ---
    def bold_header(self, enable: bool = True) -> 'Vistab':
        """Shortcut to bold the table header. Pass False to strip bold styling."""
        return self.set_header_style(bold=enable)

    def color_header(self, fg=None, bg=None) -> 'Vistab':
        """Shortcut to color the table header."""
        return self.set_header_style(fg=fg, bg=bg)

    def bold_row(self, row_idx: int, enable: bool = True) -> 'Vistab':
        """Shortcut to bold a specific row index. Pass False to strip bold styling."""
        return self.set_row_style(row_idx, bold=enable)

    def bold_col(self, col_idx: int, enable: bool = True) -> 'Vistab':
        """Shortcut to bold a specific column index. Pass False to strip bold styling."""
        return self.set_col_style(col_idx, bold=enable)

    def color_row(self, row_idx: int, fg=None, bg=None) -> 'Vistab':
        """Shortcut to color a specific row index."""
        return self.set_row_style(row_idx, fg=fg, bg=bg)

    def color_col(self, col_idx: int, fg=None, bg=None) -> 'Vistab':
        """Shortcut to color a specific column index."""
        return self.set_col_style(col_idx, fg=fg, bg=bg)
    # ----------------------------

    def set_table_style(self, fg=None, bg=None, bold: bool=None, faint: bool=None, italic: bool=None, underline: bool=None, blink: bool=None, reverse: bool=None, strike: bool=None, **kwargs) -> 'Vistab':
        """Apply a global base style mapping uniformly to all cells inside the table."""
        self._table_style = self._compile_style_dict(fg, bg, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        return self

    def set_header_style(self, fg=None, bg=None, bold: bool=None, faint: bool=None, italic: bool=None, underline: bool=None, blink: bool=None, reverse: bool=None, strike: bool=None, **kwargs) -> 'Vistab':
        """Apply styles to the header row.

        Args:
            fg (str): Foreground color (e.g. 'red').
            bg (str): Background color (e.g. 'blue').
            bold, faint, italic, underline, blink, reverse, strike (bool): Text styles.
        """
        self._header_style = self._compile_style_dict(fg, bg, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        return self

    def set_row_style(self, row_idx: int, fg=None, bg=None, bold: bool=None, faint: bool=None, italic: bool=None, underline: bool=None, blink: bool=None, reverse: bool=None, strike: bool=None, **kwargs) -> 'Vistab':
        """Apply styles to a specific row index (excluding header)."""
        self._row_styles[row_idx] = self._compile_style_dict(fg, bg, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        return self

    def set_col_style(self, col_idx: int, fg=None, bg=None, bold: bool=None, faint: bool=None, italic: bool=None, underline: bool=None, blink: bool=None, reverse: bool=None, strike: bool=None, **kwargs) -> 'Vistab':
        """Apply styles to a specific column index."""
        self._col_styles[col_idx] = self._compile_style_dict(fg, bg, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        return self

    def set_cell_style(self, row_idx: int, col_idx: int, fg=None, bg=None, bold: bool=None, faint: bool=None, italic: bool=None, underline: bool=None, blink: bool=None, reverse: bool=None, strike: bool=None, **kwargs) -> 'Vistab':
        """Apply styles to a specific cell. Has highest precedence."""
        self._cell_styles[(row_idx, col_idx)] = self._compile_style_dict(fg, bg, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        return self

    def set_alternating_row_style(self, fg1=None, bg1=None, fg2=None, bg2=None, bold: bool=None, faint: bool=None, italic: bool=None, underline: bool=None, blink: bool=None, reverse: bool=None, strike: bool=None, **kwargs) -> 'Vistab':
        """Set alternating row styling (zebra-striping) applied iteratively over table coordinates."""
        self._alt_row_styles[0] = self._compile_style_dict(fg1, bg1, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        self._alt_row_styles[1] = self._compile_style_dict(fg2, bg2, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        return self

    def set_alternating_col_style(self, fg1=None, bg1=None, fg2=None, bg2=None, bold: bool=None, faint: bool=None, italic: bool=None, underline: bool=None, blink: bool=None, reverse: bool=None, strike: bool=None, **kwargs) -> 'Vistab':
        """Set alternating column styling (zebra-striping)."""
        self._alt_col_styles[0] = self._compile_style_dict(fg1, bg1, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        self._alt_col_styles[1] = self._compile_style_dict(fg2, bg2, bold=bold, faint=faint, italic=italic, underline=underline, blink=blink, reverse=reverse, strike=strike, **kwargs)
        return self

    def set_theme(self, theme: Union[str, dict]) -> 'Vistab':
        """Apply a predefined high-level color theme over table geometries.

        Vistab provides curated default palettes (e.g. ``ocean``, ``forest``).
        You may pass a string to map from ``Vistab.THEMES``, or pass a literal active dictionary.

        Args:
        -----
        theme : Union[str, dict]
            A named theme key (e.g. ``"ocean-rows-index"``) or a custom theme dictionary.
            Named themes are looked up in ``Vistab.THEMES``.

        Returns:
        --------
        Vistab
            The instance for method chaining.

        Example:
        --------
        ```python
        # Named theme
        table = Vistab(theme="ocean-rows")

        # Custom theme dict
        custom_theme = {
            "style": "round-header",
            "padding": 2,
            "header": {"fg": "black", "bg": "bright_blue", "bold": True},
            "border": {"fg": "blue"}
        }
        table = Vistab().set_theme(custom_theme)
        ```
        """
        if isinstance(theme, str):
            if theme not in Vistab.THEMES:
                raise ValueError(f"Theme '{theme}' not found. Available: {', '.join(Vistab.THEMES.keys())}")
            theme = Vistab.THEMES[theme]
        elif not isinstance(theme, dict):
            raise TypeError("Theme must be a predefined string identifier or a literal dictionary map.")

        if "style" in theme: self.set_style(theme["style"])
        if "padding" in theme: self.set_padding(theme["padding"])
        if "table" in theme: self.set_table_style(**theme["table"])
        if "header" in theme: self.set_header_style(**theme["header"])
        if "border" in theme: self.set_border_style(**theme["border"])
        if "col_0" in theme: self.set_col_style(0, **theme["col_0"])
        if "col_-1" in theme: self.set_col_style(-1, **theme["col_-1"])
        if "row_0" in theme: self.set_row_style(0, **theme["row_0"])
        if "row_-1" in theme: self.set_row_style(-1, **theme["row_-1"])

        if "decorations" in theme: self.set_decorations(theme["decorations"])
        if "has_border" in theme: self.has_border = theme["has_border"]
        if "has_header" in theme: self._has_header = theme["has_header"]

        if "alt_rows" in theme and len(theme["alt_rows"]) == 2:
            self._alt_row_styles[0] = self._compile_style_dict(**theme["alt_rows"][0])
            self._alt_row_styles[1] = self._compile_style_dict(**theme["alt_rows"][1])

        if "alt_cols" in theme and len(theme["alt_cols"]) == 2:
            self._alt_col_styles[0] = self._compile_style_dict(**theme["alt_cols"][0])
            self._alt_col_styles[1] = self._compile_style_dict(**theme["alt_cols"][1])

        return self

    def apply_theme(self, theme: Union[str, dict]) -> 'Vistab':
        """Deprecated alias for :meth:`set_theme`. Use ``set_theme()`` instead."""
        import warnings
        warnings.warn("apply_theme() is deprecated and will be removed in a future release. Use set_theme() instead.", DeprecationWarning, stacklevel=2)
        return self.set_theme(theme)

    def set_table_wrap(self, wrap: bool) -> 'Vistab':
        """Set the global wrapping behavior for the table."""
        self._table_wrap = wrap
        return self

    def set_row_wrap(self, row_idx: int, wrap: bool) -> 'Vistab':
        """Override wrapping behavior exclusively for a specific row index."""
        self._row_wraps[row_idx] = wrap
        return self

    def set_col_wrap(self, col_idx: int, wrap: bool) -> 'Vistab':
        """Override wrapping behavior exclusively for a specific column index."""
        self._col_wraps[col_idx] = wrap
        return self

    def set_cell_wrap(self, row_idx: int, col_idx: int, wrap: bool) -> 'Vistab':
        """Override wrapping behavior for an exact cell mapping."""
        self._cell_wraps[(row_idx, col_idx)] = wrap
        return self

    def _get_active_wrap_control(self, row_idx=None, col_idx=None, is_header=False) -> bool:
        """Compute the final active Wrapping block applying precedence logic."""
        # 1. Base Table Wrap constraint
        active = self._table_wrap

        # 2. Overlap precise Column override
        if col_idx is not None and col_idx in self._col_wraps:
            active = self._col_wraps[col_idx]

        # 3. Overlap exact Row/Header override
        if is_header and "header" in self._row_wraps:
            active = self._row_wraps["header"]
        elif not is_header and row_idx is not None and row_idx in self._row_wraps:
            active = self._row_wraps[row_idx]

        # 4. Apply explicit nested Cell override exactly
        if not is_header and row_idx is not None and col_idx is not None:
            if (row_idx, col_idx) in self._cell_wraps:
                active = self._cell_wraps[(row_idx, col_idx)]

        return active

    def _get_active_ansi_wrap(self, row_idx=None, col_idx=None, is_header=False, is_abnormal=False):
        if not self._color_enabled:
            return "", ""
        """Compute the final active ANSI configuration applying precedence logic."""
        active = {}

        # 0. Base Table Level styling mapped fluidly
        if self._table_style:
            active.update(self._table_style)

        # 1. Base Alternating Columns
        if col_idx is not None and self._alt_col_styles:
            active.update(self._alt_col_styles.get(col_idx % 2, {}))

        # 2. Base Alternating Rows (Merge/Overrides Alt Cols)
        if not is_header and row_idx is not None and self._alt_row_styles:
            active.update(self._alt_row_styles.get(row_idx % 2, {}))

        # 3. Apply precise Column (Overrides Base Alternating Patterns)
        if col_idx is not None:
            if col_idx in self._col_styles:
                active.update(self._col_styles[col_idx])
            elif (-1 in self._col_styles) and hasattr(self, '_width') and (col_idx == len(self._width) - 1):
                active.update(self._col_styles[-1])

        # 4. Apply precise Row/Header (Overrides Alt Rows)
        if is_header and self._header_style:
            active.update(self._header_style)
        elif not is_header and row_idx is not None:
            if row_idx in self._row_styles:
                active.update(self._row_styles[row_idx])
            elif (-1 in self._row_styles) and (row_idx == len(self._rows) - 1):
                active.update(self._row_styles[-1])

        # 5. Apply exact Cell (Overrides EVERYTHING)
        if not is_header and row_idx is not None and col_idx is not None:
            if (row_idx, col_idx) in self._cell_styles:
                active.update(self._cell_styles[(row_idx, col_idx)])

        # 6. Apply Abnormal State Styling mapped inherently linearly
        if is_abnormal and self._abnormal_style:
            fg, bg = self._abnormal_style
            if fg is not None:
                fg_code = self.COLORS.get(fg)
                if fg_code: active["fg"] = fg_code
            if bg is not None:
                bg_code = self.BG_COLORS.get(bg)
                if bg_code: active["bg"] = bg_code

        if not active:
            return "", ""

        codes = [f"\033[{val}m" for val in active.values()]
        return "".join(codes), "\033[0m"

    def _get_border_ansi(self):
        """Compute the active ANSI configuration for table borders."""
        if not self._color_enabled or not self._border_style:
            return "", ""
        codes = [f"\033[{val}m" for val in self._border_style.values()]
        return "".join(codes), "\033[0m"

    def set_color(self, enabled: bool = True) -> 'Vistab':
        """Enable or disable vistab's own ANSI color/style output.

        When disabled (``set_color(False)``), vistab emits no styling escape
        sequences of its own: themes, coordinate styles, and borders render in
        plain monochrome. This does NOT strip ANSI that you put in cell content
        yourself. Returns ``self`` for chaining.
        """
        self._color_enabled = bool(enabled)
        return self

    def set_bidi(self, enabled: bool = True) -> 'Vistab':
        """Enable or disable bidi-safe rendering of right-to-left (RTL) content.

        When enabled (the default), if any cell contains RTL script (Arabic,
        Hebrew, etc.) vistab wraps each cell's content in Unicode LTR isolates
        (U+2066..U+2069). This keeps the table grid stable: without it, a
        terminal's bidirectional algorithm reorders the whole physical line and
        the columns visibly flip and right-align. The RTL text still reads
        correctly right-to-left inside its cell.

        The isolate characters are zero-width, so they never affect column
        widths or alignment, and tables with no RTL content are completely
        unaffected (byte-identical output). A few terminals ignore isolates; use
        ``set_bidi(False)`` (or the ``--no-bidi`` CLI flag) if yours does.
        Returns ``self`` for chaining.
        """
        self._bidi = bool(enabled)
        return self

    @property
    def max_width(self) -> int:
        """
        Gets the predefined maximum width limit of the table.

        Returns:
        --------
        int
            The max character width allowed before cells hard wrap. 0 indicates infinite width.

        Example:
        --------
        ```python
        current_max = table.max_width
        ```
        """
        return self._max_width

    @max_width.setter
    def max_width(self, val: int) -> None:
        """
        Sets the maximum width of the table programmatically.

        Args:
        -----
        val : int
            The max width limit in characters before cellular string wrapping. 0 equates to infinite wrap scale.

        Example:
        --------
        ```python
        table.max_width = 120
        ```
        """
        self.set_max_width(val)

    def set_max_width(self, max_width: int) -> 'Vistab':
        """Set the maximum width of the table.

        Args:
            max_width (int): The maximum width of the table in characters. If set to 0,
                             size is unlimited, therefore cells won't be wrapped.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_max_width(120)
        """
        self._max_width = max_width if max_width > 0 else False
        return self

    def set_style(self, style: str = "light") -> 'Vistab':
        """Set the characters used to draw lines between rows and columns to one of defined types.

        Args:
            style (str): The requested style name. Default is "light".
                         Available options include:
                           * "light": Use unicode light box borders
                           * "bold":  Use unicode bold box borders
                           * "double": Use unicode double box borders
                           * "ascii": Basic ASCII formatting
                           * "none": No lines

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_style("double")
        """
        self._style = style
        if style in Vistab.STYLES:
            self.set_table_lines(Vistab.STYLES[style])
            # Automatically disable incompatible structural decorations
            if style == "markdown":
                self._deco &= ~Vistab.HLINES
                self._deco &= ~Vistab.BORDER
            elif style == "booktabs":
                self._deco &= ~Vistab.VLINES
            elif style == "none":
                self._deco = 0
            return self
        raise ValueError("style must be one of '%s' not '%s'" % ("', '".join(sorted(Vistab.STYLES.keys())), style))

    def _set_table_lines(self, table_lines: str) -> 'Vistab':
        """Set the characters used to draw lines between rows and columns.

        The table_lines is in the following format:
        [
          ew,    # The character connecting east and west to use for a horizantal line (e.g. "-" or "─" )
          ns,    # The character connecting north and south to use for a vertical line (e.g. "|" or "|" )
          se,    # The character connecting south and east to use for the top- and left-most corner (e.g. "+", or "┌")
          sw,    # The character connecting south and west to use for the top- and right-most corner (e.g. "+" or "┐")
          ne,    # The character connecting north and east to use for the bottom- and left-most corner (e.g. "+" or "└")
          nw,    # The character connecting north and west to use for the bottom- and right-most corner (e.g. "+" or "┘")
          nse,   # The character connecting north, south, and east (e.g., "+" or "┤")
          nsw,   # The character connecting north, south, and west (e.g., "+" or "├")
          sew,   # The character connecting south, east, and west (e.g., "+" or "┬")
          new,   # The character connecting north, east, and west (e.g., "+" or "┴")
          nsew,  # The character connecting north, south, east, and west (e.g., "+" or "┴")
          hew,   # The character connecting east and west to use for a line separating headers (e.g. "=" or "═" )
          hnse,  # The character connecting north, south and east to use for a line separating headers (e.g. "+" or "╞" )
          hnsw,  # The character connecting north, south, and west to use for a line separating headers (e.g. "+" or "╡" )
          hnsew, # The character connecting north, south, east and west to use for a line separating headers (e.g. "+" or "╪" )
        ]
        For legacy default it would be "-|+++++++++=+++"
        """
        if len(table_lines) != 15:
            raise ArraySizeError("string/array should contain 15 characters not %d as in '%s'" % (len(table_lines), table_lines))
        (
            self._char_ew,
            self._char_ns,
            self._char_se,
            self._char_sw,
            self._char_ne,
            self._char_nw,
            self._char_nse,
            self._char_nsw,
            self._char_sew,
            self._char_new,
            self._char_nsew,
            self._char_hew,
            self._char_hnse,
            self._char_hnsw,
            self._char_hnsew,
        ) = table_lines
        return self

    def set_table_lines(self, table_lines: str) -> 'Vistab':
        """Set the characters used to draw lines between rows and columns.

        Args:
            table_lines (str): A string of exactly 4 or 15 characters describing lines.
                If 4 characters: [horizontal, vertical, corner, header]
                If 15 characters: each character represents specific connections.
                Default is 4 chars like "-|+=".

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_table_lines("-|+=")
        """
        if len(table_lines) == 15:
            return self._set_table_lines(table_lines)
        if len(table_lines) != 4:
            raise ArraySizeError("string/array should contain either 4 or 15 characters not %d as in '%s'" % (len(table_lines), table_lines))
        (hor, ver, cor, hea) = table_lines
        self._set_table_lines([hor, ver, cor, cor, cor, cor, cor, cor, cor, cor, cor, hea, cor, cor, cor])
        return self

    def set_decorations(self, decorations: int) -> 'Vistab':
        """Set the table decorations by specifying a bitmask.

        Args:
            decorations (int): A bitmask integer specifying which decorations to apply.
                Can be a bitwise combination of:
                  * Vistab.BORDER: Border around the table
                  * Vistab.HEADER: Horizontal line below the header
                  * Vistab.HLINES: Horizontal lines between rows
                  * Vistab.VLINES: Vertical lines between columns

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_decorations(Vistab.BORDER | Vistab.HEADER)
        """
        self._deco = decorations
        return self

    def set_header_align(self, array: Union[str, List[str]]) -> 'Vistab':
        """Set the desired header alignment.

        Args:
            array (str or List[str]): Specifier for how header cells align. Each element must be:
                * "l": column flushed left
                * "c": column centered
                * "r": column flushed right

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_header_align("lcr")
        """
        if isinstance(array, list) and len(array) == 1 and isinstance(array[0], str) and len(array[0]) > 1:
            array = array[0]
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._header_align = array
        return self

    def set_cols_align(self, array: Union[str, List[str]]) -> 'Vistab':
        """Set the desired columns alignment.

        Args:
            array (str or List[str]): Specifier for how columns align. Each element must be:
                * "l": column flushed left
                * "c": column centered
                * "r": column flushed right

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_cols_align(["l", "r", "l"])
        """
        if isinstance(array, list) and len(array) == 1 and isinstance(array[0], str) and len(array[0]) > 1:
            array = array[0]
        if isinstance(array, str):
            array = [c for c in array]
            pass
        for a in array:
            if a not in ('l', 'c', 'r'):
                raise ValueError(f"Alignment '{a}' is invalid. Allowed alignment characters are: 'l', 'c', 'r'.")
        self._check_row_size(array)
        self._align = array
        return self

    def set_cols_valign(self, array: Union[str, List[str]]) -> 'Vistab':
        """Set the desired columns vertical alignment.

        Args:
            array (str or List[str]): Specifier for how columns align vertically. Each element must be:
                * "t": column aligned on the top of the cell
                * "m": column aligned on the middle of the cell
                * "b": column aligned on the bottom of the cell

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_cols_valign(["t", "m", "b"])
        """
        if isinstance(array, list) and len(array) == 1 and isinstance(array[0], str) and len(array[0]) > 1:
            array = array[0]
        if isinstance(array, str):
            array = [c for c in array]
            pass
        for a in array:
            if a not in ('t', 'm', 'b'):
                raise ValueError(f"Vertical alignment '{a}' is invalid. Allowed vertical alignment characters are: 't', 'm', 'b'.")
        self._check_row_size(array)
        self._valign = array
        return self

    def set_cols_dtype(self, array: Union[str, List[str]]) -> 'Vistab':
        """
        Sets the data types for the columns in the table.

        Args:
            array (Union[str, List[str]]): A list of strings representing the data types for the columns.
                           Acceptable values are: 't' (text), 'f' (float, decimal),
                           'e' (float, exponent), 'i' (integer), 'I' (integer with thousands
                           separators), and 'a' (automatic). Numeric codes accept an optional
                           precision suffix, e.g. 'f2'. An invalid code raises ValueError that
                           enumerates and explains every valid type.

        Example usage:
        ```
        table = Vistab()
        table.set_cols_dtype("ti")  # one text column, one integer column
        table.set_cols_dtype(['t', 'i'])
        ```

        - the elements of the array should be either a callable or any of
          "a", "t", "f", "e" or "i":

            * "a": automatic (try to use the most appropriate datatype)
            * "t": treat as text
            * "f": treat as float in decimal format
            * "e": treat as float in exponential format
            * "i": treat as int
            * "I": treat as int, but print with commas separating thousands
            * a callable: should return formatted string for any value given

        - by default, automatic datatyping is used for each column
        """
        import re
        if isinstance(array, list) and len(array) == 1 and isinstance(array[0], str) and len(array[0]) > 1:
            array = array[0]
        if isinstance(array, str):
            # Parse alphanumeric blocks precisely (e.g., 'f2', 'i', 't') splitting raw strings
            array = re.findall(r'[a-zA-Z]\d*', array.replace(",", ""))

        for a in array:
            if not callable(a) and (not isinstance(a, str) or len(a) == 0 or a[0] not in _DTYPE_CODES):
                raise ValueError(
                    f"Column data type '{a}' is invalid. Valid column data types are:\n"
                    f"{_dtype_help()}"
                )
        self._check_row_size(array)
        self._dtype = array
        return self

    def set_cols_width(self, array: Union[str, List[Any]]) -> 'Vistab':
        """Set the desired columns width in characters.

        Args:
            array (str or List[int]): An array of integers specifying the fixed width of each column.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_cols_width([10, 20, 5])
        """
        self._check_row_size(array)
        try:
            array = list(map(int, array))
        except ValueError:
            sys.stderr.write("Wrong argument in column width specification\n")
            raise
        if reduce(min, array) <= 0:
            raise ValueError("Values less than or equal to zero not allowed. Input: %s" % array)
        self._width = array
        return self

    def set_precision(self, width: int) -> 'Vistab':
        """Set the desired precision for float and exponential formats.

        Args:
            width (int): Decimal string precision. Must be an integer >= 0.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_precision(5)
        """
        if not type(width) is int or width < 0:
            raise ValueError('precision must be an integer greater than or equal to 0')
        self._precision = width
        return self

    @property
    def padding(self) -> int:
        """Get the amount of padding."""
        return self._pad

    @padding.setter
    def padding(self, val: int) -> 'Vistab':
        """Set the amount of padding."""
        self.set_padding(val)
        return self

    def set_padding(self, amount: int) -> 'Vistab':
        """Set the amount of spaces to pad cells horizontally.

        Args:
            amount (int): The number of spaces to pad the left and right sides of each cell's text.
                          Top and bottom padding are not supported. Must be an integer >= 0.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_padding(2)
        """
        if not type(amount) is int or amount < 0:
            raise ValueError('padding must be an integer greater than or equal to 0')
        self._pad = amount
        return self

    def header(self, array: List[Any]) -> 'Vistab':
        """[DEPRECATED] Alias for set_header()."""
        import warnings
        warnings.warn("table.header() is deprecated and will be removed. Please use table.set_header() instead.", DeprecationWarning)
        return self.set_header(array)

    def set_header(self, array: List[Any]) -> 'Vistab':
        """Specify the header of the table.

        Args:
            array (List[Any]): A list of objects/strings to use as the table's header.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.header(["Name", "Age"])
        """
        expanded = self._expand_spans_in_row(array)
        processed_array = self._check_row_size(expanded, is_data_row=True)
        if processed_array is not None:
            for cell in processed_array:
                if isinstance(cell, VistabCell):
                    cell.value = obj2unicode(cell.value)
            self._header = processed_array
        return self

    def set_header_span(self, col_idx: int, colspan: int, combine: Optional[str] = " ") -> 'Vistab':
        """Set the column span of a specific header cell."""
        if not self._header:
            raise ValueError("Header must be set before applying spans.")

        # Resolve negative col_idx
        if col_idx < 0:
            col_idx = len(self._header) + col_idx
        if col_idx >= len(self._header) or col_idx < 0:
            raise IndexError("Column index out of range.")

        self._apply_span_to_list(self._header, col_idx, colspan, combine)
        return self

    def set_cell_span(self, row_idx: int, col_idx: int, colspan: int, combine: Optional[str] = " ") -> 'Vistab':
        """Set the column span of a specific data cell."""
        if row_idx < 0:
            row_idx = len(self._rows) + row_idx
        if row_idx >= len(self._rows) or row_idx < 0:
            raise IndexError("Row index out of range.")

        row_list = self._rows[row_idx]
        if col_idx < 0:
            col_idx = len(row_list) + col_idx
        if col_idx >= len(row_list) or col_idx < 0:
            raise IndexError("Column index out of range.")

        self._apply_span_to_list(row_list, col_idx, colspan, combine)
        return self

    def _apply_span_to_list(self, row_list: List[VistabCell], col_idx: int, colspan: int, combine: Optional[str] = " "):
        if combine is not None and not isinstance(combine, str):
            raise TypeError("combine must be a string or None")

        if not isinstance(colspan, int) or colspan < 1:
            raise ValueError("Colspan must be an integer >= 1")
        if colspan == 1:
            return # No-op

        if col_idx + colspan > len(row_list):
            raise ValueError(f"Span of {colspan} from column {col_idx} exceeds column count limit of {len(row_list)}.")

        target_cell = row_list[col_idx]
        if isinstance(target_cell, VistabPlaceholderCell) or (isinstance(target_cell, VistabCell) and target_cell.is_placeholder):
            # Find the owner cell
            owner_idx = "unknown"
            for idx, cell in enumerate(row_list):
                if cell is target_cell.source_cell:
                    owner_idx = idx
                    break
            raise ValueError(f"Cannot span from column {col_idx} because it is a placeholder owned by column {owner_idx}.")

        # Overlap checks & covered non-empty cell checks (validate first to prevent partial mutation)
        for offset in range(colspan):
            curr_idx = col_idx + offset
            if curr_idx == col_idx:
                continue

            cell = row_list[curr_idx]

            # 1. Overlap checks
            if isinstance(cell, VistabCell) and cell.colspan > 1 and not cell.is_placeholder:
                raise ValueError(f"Span of {colspan} from column {col_idx} would overlap with an existing span starting at column {curr_idx}.")
            if isinstance(cell, VistabPlaceholderCell) or (isinstance(cell, VistabCell) and cell.is_placeholder):
                if cell.source_cell is not target_cell:
                    owner_idx = "unknown"
                    for idx, o_cell in enumerate(row_list):
                        if o_cell is cell.source_cell:
                            owner_idx = idx
                            break
                    raise ValueError(f"Span of {colspan} from column {col_idx} would overlap with an existing span starting at column {owner_idx}.")

            # 2. Non-empty checks (only raise in strict mode combine=None)
            if combine is None:
                val = cell.value if isinstance(cell, VistabCell) else cell
                if val is not None and str(val).strip() != "":
                    raise ValueError(f"column {curr_idx} is non-empty and combine=None; pass combine=' ' (or another separator) to merge these values, or clear the cell first.")

        # Validated successfully. Apply mutations transactionally.
        if isinstance(combine, str):
            parts = []
            t_val = target_cell.value if isinstance(target_cell, VistabCell) else target_cell
            if t_val is not None and str(t_val).strip() != "":
                parts.append(str(t_val))

            for offset in range(1, colspan):
                curr_idx = col_idx + offset
                cell = row_list[curr_idx]
                val = cell.value if isinstance(cell, VistabCell) else cell
                if val is not None and str(val).strip() != "":
                    parts.append(str(val))

            source_val = combine.join(parts)
        else:
            source_val = target_cell.value if isinstance(target_cell, VistabCell) else target_cell

        source_cell = VistabCell(source_val, colspan=colspan)
        row_list[col_idx] = source_cell

        for offset in range(1, colspan):
            row_list[col_idx + offset] = VistabPlaceholderCell(source_cell)

    def add_row(self, array: List[Any]) -> 'Vistab':
        """Add a row to the table.

        Args:
            array (List[str]): Extracted strings or display values for each column.
                               Cells can contain newlines and tabs.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.add_row(["Arnold", "Fitzpatrick"])
        """
        expanded = self._expand_spans_in_row(array)
        processed_array = self._check_row_size(expanded, is_data_row=True)
        if processed_array is None:
            return self

        if not hasattr(self, "_dtype"):
            self._dtype = ["a"] * self._row_size
        self._rows.append(processed_array)
        return self
    def add_rows(self, rows: Iterable[Iterable[Any]], header: bool = True) -> 'Vistab':
        """Add several rows in the rows stack.

        Args:
            rows (Iterable[Iterable[Any]]): An iterator or 2D array of rows to add.
            header (bool): Specifies if the first row in the sequence should be used as the
                           header of the table. Default is True.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.add_rows([["Name", "Age"], ["Gabriel", 25]])
        """
        # nb: iterate parsing python 3 backwards mapping
        if header:
            if hasattr(rows, '__iter__') and (hasattr(rows, '__next__') or hasattr(rows, 'next')):
                self.set_header(next(rows))
            else:
                self.set_header(rows[0])
                rows = rows[1:]
        for row in rows:
            self.add_row(row)
        return self

    def set_rows(self, rows: Iterable[Iterable[Any]], header: bool = True) -> 'Vistab':
        """Replace all rows in the table with the provided rows.

        Args:
            rows (Iterable[Iterable[Any]]): An iterator or 2D array of rows to replace the current ones.
            header (bool): Specifies if the first row in the sequence should be used as the
                           header of the table. Default is True.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_rows([["Name", "Age"], ["Alice", 25]])
        """
        self._rows = []
        return self.add_rows(rows, header)

    def draw(self) -> Optional[str]:
        """Draw the table and return as an ASCII/Unicode string.

        Returns:
            str: The fully rendered string representation of the table.
                 Returns None if there is no data to draw.

        Example:
            print(table.draw())
        """
        if not self._header and not self._rows:
            return

        self._apply_sorting()

        # Back up original data to handle max_rows and max_cols
        original_header = self._header.copy()
        original_rows = self._rows.copy()
        original_row_size = self._row_size

        # Apply limits for rendering
        if self._max_rows:
            self._rows = self._rows[:self._max_rows]
        if self._max_cols:
            self._header = self._header[:self._max_cols]
            for i, cell in enumerate(self._header):
                if isinstance(cell, VistabCell) and not cell.is_placeholder:
                    if i + cell.colspan > len(self._header):
                        cell.colspan = len(self._header) - i

            new_rows = []
            for row in self._rows:
                sliced = row[:self._max_cols]
                for i, cell in enumerate(sliced):
                    if isinstance(cell, VistabCell) and not cell.is_placeholder:
                        if i + cell.colspan > len(sliced):
                            cell.colspan = len(sliced) - i
                new_rows.append(sliced)
            self._rows = new_rows
            self._row_size = self._max_cols

            # Force cache refresh so dynamic widths don't mismatch
            for cached_prop in ["_width", "_align", "_valign", "_header_align"]:
                if hasattr(self, cached_prop):
                    delattr(self, cached_prop)

        try:
            self._infer_auto_dtypes()

            # Compile raw arrays sequentially integrating explicit formatting
            processed_rows = []
            for row in self._rows:
                cells = []
                old_to_new = {}
                for i, x in enumerate(row):
                    formatted_val = self._str(i, x)
                    if isinstance(x, VistabCell):
                        if x.is_placeholder:
                            new_cell = VistabPlaceholderCell(old_to_new[x.source_cell])
                        else:
                            new_cell = VistabCell(formatted_val, colspan=x.colspan, rowspan=x.rowspan)
                            old_to_new[x] = new_cell
                        cells.append(new_cell)
                    else:
                        new_cell = VistabCell(formatted_val)
                        cells.append(new_cell)
                processed_rows.append(cells)
            self._rows = processed_rows

            self._compute_cols_width()
            self._check_align()

            # Bidi gate: isolate cells only when bidi is on AND the table actually
            # contains RTL content. One pass here keeps non-RTL tables byte-identical
            # (and zero-cost) while _draw_line stays a tight loop.
            self._bidi_active = bool(self._bidi) and (
                any(_contains_rtl(str(c)) for c in self._header)
                or any(_contains_rtl(str(c)) for row in self._rows for c in row)
            )

            out = ""

            # Draw Title horizontally centered over the resulting table width
            if self._title:
                w_cells = sum(self._width)
                w_pads = len(self._width) * 2 * self._pad
                w_seps = len(self._width) - 1
                w_borders = 2 if self.has_border else 0
                total_width = w_cells + w_pads + w_seps + w_borders
                out += self._title.center(total_width) + "\n"

            if self.has_border:
                out += self._hline(location=Vistab.TOP)
            if self._header:
                out += self._draw_line(self._header, isheader=True)
                if self.has_header and len(self._rows) > 0 and ((self._deco & Vistab.HEADER) > 0):
                    out += self._hline_header(location=Vistab.MIDDLE)
            length = len(self._rows)
            for idx, row in enumerate(self._rows):
                out += self._draw_line(row, row_idx=idx)
                if self.has_hlines() and (idx + 1) < length:
                    out += self._hline(location=Vistab.MIDDLE, row_idx=idx)

            if self.has_border:
                out += self._hline(location=Vistab.BOTTOM)
            return out[:-1]
        finally:
            # Safely restore original data post-render
            self._header = original_header
            self._rows = original_rows
            self._row_size = original_row_size

    def stream(self, stream_iterator: Iterable, sample_size: int = 100) -> Iterator[str]:
        """
        Stream table formatting infinitely avoiding memory buffering.

        Args:
            stream_iterator (Iterable[Iterable[Any]]): The iterable yielding matrix rows sequentially.
            sample_size (int): The number of rows to sample at the beginning to calculate column widths naturally.

        Yields:
            str: Each formatted table line (borders, headers, and rows).
        """
        stream_iterator = iter(stream_iterator)
        sample = []

        # 1. Capture the initial subset to derive geometry logic.
        try:
            for _ in range(sample_size):
                sample.append(next(stream_iterator))
        except StopIteration:
            pass

        if not sample:
            return

        # Temporarily back up internal state
        original_header = self._header.copy()
        original_rows = self._rows.copy()
        original_row_size = self._row_size

        # We must clear physical structures to calculate geometries on the sample properly
        self._header = []
        self._rows = []
        self._row_size = original_row_size if original_row_size else 0

        # Ingest sampled boundary
        if self._has_header:
            self.set_header(sample[0])
            sample = sample[1:]

        for row in sample:
            self.add_row(row)

        # Limits mappings safely on sample sizes
        if self._max_cols:
            self._header = self._header[:self._max_cols]
            for i, cell in enumerate(self._header):
                if isinstance(cell, VistabCell) and not cell.is_placeholder:
                    if i + cell.colspan > len(self._header):
                        cell.colspan = len(self._header) - i

            new_rows = []
            for row in self._rows:
                sliced = row[:self._max_cols]
                for i, cell in enumerate(sliced):
                    if isinstance(cell, VistabCell) and not cell.is_placeholder:
                        if i + cell.colspan > len(sliced):
                            cell.colspan = len(sliced) - i
                new_rows.append(sliced)
            self._rows = new_rows
            self._row_size = self._max_cols

            # Force cache refresh so dynamic widths don't mismatch
            for cached_prop in ["_width", "_align", "_valign", "_header_align"]:
                if hasattr(self, cached_prop):
                    delattr(self, cached_prop)

        # Apply cell transformations sequentially on the sample slice
        processed_rows = []
        for row in self._rows:
            cells = []
            old_to_new = {}
            for i, x in enumerate(row):
                formatted_val = self._str(i, x)
                if isinstance(x, VistabCell):
                    if x.is_placeholder:
                        new_cell = VistabPlaceholderCell(old_to_new[x.source_cell])
                    else:
                        new_cell = VistabCell(formatted_val, colspan=x.colspan, rowspan=x.rowspan)
                        old_to_new[x] = new_cell
                    cells.append(new_cell)
                else:
                    new_cell = VistabCell(formatted_val)
                    cells.append(new_cell)
            processed_rows.append(cells)
        self._rows = processed_rows

        # Compute exact geometries!
        self._compute_cols_width()
        self._check_align()

        # Bidi gate (streaming): decide from the sampled rows + header. This is best-effort
        # for an unbounded stream (RTL that first appears only after the sample window will
        # not retroactively toggle it), which is acceptable and matches how geometry itself
        # is sampled here.
        self._bidi_active = bool(self._bidi) and (
            any(_contains_rtl(str(c)) for c in self._header)
            or any(_contains_rtl(str(c)) for row in self._rows for c in row)
        )

        # Yield the top structural bounds
        if self._title:
            w_cells = sum(self._width)
            w_pads = len(self._width) * 2 * self._pad
            w_seps = len(self._width) - 1
            w_borders = 2 if self.has_border else 0
            total_width = w_cells + w_pads + w_seps + w_borders
            yield self._title.center(total_width) + "\n"

        if self.has_border:
            yield self._hline(location=Vistab.TOP)

        if self._header:
            yield self._draw_line(self._header, isheader=True)
            # Standard CLI doesn't yield the header unless rows exist
            if self.has_header and len(self._rows) > 0 and ((self._deco & Vistab.HEADER) > 0):
                yield self._hline_header(location=Vistab.MIDDLE)

        # Define internal generator chain merging sample and remainder streams!
        def stream_exhaust():
            # Yield pre-buffered rows parsed already mechanically
            for parsed_row in self._rows:
                yield parsed_row, False  # Already parsed, not abnormal
            # Yield remainder rows
            for raw_row in stream_iterator:
                old_pad = self._metrics.get("padded", 0)
                old_trunc = self._metrics.get("truncated", 0)

                expanded = self._expand_spans_in_row(raw_row)
                processed_row = self._check_row_size(expanded, is_data_row=True)
                if processed_row is None:
                    continue  # Skipped

                is_abnormal = (self._metrics.get("padded", 0) > old_pad) or (self._metrics.get("truncated", 0) > old_trunc)

                if self._max_cols:
                    processed_row = processed_row[:self._max_cols]
                    for i, cell in enumerate(processed_row):
                        if isinstance(cell, VistabCell) and not cell.is_placeholder:
                            if i + cell.colspan > len(processed_row):
                                cell.colspan = len(processed_row) - i

                # Format cells preserving wrappers
                cells = []
                old_to_new = {}
                for i, x in enumerate(processed_row):
                    formatted_val = self._str(i, x)
                    if isinstance(x, VistabCell):
                        if x.is_placeholder:
                            new_cell = VistabPlaceholderCell(old_to_new[x.source_cell])
                        else:
                            new_cell = VistabCell(formatted_val, colspan=x.colspan, rowspan=x.rowspan)
                            old_to_new[x] = new_cell
                        cells.append(new_cell)
                    else:
                        new_cell = VistabCell(formatted_val)
                        cells.append(new_cell)

                yield cells, is_abnormal
        # Final yielding phase
        drawn_rows = 0
        gen = stream_exhaust()
        try:
            prev_row, is_abn = next(gen)
            while True:
                # Max rows check
                if self._max_rows and drawn_rows >= self._max_rows:
                    break

                drawn_rows += 1
                try:
                    next_row, next_abn = next(gen)
                    # We have a next row, so yield current and hline
                    yield self._draw_line(prev_row, row_idx=drawn_rows-1, is_abnormal=is_abn)
                    if self.has_hlines():
                        yield self._hline(location=Vistab.MIDDLE, row_idx=drawn_rows-1)
                    prev_row, is_abn = next_row, next_abn
                except StopIteration:
                    # We are at the final row
                    yield self._draw_line(prev_row, row_idx=drawn_rows-1, is_abnormal=is_abn)
                    break
        except StopIteration:
            pass

        if self.has_border:
            yield self._hline(location=Vistab.BOTTOM)

        # restore instance properties
        self._header = original_header
        self._rows = original_rows
        self._row_size = original_row_size

    @classmethod
    def _to_float(cls, x):
        if x is None:
            raise FallbackToText()
        try:
            return float(x)
        except (TypeError, ValueError):
            raise FallbackToText()

    @classmethod
    def _fmt_int(cls, x, **kw):
        """Integer formatting class-method.

        - x will be float-converted and then used.
        - fractional values round half away from zero (2.5 -> 3, -2.5 -> -3).
        """
        return str(_round_half_up(cls._to_float(x)))

    @classmethod
    def _fmt_comma_int(cls, x, **kw):
        """Integer formatting class-method with thousands separators.

        - x will be float-converted and then used.
        - fractional values round half away from zero (2.5 -> 3, -2.5 -> -3).
        """
        return f"{_round_half_up(cls._to_float(x)):,d}"

    @classmethod
    def _fmt_float(cls, x, **kw):
        """Float formatting class-method.

        - x parameter is ignored. Instead kw-argument f being x float-converted
          will be used.

        - precision will be taken from `n` kw-argument.
        """
        n = kw.get('n')
        return '%.*f' % (n, cls._to_float(x))

    @classmethod
    def _fmt_exp(cls, x, **kw):
        """Format exponent.

        Args:
            x(any): parameter is ignored. Instead kw-argument f being x
            float-converted will be used.

        Note:
            precision will be taken from `n` kwarg.
        """
        n = kw.get('n')
        return '%.*e' % (n, cls._to_float(x))

    @classmethod
    def _fmt_comma_float(cls, x, **kw):
        """Float with thousands separators (grouped), e.g. 123,456.79.

        Precision is taken from the `n` kw-argument (or the global precision).
        Non-numeric input raises FallbackToText, matching the other numeric codes.
        """
        n = kw.get('n')
        return f"{cls._to_float(x):,.{n}f}"

    @classmethod
    def _fmt_comma_exp(cls, x, **kw):
        """Scientific/exponential with thousands separators on the mantissa's integer
        part (rarely needed, provided for symmetry with the grouped float code).
        """
        n = kw.get('n')
        return f"{cls._to_float(x):,.{n}e}"

    @classmethod
    def _fmt_text(cls, x, **kw):
        """Format string / text."""
        return obj2unicode(x)

    @classmethod
    def _fmt_auto(cls, x, **kw):
        """Auto formatting class-method."""
        f = cls._to_float(x)
        if abs(f) > 1e8:
            fn = cls._fmt_exp
        elif f != f:  # NaN
            fn = cls._fmt_text
        elif f - round(f) == 0:
            fn = cls._fmt_int
        else:
            fn = cls._fmt_float
        return fn(x, **kw)

    def _str(self, i, x):
        """Handle string formatting of cell data.

        Args:
            i(int): index of the cell datatype in self._dtype
            x(any): cell data to format
        """
        raw_val = x.value if isinstance(x, VistabCell) else x

        format_map = {
            'a': self._fmt_auto,
            'i': self._fmt_int,
            'I': self._fmt_comma_int,
            'f': self._fmt_float,
            'F': self._fmt_comma_float,
            'e': self._fmt_exp,
            'E': self._fmt_comma_exp,
            't': self._fmt_text,
        }

        n = self._precision
        dtype = self._dtype[i] if hasattr(self, '_dtype') else "a"

        if isinstance(dtype, str) and len(dtype) > 1 and dtype[1:].isdigit():
            n = int(dtype[1:])
            dtype = dtype[0]

        # None in a NUMERIC column renders as an empty cell, not the literal string "None"
        # (B3). Text columns ('t') and callables keep full control over None.
        if raw_val is None and isinstance(dtype, str) and dtype in ('a', 'i', 'I', 'f', 'F', 'e', 'E'):
            return ""

        try:
            if callable(dtype):
                return dtype(raw_val)
            else:
                return format_map[dtype](raw_val, n=n)
        except FallbackToText:
            return self._fmt_text(raw_val)

    def _check_row_size(self, array, is_data_row=False):
        """Check that the specified array fits the previous rows size and apply handlers if it is jagged."""
        if not self._row_size:
            self._row_size = len(array)
            return array

        if self._row_size != len(array):
            array_len = len(array)

            # Identify row being short or long
            if array_len < self._row_size:
                action = self.on_short_row if is_data_row else "raise"
                if action == "raise":
                    raise ArraySizeError("array should contain %d elements not %s (array=%s)" % (self._row_size, array_len, array))
                elif action == "skip":
                    self._metrics["skipped"] += 1
                    return None
                elif action == "pad":
                    # Pad out to the defined max lengths using VistabCell objects if the row is object-wrapped
                    padding_item = VistabCell("") if any(isinstance(x, VistabCell) for x in array) else ""
                    array = list(array) + [padding_item] * (self._row_size - array_len)
                    self._metrics["padded"] += 1
            else:
                action = self.on_long_row if is_data_row else "raise"
                if action == "raise":
                    raise ArraySizeError("array should contain %d elements not %s (array=%s)" % (self._row_size, array_len, array))
                elif action == "skip":
                    self._metrics["skipped"] += 1
                    return None
                elif action == "truncate":
                    # Slice truncating excess cells mapping.
                    array = list(array)[:self._row_size]
                    # Adjust spans if sliced in the middle of placeholders
                    for i in range(len(array)):
                        cell = array[i]
                        if isinstance(cell, VistabCell) and not cell.is_placeholder:
                            if i + cell.colspan > len(array):
                                cell.colspan = len(array) - i
                    self._metrics["truncated"] += 1

        return array

    def has_vlines(self):
        """Return a boolean, if vlines are required or not."""
        return self._deco & Vistab.VLINES > 0

    def has_hlines(self):
        """Return a boolean, if hlines are required or not."""
        return self._deco & Vistab.HLINES > 0
    def _hline_header(self, location=MIDDLE):
        """Print header's horizontal line."""
        return self._build_hline(is_header=True, location=location)

    def _hline(self, location, row_idx=None):
        """Print an horizontal line."""
        return self._build_hline(is_header=False, location=location, row_idx=row_idx)

    def _get_spanned_boundaries(self, row: List[Any]) -> Set[int]:
        """Returns the set of column indices that are interior to a colspan block in the row."""
        spanned = set()
        if not row:
            return spanned
        i = 0
        while i < len(row):
            cell = row[i]
            colspan = cell.colspan if isinstance(cell, VistabCell) else 1
            for offset in range(1, colspan):
                spanned.add(i + offset)
            i += colspan
        return spanned

    def _build_hline(self, is_header=False, location=MIDDLE, row_idx=None):
        """Return a string used to separated rows or separate header from rows."""
        if self._style == "none":
            return ""
        horiz_char = self._char_hew if is_header else self._char_ew
        if Vistab.TOP == location:
            left, mid, right = self._char_se, self._char_sew, self._char_sw
        elif Vistab.MIDDLE == location:
            if is_header:
                left, mid, right = self._char_hnse, self._char_hnsew, self._char_hnsw
            else:
                left, mid, right = self._char_nse, self._char_nsew, self._char_nsw
                pass
        elif Vistab.BOTTOM == location:
            left, mid, right = self._char_ne, self._char_new, self._char_nw
        else:
            raise ValueError("Unknown location '%s'. Should be one of Vistab.TOP, Vistab.MIDDLE, or Vistab.BOTTOM." % (location))

        row_above = None
        row_below = None

        if Vistab.TOP == location:
            row_below = self._header if self._header else (self._rows[0] if self._rows else None)
        elif Vistab.BOTTOM == location:
            # The row above the bottom border is the last data row, or the header for a
            # header-only table (no data rows).
            row_above = self._rows[-1] if self._rows else (self._header if self._header else None)
        elif Vistab.MIDDLE == location:
            if is_header:
                row_above = self._header
                row_below = self._rows[0] if self._rows else None
            else:
                if row_idx is not None and row_idx < len(self._rows):
                    row_above = self._rows[row_idx]
                    if row_idx + 1 < len(self._rows):
                        row_below = self._rows[row_idx + 1]

        # A divider touches this rule from a given side only if a row exists on that
        # side AND the boundary is not interior to a spanned block in that row. A
        # boundary interior to a span has no vertical divider on that side.
        spanned_above = self._get_spanned_boundaries(row_above)
        spanned_below = self._get_spanned_boundaries(row_below)
        has_above = row_above is not None
        has_below = row_below is not None

        # Directional junction glyphs. `mid` already carries the arms appropriate to the
        # rule location (down-tee at TOP, up-tee at BOTTOM, full cross at MIDDLE). For a
        # MIDDLE rule we additionally need the one-sided tees so a spanned block on one
        # side is not pierced by a dangling junction (e.g. a header `|` above a merged
        # data cell terminates as an up-tee, not a flat line). `_char_new` = up-tee
        # (arms N-E-W); `_char_sew` = down-tee (arms S-E-W). Header double-line styles
        # lack dedicated header tees, so MIDDLE falls back to these (see remediation).
        if Vistab.MIDDLE == location:
            up_tee, down_tee = self._char_new, self._char_sew
        else:
            up_tee = down_tee = mid

        segments = []
        for col_idx, w in enumerate(self._width):
            segments.append(horiz_char * w)
            if col_idx < len(self._width) - 1:
                boundary_idx = col_idx + 1
                divider_above = has_above and (boundary_idx not in spanned_above)
                divider_below = has_below and (boundary_idx not in spanned_below)
                if divider_above and divider_below:
                    junction = mid
                elif divider_above:
                    junction = up_tee
                elif divider_below:
                    junction = down_tee
                else:
                    junction = horiz_char
                segments.append("%s%s%s" % (horiz_char * self._pad, junction if self.has_vlines() else horiz_char, horiz_char * self._pad))
        hline = "".join(segments)
        if self.has_border:
            hline = "%s%s%s%s%s\n" % (left, horiz_char * self._pad, hline, horiz_char * self._pad, right)
        else:
            hline += "\n"

        b_on, b_off = self._get_border_ansi()
        return b_on + hline[:-1] + b_off + "\n"
    def _len_cell(self, cell):
        """Return the width of the cell.

        Special characters are taken into account to return the width of the
        cell, such like newlines and tabs.
        """
        cell_lines = str(cell).split('\n')
        maxi = 0
        for line in cell_lines:
            length = 0
            parts = line.split('\t')
            for part, i in zip(parts, list(range(1, len(parts) + 1))):
                length = length + self.vislen(part)
                if i < len(parts):
                    length = (length // 8 + 1) * 8
            maxi = max(maxi, length)
        return maxi

    def _compute_cols_width(self) -> None:
        """
        Compute and set the width of each column in the table.

        This method calculates the width of each column based on the content and
        adjusts the widths to fit within the maximum table width if specified.
        If a specific column width is already set, the method exits early.
        If the total width exceeds the desired table width, the column widths
        are recomputed to fit, and cell content is wrapped as necessary.

        Raises:
        -------
        ValueError
            If the maximum width is too low to render the data properly.

        Example:
        --------
        ```
        table = Vistab()
        table.add_rows([["Name", "Age"], ["Alice", 25], ["Bob", 30]])
        table._compute_cols_width()
        ```
        """

        if hasattr(self, "_width"):
            return

        ncols = self._row_size
        maxi = [0] * ncols

        # 1. Calculate standard maximum width using only non-spanned cells
        if self._header:
            for i, cell in enumerate(self._header):
                is_spanned = isinstance(cell, VistabCell) and (cell.colspan > 1 or cell.is_placeholder)
                if not is_spanned:
                    if i < len(maxi):
                        maxi[i] = max(maxi[i], self._len_cell(cell))
                    else:
                        maxi.append(self._len_cell(cell))

        for row in self._rows:
            for i, cell in enumerate(row):
                is_spanned = isinstance(cell, VistabCell) and (cell.colspan > 1 or cell.is_placeholder)
                if not is_spanned:
                    if i < len(maxi):
                        maxi[i] = max(maxi[i], self._len_cell(cell))
                    else:
                        maxi.append(self._len_cell(cell))

        ncols = len(maxi)
        content_width = sum(maxi)
        deco_width = 3 * (ncols - 1) + [0, 4][self.has_border]

        if self._max_width and (content_width + deco_width) > self._max_width:
            if self._max_width < (ncols + deco_width):
                raise ValueError(f"max_width ({self._max_width}) too low to render data. The minimum for this table would be {ncols + deco_width}.")

            available_width = self._max_width - deco_width
            newmaxi = [0] * ncols
            i = 0

            while available_width > 0:
                if newmaxi[i] < maxi[i]:
                    newmaxi[i] += 1
                    available_width -= 1
                i = (i + 1) % ncols

            maxi = newmaxi

        self._width = maxi

        # 2. Distribute spanned widths using divmod over self._width
        spanned_cells_to_process = []
        if self._header:
            for i, cell in enumerate(self._header):
                if isinstance(cell, VistabCell) and cell.colspan > 1 and not cell.is_placeholder:
                    spanned_cells_to_process.append((i, cell.colspan, self._len_cell(cell)))

        for row in self._rows:
            for i, cell in enumerate(row):
                if isinstance(cell, VistabCell) and cell.colspan > 1 and not cell.is_placeholder:
                    spanned_cells_to_process.append((i, cell.colspan, self._len_cell(cell)))

        for c, k, req in spanned_cells_to_process:
            curr = self._span_block_width(c, k)
            if req <= curr:
                continue
            deficit = req - curr

            if self._max_width:
                # A width ceiling is in force. Expand the span to fit on one line
                # only as far as the remaining budget allows; beyond that the content
                # wraps into its block instead of growing the table past max_width.
                deco_width = 3 * (ncols - 1) + [0, 4][self.has_border]
                headroom = self._max_width - (sum(self._width) + deco_width)
                grow = min(deficit, max(0, headroom))
                if grow > 0:
                    base, extra = divmod(grow, k)
                    for j in range(c, c + k):
                        self._width[j] += base
                    for j in range(c, min(c + extra, c + k)):
                        self._width[j] += 1

                # A block can still be too narrow to wrap legibly when its covered
                # columns have little or no standalone content (their maxi was 0/tiny,
                # so the shrink pass gave them almost nothing) and no budget headroom
                # was available. In that case borrow width from the widest columns
                # OUTSIDE the span, keeping the total (and therefore max_width)
                # unchanged, until the block reaches a minimum legible width.
                covered = set(range(c, c + k))
                min_block = k + (k - 1) * self._sep_width()
                while self._span_block_width(c, k) < min_block:
                    donor = -1
                    donor_w = 1
                    for j in range(ncols):
                        if j in covered:
                            continue
                        if self._width[j] > donor_w:
                            donor_w = self._width[j]
                            donor = j
                    if donor < 0:
                        break  # no slack to borrow; block wraps as best it can
                    self._width[donor] -= 1
                    self._width[c] += 1
                continue

            # No width ceiling: expand covered columns to fit on one line (original
            # behavior, unchanged).
            base, extra = divmod(deficit, k)
            for j in range(c, c+k):
                self._width[j] += base
            for j in range(c, c+extra):
                self._width[j] += 1

    def _infer_auto_dtypes(self) -> None:
        """ upgrade 'a' (automatic) columns into strict numeric constraints.

        This prevents jagged decimal alignments (e.g. 10 mixed with 12.3456) by
        guaranteeing column-wide uniformity if the array is perfectly bounded.
        """
        if not self._rows:
            return

        if not hasattr(self, "_dtype"):
            self._dtype = ["a"] * self._row_size

        for c in range(self._row_size):
            if self._dtype[c] == "a":
                valid_cells = 0
                numeric_cells = 0
                has_scientific = False
                has_float = False

                for row in self._rows:
                    if c < len(row):
                        val = str(row[c]).strip()
                        if val:
                            valid_cells += 1
                            try:
                                clean_val = val.replace(",", "")
                                f_val = float(clean_val)
                                numeric_cells += 1

                                if 'e' in clean_val.lower():
                                    has_scientific = True
                                elif '.' in clean_val or f_val % 1 != 0:
                                    has_float = True
                            except ValueError:
                                pass

                if valid_cells > 0 and numeric_cells == valid_cells:
                    if has_scientific:
                        self._dtype[c] = "e"
                    elif has_float:
                        self._dtype[c] = "f"
                    else:
                        self._dtype[c] = "i"

    def _check_align(self) -> None:
        """
        Ensure that column alignment settings are specified, set default values if not.

        This method checks if the alignment, header alignment, and vertical alignment
        settings for the columns are specified. If not, it sets default alignment values.

        Example:
        --------
        ```
        table = Vistab()
        table._check_align()
        ```
        """
        # Check if header alignment is set; if not, set default alignment to center.
        if not hasattr(self, "_header_align"):
            self._header_align = ["c"] * self._row_size

        # Check if column alignment is set; if not, compute data-centric defaults
        if not hasattr(self, "_align"):
            self._align = ["l"] * self._row_size
            if hasattr(self, "_dtype") and self._rows:
                for c in range(self._row_size):
                    # Safely map the root type definition (extracting 'f' from 'f2')
                    dtype_val = self._dtype[c]
                    dtype_char = dtype_val[0] if isinstance(dtype_val, str) and len(dtype_val) > 0 else dtype_val

                    # Explicit numeric types physically lock right-alignment
                    if dtype_char in ("i", "I", "f", "e"):
                        self._align[c] = "r"
                    # Auto types physically parse physical storage mapping characters
                    elif dtype_char == "a":
                        valid_cells = 0
                        numeric_cells = 0
                        for row in self._rows:
                            if c < len(row):
                                val = str(row[c]).strip()
                                if val:
                                    valid_cells += 1
                                    try:
                                        float(val.replace(",", "")) # Catch formatted sequences
                                        numeric_cells += 1
                                    except ValueError:
                                        pass
                        # If row data is purely numerical, evaluate 'r' structurally
                        if valid_cells > 0 and numeric_cells == valid_cells:
                            self._align[c] = "r"

        # Check if vertical alignment is set; if not, set default alignment to top.
        if not hasattr(self, "_valign"):
            self._valign = ["t"] * self._row_size

    def _ansi_safe_clip(self, text: str, limit: int) -> str:
        """Clip a string to a specific visible limit structurally preserving nested formatting correctly."""
        if self.vislen(text) <= limit:
            return text

        vis_count = 0
        clamped = ""
        parts = re.split(self._vislen.ansi_escape, text)
        codes = self._vislen.ansi_escape.findall(text)

        for i, part in enumerate(parts):
            available = limit - vis_count
            part_len = self.vislen(part)

            if part_len <= available:
                clamped += part
                vis_count += part_len
                if i < len(codes):
                    clamped += codes[i]
            else:
                for char in part:
                    char_len = self.vislen(char)
                    if vis_count + char_len > limit:
                        break
                    clamped += char
                    vis_count += char_len
                break

        return clamped + "\033[0m"

    def _draw_line(self, line: List[str], isheader: bool = False, row_idx: int = None, is_abnormal: bool = False) -> str:
        """
        Draw a line of the table.

        This method splits the given line into individual cells and arranges them
        according to the specified alignments and widths. It handles the drawing
        of borders and spaces between cells as well.

        Args:
        -----
        line : List[str]
            The line (list of cell content) to be drawn.
        isheader : bool, optional
            Indicates if the line to be drawn is a header line. Default is False.
        row_idx : int, optional
            Indicates the 0-indexed row position for structural styling targets.
        is_abnormal : bool, optional
            Internal tracker checking if the row length structurally violated boundary boundaries.

        Returns:
        --------
        str
            The formatted line as a string.

        Example:
        --------
        ```
        table = Vistab()
        line = ["Name", "Age"]
        print(table._draw_line(line, isheader=True, row_idx=0))
        ```
        """

        # Split the line into individual cells, handling headers if necessary.
        original_line = list(line)
        line = self._splitit(line, isheader, row_idx=row_idx)
        space = " "
        out_parts = []

        # Cache repetitive property access inside local namespace for high-speed loops
        b_on, b_off = self._get_border_ansi()
        has_border = self.has_border
        pad_str = space * self._pad
        char_ns = self._char_ns
        v_delim = b_on + [space, char_ns][self.has_vlines()] + b_off
        num_cols = len(line)

        # Iterate over each row of the split line.
        for i in range(self.vislen(line[0])):
            if has_border:
                out_parts.append(b_on)
                out_parts.append(char_ns)
                out_parts.append(b_off)

            col_idx = 0
            while col_idx < num_cols:
                cell_obj = original_line[col_idx]
                if isinstance(cell_obj, VistabPlaceholderCell) or (isinstance(cell_obj, VistabCell) and cell_obj.is_placeholder):
                    col_idx += 1
                    continue

                colspan = cell_obj.colspan if isinstance(cell_obj, VistabCell) else 1
                w = self._span_block_width(col_idx, colspan)
                align = self._header_align[col_idx] if (isheader and self._has_header) else self._align[col_idx]

                ansi_on, ansi_off = self._get_active_ansi_wrap(row_idx, col_idx, isheader, is_abnormal=is_abnormal)
                if ansi_on: out_parts.append(ansi_on)

                if col_idx > 0 or has_border:
                    out_parts.append(pad_str)

                cell_line = line[col_idx][i]
                cell_line = self._sanitize_destructive_ansi(cell_line)
                if ansi_on:
                    cell_line = self._reassert_ansi_context(cell_line, ansi_on)

                fill = w - self.vislen(cell_line)

                if fill < 0:
                    if self.on_wrap_conflict == "error":
                        raise VistabOverflowError(f"Cell string mapped wrap=False exceeded layout width {w}.")
                    elif self.on_wrap_conflict == "warn":
                        sys.stderr.write(f"[\033[1;33mWARN\033[0m] Vistab geometry cell length ({self.vislen(cell_line)}) bypasses {w} max_width boundary. Deflecting to clipping fallback.\n")
                        cell_line = self._ansi_safe_clip(cell_line, w)
                        fill = 0
                    elif self.on_wrap_conflict == "clip":
                        cell_line = self._ansi_safe_clip(cell_line, w)
                        fill = 0
                    elif self.on_wrap_conflict == "overflow":
                        fill = 0

                # Bidi isolation: wrap the finalized cell content in LTR isolates so RTL
                # text does not reorder the whole line. Done after clipping (so a clip can
                # never orphan an isolate) and after fill is computed (the isolates are
                # zero-width, so alignment/padding math is unchanged). Padding stays OUTSIDE
                # the isolate, which is correct: fill spaces must not join the RTL run.
                if self._bidi_active:
                    cell_line = _LRI + cell_line + _PDI

                if align == "r":
                    if fill > 0: out_parts.append(fill * space)
                    out_parts.append(cell_line)
                elif align == "c":
                    if fill > 0: out_parts.append(int(fill / 2) * space)
                    out_parts.append(cell_line)
                    if fill > 0: out_parts.append(int(fill / 2 + fill % 2) * space)
                else:
                    out_parts.append(cell_line)
                    if fill > 0: out_parts.append(fill * space)

                if col_idx + colspan < num_cols or has_border:
                    out_parts.append(pad_str)

                if ansi_off: out_parts.append(ansi_off)

                if col_idx + colspan < num_cols:
                    out_parts.append(v_delim)

                col_idx += colspan

            if has_border:
                out_parts.append(b_on)
                out_parts.append(char_ns)
                out_parts.append(b_off)

            out_parts.append("\n")

        return "".join(out_parts)

    def _splitit(self, line: List[str], isheader: bool, row_idx: int = None) -> List[List[str]]:
        """
        Split each element of the line to fit the column width.

        Each element is turned into a list, resulting from wrapping the string
        to the desired width. This method ensures that each cell content fits
        within the specified column width and handles vertical alignment.
        It also conditionally respects wrap=False bypass modifiers.

        Args:
        -----
        line : List[str]
            The line (list of cell content) to be split and wrapped.
        isheader : bool
            Indicates if the line to be split is a header line.
        row_idx : int, optional
            The coordinate index tracking structural overrides.

        Returns:
        --------
        List[List[str]]
        """

        line_wrapped = []

        col_idx = 0
        while col_idx < len(line):
            cell = line[col_idx]

            if isinstance(cell, VistabPlaceholderCell) or (isinstance(cell, VistabCell) and cell.is_placeholder):
                line_wrapped.append([])
                col_idx += 1
                continue

            colspan = cell.colspan if isinstance(cell, VistabCell) else 1
            w = self._span_block_width(col_idx, colspan)

            array = []
            do_wrap = self._get_active_wrap_control(row_idx, col_idx, isheader)

            for c in str(cell).split('\n'):
                if c.strip() == "" and do_wrap:
                    array.append("")
                elif not do_wrap:
                    array.append(c)
                else:
                    array.extend(self._cwrap.wrap_list(c, w))
            line_wrapped.append(array)
            col_idx += 1

        # Find the maximum number of lines in any cell
        max_cell_lines = reduce(max, list(map(len, line_wrapped)))

        # Adjust each cell's vertical alignment
        for cell, valign in zip(line_wrapped, self._valign):
            if isheader:
                valign = "t"  # Header cells are always top-aligned
            if valign == "m":
                # Middle alignment: add missing lines evenly to the top and bottom
                missing = max_cell_lines - len(cell)
                cell[:0] = [""] * (missing // 2)
                cell.extend([""] * (missing // 2 + missing % 2))
            elif valign == "b":
                # Bottom alignment: add missing lines to the top
                cell[:0] = [""] * (max_cell_lines - len(cell))
            else:
                # Top alignment (default): add missing lines to the bottom
                cell.extend([""] * (max_cell_lines - len(cell)))
                pass
            pass

        return self._process_lines(line_wrapped)

    def _process_lines(self, lines_2d: List[List[str]]) -> List[List[str]]:
        """
        Process a list of lines to ensure all ANSI escape sequences are
        properly terminated and continued onto the next line if necessary.

        This method handles ANSI escape sequences in table content, ensuring
        that they do not disrupt the visual layout when lines are wrapped.

        Args:
        -----
        lines_2d : List[List[str]]
            The lines to process, where each line is a list of cell content.

        Returns:
        --------
        List[List[str]]
            The processed lines with proper ANSI sequence handling.

        Example:
        --------
        ```
        table = Vistab()
        lines_2d = [["\033[1mBold\033[0m", "Text"], ["Normal", "Text"]]
        processed_lines = table._process_lines(lines_2d)
        print(processed_lines)
        ```
        """
        # Initialize a variable to hold any unterminated ANSI escape sequences
        unterminated_sequences = ""

        # Iterate over each line in the 2D list
        for lines in lines_2d:
            for i in range(len(lines)):
                # If there was a non-reset sequence in the last line, prepend it to this line
                if unterminated_sequences:
                    lines[i] = unterminated_sequences + lines[i]
                    unterminated_sequences = ""

                # Save any ANSI escape sequences that are not terminated by a reset sequence
                unterminated_sequences = "".join(self.non_reset_not_followed_by_reset.findall(lines[i]))
                if unterminated_sequences:
                    # Add a reset sequence to the end of the line
                    lines[i] += "\033[0m"
                    pass
                pass
            pass

        return lines_2d

    pass


def split_list(input_list: List[Any], split_length: int, fill_value: Optional[Any] = None) -> List[List[Any]]:
    """
    Split a list into sub-lists of a specified length.

    If the last sub-list is shorter than the specified length, it will be filled
    with the specified fill value.

    Args:
    -----
    input_list : List[Any]
        The list to split.
    split_length : int
        The length of the sub-lists.
    fill_value : Optional[Any], optional
        The value to fill the last sub-list with. Default is None.

    Returns:
    --------
    List[List[Any]]
        A list of sub-lists.

    Example:
    --------
    ```
    original_list = [1, 2, 3, 4, 5, 6, 7, 8]
    result = split_list(original_list, 3, fill_value=0)
    print(result)  # Outputs: [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
    ```
    """
    # Calculate the number of chunks needed
    num_chunks = (len(input_list) + split_length - 1) // split_length

    # Create the chunks by slicing the input list
    chunks = [input_list[i * split_length:(i + 1) * split_length] for i in range(num_chunks)]

    # If the last chunk is shorter than split_length, fill it with the fill_value
    if len(chunks[-1]) < split_length:
        chunks[-1] += [fill_value] * (split_length - len(chunks[-1]))

    return chunks


def example_table(style: str, padding: int = 1) -> str:
    """
    Create an example table with specified style and padding.

    This function generates a simple table with a specified style and padding
    and returns its string representation.

    Args:
    -----
    style : str
        The style of the table.
    padding : int, optional
        The padding for the cells. Default is 1.

    Returns:
    --------
    str
        The string representation of the example table.

    Example:
    --------
    ```
    print(example_table("bold"))
    ```
    """
    return Vistab([["Hd1", "Hd2", "Hd3"], ["Ce1", "Ce2", "Ce3"], ["Ce4", "Ce5", "Ce6"], ["Ce7", "Ce8", "Ce9"]], style=style, padding=padding).draw()


def print_test_demo():
    tdata = [
        ["Test 1", "Test 2", "Test 3", "Test 4", "Test 5"],
        [
            "\033[1;36mExtraordinar\033[0m\033[3minly\033[0m \033[43;30mlong\033[0m text mapped exactly at the \033[1;32mstart\033[0m to ensure \033[41;37mstrict\033[0m constraint wrapping.",
            "This is some \033[1;31mRed text\033[0m to show the ability to wrap \033[38;5;226mcolored text\033[0m correctly.",
            "\033[4mThis text is underlined, \033[1mbold, and \033[34mblue.\033[0m This is not.",
            "Some \033[1;31mRed mandarin: 这是一个 美好的世界\033[0m for testing.",
            "RTL: هذا \033[32mأخضر\033[0m بينما هذا \033[31mأحمر\033[0m (Arabic) זה \033[34mכחול\033[0m וזה \033[1mמודגש\033[0m (Hebrew)",
        ],
        [
            "This is some normal text to ensure that it is working properly. There is nothing special to be seen here.",
            "\033[44;37m White on Blue \033[0m and \033[43;30m Black on Yellow \033[0m interleaved.\n\nTwo line breaks preceeded this line.",
            "Standard paragraph containing an \033[AIncomprehensible\033[D word geometrically injected in the middle. up and left characters:[\033[A\033[D]",
            "\033[105;30m Bright Magenta BG \033[0m + \033[106;30m Bright Cyan BG \033[0m.",
            "Testing \033[42;37m Green \033[0m \033[41;37m Red \033[0m \033[44;37m Blue \033[0m blocks.",
        ]
    ]

    # Print the second row of the table outside a table line-by-line.
    # NOTE: this demo's colored CONTENT is the whole point (it proves ANSI/CJK-aware
    # wrapping), so content color is preserved even under --no-color; only the chrome
    # (section titles, table styling) honors color-off, and a warning is emitted.
    print(_demo_text("\033[1mTest text line-by-line:\033[0m"))
    for phrase in tdata[1]:
        print(phrase)
    print()


    print(_demo_text("\033[1m\033[1;31mANSI\033[0m\033[1m Color / Escape Sequence Aware Text-Based Tables (width=80)\033[0m:"))
    t1 = Vistab(tdata).set_color(_CLI_COLOR)
    t1.set_max_width(80)
    t1.set_cell_style(1, 4, bg="blue")
    print(t1.draw())

    print(_demo_text("\n\033[1mBelow is the same table without ANSI color / escape sequences. They should wrap the same way.\033[0m"))
    tdata2 = [
        [_strip_ansi(cell) for cell in row]
        for row in tdata
    ]
    t2 = Vistab(tdata2).set_color(_CLI_COLOR)
    t2.set_max_width(80)
    t2.set_cell_style(1, 4, bg="blue")
    print(t2.draw())
    _maybe_warn_color_off()



def print_styles_list():
    print(_demo_text("\033[1mAvailable Styles\033[0m (Note: the default is \"light\"):"))
    style_list = sorted(Vistab.STYLES.keys())
    data = []
    for row in split_list(style_list, 5):
        style_row = []
        tables_row = []
        for style in row:
            if style is None:
                style_row.append("")
                tables_row.append("")
            else:
                style_row.append(style)
                tables_row.append(example_table(style))
        data.append(style_row)
        data.append(tables_row)
        data.append(["", "", "", "", ""])
    t1 = Vistab(data, max_width=120, style="none", alignment="ccccc")
    print(t1.draw())

def print_coordinate_styles_demo():
    print(_demo_text("\033[1m\033[1;36mCoordinate-Based Styling Demonstration\033[0m"))
    print("These styles target specific cells, columns, and rows without mutating structural padding strings or column decorators!\n")

    t = Vistab([
        ["Target Node", "Configuration Profile", "Metric", "Status", "Delta"],
        ["System Core", "x86_64 Architecture\nBoot Sequence\nHardware Layer", "98.2%", "Offline", "-1.2"],
        ["Network Edge", "eth0 / IPv4 Bridge Interface", "10Gbps", "Active", "+4.5"],
        ["Database", "PostgreSQL\nShard Cluster", "4,210 qs", "Syncing", "0.0"],
        ["Memory Cache", "Redis Local Buffer Sequence", "99.9%", "Active", "+0.1"]
    ], style="round-header", padding=2).set_color(_CLI_COLOR)

    # 1. Structural alignments and format geometries
    t.set_max_width(75)  # Aggressive shrink to violently force all rows to wrap and demonstrate valigns
    t.set_cols_align("clrcr")
    t.set_cols_valign("mmbmt")

    # 2. Broad structural targeting
    t.set_header_style(bg="red", fg="bright_white", bold=True)
    t.set_border_style(fg="yellow")

    # 3. Column and Row orthogonal intersections
    t.set_col_style(0, fg="bright_blue", bold=True)
    t.set_row_style(2, bg="blue", fg="white")  # Highlight the entire Network row

    # 4. Strict cellular coordinate overrides (Row, Col)
    t.set_cell_style(1, 3, bg="bright_red", fg="white", bold=True, blink=True)  # Offline status
    t.set_cell_style(4, 3, fg="bright_green", bold=True) # Active status
    t.set_cell_style(1, 4, fg="red", bold=True)          # -1.2
    t.set_cell_style(2, 4, fg="bright_white", bold=True) # Overrides the blue row style!
    t.set_cell_style(3, 1, bg="magenta", fg="bright_white", italic=True) # Deep orthogonal mapping

    print(t.draw())
    print(_demo_text("\n\033[3mCode executed:\033[0m"))
    print("table.set_cols_align('clrcr')")
    print("table.set_cols_valign('mmbmt')")
    print("table.set_header_style(bg='red', fg='bright_white', bold=True)")
    print("table.set_border_style(fg='yellow')")
    print("table.set_col_style(0, fg='bright_blue', bold=True)")
    print("table.set_row_style(2, bg='blue', fg='white')")
    print("table.set_cell_style(1, 3, bg='bright_red', fg='white', bold=True, blink=True) # Offline")
    print("table.set_cell_style(2, 4, fg='bright_white', bold=True)             # Priority intercept")
    print("table.set_cell_style(3, 1, bg='magenta', fg='bright_white')          # Deep override")
    print()
    _maybe_warn_color_off()

def print_colors_list():
    fg_data = []
    keys = list(Vistab.COLORS.keys())
    for chunk in split_list(keys, 4):
        row = []
        for key in chunk:
            if key:
                val = Vistab.COLORS[key]
                row.extend([key, f"\033[{val}m Sample \033[0m"])
            else:
                row.extend(["", ""])
        fg_data.append(row)
    t_fg = Vistab(style="round-header", padding=0)
    t_fg.set_title("\033[1;36m\033[4mForeground Colors (fg=...)\033[0m")
    t_fg.set_rows(fg_data, header=False)

    bg_data = []
    keys = list(Vistab.BG_COLORS.keys())
    for chunk in split_list(keys, 4):
        row = []
        for key in chunk:
            if key:
                val = Vistab.BG_COLORS[key]
                # Combine foreground contrasting text over requested background
                fg_contrast = "30" if "white" in key or "yellow" in key or "cyan" in key else "37"
                row.extend([key, f"\033[{val};{fg_contrast}m Sample \033[0m"])
            else:
                row.extend(["", ""])
        bg_data.append(row)
    t_bg = Vistab(style="round-header", padding=0)
    t_bg.set_title("\033[1;36m\033[4mBackground Colors (bg=...)\033[0m")
    t_bg.set_rows(bg_data, header=False)

    ts_data = []
    keys = list(Vistab.TEXT_STYLES.keys())
    for chunk in split_list(keys, 4):
        row = []
        for key in chunk:
            if key:
                val = Vistab.TEXT_STYLES[key]
                row.extend([key, f"\033[{val}m Sample \033[0m"])
            else:
                row.extend(["", ""])
        ts_data.append(row)
    t_ts = Vistab(style="round-header", padding=0)
    t_ts.set_title("\033[1;36m\033[4mText Decorators (bold=True, etc)\033[0m")
    t_ts.set_rows(ts_data, header=False)

    master = Vistab(style="round", padding=0).set_color(_CLI_COLOR)
    master.set_table_wrap(False)
    master.set_cols_align("c")
    combined_output = f"{t_fg.draw()}\n{t_bg.draw()}\n{t_ts.draw()}"
    master.set_rows([[combined_output]], header=False)
    # Swatches/titles embed literal ANSI as content; _demo_text strips it under --no-color.
    print(_demo_text(master.draw()))
    _maybe_warn_color_off()

def _highlight_span_code(code: str) -> str:
    """Emphasize span-specific tokens in example code (bright cyan), gated on CLI color.

    Literal substring replacement over a small fixed token list. No tokenizer/parser.
    """
    if not _CLI_COLOR:
        return code
    on, off = "\033[1;96m", "\033[0m"
    for tok in ("ColSpan", "set_cell_span", "set_header_span", "combine="):
        code = code.replace(tok, f"{on}{tok}{off}")
    return code


def _print_span_code(code: str):
    """Print an example-code block with span-token highlighting (color-aware)."""
    print(_demo_text("\033[3mExample code:\033[0m") if _CLI_COLOR else "Example code:")
    print(_highlight_span_code(code))


def print_span_demo():
    print(_demo_text("\033[1m\033[1;36mColumn Spanning (Colspan) Demonstration\033[0m"))
    print("Vistab supports inline and post-ingestion column spanning. Note: Rowspan is coming soon.\n")

    # 1. Inline spans, with the code directly beneath the table it produced.
    print("--- 1. Inline Spans in Headers and Rows ---")
    table = Vistab(style="round", padding=1).set_color(_CLI_COLOR)
    table.set_header(["Category", ColSpan("Sub-header Block", 2), "Status"])
    table.add_row(["Engine", ColSpan("Data block spanning 2 columns", 2), "Active"])
    table.add_row(["Memory", "16 GB", "LPDDR5", "Healthy"])
    print(table.draw())
    _print_span_code(
        "from vistab import Vistab, ColSpan\n"
        "table = Vistab(style='round')\n"
        "table.set_header(['Category', ColSpan('Sub-header Block', 2), 'Status'])\n"
        "table.add_row(['Engine', ColSpan('Data block spanning 2 columns', 2), 'Active'])"
    )
    print()

    # 2. Coordinate mutators, code beneath.
    print("--- 2. Programmatic Coordinate Mutators ---")
    table2 = Vistab(style="light", padding=1).set_color(_CLI_COLOR)
    table2.set_header(["Name", "", "", "Status"])
    table2.add_row(["Alice", "Age: 25", "City: Paris", "Active"])
    table2.add_row(["Bob", "", "", "Inactive"])
    table2.set_header_span(0, 3)
    table2.set_cell_span(1, 1, 2)
    print(table2.draw())
    _print_span_code(
        "table2 = Vistab(style='light')\n"
        "table2.set_header(['Name', '', '', 'Status'])\n"
        "table2.add_row(['Alice', 'Age: 25', 'City: Paris', 'Active'])\n"
        "table2.set_header_span(0, 3)\n"
        "table2.set_cell_span(1, 1, 2)  # merge Alice's age/city cells"
    )
    print()

    # 3. Lossless content merging, code beneath.
    print("--- 3. Lossless Content Merging ---")
    table3 = Vistab(style="light", padding=1).set_color(_CLI_COLOR)
    table3.set_header(["Name", "Age", "City"])
    table3.add_row(["Alice", 25, "Paris"])
    print("Pre-merged:")
    print(table3.draw())
    table3.set_cell_span(0, 0, 3, combine=", ")
    print("Post-merged (combine=', '):")
    print(table3.draw())
    _print_span_code(
        "table3 = Vistab(style='light')\n"
        "table3.set_header(['Name', 'Age', 'City'])\n"
        "table3.add_row(['Alice', 25, 'Paris'])\n"
        "table3.set_cell_span(0, 0, 3, combine=', ')  # -> 'Alice, 25, Paris'"
    )
    print()
    _maybe_warn_color_off()


def print_showcase_demo():
    """Curated 'hero' demo: colspan + a theme + CJK/ANSI content + wrapping in one table.

    Fits within 80 columns so it reads cleanly as a README screenshot. Honors --no-color:
    the table is built with the CLI color state, its title flows through _demo_text, and a
    color-off warning fires (this is a color-centric demo).
    """
    print(_demo_text("\033[1m\033[1;36mvistab showcase: colspan + theme + CJK/ANSI wrapping\033[0m"))
    print("One table exercising the headline capabilities at once.\n")

    t = Vistab(style="round-header", max_width=72).set_color(_CLI_COLOR).set_bidi(_CLI_BIDI)
    t.set_theme("ocean-rows-index")
    # "Notes" header in Thai ("put notes here"): Thai is LTR but has no inter-word
    # spaces and uses zero-width combining marks, exercising width measurement.
    t.set_header(["ID", ColSpan("Contact", 2), "ใส่บันทึกที่นี่"])
    t.set_cols_align(["r", "l", "l", "l"])
    t.add_row(["1", "Ada Lovelace", "ada@lovelace.io",
               "First programmer; notes wrap across lines cleanly."])
    t.add_row(["2", "关羽 (Guan Yu)", "guan@shu.han",
               "CJK width handled beside ASCII."])
    t.add_row(["3", _demo_text("José \033[1;31mÑoño\033[0m"), "jose@ex.com",
               "Accents + inline ANSI coexist with the theme."])
    # Row with interleaved partial-word coloring (only parts of words are colored).
    t.add_row(["4",
               _demo_text("Gr\033[1;32mace\033[0m Ho\033[1;35mpper\033[0m"),
               _demo_text("grace@\033[1;33mnavy\033[0m.mil"),
               _demo_text("Coined \033[1;36mde\033[0mbug\033[1;36mging\033[0m; color spans mid-word.")])
    # Arabic (RTL) content beside ASCII.
    t.add_row(["5", "الخوارزمي (al-Khwarizmi)", "al@bayt.hikma",
               "Arabic script measured for width."])
    # Hebrew (RTL) content beside ASCII.
    t.add_row(["6", "אדה לאבלייס (Ada)", "ada@he.example",
               "Hebrew script measured for width."])
    # Row whose ID + name are merged into one cell (first two columns).
    t.add_row(["Grace Hopper (merged ID + name)", "", "grace@navy.mil",
               "First two columns merged."])
    # Row merging every column into a single banner cell.
    t.add_row([_demo_text("\033[1;36m--- section break: everything merged ---\033[0m"),
               "", "", ""])
    # Row merging the last three columns (name + email + Notes), ID kept separate.
    t.add_row(["9", "Katherine Johnson orbital mechanics; last three columns merged.",
               "", ""])

    # Merge the email + Notes columns on the CJK row into one wide cell, so the
    # showcase also demonstrates a colspan inside a data row (not just the header)
    # and that the merged block still wraps to honor max_width.
    t.set_cell_span(1, 2, 2)
    t.set_cell_span(6, 0, 2)   # row "Grace Hopper ...": merge ID + name
    t.set_cell_span(7, 0, 4)   # section-break row: merge all four columns
    t.set_cell_span(8, 1, 3)   # row "9": merge the last three columns
    print(t.draw())

    print(_demo_text("\n\033[3mExample code:\033[0m") if _CLI_COLOR else "\nExample code:")
    print(_highlight_span_code(
        "from vistab import Vistab, ColSpan\n"
        "t = Vistab(style='round-header', max_width=72)\n"
        "t.set_theme('ocean-rows-index')\n"
        "t.set_header(['ID', ColSpan('Contact', 2), 'Notes'])\n"
        "t.set_cols_align(['r', 'l', 'l', 'l'])\n"
        "t.add_row(['1', 'Ada Lovelace', 'ada@lovelace.io', 'First programmer; ...'])\n"
        "t.set_cell_span(1, 2, 2)  # merge email + Notes on the CJK row\n"
        "print(t.draw())"
    ))
    print()
    _maybe_warn_color_off()

def print_themes_demo():
    print(_demo_text("\033[1m\033[1;36mBuilt-In Theme Macro Demonstrations\033[0m"))
    print("Predefined themes combining geometry layouts with zebra-striping and boundary padding!\n")

    tdata = [
        ["A", "B", "C", "D"],
        ["1", "Al", "123", "Good"],
        ["2", "Bob", "122", "Bad"],
        ["3", "Cat", "111", "Good"],
        ["4", "Dan", "93", "Bad"],
        # ["5", "Ed", "41", "Good"]
    ]

    t2data = []
    for theme in ["ocean", "forest", "graphite", "orchid", "sunflower"]:
        t2data.append([
            f"{theme}\n" + Vistab(tdata).set_theme(f"{theme}").set_padding(0).draw(),
            f"{theme}-index\n" + Vistab(tdata).set_theme(f"{theme}-index").set_padding(0).draw(),
            f"{theme}-rows\n" + Vistab(tdata).set_theme(f"{theme}-rows").set_padding(0).draw(),
            f"{theme}-rows-index\n" + Vistab(tdata).set_theme(f"{theme}-rows-index").set_padding(0).draw(),
            f"{theme}-cols\n" + Vistab(tdata).set_theme(f"{theme}-cols").set_padding(0).draw(),
            f"{theme}-cols-index\n" + Vistab(tdata).set_theme(f"{theme}-cols-index").set_padding(0).draw()
        ])
        t2data.append([
            f"{theme}-slim\n" + Vistab(tdata).set_theme(f"{theme}-slim").set_padding(0).draw(),
            f"{theme}-slim-index\n" + Vistab(tdata).set_theme(f"{theme}-slim-index").set_padding(0).draw(),
            f"{theme}-rows-slim\n" + Vistab(tdata).set_theme(f"{theme}-rows-slim").set_padding(0).draw(),
            f"{theme}-rows-slim-index\n" + Vistab(tdata).set_theme(f"{theme}-rows-slim-index").set_padding(0).draw(),
            f"{theme}-cols-slim\n" + Vistab(tdata).set_theme(f"{theme}-cols-slim").set_padding(0).draw(),
            f"{theme}-cols-slim-index\n" + Vistab(tdata).set_theme(f"{theme}-cols-slim-index").set_padding(0).draw()
        ])

    demo_tb = Vistab(t2data, header=False, style="none", padding=0)
    demo_tb.set_table_wrap(False)
    # Inner theme tables embed ANSI as content; _demo_text strips it under --no-color.
    print(_demo_text(demo_tb.draw()))
    print()
    _maybe_warn_color_off()

def main():
    import argparse
    import sys
    import csv
    import json
    import os

    # Safely force standard output to UTF-8. Vistab draws tables with rich Unicode box-drawing
    # characters (e.g. `┌`, `─`) plus CJK/RTL content, so if `sys.stdout` is bound to a
    # non-UTF-8 codec, writing a table raises a fatal `UnicodeEncodeError`. This happens on
    # Windows (region charmaps like cp1252) AND on POSIX runners under a C/POSIX locale where
    # stdout defaults to ASCII (this is exactly what makes CI fail on Python < 3.14, which do
    # not enable UTF-8 mode by default). `reconfigure` exists on Python >= 3.7 text streams;
    # guard it defensively so an exotic stream that lacks it never crashes startup.
    # stdin is included because vistab reads CSV from stdin; under an ASCII ambient the CLI
    # would otherwise fail to decode non-ASCII input (CJK/RTL) the same way it failed to encode
    # non-ASCII output.
    for _stream in (sys.stdin, sys.stdout, sys.stderr):
        _rc = getattr(_stream, "reconfigure", None)
        if callable(_rc):
            try:
                _rc(encoding="utf-8")
            except Exception:
                pass  # best effort; if it cannot be reconfigured, fall through unchanged

    # Resolve CLI color state early so the verb dispatch (built-in demos) honors it too.
    # Explicit --no-color and the NO_COLOR env var suppress vistab's own styling ANSI.
    # (Non-TTY output is intentionally left colored for now to avoid changing piped output;
    # see the IPD Open Question.)
    global _CLI_COLOR, _CLI_COLOR_TRIGGER, _CLI_BIDI
    if "--no-color" in sys.argv:
        _CLI_COLOR, _CLI_COLOR_TRIGGER = False, "--no-color"
    elif os.environ.get("NO_COLOR"):
        _CLI_COLOR, _CLI_COLOR_TRIGGER = False, "NO_COLOR"

    # --no-bidi disables the RTL LTR-isolate wrapping (for terminals that ignore isolates).
    if "--no-bidi" in sys.argv:
        _CLI_BIDI = False

    # Enable global theme resolution mapping native OS layers
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "vistab")
    themes_file = os.path.join(config_dir, "themes.json")
    if os.path.exists(themes_file):
        try:
            with open(themes_file, "r", encoding="utf8") as f:
                Vistab.THEMES.update(json.load(f))
        except Exception as theme_err:
            # Do not silently swallow a broken config: tell the user their custom themes did not
            # load and why, then continue with the built-in themes. (B2)
            sys.stderr.write(f"[\033[1;33mWARN\033[0m] Could not load custom themes from "
                             f"'{themes_file}': {theme_err}. Continuing with built-in themes.\n")

    # Pre-parse dispatch for subject/verb/object command grammar
    if len(sys.argv) > 1:
        verb = sys.argv[1].lower()
        if verb in ["show", "help", "demo"]:
            args_rest = sys.argv[2:]

            alias_map = {
                "caps": "capabilities",
                "wrapping": "capabilities",
                "colspan": "span",
                "rowspan": "span",
                "spans": "span",
                "adv": "advanced",
            }

            subject = None
            if args_rest:
                subject = args_rest[0].lower()
                subject = alias_map.get(subject, subject)

            if verb == "help":
                if not subject:
                    sys.argv = [sys.argv[0], "--help"]
                elif subject == "colors":
                    sys.argv = [sys.argv[0], "--help-colors"]
                elif subject == "advanced":
                    sys.argv = [sys.argv[0], "--help-advanced"]
                else:
                    sys.stderr.write(f"\033[1;31m[ERROR]\033[0m Unknown help subject '{args_rest[0]}'.\n\n")
                    sys.stderr.write("Usage: vistab help [subject]\n\n")
                    sys.stderr.write("Available subjects:\n")
                    sys.stderr.write("  colors         Show advanced coordinate-based color parameters\n")
                    sys.stderr.write("  advanced       Show advanced streaming, sorting, and jagged matrix behaviors\n")
                    sys.exit(2)

            elif verb == "show":
                valid_subjects = {
                    "styles": print_styles_list,
                    "colors": print_colors_list,
                    "capabilities": print_test_demo,
                    "anatomy": print_coordinate_styles_demo,
                    "themes": print_themes_demo,
                    "span": print_span_demo,
                    "showcase": print_showcase_demo,
                }
                def _show_subject_lines(w):
                    w("Available subjects:\n")
                    w("  showcase       One curated table: colspan + theme + CJK/ANSI wrapping (the flagship demo)\n")
                    w("  styles         Compare all available grid boundary styles\n")
                    w("  colors         Color swatch matrix of foreground/background colors and text styles\n")
                    w("  capabilities   ANSI + CJK-safe word-wrapping and datatype-parsing conformance (alias: caps, wrapping)\n")
                    w("  anatomy        Labeled diagram of a table's parts (borders, header, cells) and coordinate styling\n")
                    w("  themes         Grid of built-in color theme macros\n")
                    w("  span           Column-spanning demonstration with example code (alias: spans, colspan, rowspan)\n")
                if not subject:
                    sys.stdout.write("Usage: vistab show <subject>\n\n")
                    _show_subject_lines(sys.stdout.write)
                    sys.exit(0)
                elif subject in valid_subjects:
                    valid_subjects[subject]()
                    sys.exit(0)
                else:
                    sys.stderr.write(f"\033[1;31m[ERROR]\033[0m Unknown show subject '{args_rest[0]}'.\n\n")
                    sys.stderr.write("Usage: vistab show <subject>\n\n")
                    _show_subject_lines(sys.stderr.write)
                    sys.exit(2)

            elif verb == "demo":
                valid_subjects = {
                    "showcase": print_showcase_demo,
                    "span": print_span_demo,
                    "styles": print_styles_list,
                    "colors": print_colors_list,
                    "capabilities": print_test_demo,
                    "anatomy": print_coordinate_styles_demo,
                    "themes": print_themes_demo,
                }
                def _demo_subject_lines(w):
                    w("Available subjects:\n")
                    w("  showcase       One curated table: colspan + theme + CJK/ANSI wrapping (the flagship demo)\n")
                    w("  span           Show a demonstration of column spanning with example code\n")
                    w("  styles         Show a table comparing all available grid boundary styles\n")
                    w("  colors         Show a color swatch matrix of foreground/background colors and styles\n")
                    w("  capabilities   Show a demonstration of Vistab's parsing and formatting capabilities\n")
                    w("  anatomy        Show a coordinate-based styling demonstration\n")
                    w("  themes         Show a grid of built-in color theme macros\n")
                if not subject:
                    sys.stdout.write("Usage: vistab demo <subject>\n\n")
                    _demo_subject_lines(sys.stdout.write)
                    sys.exit(0)
                elif subject in valid_subjects:
                    valid_subjects[subject]()
                    sys.exit(0)
                else:
                    sys.stderr.write(f"\033[1;31m[ERROR]\033[0m Unknown demo subject '{args_rest[0]}'.\n\n")
                    sys.stderr.write("Usage: vistab demo <subject>\n\n")
                    _demo_subject_lines(sys.stderr.write)
                    sys.exit(2)

    usage_str = (
        "vistab is usable on the command line, but is intended primarily as a Python library:\n"
        "           from vistab import Vistab   (see docs/API.md)\n\n"
        "vistab [options] [files ...]\n"
        "       cat data.csv | vistab -t ocean -w 120\n\n"
        "       vistab show <subject>    (styles, colors, capabilities, anatomy, themes, span)\n"
        "       vistab help [subject]    (colors, advanced)\n\n"
        "       vistab --help            (standard table formatting options)\n"
        "       vistab --help-colors     (target-specific color coordinates)\n"
        "       vistab --help-advanced   (streams and jagged data matrices)\n"
        "       vistab --demo {styles|colors|capabilities|anatomy|themes|span}"
    )

    parser = argparse.ArgumentParser(
        prog="vistab",
        usage=usage_str,
        add_help=False,
        description="A lightweight Python utility for rendering rich terminal tables with ANSI color awareness.",
        epilog=(
            "Notes on Extensibility:\n"
            "  * Vistab uses standard built-in libraries safely.\n"
            "  * Install `pip install vistab[cjk]` to safely wrap Asian/CJK language multi-space characters.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    show_colors = "--help-colors" in sys.argv
    show_adv = "--help-advanced" in sys.argv
    show_basic = not show_colors and not show_adv

    c_help = lambda text: text if show_colors else argparse.SUPPRESS
    a_help = lambda text: text if show_adv else argparse.SUPPRESS
    b_help = lambda text: text if show_basic else argparse.SUPPRESS

    parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help=b_help("show this help message and exit"))
    parser.add_argument("--version", action="version", version=f"vistab {__version__}", help=b_help("show version and exit"))

    diag_grp = parser.add_argument_group("Diagnostic & Demo Operations")
    diag_grp.add_argument("--demo", type=str, choices=["showcase", "styles", "colors", "capabilities", "caps", "wrapping", "anatomy", "themes", "span", "spans", "colspan", "rowspan"], help=b_help("Run built-in demonstrations (preferred: 'vistab show <subject>')"))
    diag_grp.add_argument("--help-colors", action="store_true", help=b_help("Show advanced coordinate-based color parameters (-0, -E, -b, etc.)"))
    diag_grp.add_argument("--help-advanced", action="store_true", help=b_help("Show advanced streaming, sorting, and jagged matrix behaviors"))

    data_grp = parser.add_argument_group("Data Ingestion & Parsing Logic")
    data_grp.add_argument("-i", "--input", type=str, help=b_help("Auto-detect and format a delimited structural file (CSV, TSV, etc.)"))
    data_grp.add_argument("--csv-dialect", type=str, help=a_help("Enforce explicit CSV dialect mechanically without sniffing (e.g. 'excel-tab')."))
    data_grp.add_argument("--sort-by", type=int, help=a_help("Column index (0-indexed) to buffer and sort standard input (Caveat Emptor: memory intensive over streams)."))
    data_grp.add_argument("--sort-reverse", action="store_true", help=a_help("Reverse the sorting order."))
    data_grp.add_argument("--stream", action="store_true", help=a_help("Force infinite memoryless streaming output over buffer allocations."))
    data_grp.add_argument("--stream-probe", type=int, default=100, help=a_help("Number of records to probe formatting constraints synchronously (default: 100)"))
    data_grp.add_argument("--on-short", type=str, choices=["pad", "skip", "raise"], default="pad", help=a_help("Jagged array handler for missing fields (pad|skip|raise)"))
    data_grp.add_argument("--on-long", type=str, choices=["truncate", "skip", "raise"], default="truncate", help=a_help("Jagged array handler for overflow fields (truncate|skip|raise)"))
    data_grp.add_argument("files", nargs="*", help=b_help("Sequential file path(s). Leave empty to parse STDIN."))

    layout_grp = parser.add_argument_group("Output Constraints & Layout Structure")
    layout_grp.add_argument("-w", "--width", type=int, default=0, help=b_help("Maximum table width before wrapping cells (default: 0 / infinite)"))
    layout_grp.add_argument("-W", "--col-widths", type=str, help=b_help("Comma-separated list of strict widths for columns (e.g. '10,20,5')"))
    layout_grp.add_argument("-r", "--max-rows", type=int, default=0, help=b_help("Maximum number of rows to render (default: 0 / infinite)"))
    layout_grp.add_argument("-c", "--max-cols", type=int, default=0, help=b_help("Maximum number of columns to render (default: 0 / infinite)"))
    layout_grp.add_argument("-p", "--padding", type=int, default=1, help=b_help("Cell padding integer (default: 1)"))
    layout_grp.add_argument("-a", "--align", type=str, help=b_help("Column alignment string (e.g. 'lrc')"))
    layout_grp.add_argument("-v", "--valign", type=str, help=b_help("Column vertical alignment string (e.g. 'tmb')"))
    layout_grp.add_argument("-d", "--dtype", type=str, help=b_help(f"Per-column data types, one char per column (e.g. 'tfi'). Valid: {_dtype_help(oneline=True)}; numeric codes take an optional precision suffix like 'f2'"))
    layout_grp.add_argument("-P", "--precision", type=int, help=b_help("Float decimal precision mapping globally"))

    visual_grp = parser.add_argument_group("Visual Elements & Toggles")
    visual_grp.add_argument("-N", "--title", type=str, help=b_help("Table title string rendered centered above output"))
    visual_grp.add_argument("-s", "--style", type=str, default="light", help=b_help("Override the visual rendering style (default: 'light')"))
    visual_grp.add_argument("--style-def", type=str, help=b_help("Explicit 15 or 4 character string defining the structural box boundaries"))
    visual_grp.add_argument("-t", "--theme", type=str, help=b_help("Apply a dynamic color theme matrix to the input data (e.g. 'forest-cols')"))
    visual_grp.add_argument("-H", "--no-header", action="store_true", help=b_help("Bypass popping the first row as the table header"))
    visual_grp.add_argument("-B", "--no-borders", action="store_true", help=b_help("Disable the outer table border"))
    visual_grp.add_argument("-X", "--no-hlines", action="store_true", help=b_help("Disable horizontal lines iteratively between rows"))
    visual_grp.add_argument("-V", "--no-vlines", action="store_true", help=b_help("Disable vertical lines between columns"))
    visual_grp.add_argument("-U", "--no-header-line", action="store_true", help=b_help("Disable the horizontal divider below the header"))
    visual_grp.add_argument("--no-color", action="store_true", help=b_help("Disable all color/style output (also honors the NO_COLOR env var)"))
    visual_grp.add_argument("--no-bidi", action="store_true", help=b_help("Disable RTL bidi isolation (use if your terminal ignores Unicode LTR isolates)"))

    color_grp = parser.add_argument_group("Coordinate-Based Targeting (Colors)")
    color_grp.add_argument("--mark-abnormal", type=str, metavar="COLOR", help=a_help("Highlight skipped strings mutated."))
    color_grp.add_argument("-b", "--border-color", type=str, metavar="COLOR", help=c_help("Override table outer border color"))
    color_grp.add_argument("-f", "--header-color", type=str, metavar="COLOR", help=c_help("Override header row color"))
    color_grp.add_argument("-0", "--col0-color", type=str, metavar="COLOR", help=c_help("Override first data column color (index 0)"))
    color_grp.add_argument("-E", "--even-row-color", type=str, metavar="COLOR", help=c_help("Override even data rows color"))
    color_grp.add_argument("-O", "--odd-row-color", type=str, metavar="COLOR", help=c_help("Override odd data rows color"))
    color_grp.add_argument("-e", "--even-col-color", type=str, metavar="COLOR", help=c_help("Override even columns color"))
    color_grp.add_argument("-o", "--odd-col-color", type=str, metavar="COLOR", help=c_help("Override odd columns color"))
    color_grp.add_argument("-l", "--last-row-color", type=str, metavar="COLOR", help=c_help("Override last data row color"))
    color_grp.add_argument("-x", "--last-col-color", type=str, metavar="COLOR", help=c_help("Override last data column color"))
    color_grp.add_argument("-Z", "--border-bg-color", type=str, metavar="COLOR", help=c_help("Override table outer border background color"))
    color_grp.add_argument("-G", "--header-bg-color", type=str, metavar="COLOR", help=c_help("Override header row background color"))
    color_grp.add_argument("-1", "--col0-bg-color", type=str, metavar="COLOR", help=c_help("Override first data column background color"))
    color_grp.add_argument("-2", "--even-row-bg-color", type=str, metavar="COLOR", help=c_help("Override even data rows background color"))
    color_grp.add_argument("-3", "--odd-row-bg-color", type=str, metavar="COLOR", help=c_help("Override odd data rows background color"))
    color_grp.add_argument("-4", "--even-col-bg-color", type=str, metavar="COLOR", help=c_help("Override even columns background color"))
    color_grp.add_argument("-5", "--odd-col-bg-color", type=str, metavar="COLOR", help=c_help("Override odd columns background color"))
    color_grp.add_argument("-A", "--last-row-bg-color", type=str, metavar="COLOR", help=c_help("Override last data row background color"))
    color_grp.add_argument("-y", "--last-col-bg-color", type=str, metavar="COLOR", help=c_help("Override last data column background color"))
    color_grp.add_argument("-g", "--table-bg-color", type=str, metavar="COLOR", help=c_help("Override global table background color uniformly"))

    config_grp = parser.add_argument_group("Configuration Workflow")
    config_grp.add_argument("-K", "--create-config", type=str, nargs="?", const=os.path.join(config_dir, "config.toml"), metavar="TARGET", help=b_help("Generate TOML configuration internally (default: ~/.config/vistab/config.toml)"))
    config_grp.add_argument("-Q", "--show-config", action="store_true", help=b_help("Print global dynamic config paths and exit"))
    config_grp.add_argument("-S", "--save-theme", type=str, metavar="THEME", help=b_help("Save the current CLI styling arguments to the themes registry under THEME"))
    config_grp.add_argument("-Y", "--show-code", action="store_true", help=b_help("Print equivalent Python initialization code for the generated layout"))

    args = parser.parse_args()

    if args.help_colors or args.help_advanced:
        parser.print_help()
        sys.exit(0)

    _printed_anything = False

    # CLI Validation Safety Nets
    if args.style and args.style not in Vistab.STYLES:
        print(f"\033[1;31m[ERROR]\033[0m Unknown layout style '{args.style}'", file=sys.stderr)
        print(f"Available styles: {', '.join(sorted(Vistab.STYLES.keys()))}", file=sys.stderr)
        print("Tip: Run 'vistab show styles' to view a rendered matrix of all available layout styles.", file=sys.stderr)
        sys.exit(1)

    if getattr(args, 'theme', None) and args.theme not in Vistab.THEMES:
        print(f"\033[1;31m[ERROR]\033[0m Unknown color theme '{args.theme}'", file=sys.stderr)
        print(f"Available themes: {', '.join(sorted(Vistab.THEMES.keys()))}", file=sys.stderr)
        print("Tip: Run 'vistab show themes' to view a rendered matrix of all available color themes.", file=sys.stderr)
        sys.exit(1)

    for color_arg in ['border_color', 'header_color', 'row0_color', 'even_row_color', 'odd_row_color', 'even_col_color', 'odd_col_color', 'last_row_color', 'last_col_color']:
        val = getattr(args, color_arg, None)
        if val and val.lower() != "none" and val not in Vistab.COLORS:
            print(f"\n\033[1;31m[ERROR]\033[0m Foreground color '{val}' is not a valid color. You may also use 'none' to remove colors.", file=sys.stderr)
            sys.exit(1)

    for color_arg in ['border_bg_color', 'header_bg_color', 'row0_bg_color', 'even_row_bg_color', 'odd_row_bg_color', 'even_col_bg_color', 'odd_col_bg_color', 'last_row_bg_color', 'last_col_bg_color', 'table_bg_color']:
        val = getattr(args, color_arg, None)
        if val and val.lower() != "none" and val not in Vistab.BG_COLORS:
            print(f"\n\033[1;31m[ERROR]\033[0m Background color '{val}' is not a valid background color. You may also use 'none'.", file=sys.stderr)
            sys.exit(1)

    if args.show_config:
        core_config = os.path.join(config_dir, "config.toml")
        print(f"[\033[36mINFO\033[0m] Vistab Global Configuration Paths:\n")

        if os.path.exists(themes_file):
            print(f"  Themes Registry (JSON):  \033[32m{themes_file}\033[0m (Found)")
        else:
            print(f"  Themes Registry (JSON):  \033[33m{themes_file}\033[0m (Missing)")
            print("                           Create by running: \033[36mvistab --save-theme <name>\033[0m\n")

        if os.path.exists(core_config):
            print(f"  Core Settings (TOML):    \033[32m{core_config}\033[0m (Found)")
        else:
            print(f"  Core Settings (TOML):    \033[33m{core_config}\033[0m (Missing)")
            print("                           Create by running: \033[36mvistab --create-config\033[0m")
        sys.exit(0)

    if args.create_config:
        config_content = (
            "# Vistab Core Configuration File\n"
            "# This file overrides factory defaults quietly in the background when Vistab initializes.\n\n"
            "[vistab]\n"
            'style = "light"  # Options: light, double, bold, heavy, dashed, round, markdown, etc.\n'
            "padding = 1      # Integer spaces injected left and right inside cells\n"
            'align = "l"      # String sequence for layout (l/c/r)\n'
            "max_width = 0    # Hard limit on terminal wrap limits (0 = infinite)\n"
            "max_rows = 0     # Hard limit on rendered rows (0 = infinite)\n"
            "max_cols = 0     # Hard limit on rendered columns (0 = infinite)\n"
        )
        try:
            config_dir_path = os.path.dirname(args.create_config)
            if config_dir_path:
                os.makedirs(config_dir_path, exist_ok=True)
            with open(args.create_config, "w", encoding="utf8") as f:
                f.write(config_content)
            print(f"[\033[32mSUCCESS\033[0m] Generated Vistab config template at: {args.create_config}")
        except Exception as e:
            print(f"[\033[1;31mERROR\033[0m] Could not create config: {e}")
            sys.exit(1)
        # Exit without disrupting
        sys.exit(0)

    # Resolve aliases for --demo flags (same alias set as the show/demo verbs)
    demo_val = args.demo
    if demo_val:
        demo_val = demo_val.lower()
        _demo_aliases = {"caps": "capabilities", "wrapping": "capabilities",
                         "colspan": "span", "rowspan": "span", "spans": "span"}
        demo_val = _demo_aliases.get(demo_val, demo_val)

    if demo_val == "styles":
        print_styles_list()
        _printed_anything = True

    if demo_val == "colors":
        print_colors_list()
        _printed_anything = True

    if demo_val == "themes":
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_themes_demo()
        _printed_anything = True

    if demo_val == "capabilities":
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_test_demo()
        _printed_anything = True

    if demo_val == "anatomy":
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_coordinate_styles_demo()
        _printed_anything = True

    if demo_val == "span":
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_span_demo()
        _printed_anything = True

    if _printed_anything:
        sys.exit(0)

    # Process inputs (backwards compatible with -i)
    target_files = getattr(args, 'files', [])
    if args.input and args.input not in target_files:
        target_files.append(args.input)

    streams_to_parse = [("file", fp) for fp in target_files]

    # Grab STDIN if terminal is executing a piped stream smoothly
    is_config_only = getattr(args, 'save_theme', None) or getattr(args, 'show_code', False)

    if not is_config_only and not sys.stdin.isatty() and not target_files:
        streams_to_parse.append(("stdin", "STDIN Stream"))

    # Validation fallback
    if not streams_to_parse:
        if is_config_only:
            streams_to_parse.append(("dummy", "Config Mapping"))
        elif not _printed_anything:
            parser.print_usage(sys.stderr)
            sys.stderr.write("vistab is primarily a Python library; the CLI is for ad-hoc use. In code: from vistab import Vistab\n")
            sys.stderr.write("[\033[1;31mERROR\033[0m] No tabular dataset found. Please provide a file path argument or pipe data into STDIN.\n")
            sys.stderr.write("Tip: Run 'vistab --help' for a complete list of configurations and options.\n")
            sys.exit(1)

        if not streams_to_parse and not _printed_anything:
            return

    # Execution Engine Loop Mapping!
    import io

    class LinePeekableStream:
        """Safe infinite stream interceptor generating native buffer subsets transparently organically."""
        def __init__(self, stream, num_lines=15):
            self.stream = stream
            self.peeked = []
            for _ in range(num_lines):
                try:
                    line = next(stream)
                    self.peeked.append(line)
                except Exception:
                    break
        def sample(self): return "".join(self.peeked)
        def __iter__(self):
            yield from self.peeked
            yield from self.stream

    def _process_stream(f_stream, source_name, source_type):
        nonlocal _printed_anything
        # Parse CSV payload structurally
        peek_stream = LinePeekableStream(f_stream)

        try:
            if getattr(args, 'csv_dialect', None):
                reader = csv.reader(peek_stream, dialect=args.csv_dialect)
            else:
                dialect = csv.Sniffer().sniff(peek_stream.sample(), delimiters=",\t|;")
                reader = csv.reader(peek_stream, dialect)
        except csv.Error:
            reader = csv.reader(peek_stream)

        is_streaming = getattr(args, 'stream', False) or (source_type == "stdin")
        if is_streaming and getattr(args, 'sort_by', None) is not None:
            print("[\033[1;31mERROR\033[0m] Cannot use --sort-by with a stream. Sorting requires loading the full dataset into physical memory.", file=sys.stderr)
            sys.exit(1)

        rows = None

        if not is_streaming:
            if getattr(args, 'max_rows', 0) > 0:
                rows = []
                limit = args.max_rows + (not getattr(args, 'no_header', False))
                for _ in range(limit):
                    try: rows.append(next(reader))
                    except StopIteration: break
            else:
                rows = list(reader)

            if not rows:
                # Empty (non-streaming) input, e.g. an empty file. Report on stderr and exit
                # non-zero rather than a silent WARN + success, consistent with the empty-pipe
                # path and the documented exit semantics. (self-documentation IPD S1)
                sys.stderr.write(f"[\033[1;31mERROR\033[0m] No tabular data found in '{source_name}'. "
                                 "The input is empty.\n")
                sys.stderr.write("Tip: run 'vistab --help' for usage, or 'from vistab import Vistab' to use the library.\n")
                sys.exit(1)

        # Instantiate physical mapping structure
        table = Vistab(
            style=args.style,
            max_width=args.width,
            padding=args.padding
        )
        table.set_color(_CLI_COLOR)  # honor --no-color / NO_COLOR for the rendered table
        table.set_bidi(_CLI_BIDI)    # honor --no-bidi for the rendered table

        # Apply jagged logic mapped constraints
        table.on_short_row = args.on_short
        table.on_long_row = args.on_long
        if getattr(args, 'mark_abnormal', None):
            table.set_abnormal_row_style(fg=args.mark_abnormal)

        try:
            table.set_max_rows(args.max_rows)
            table.set_max_cols(args.max_cols)
            if not getattr(args, 'no_header', False):
                table.has_header = True
            else:
                table.has_header = False

            # Buffer if memory fallback mapped
            if rows is not None:
                table.set_rows(rows, header=not args.no_header)

            # Apply custom decorations inheriting table style boundaries
            deco = table._deco
            if args.no_borders:
                deco &= ~Vistab.BORDER
            if args.no_hlines:
                deco &= ~Vistab.HLINES
            if args.no_vlines:
                deco &= ~Vistab.VLINES
            if args.no_header_line:
                deco &= ~Vistab.HEADER
            table.set_decorations(deco)

            # Proceed with applying explicit dimension mapping arrays
            if getattr(args, 'style_def', None):
                table.set_table_lines(args.style_def)
            if args.align:
                table.set_cols_align(args.align)

            if args.valign:
                table.set_cols_valign(args.valign)

            if args.dtype:
                table.set_cols_dtype(args.dtype)

            if args.col_widths:
                string_array = args.col_widths.split(",")
                table.set_cols_width(string_array)

            # Apply title logic
            if args.title:
                table.set_title(args.title)
            elif len(target_files) > 1 and source_type == "file":
                table.set_title(f"[ {source_name} ]") # Add implicit filename title

            if args.precision is not None:
                table.set_precision(args.precision)

            if args.theme:
                table.set_theme(args.theme)

                # Ensure explicit command-line style or padding overrides theme defaults
                if "-s" in sys.argv or "--style" in sys.argv:
                    table.set_style(args.style)
                if "-p" in sys.argv or "--padding" in sys.argv:
                    table.set_padding(args.padding)

            if getattr(args, 'sort_by', None) is not None:
                table.sort_by(args.sort_by, reverse=getattr(args, 'sort_reverse', False))

            # Helper to map CLI string states to API logic, dropping keys if "none"
            def _apply_clr(style_dict, arg_fg, arg_bg):
                if arg_fg:
                    if arg_fg.lower() == "none": style_dict.pop("fg", None)
                    else: style_dict.update(table._compile_style_dict(fg=arg_fg))
                if arg_bg:
                    if arg_bg.lower() == "none": style_dict.pop("bg", None)
                    else: style_dict.update(table._compile_style_dict(bg=arg_bg))

            _apply_clr(table._border_style, getattr(args, 'border_color', None), getattr(args, 'border_bg_color', None))
            _apply_clr(table._header_style, getattr(args, 'header_color', None), getattr(args, 'header_bg_color', None))
            _apply_clr(table._table_style, None, getattr(args, 'table_bg_color', None))

            clr_r0_f, clr_r0_b = getattr(args, 'col0_color', None), getattr(args, 'col0_bg_color', None)
            if clr_r0_f or clr_r0_b:
                if 0 not in table._col_styles: table._col_styles[0] = {}
                _apply_clr(table._col_styles[0], clr_r0_f, clr_r0_b)

            clr_er_f, clr_er_b = getattr(args, 'even_row_color', None), getattr(args, 'even_row_bg_color', None)
            if clr_er_f or clr_er_b:
                if 0 not in table._alt_row_styles: table._alt_row_styles[0] = {}
                _apply_clr(table._alt_row_styles[0], clr_er_f, clr_er_b)

            clr_or_f, clr_or_b = getattr(args, 'odd_row_color', None), getattr(args, 'odd_row_bg_color', None)
            if clr_or_f or clr_or_b:
                if 1 not in table._alt_row_styles: table._alt_row_styles[1] = {}
                _apply_clr(table._alt_row_styles[1], clr_or_f, clr_or_b)

            clr_ec_f, clr_ec_b = getattr(args, 'even_col_color', None), getattr(args, 'even_col_bg_color', None)
            clr_oc_f, clr_oc_b = getattr(args, 'odd_col_color', None), getattr(args, 'odd_col_bg_color', None)
            if clr_oc_f or clr_oc_b:
                if 1 not in table._alt_col_styles: table._alt_col_styles[1] = {}
                _apply_clr(table._alt_col_styles[1], clr_oc_f, clr_oc_b)

            clr_lr_f, clr_lr_b = getattr(args, 'last_row_color', None), getattr(args, 'last_row_bg_color', None)
            if clr_lr_f or clr_lr_b:
                if -1 not in table._row_styles: table._row_styles[-1] = {}
                _apply_clr(table._row_styles[-1], clr_lr_f, clr_lr_b)

            clr_lc_f, clr_lc_b = getattr(args, 'last_col_color', None), getattr(args, 'last_col_bg_color', None)
            if clr_lc_f or clr_lc_b:
                if -1 not in table._col_styles: table._col_styles[-1] = {}
                _apply_clr(table._col_styles[-1], clr_lc_f, clr_lc_b)

            if clr_oc_f or clr_oc_b:
                if 1 not in table._alt_col_styles: table._alt_col_styles[1] = {}
                _apply_clr(table._alt_col_styles[1], clr_oc_f, clr_oc_b)

            # Evaluate save-theme and show-code intercept blocks
            if getattr(args, 'save_theme', None) or getattr(args, 'show_code', False):
                if is_streaming:
                    raise ValueError("Cannot extract metadata while memoryless streaming. Please pass a standard file path.")

                rev_fg = {v: k for k, v in Vistab.COLORS.items()}
                rev_bg = {v: k for k, v in Vistab.BG_COLORS.items()}
                rev_st = {v: k for k, v in Vistab.TEXT_STYLES.items()}

                def _rev(d):
                    o = {}
                    if "fg" in d: o["fg"] = rev_fg.get(d["fg"])
                    if "bg" in d: o["bg"] = rev_bg.get(d["bg"])
                    for k, v in d.items():
                        if k not in ["fg", "bg"] and v in rev_st: o[rev_st[v]] = True
                    return o

                compiled_theme = {}
                if table._style != "light": compiled_theme["style"] = table._style
                if table._pad != 1: compiled_theme["padding"] = table._pad
                compiled_theme["decorations"] = table._deco
                if not table._has_border: compiled_theme["has_border"] = False
                if not table._has_header: compiled_theme["has_header"] = False

                if table._table_style: compiled_theme["table"] = _rev(table._table_style)
                if table._header_style: compiled_theme["header"] = _rev(table._header_style)
                if table._border_style: compiled_theme["border"] = _rev(table._border_style)
                if 0 in table._col_styles: compiled_theme["col_0"] = _rev(table._col_styles[0])
                if -1 in table._col_styles: compiled_theme["col_-1"] = _rev(table._col_styles[-1])
                if -1 in table._row_styles: compiled_theme["row_-1"] = _rev(table._row_styles[-1])

                if 0 in table._alt_row_styles and 1 in table._alt_row_styles:
                    compiled_theme["alt_rows"] = [_rev(table._alt_row_styles[0]), _rev(table._alt_row_styles[1])]
                if 0 in table._alt_col_styles and 1 in table._alt_col_styles:
                    compiled_theme["alt_cols"] = [_rev(table._alt_col_styles[0]), _rev(table._alt_col_styles[1])]

                if getattr(args, 'save_theme', None):
                    import tempfile
                    os.makedirs(config_dir, exist_ok=True)
                    try:
                        with open(themes_file, "r") as f: tdb = json.load(f)
                    except Exception: tdb = {}

                    tdb[args.save_theme] = compiled_theme

                    fd, temp_path = tempfile.mkstemp(dir=config_dir, suffix=".json")
                    with os.fdopen(fd, "w", encoding="utf8") as f:
                        json.dump(tdb, f, indent=4)

                    os.replace(temp_path, themes_file)
                    print(f"[\033[32mSUCCESS\033[0m] Saved layout globally as '{args.save_theme}' in {themes_file}")

                if getattr(args, 'show_code', False):
                    print("import vistab\n")
                    print("custom_theme = " + json.dumps(compiled_theme, indent=4) + "\n")
                    print("table = vistab.Vistab().set_theme(custom_theme)")

                    has_geometry = any([
                        getattr(args, 'col_widths', None), getattr(args, 'align', None),
                        getattr(args, 'valign', None), getattr(args, 'dtype', None),
                        getattr(args, 'style_def', None),
                        getattr(args, 'precision', None) is not None, getattr(args, 'title', None),
                        getattr(args, 'width', 0) > 0, getattr(args, 'max_rows', 0) > 0, getattr(args, 'max_cols', 0) > 0
                    ])

                    if has_geometry:
                        print("\n# Data-specific parameters are mapped outside the theme registry")
                        print("# This prevents shape-specific geometries from breaking theme reusability")
                        if getattr(args, 'col_widths', None): print(f"table.set_cols_width([{args.col_widths}])")
                        if getattr(args, 'align', None): print(f"table.set_cols_align('{args.align}')")
                        if getattr(args, 'valign', None): print(f"table.set_cols_valign('{args.valign}')")
                        if getattr(args, 'dtype', None): print(f"table.set_cols_dtype('{args.dtype}')")
                        if getattr(args, 'precision', None) is not None: print(f"table.set_precision({args.precision})")
                        if getattr(args, 'title', None): print(f"table.set_title('{args.title}')")
                        if getattr(args, 'width', 0) > 0: print(f"table.set_max_width({args.width})")
                        if getattr(args, 'max_rows', 0) > 0: print(f"table.set_max_rows({args.max_rows})")
                        if getattr(args, 'max_cols', 0) > 0: print(f"table.set_max_cols({args.max_cols})")

                    print("\n# ... map inputs and execute drawing")
                    print("print(table.draw())")

                sys.exit(0)

            if is_streaming:
                emitted = False
                for line in table.stream(reader, sample_size=args.stream_probe):
                    sys.stdout.write(line)
                    emitted = True
                if not emitted:
                    # A stream (e.g. an empty pipe, or an upstream command that produced
                    # nothing) yielded zero rows. Do not exit silently: emit the same no-data
                    # guidance the TTY/no-input path uses and exit 1, matching the documented
                    # exit semantics in FUNCTIONAL_SPEC ("an empty data pipe ... exits with
                    # code 1"). (self-documentation IPD S1)
                    sys.stderr.write("[\033[1;31mERROR\033[0m] No tabular data found on the input stream. "
                                     "Please provide a file path argument or pipe non-empty data into STDIN.\n")
                    sys.stderr.write("Tip: run 'vistab --help' for usage, or 'from vistab import Vistab' to use the library.\n")
                    sys.exit(1)
            else:
                drawn = table.draw()
                if drawn: print(drawn)

            _printed_anything = True

        except Exception as eval_err:
            print(f"\n\033[1;31m[COMMAND-LINE FORMAT ERROR]\033[0m within stream '{source_name}'")
            print(f"Details: {eval_err}\n")
            print("Tip: format strings take one character per column; check they match your column count and use valid codes.")
            print("--align:  l (left), c (center), r (right)                   | e.g., 'lrc'")
            print("--valign: t (top), m (middle), b (bottom)                   | e.g., 'tmb'")
            print("--col-widths: Comma-separated integers                      | e.g., '40,10,15'")
            print("--dtype:  one character per column (e.g. 'ttfi'). Valid column data types:")
            print(_dtype_help())
            sys.exit(1)

    for i, (source_type, source_name) in enumerate(streams_to_parse):
        if _printed_anything or i > 0:
            print("\n")
        try:
            if source_type == "file":
                with open(source_name, "r", encoding="utf8", errors="replace") as f_stream:
                    _process_stream(f_stream, source_name, source_type)
            elif source_type == "stdin":
                _process_stream(sys.stdin, source_name, source_type)
            else:
                _process_stream(io.StringIO("foo,bar\n1,2"), source_name, source_type)
        except Exception as e:
            print(f"\033[1;31m[ERROR]\033[0m parsing output matrix '{source_name}': {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':

    main()
