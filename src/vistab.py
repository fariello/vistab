#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This was inspired by texttable, an excellent lightweight module for creating simple ASCII tables by Gerome Fournier <jef(at)foutaise.org>. Thank you for your inspiration.
# Copyright (C) 2018-2026 Gabriele Fariello where applicable.

r"""module for creating simple ASCII tables.

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

try:
    from wcwidth import wcswidth  # For calculating the display width of unicode characters
except ImportError:
    import sys
    sys.stderr.write("[\033[1;33mWARN\033[0m] For accurate terminal rendering alignment with wide characters, the wcwidth library is needed. Please use `pip install wcwidth` to fix this issue.\n")
    def wcswidth(text):
        return sum(1 for _ in text)
import re  # Regular expressions for text processing
import sys  # System-specific parameters and functions
from typing import List, Optional, Iterable, Any  # Type hints for better code clarity
from functools import reduce  # Higher-order function for performing cumulative operations

__all__ = ["Vistab", "ArraySizeError", "StringLengthCalculator"]

__author__ = 'Gabriele Fariello <gfariello@fariel.com>'
__license__ = 'BSD'
__version__ = '3 Clause 2026'
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

    def __init__(self):
        # Regular expression to match ANSI escape sequences
        # ANSI escape sequences are used for text formatting (e.g., colors)
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        pass  # Close block to ensure proper indentation

    def len(self, string: str) -> int:
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
        visible_string = self.ansi_escape.sub('', string)

        # Return the length of the visible string
        # wcswidth returns the number of cells the string occupies when printed
        return wcswidth(visible_string)
        pass  # Close block to ensure proper indentation

    pass  # Close block to ensure proper indentation


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
        pass  # Close block to ensure proper indentation

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
                    line = [word]
                else:
                    # Individual word is larger than column width constraint. Force break it onto its own line.
                    result.append(word)
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
        pass  # Close block to ensure proper indentation

    pass  # Close block to ensure proper indentation


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
        pass  # Close block to ensure proper indentation

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
        pass  # Close block to ensure proper indentation

    pass  # Close block to ensure proper indentation


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
    pass  # Close block to ensure proper indentation


class Vistab:
    """
    A class that provides functionality for creating and manipulating ASCII tables.

    This class allows users to create, style, and manipulate text-based tables in ASCII format.
    It supports various styles, borders, headers, and decorations to enhance the table presentation.

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
        "ascii2": "-|+=",  # ASCII style with different corner characters
        "double": "═║╔╗╚╝╠╣╦╩╬═╠╣╬",  # Double line style
        "light2": "─│┌┐└┘├┤┬┴┼═╞╡╪",  # Light line style with different corners
        "round": "─│╭╮╰╯├┤┬┴┼─├┤┼",  # Round corners style
        "round2": "─│╭╮╰╯├┤┬┴┼═╞╡╪",  # Another round corners style
        "light": "─│┌┐└┘├┤┬┴┼─├┤┼",  # Light line style
        "heavy": "━┃┏┓┗┛┣┫┳┻╋━┣┫╋",  # Heavy style (same as bold but discrete name)
        "dashed": "┄┆┌┐└┘├┤┬┴┼┄├┤┼", # Dashed lines
        "markdown": " |         -|||", # GitHub Flavored Markdown
        "none": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ],  # No lines style
        "none2": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ],  # Another no lines style
    }

    # Dictionary mapping complex style patterns to specific characters
    STYLE_MAPPER = {
        "heavy": {
            "---w": " ", "--e-": " ", "--ew": "━", "-s--": " ", "-s-w": "┓", "-se-": "┏", "-sew": "┳",
            "n---": " ", "n--w": "┛", "n-e-": "┗", "n-ew": "┻", "ns--": "┃", "ns-w": "┫", "nse-": "┣", "nsew": "╋",
        },
        "light2": {
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

    def __init__(self, rows=None, header=None, max_width=0, alignment=None, style=None, padding=None):
        """
        Initializes a new instance of the Vistab class.

        This constructor sets up the initial state of the table, allowing for optional
        initial rows, maximum width, style, padding, and column alignment.

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
        padding : int, optional
            The amount of padding (left and right) for the cells. Default is 1 or whatever is in .config/vistab.toml.

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
        if header is not None:
            self.header(header)
        if rows is not None:
            self.add_rows(rows)  # Add initial rows to the table if provided

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
            self.set_style(self._style) # Ensure char boundaries map out cleanly

        if padding is not None:
            self.set_padding(padding)  # Set the cell padding
        if alignment is not None:
            self.set_cols_align(alignment)  # Set the column alignment if provided
            pass  # Close block to ensure proper indentation

        pass  # Close block to ensure proper indentation

    def _load_config(self):
        """Internal routine loading default attributes natively from vistab.toml settings"""
        import sys
        # Attempt to import built-in TOML parser based on python version constraint
        try:
            if sys.version_info >= (3, 11):
                import tomllib
            else:
                import tomli as tomllib
        except ImportError:
            # Silent fallback if TOML library dependencies are completely unfulfilled
            return

        from pathlib import Path

        # Standard recursive application configurations directory map
        search_paths = [
            Path(__file__).parent / "vistab.toml",
            Path.home() / ".vistab.toml",
            Path.home() / ".config" / "vistab.toml",
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
        """Get is this has a border."""
        return self._has_border

    @has_border.setter
    def has_border(self, value):
        self._has_border = value
        return value

    @property
    def has_header(self):
        """Get if this has a header."""
        return self._has_header

    @has_header.setter
    def has_header(self, value):
        self._has_header = value
        return value

    def reset(self):
        """Reset the instance.

        Clears all row data, header data, and resets the style to default ("light").

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.reset()
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
        self._header_style = {}
        self._border_style = {}
        self._title = None
        return self

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

    def set_border_style(self, fg=None, bg=None, **kwargs) -> 'Vistab':
        """Apply colors/styles strictly to the table border and intersection characters."""
        self._border_style = self._compile_style_dict(fg, bg, **kwargs)
        return self

    def set_title(self, title: str) -> 'Vistab':
        """Set a title string to be rendered centered above the table."""
        self._title = title
        return self

    def sort_by(self, col_idx: int, reverse: bool = False, key=None) -> 'Vistab':
        """Sort the internal rows array by the value of a specific column.
        
        Args:
            col_idx (int): The 0-indexed column to sort by.
            reverse (bool): Reverse the sort direction (descending).
            key: An optional callable applied to each cell before comparison.
        """
        def _get_key(row):
            val = row[col_idx] if col_idx < len(row) else ""
            return key(val) if key else val
            
        self._rows.sort(key=_get_key, reverse=reverse)
        return self

    # --- Shorthand UX Stylers ---
    def bold_header(self) -> 'Vistab':
        """Shortcut to bold the table header."""
        return self.set_header_style(bold=True)
        
    def color_header(self, fg=None, bg=None) -> 'Vistab':
        """Shortcut to color the table header."""
        return self.set_header_style(fg=fg, bg=bg)
        
    def bold_row(self, row_idx: int) -> 'Vistab':
        """Shortcut to bold a specific row index."""
        return self.set_row_style(row_idx, bold=True)
        
    def bold_col(self, col_idx: int) -> 'Vistab':
        """Shortcut to bold a specific column index."""
        return self.set_col_style(col_idx, bold=True)

    def color_row(self, row_idx: int, fg=None, bg=None) -> 'Vistab':
        """Shortcut to color a specific row index."""
        return self.set_row_style(row_idx, fg=fg, bg=bg)
        
    def color_col(self, col_idx: int, fg=None, bg=None) -> 'Vistab':
        """Shortcut to color a specific column index."""
        return self.set_col_style(col_idx, fg=fg, bg=bg)
    # ----------------------------

    def set_header_style(self, fg=None, bg=None, **kwargs) -> 'Vistab':
        """Apply styles specifically to the header row.
        
        Args:
            fg (str): Foreground color (e.g. 'red').
            bg (str): Background color (e.g. 'blue').
            kwargs: Any boolean text style (e.g. bold=True).
        """
        self._header_style = self._compile_style_dict(fg, bg, **kwargs)
        return self

    def set_row_style(self, row_idx: int, fg=None, bg=None, **kwargs) -> 'Vistab':
        """Apply styles to a specific row index (excluding header)."""
        self._row_styles[row_idx] = self._compile_style_dict(fg, bg, **kwargs)
        return self

    def set_col_style(self, col_idx: int, fg=None, bg=None, **kwargs) -> 'Vistab':
        """Apply styles to a specific column index."""
        self._col_styles[col_idx] = self._compile_style_dict(fg, bg, **kwargs)
        return self
        
    def set_cell_style(self, row_idx: int, col_idx: int, fg=None, bg=None, **kwargs) -> 'Vistab':
        """Apply styles to a specific cell. Has highest precedence."""
        self._cell_styles[(row_idx, col_idx)] = self._compile_style_dict(fg, bg, **kwargs)
        return self

    def _get_active_ansi_wrap(self, row_idx=None, col_idx=None, is_header=False):
        """Compute the final active ANSI configuration by priority: Cell > Row/Header > Col"""
        active = {}
        # Apply Column
        if col_idx is not None and col_idx in self._col_styles:
            active.update(self._col_styles[col_idx])
            
        # Apply Row/Header (Overrides Col)
        if is_header and self._header_style:
            active.update(self._header_style)
        elif not is_header and row_idx is not None and row_idx in self._row_styles:
            active.update(self._row_styles[row_idx])
            
        # Apply Cell (Overrides everything)
        if not is_header and row_idx is not None and col_idx is not None:
            if (row_idx, col_idx) in self._cell_styles:
                active.update(self._cell_styles[(row_idx, col_idx)])
                
        if not active:
            return "", ""
            
        codes = []
        for key, val in active.items():
            codes.append(val)
            
        return f"\033[{';'.join(codes)}m", "\033[0m"

    def _get_border_ansi(self):
        """Compute the active ANSI configuration for table borders."""
        if not self._border_style:
            return "", ""
        codes = [str(val) for val in self._border_style.values()]
        return f"\033[{';'.join(codes)}m", "\033[0m"

    @property
    def max_width(self):
        """Get the maximum width of the table. If 0, no max."""
        return self._max_width

    @max_width.setter
    def max_width(self, val):
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
        """Set the characters used to draw lines between rows and columns explicitly.

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

    def set_header_align(self, array: str) -> 'Vistab':
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
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._header_align = array
        return self

    def set_cols_align(self, array: str) -> 'Vistab':
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
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._align = array
        return self

    def set_cols_valign(self, array: str) -> 'Vistab':
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
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._valign = array
        return self

    def set_cols_dtype(self, array: str) -> 'Vistab':
        """
        Sets the data types for the columns in the table.

        Args:
        array (List[str]): A list of strings representing the data types for the columns.
                           Acceptable values are: 't' (text), 'f' (float, decimal),
                           'e' (float, exponent), 'i' (integer), and 'a' (automatic).

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
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._dtype = array
        return self

    def set_cols_width(self, array: str) -> 'Vistab':
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
            raise ValueError('width must be an integer greater then 0')
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
            raise ValueError('padding must be an integer greater then 0')
        self._pad = amount
        return self

    def header(self, array: List[Any]) -> 'Vistab':
        """Specify the header of the table.

        Args:
            array (List[Any]): A list of objects/strings to use as the table's header.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.header(["Name", "Age"])
        """
        self._check_row_size(array)
        self._header = list(map(obj2unicode, array))
        return self

    def add_row(self, array: List[str]) -> 'Vistab':
        """Add a row to the table.

        Args:
            array (List[str]): Extracted strings or display values for each column.
                               Cells can contain newlines and tabs.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.add_row(["Gabriele", "Fariello"])
        """
        self._check_row_size(array)
        if not hasattr(self, "_dtype"):
            self._dtype = ["a"] * self._row_size
        cells = []
        for i, x in enumerate(array):
            cells.append(self._str(i, x))
        self._rows.append(cells)
        return self

    def add_rows(self, rows, header=True) -> 'Vistab':
        """Add several rows in the rows stack.

        Args:
            rows (Iterable[List[str]]): An iterator or 2D array of rows to add.
            header (bool): Specifies if the first row in the sequence should be used as the 
                           header of the table. Default is True.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.add_rows([["Name", "Age"], ["Gabriele", 25]])
        """
        # nb: don't use 'iter' on by-dimensional arrays, to get a
        #     usable code for python 2.1
        if header:
            if hasattr(rows, '__iter__') and hasattr(rows, 'next'):
                self.header(rows.next())
            else:
                self.header(rows[0])
                rows = rows[1:]
        for row in rows:
            self.add_row(row)
        return self

    def set_rows(self, rows, header=True) -> 'Vistab':
        """Replace all rows in the table with the provided rows.

        Args:
            rows (Iterable[List[str]]): An iterator or 2D array of rows to replace the current ones.
            header (bool): Specifies if the first row in the sequence should be used as the 
                           header of the table. Default is True.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.set_rows([["Name", "Age"], ["Alice", 25]])
        """
        self._rows = []
        return self.add_rows(rows, header)

    def draw(self):
        """Draw the table and return as an ASCII/Unicode string.

        Returns:
            str: The fully rendered string representation of the table.
                 Returns None if there is no data to draw.

        Example:
            print(table.draw())
        """
        if not self._header and not self._rows:
            return
            
        # Back up original data to handle max_rows and max_cols dynamically
        original_header = self._header.copy()
        original_rows = self._rows.copy()
        original_row_size = self._row_size
        
        # Apply limits securely for rendering
        if self._max_rows:
            self._rows = self._rows[:self._max_rows]
            
        if self._max_cols:
            self._header = self._header[:self._max_cols]
            self._rows = [row[:self._max_cols] for row in self._rows]
            self._row_size = self._max_cols
            
            # Force cache refresh so dynamic widths don't mismatch
            for cached_prop in ["_width", "_align", "_valign", "_header_align"]:
                if hasattr(self, cached_prop):
                    delattr(self, cached_prop)

        try:
            self._compute_cols_width()
            self._check_align()
            out = ""
            
            # Draw Title horizontally centered over the resulting table width
            if self._title:
                total_width = sum(self._width) + (3 * (len(self._width) - 1)) + [0, 4][self.has_border]
                out += self._title.center(total_width) + "\n"
                
            if self.has_border:
                out += self._hline(location=Vistab.TOP)
            if self._header:
                out += self._draw_line(self._header, isheader=True)
                if self.has_header:
                    out += self._hline_header(location=Vistab.MIDDLE)
            length = len(self._rows)
            for idx, row in enumerate(self._rows):
                out += self._draw_line(row, row_idx=idx)
                if self.has_hlines() and (idx + 1) < length:
                    out += self._hline(location=Vistab.MIDDLE)
            if self._has_border:
                out += self._hline(location=Vistab.BOTTOM)
            return out[:-1]
        finally:
            # Safely restore original data post-render
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
        """
        return str(int(round(cls._to_float(x))))

    @classmethod
    def _fmt_comma_int(cls, x, **kw):
        """Integer formatting class-method.

        - x will be float-converted and then used.
        """
        return f"{int(round(cls._to_float(x))):,d}"

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
        format_map = {
            'a': self._fmt_auto,
            'i': self._fmt_int,
            'I': self._fmt_comma_int,
            'f': self._fmt_float,
            'e': self._fmt_exp,
            't': self._fmt_text,
        }

        n = self._precision
        dtype = self._dtype[i]
        try:
            if callable(dtype):
                return dtype(x)
            else:
                return format_map[dtype](x, n=n)
        except FallbackToText:
            return self._fmt_text(x)

    def _check_row_size(self, array):
        """Check that the specified array fits the previous rows size."""
        if not self._row_size:
            self._row_size = len(array)
        elif self._row_size != len(array):
            raise ArraySizeError("array should contain %d elements not %s (array=%s)"
                                 % (self._row_size, len(array), array))

    def has_vlines(self):
        """Return a boolean, if vlines are required or not."""
        return self._deco & Vistab.VLINES > 0

    def has_hlines(self):
        """Return a boolean, if hlines are required or not."""
        return self._deco & Vistab.HLINES > 0

    def _hline_header(self, location=MIDDLE):
        """Print header's horizontal line."""
        return self._build_hline(is_header=True, location=location)

    def _hline(self, location):
        """Print an horizontal line."""
        # if not self._hline_string:
        #   self._hline_string = self._build_hline(location)
        # return self._hline_string
        return self._build_hline(is_header=False, location=location)

    def _build_hline(self, is_header=False, location=MIDDLE):
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
            # NOTE: This will not work as expected if the table is only headers.
            left, mid, right = self._char_ne, self._char_new, self._char_nw
        else:
            raise ValueError("Unknown location '%s'. Should be one of Vistab.TOP, Vistab.MIDDLE, or Vistab.BOTTOM." % (location))
        # compute cell separator
        cell_sep = "%s%s%s" % (horiz_char * self._pad, [horiz_char, mid][self.has_vlines()], horiz_char * self._pad)
        # build the line
        hline = cell_sep.join([horiz_char * n for n in self._width])
        # add border if needed
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
        cell_lines = cell.split('\n')
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
        # Check if column widths have already been computed. If so, exit early.
        if hasattr(self, "_width"):
            return

        # Initialize a list to store the maximum width of each column.
        maxi = []

        # If there is a header, calculate the maximum width for each column in the header.
        if self._header:
            maxi = [self._len_cell(x) for x in self._header]

        # Calculate the maximum width for each column based on the content of each row.
        for row in self._rows:
            for cell, i in zip(row, range(len(row))):
                try:
                    # Update the maximum width for the current column.
                    maxi[i] = max(maxi[i], self._len_cell(cell))
                except (TypeError, IndexError):
                    # If the column index doesn't exist in maxi, append the new width.
                    maxi.append(self._len_cell(cell))

        # Calculate the number of columns in the table.
        ncols = len(maxi)
        # Calculate the total content width by summing the maximum widths of all columns.
        content_width = sum(maxi)
        # Calculate the width required for decorations (borders and spaces).
        deco_width = 3 * (ncols - 1) + [0, 4][self.has_border]

        # Check if the total width (content + decorations) exceeds the maximum allowed width.
        if self._max_width and (content_width + deco_width) > self._max_width:
            # If the maximum width is too low to render the table, raise an error.
            if self._max_width < (ncols + deco_width):
                raise ValueError(f"max_width ({self._max_width}) too low to render data. The minimum for this table would be {ncols + deco_width}.")

            # Calculate the available width for content after accounting for decorations.
            available_width = self._max_width - deco_width
            # Initialize a new list to store the adjusted maximum widths.
            newmaxi = [0] * ncols
            i = 0

            # Distribute the available width among the columns.
            while available_width > 0:
                if newmaxi[i] < maxi[i]:
                    newmaxi[i] += 1
                    available_width -= 1
                # Cycle through columns to distribute width evenly.
                i = (i + 1) % ncols

            # Update the column widths with the adjusted values.
            maxi = newmaxi

        # Set the computed column widths as the table's column widths.
        self._width = maxi

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
        # Check if column alignment is set; if not, set default alignment to left.
        if not hasattr(self, "_align"):
            self._align = ["l"] * self._row_size
        # Check if vertical alignment is set; if not, set default alignment to top.
        if not hasattr(self, "_valign"):
            self._valign = ["t"] * self._row_size

    def _draw_line(self, line: List[str], isheader: bool = False, row_idx: int = None) -> str:
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
        line = self._splitit(line, isheader)
        space = " "
        out = ""
        b_on, b_off = self._get_border_ansi()

        # Iterate over each row of the split line.
        for i in range(self.vislen(line[0])):
            if self.has_border:
                out += b_on + self._char_ns + b_off
                
            for col_idx, (cell, width, align) in enumerate(zip(line, self._width, self._align)):
                # Get compiled active ANSI mapping
                ansi_on, ansi_off = self._get_active_ansi_wrap(row_idx, col_idx, isheader)
                out += ansi_on
                
                # Left padding block
                if col_idx > 0 or self.has_border:
                    out += " " * self._pad
                    
                cell_line = cell[i]
                fill = width - self.vislen(cell_line)
                
                if isheader:
                    align = self._header_align[col_idx]
                    
                # Alignment logic
                if align == "r":
                    out += fill * space + cell_line
                elif align == "c":
                    out += (int(fill / 2) * space + cell_line + int(fill / 2 + fill % 2) * space)
                else:
                    out += cell_line + fill * space
                    
                # Right padding block
                if col_idx < len(line) - 1 or self.has_border:
                    out += " " * self._pad
                    
                # Terminate active ANSI block securely BEFORE structural decorators
                out += ansi_off
                
                # Structural cell delimiter
                if col_idx < len(line) - 1:
                    out += b_on + [space, self._char_ns][self.has_vlines()] + b_off
                    
            if self.has_border:
                out += b_on + self._char_ns + b_off
            out += "\n"

        return out

    def _splitit(self, line: List[str], isheader: bool) -> List[List[str]]:
        """
        Split each element of the line to fit the column width.

        Each element is turned into a list, resulting from wrapping the string
        to the desired width. This method ensures that each cell content fits
        within the specified column width and handles vertical alignment.

        Args:
        -----
        line : List[str]
            The line (list of cell content) to be split and wrapped.
        isheader : bool
            Indicates if the line to be split is a header line.

        Returns:
        --------
        List[List[str]]
            The processed and wrapped lines.

        Example:
        --------
        ```
        table = Vistab()
        line = ["Name", "Age"]
        wrapped_line = table._splitit(line, isheader=True)
        print(wrapped_line)
        ```
        """
        line_wrapped = []

        # Iterate over each cell and its corresponding column width
        for cell, width in zip(line, self._width):
            array = []
            # Split cell content by new lines and wrap each part to fit the column width
            for c in cell.split('\n'):
                if c.strip() == "":
                    array.append("")  # Preserve empty lines
                else:
                    # Dynamically utilize ColorAwareWrapper to segregate layout correctly without mutating ANSI sequences 
                    array.extend(self._cwrap.wrap_list(c, width))
            line_wrapped.append(array)

        # Find the maximum number of lines in any cell
        max_cell_lines = reduce(max, list(map(len, line_wrapped)))

        # Adjust each cell's vertical alignment
        for cell, valign in zip(line_wrapped, self._valign):
            if isheader:
                valign = "t"  # Header cells are always top-aligned
            if valign == "m":
                # Middle alignment: add missing lines evenly to the top and bottom
                missing = max_cell_lines - self._vislen.len(cell)
                cell[:0] = [""] * (missing // 2)
                cell.extend([""] * (missing // 2 + missing % 2))
            elif valign == "b":
                # Bottom alignment: add missing lines to the top
                cell[:0] = [""] * (max_cell_lines - self.vislen(cell))
            else:
                # Top alignment (default): add missing lines to the bottom
                cell.extend([""] * (max_cell_lines - self.vislen(cell)))
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
    return Vistab([["Hd1", "Hd2"], ["Ce1", "Ce2"], ["Ce3", "Ce4"]], style=style, padding=padding).draw()


def print_test_demo():
    print("\033[1m\033[1;31mANSI\033[0m\033[1m Color / Escape Sequence Aware Text-Based Tables\033[0m:")
    tdata = [
        ["Test 1", "Test 2", "Test 3", "Test 4"],
        [
            "This is some \033[1;31mRed text\033[0m to show the ability to wrap \033[38;5;226mcolored text\033[0m correctly.",
            "\033[4mThis text is underlined, \033[1mbold, and \033[34mblue.\033[0m This is not.",
            "This is some normal text in the middle to ensure that it is working properly.",
            "Some \033[1;31mRed mandarin: 这是一个 美好的世界！\033[0m for testing.",
        ]
    ]
    t1 = Vistab(tdata)
    t1.set_max_width(80)
    print(t1.draw())

    print("\n\033[1mBelow is the same table but with the color controls removed. They should wrap the same way.\033[0m")
    tdata = [
        ["Test 1", "Test 2", "Test 3", "Test 4"],
        [
            "This is some Red text to show the ability to wrap colored text correctly.",
            "This text is underlined, bold, and blue. This is not.",
            "This is some normal text in the middle to ensure that it is working properly.",
            "Some Red mandarin: 这是一个 美好的世界！ for testing.",
        ]
    ]
    t2 = Vistab(tdata)
    t2.set_max_width(80)
    print(t2.draw())



def print_styles_list():
    print("\033[1mAvailable Styles\033[0m (Note: the default is \"light\"):")
    style_list = sorted(Vistab.STYLES.keys())
    data = []
    for row in split_list(style_list, 4):
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
        data.append(["", "", "", ""])
    t1 = Vistab(data, max_width=120, style="none", alignment="cccc")
    print(t1.draw())

def print_coordinate_styles_demo():
    print("\033[1m\033[1;36mCoordinate-Based Styling Demonstration\033[0m")
    print("These styles target specific cells, columns, and rows without mutating structural padding strings or column decorators!\n")
    
    t = Vistab([
        ["Rank", "Player", "Score", "Status"], 
        ["1", "Gabriele", "15,230", "Up"],
        ["2", "Alice", "12,940", "Stable"],
        ["3", "Bob", "8,100", "Down"]
    ], style="double")

    t.set_header_style(bg="red", fg="bright_white", bold=True)
    t.set_border_style(fg="yellow")
    t.set_col_style(0, fg="bright_cyan", bold=True)
    t.set_cell_style(1, 1, bg="green", fg="black")  # Gabriele
    t.set_cell_style(3, 3, fg="red", blink=True)    # Down

    print(t.draw())
    print("\n\033[3mCode executed:\033[0m")
    print("table.set_header_style(bg='red', fg='bright_white', bold=True)")
    print("table.set_border_style(fg='yellow')")
    print("table.set_col_style(0, fg='bright_cyan', bold=True)")
    print("table.set_cell_style(1, 1, bg='green', fg='black')")
    print("table.set_cell_style(3, 3, fg='red', blink=True)")
    print()

def main():
    import argparse
    import sys
    import csv
    
    parser = argparse.ArgumentParser(
        prog="vistab",
        description="A zero-dependency Python utility for rendering rich terminal tables with ANSI color awareness.",
        epilog=(
            "Notes on Extensibility:\n"
            "  * Vistab gracefully uses standard built-in libraries safely.\n"
            "  * Install `pip install vistab[cjk]` to safely wrap Asian/CJK language multi-space characters.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-L", "--list-styles", action="store_true", help="Print all available built-in rendering styles")
    parser.add_argument("-T", "--test", action="store_true", help="Print a demonstration of color-wrapping and complex unicode characters")
    parser.add_argument("-D", "--demo-styling", action="store_true", help="Print a demonstration of coordinate-based row, column, and cell styling")
    parser.add_argument("-i", "--input", type=str, help="Auto-detect and format a delimited structural file (CSV, TSV, etc.)")
    parser.add_argument("-s", "--style", type=str, default="light", help="Override the visual rendering style (default: 'light')")
    parser.add_argument("-w", "--max-width", type=int, default=0, help="Maximum table width before wrapping cells (default: 0 / infinite)")
    parser.add_argument("-r", "--max-rows", type=int, default=0, help="Maximum number of rows to render (default: 0 / infinite)")
    parser.add_argument("-c", "--max-cols", type=int, default=0, help="Maximum number of columns to render (default: 0 / infinite)")
    parser.add_argument("-p", "--padding", type=int, default=1, help="Cell padding integer (default: 1)")
    parser.add_argument("-a", "--align", type=str, help="Column alignment string (e.g. 'lrc')")
    parser.add_argument("--create-config", type=str, metavar="TARGET", help="Generate a verbose boilerplate TOML configuration file at the target path (e.g., .vistab.toml)")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    _printed_anything = False

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
            with open(args.create_config, "w", encoding="utf8") as f:
                f.write(config_content)
            print(f"[\033[32mSUCCESS\033[0m] Generated Vistab config template at: {args.create_config}")
        except Exception as e:
            print(f"[\033[1;31mERROR\033[0m] Could not create config: {e}")
            sys.exit(1)
        # Exit cleanly without disrupting
        sys.exit(0)

    if args.list_styles:
        print_styles_list()
        _printed_anything = True
        
    if args.test:
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_test_demo()
        _printed_anything = True
        
    if args.demo_styling:
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_coordinate_styles_demo()
        _printed_anything = True
        
    if args.input:
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        try:
            with open(args.input, "r", encoding="utf8") as f:
                sample = f.read(1024)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    reader = csv.reader(f, dialect)
                except csv.Error:
                    # Sniffer fails on single-column or un-delimitered text. Fallback to generic parsing.
                    reader = csv.reader(f)
                
                rows = list(reader)
                if not rows:
                    print("Error: The provided input file is empty.")
                    sys.exit(1)
                    
                table = Vistab(
                    style=args.style,
                    max_width=args.max_width,
                    padding=args.padding
                )
                table.set_max_rows(args.max_rows)
                table.set_max_cols(args.max_cols)
                
                if args.align:
                    table.set_cols_align(args.align)
                
                table.set_rows(rows, header=True)
                print(table.draw())
        except Exception as e:
            print(f"Error parsing input file: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
