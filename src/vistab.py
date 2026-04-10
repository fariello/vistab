#!/usr/bin/env python3
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

import os
import sys

# Ensure Windows legacy cmd.exe supports ANSI formatting naturally
if os.name == 'nt':
    os.system("")

from typing import Union

try:
    from wcwidth import wcswidth  # For calculating the display width of unicode characters
except ImportError:
    import sys
    sys.stderr.write("[\033[1;33mWARN\033[0m] For accurate terminal rendering alignment with wide characters, the wcwidth library is needed. Please use `pip install wcwidth` to fix this issue.\n")
    def wcswidth(text):
        return sum(1 for _ in text)
import re  # Regular expressions for text processing
import sys  # System-specific parameters and functions
from typing import List, Optional, Iterable, Any, Union, Iterator  # Type hints for better code clarity
from functools import reduce, lru_cache  # Higher-order function for performing cumulative operations

__all__ = ["Vistab", "ArraySizeError", "StringLengthCalculator"]

__author__ = 'Gabriele Fariello <gfariello@fariel.com>'
__license__ = 'BSD 3-Clause 2026'
__version__ = '1.1.0'
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
        pass # for auto-indentation

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

    pass # for auto-indentation


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
        pass # for auto-indentation

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

    pass # for auto-indentation


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
        pass # for auto-indentation

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

    pass # for auto-indentation


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
    pass # for auto-indentation


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

    # High-level color/style base palettes
    _BASE_PALETTES = {
        "ocean": {
            "style": "round2",
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
        "minimalist": {
            "style": "light",
            "header": {"fg": "black", "bg": "bright_white", "bold": True},
            "border": {"fg": "bright_black"},
            "col_0": {"fg": "black", "bg": "bright_white", "bold": True},
            "fg2": "bright_white"
        }
    }

    THEMES = {}
    for _name, _config in _BASE_PALETTES.items():
        _base = {"style": _config["style"], "header": _config["header"], "border": _config["border"]}
        _alt_sequence = [{"bg": "black", "fg": "white"}, {"bg": "bright_black", "fg": _config["fg2"]}]
        
        # 1. Alternating Rows (Default)
        THEMES[f"{_name}"] = {**_base, "alt_rows": _alt_sequence}
        THEMES[f"{_name}-index"] = {**_base, "alt_rows": _alt_sequence, "col_0": _config["col_0"]}
        
        # 2. Alternating Columns (-cols)
        THEMES[f"{_name}-cols"] = {**_base, "alt_cols": _alt_sequence}
        THEMES[f"{_name}-cols-index"] = {**_base, "alt_cols": _alt_sequence, "col_0": _config["col_0"]}
        
        # 3. Solid (-solid)
        _solid_base = {"bg": "black", "fg": "white"}
        THEMES[f"{_name}-solid"] = {**_base, "alt_rows": [_solid_base, _solid_base]}
        THEMES[f"{_name}-solid-index"] = {**_base, "alt_rows": [_solid_base, _solid_base], "col_0": _config["col_0"]}

    def __init__(self, rows: Optional[Iterable[Iterable[Any]]] = None, header: Optional[Iterable[Any]] = None, max_width: int = 0, alignment: Optional[str] = None, style: Optional[str] = None, padding: Optional[int] = None, title: Optional[str] = None, max_rows: int = 0, max_cols: int = 0) -> None:
        """
        Initializes a new instance of the Vistab styling rendering class.

        This constructor sets up the initial default state of the table, compiling configuration files dynamically
        and initiating decorators to allow optional parameters explicitly.

        Args:
        -----
        rows : Optional[Iterable[Iterable[Any]]]
            An iterable containing grouped row sequences to be added immediately. Default is None.
        header : Union[bool, Iterable[Any], str, None]
            If True (default), extracts the first row as the top-most table header dynamically.
            If False, "" or None, bypasses extraction mapping structurally rows naturally.
            If an Iterable is passed, maps directly into `self.header()`.
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
        table = Vistab(style="round2", padding=1, max_width=100)
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
        padding : int, optional
            The amount of padding (left and right) for the cells. Default is 1 or whatever is in .config/vistab.toml.
        title : str, optional
            Optional title printed above the table.
        max_rows : int, optional
            Maximum rows to render natively (0 = infinite).
        max_cols : int, optional
            Maximum columns to render natively (0 = infinite).

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
        if header is False or header is None or header == "":
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
            self.set_style(self._style) # Ensure char boundaries map out cleanly

        if padding is not None:
            self.set_padding(padding)  # Set the cell padding
        if alignment is not None:
            self.set_cols_align(alignment)  # Set the column alignment if provided
            pass # for auto-indentation
            
        if title is not None:
            self.set_title(title)
        if max_rows > 0:
            self.set_max_rows(max_rows)
        if max_cols > 0:
            self.set_max_cols(max_cols)

        pass # for auto-indentation

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
            Configuration boolean defining whether the table draws border decorators natively.

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
        By default, Vistab initializes with `has_header=True`. If you append raw datasets without wanting headers drawn, set this to False.

        Args:
        -----
        value : bool
            Boolean indicating if the top-most table string sequences are styled natively as center-aligned headers.

        Example:
        --------
        ```python
        table.has_header = False
        ```
        """
        self._has_header = value

    def reset(self) -> 'Vistab':
        """
        Reset the Vistab instance safely to its default state.

        Clears all row data, header data, and restores styling logic configurations dynamically back to standard initialization values (such as reinstating 'light' mode lines, and purging coordinate-based coloring injections natively).

        Returns:
        --------
        Vistab
            The instance for method chaining.

        Important Behavior:
        -------------------
        Does not mutate the `None` fallbacks. Resets layout decorators dynamically.

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
        self._title = None
        self.on_wrap_conflict = "warn"
        self.on_short_row = "pad"
        self.on_long_row = "truncate"
        self._metrics = {"padded": 0, "truncated": 0, "skipped": 0}
        self._abnormal_style = None  # Tuple of (fg, bg) injected directly into flawed row lines natively cleanly.
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
        Returns a dictionary containing tallies of how many matrix rows bypassed pure structure natively.
        
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

    def set_border_style(self, fg=None, bg=None, **kwargs) -> 'Vistab':
        """Apply colors/styles strictly to the table border and intersection characters."""
        self._border_style = self._compile_style_dict(fg, bg, **kwargs)
        return self

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
        """Evaluate structural sort flags dynamically securely converting natively accurately."""
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

    def set_table_style(self, fg=None, bg=None, **kwargs) -> 'Vistab':
        """Apply a global base style mapping uniformly to all cells inside the table natively."""
        self._table_style = self._compile_style_dict(fg, bg, **kwargs)
        return self

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

    def set_alternating_row_style(self, fg1=None, bg1=None, fg2=None, bg2=None, **kwargs) -> 'Vistab':
        """Set alternating row styling (zebra-striping) applied iteratively over table coordinates."""
        self._alt_row_styles[0] = self._compile_style_dict(fg1, bg1, **kwargs)
        self._alt_row_styles[1] = self._compile_style_dict(fg2, bg2, **kwargs)
        return self

    def set_alternating_col_style(self, fg1=None, bg1=None, fg2=None, bg2=None, **kwargs) -> 'Vistab':
        """Set alternating column styling (zebra-striping)."""
        self._alt_col_styles[0] = self._compile_style_dict(fg1, bg1, **kwargs)
        self._alt_col_styles[1] = self._compile_style_dict(fg2, bg2, **kwargs)
        return self

    def apply_theme(self, theme: Union[str, dict]) -> 'Vistab':
        """Apply a predefined high-level color theme dynamically over table geometries.
        
        Vistab provides curated default palettes natively (e.g. `ocean`, `forest`).
        You may pass a string to map from `Vistab.THEMES`, or pass a literal active dictionary seamlessly.
        
        Example:
        --------
        ```python
        custom_theme = {
            "style": "round2",
            "padding": 2,
            "header": {"fg": "black", "bg": "bright_blue", "bold": True},
            "border": {"fg": "blue"}
        }
        
        table = Vistab().apply_theme(custom_theme)
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
        """Override wrapping behavior securely for an exact cell mapping."""
        self._cell_wraps[(row_idx, col_idx)] = wrap
        return self

    def _get_active_wrap_control(self, row_idx=None, col_idx=None, is_header=False) -> bool:
        """Compute the final active Wrapping block applying precedence logic efficiently cleanly."""
        # 1. Base Table Wrap constraint
        active = self._table_wrap
        
        # 2. Overlap precise Column override natively
        if col_idx is not None and col_idx in self._col_wraps:
            active = self._col_wraps[col_idx]
            
        # 3. Overlap exact Row/Header override natively
        if is_header and "header" in self._row_wraps:
            active = self._row_wraps["header"]
        elif not is_header and row_idx is not None and row_idx in self._row_wraps:
            active = self._row_wraps[row_idx]
            
        # 4. Apply explicit nested Cell override exactly natively
        if not is_header and row_idx is not None and col_idx is not None:
            if (row_idx, col_idx) in self._cell_wraps:
                active = self._cell_wraps[(row_idx, col_idx)]
                
        return active

    def _get_active_ansi_wrap(self, row_idx=None, col_idx=None, is_header=False, is_abnormal=False):
        """Compute the final active ANSI configuration applying precedence logic gracefully."""
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
            
        codes = [str(val) for val in active.values()]
        return f"\033[{';'.join(codes)}m", "\033[0m"

    def _get_border_ansi(self):
        """Compute the active ANSI configuration for table borders."""
        if not self._border_style:
            return "", ""
        codes = [str(val) for val in self._border_style.values()]
        return f"\033[{';'.join(codes)}m", "\033[0m"

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
        if isinstance(array, str):
            array = [c for c in array]
            pass
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
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._valign = array
        return self

    def set_cols_dtype(self, array: Union[str, List[str]]) -> 'Vistab':
        """
        Sets the data types for the columns in the table.

        Args:
            array (Union[str, List[str]]): A list of strings representing the data types for the columns.
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
        processed_array = self._check_row_size(array, is_data_row=True)
        if processed_array is not None:
            self._header = list(map(obj2unicode, processed_array))
        return self

    def add_row(self, array: List[str]) -> 'Vistab':
        """Add a row to the table.

        Args:
            array (List[str]): Extracted strings or display values for each column.
                               Cells can contain newlines and tabs.

        Returns:
            Vistab: The instance for method chaining.

        Example:
            table.add_row(["Arnold", "Fitzpatrick"])
        """
        processed_array = self._check_row_size(array, is_data_row=True)
        if processed_array is None:
            return self
            
        array = processed_array
        if not hasattr(self, "_dtype"):
            self._dtype = ["a"] * self._row_size
        cells = []
        for i, x in enumerate(array):
            cells.append(self._str(i, x))
        self._rows.append(cells)
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
        # nb: iterate cleanly parsing python 3 backwards mapping
        if header:
            if hasattr(rows, '__iter__') and (hasattr(rows, '__next__') or hasattr(rows, 'next')):
                self.header(next(rows))
            else:
                self.header(rows[0])
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
                    out += self._hline(location=Vistab.MIDDLE)
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
        
        # 1. Capture the initial subset to derive geometry logic seamlessly.
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
        
        # We must clear physical structures to natively calculate geometries on the sample properly
        self._header = []
        self._rows = []
        self._row_size = original_row_size if original_row_size else 0
        
        # Ingest sampled boundary
        if self._has_header:
            self.header(sample[0])
            sample = sample[1:]
            
        for row in sample:
            self.add_row(row)
            
        # Limits mappings safely on sample sizes
        if self._max_cols:
            self._header = self._header[:self._max_cols]
            self._rows = [row[:self._max_cols] for row in self._rows]
            self._row_size = self._max_cols
            
            # Force cache refresh so dynamic widths don't mismatch
            for cached_prop in ["_width", "_align", "_valign", "_header_align"]:
                if hasattr(self, cached_prop):
                    delattr(self, cached_prop)
                    
        # Compute exact geometries!
        self._compute_cols_width()
        self._check_align()
        
        # Yield the top structural bounds natively
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
            # Standard CLI doesn't natively yield the header unless rows exist
            if self.has_header and ((self._deco & Vistab.HEADER) > 0):
                yield self._hline_header(location=Vistab.MIDDLE)
                
        # Define internal generator chain merging sample and remainder streams gracefully!
        def stream_exhaust():
            # Yield pre-buffered rows parsed already mechanically
            for parsed_row in self._rows:
                yield parsed_row, False  # Already parsed strictly, not abnormal
                
            # Yield remainder rows explicitly
            for raw_row in stream_iterator:
                old_pad = self._metrics.get("padded", 0)
                old_trunc = self._metrics.get("truncated", 0)
                
                processed_row = self._check_row_size(raw_row, is_data_row=True)
                if processed_row is None:
                    continue  # Skipped
                    
                is_abnormal = (self._metrics.get("padded", 0) > old_pad) or (self._metrics.get("truncated", 0) > old_trunc)
                
                if self._max_cols:
                    processed_row = processed_row[:self._max_cols]
                    
                # Format cells natively
                cells = []
                for i, x in enumerate(processed_row):
                    cells.append(self._str(i, x))
                    
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
                        yield self._hline(location=Vistab.MIDDLE)
                    prev_row, is_abn = next_row, next_abn
                except StopIteration:
                    # We are at the final row explicitly cleanly
                    yield self._draw_line(prev_row, row_idx=drawn_rows-1, is_abnormal=is_abn)
                    break
        except StopIteration:
            pass
            
        if self.has_border:
            yield self._hline(location=Vistab.BOTTOM)
            
        # Cleanly restore instance properties natively
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
        dtype = self._dtype[i] if hasattr(self, '_dtype') else "a"
        try:
            if callable(dtype):
                return dtype(x)
            else:
                return format_map[dtype](x, n=n)
        except FallbackToText:
            return self._fmt_text(x)

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
                    # Pad out to the defined max lengths
                    array = list(array) + [""] * (self._row_size - array_len)
                    self._metrics["padded"] += 1
            else:
                action = self.on_long_row if is_data_row else "raise"
                if action == "raise":
                    raise ArraySizeError("array should contain %d elements not %s (array=%s)" % (self._row_size, array_len, array))
                elif action == "skip":
                    self._metrics["skipped"] += 1
                    return None
                elif action == "truncate":
                    # Slice natively truncating excess cells mapping gracefully efficiently.
                    array = list(array)[:self._row_size]
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
            
        # Check if column alignment is set natively; if not, compute data-centric defaults dynamically
        if not hasattr(self, "_align"):
            self._align = ["l"] * self._row_size
            if hasattr(self, "_dtype") and self._rows:
                for c in range(self._row_size):
                    # Explicit numeric types physically lock right-alignment securely
                    if self._dtype[c] in ("i", "I", "f", "e"):
                        self._align[c] = "r"
                    # Auto types physically parse physical storage mapping characters
                    elif self._dtype[c] == "a":
                        valid_cells = 0
                        numeric_cells = 0
                        for row in self._rows:
                            if c < len(row):
                                val = str(row[c]).strip()
                                if val:
                                    valid_cells += 1
                                    try:
                                        float(val.replace(",", "")) # Catch formatted sequences seamlessly
                                        numeric_cells += 1
                                    except ValueError:
                                        pass
                        # If row data is purely numerical cleanly, evaluate 'r' structurally efficiently
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
            Internal tracker checking if the row length structurally violated boundary boundaries natively.

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
        line = self._splitit(line, isheader, row_idx=row_idx)
        space = " "
        out_parts = []
        
        # Cache repetitive property access natively inside local namespace for high-speed loops
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
                
            for col_idx, (cell, width, align) in enumerate(zip(line, self._width, self._align)):
                # Get compiled active ANSI mapping
                ansi_on, ansi_off = self._get_active_ansi_wrap(row_idx, col_idx, isheader, is_abnormal=is_abnormal)
                if ansi_on: out_parts.append(ansi_on)
                
                # Left padding block
                if col_idx > 0 or has_border:
                    out_parts.append(pad_str)
                    
                cell_line = cell[i]
                fill = width - self.vislen(cell_line)
                
                # Routing strict native layout bounding collisions seamlessly
                if fill < 0:
                    if self.on_wrap_conflict == "error":
                        raise VistabOverflowError(f"Cell string explicitly mapped wrap=False natively exceeded layout width {width}.")
                    elif self.on_wrap_conflict == "warn":
                        sys.stderr.write(f"[\033[1;33mWARN\033[0m] Vistab geometry cell length ({self.vislen(cell_line)}) explicitly bypasses {width} max_width boundary natively. Deflecting to clipping fallback.\n")
                        cell_line = self._ansi_safe_clip(cell_line, width)
                        fill = 0
                    elif self.on_wrap_conflict == "clip":
                        cell_line = self._ansi_safe_clip(cell_line, width)
                        fill = 0
                    elif self.on_wrap_conflict == "overflow":
                        fill = 0  # Override space mapping forcefully bleeding into structural delimiters
                        
                if isheader:
                    align = self._header_align[col_idx]
                    
                # Alignment logic
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
                    
                # Right padding block
                if col_idx < num_cols - 1 or has_border:
                    out_parts.append(pad_str)
                    
                # Terminate active ANSI block securely BEFORE structural decorators
                if ansi_off: out_parts.append(ansi_off)
                
                # Structural cell delimiter
                if col_idx < num_cols - 1:
                    out_parts.append(v_delim)
                    
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
            The coordinate index tracking structural overrides natively.

        Returns:
        --------
        List[List[str]]
            The processed and wrapped lines.
        """
        line_wrapped = []

        # Iterate over each cell and its corresponding column width
        for col_idx, (cell, width) in enumerate(zip(line, self._width)):
            array = []
            
            # Fetch active boolean wrap logic executing precedence mapping
            do_wrap = self._get_active_wrap_control(row_idx, col_idx, isheader)
            
            # Split cell content by new lines and wrap each part to fit the column width
            for c in cell.split('\n'):
                if c.strip() == "" and do_wrap:
                    array.append("")  # Preserve empty lines safely if wrapping
                elif not do_wrap:
                    array.append(c) # Actively bypass logic natively saving space literals verbatim
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
    tdata = [
        ["Test 1", "Test 2", "Test 3", "Test 4"],
        [
            "This is some \033[1;31mRed text\033[0m to show the ability to wrap \033[38;5;226mcolored text\033[0m correctly.",
            "\033[4mThis text is underlined, \033[1mbold, and \033[34mblue.\033[0m This is not.",
            "This is some normal text in the middle to ensure that it is working properly.",
            "Some \033[1;31mRed mandarin: 这是一个 美好的世界\033[0m for testing.",
        ]
    ]

    # Print the second row of the table outside a table line-by-line.
    print("\033[1mTest text line-by-line:\033[0m")
    for phrase in tdata[1]:
        print(phrase)
    print()


    print("\033[1m\033[1;31mANSI\033[0m\033[1m Color / Escape Sequence Aware Text-Based Tables\033[0m:")
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
            "Some Red mandarin: 这是一个 美好的世界 for testing.",
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
        ["1", "Gabriel", "15,230", "Up"],
        ["2", "Alice", "12,940", "Stable"],
        ["3", "Bob", "8,100", "Down"]
    ], style="double")

    t.set_header_style(bg="red", fg="bright_white", bold=True)
    t.set_border_style(fg="yellow")
    t.set_col_style(0, fg="bright_cyan", bold=True)
    t.set_cell_style(1, 1, bg="green", fg="black")  # Gabriel
    t.set_cell_style(3, 3, fg="red", blink=True)    # Down

    print(t.draw())
    print("\n\033[3mCode executed:\033[0m")
    print("table.set_header_style(bg='red', fg='bright_white', bold=True)")
    print("table.set_border_style(fg='yellow')")
    print("table.set_col_style(0, fg='bright_cyan', bold=True)")
    print("table.set_cell_style(1, 1, bg='green', fg='black')")
    print("table.set_cell_style(3, 3, fg='red', blink=True)")
    print()

def print_colors_list():
    fg_data = []
    keys = list(Vistab.COLORS.keys())
    for chunk in split_list(keys, 4):
        row = []
        for key in chunk:
            if key:
                val = Vistab.COLORS[key]
                row.extend([key, f"\033[{val}m {val.rjust(3)} \033[0m"])
            else:
                row.extend(["", ""])
        fg_data.append(row)
    t_fg = Vistab(style="round2", padding=0)
    t_fg.set_title("\033[1;36m\033[4mForeground Colors (fg=...)\033[0m\n")
    t_fg.set_cols_align(["l"] * 8)
    t_fg.set_rows(fg_data, header=False)
    print(t_fg.draw())

    bg_data = []
    keys = list(Vistab.BG_COLORS.keys())
    for chunk in split_list(keys, 4):
        row = []
        for key in chunk:
            if key:
                val = Vistab.BG_COLORS[key]
                # Combine foreground contrasting text cleanly over requested background
                fg_contrast = "30" if "white" in key or "yellow" in key or "cyan" in key else "37"
                row.extend([key, f"\033[{val};{fg_contrast}m {val.rjust(4)} \033[0m"])
            else:
                row.extend(["", ""])
        bg_data.append(row)
    t_bg = Vistab(style="round2", padding=0)
    t_bg.set_title("\n\033[1;36m\033[4mBackground Colors (bg=...)\033[0m\n")
    t_bg.set_cols_align(["l"] * 8)
    t_bg.set_rows(bg_data, header=False)
    print(t_bg.draw())

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
    t_ts = Vistab(style="round2", padding=0)
    t_ts.set_title("\n\033[1;36m\033[4mText Decorators (bold=True, etc)\033[0m\n")
    t_ts.set_cols_align(["l"] * 8)
    t_ts.set_rows(ts_data, header=False)
    print(t_ts.draw())
    print()

def print_themes_demo():
    print("\033[1m\033[1;36mBuilt-In Theme Macro Demonstrations\033[0m")
    print("Predefined themes combining geometry layouts with zebra-striping and boundary padding natively!\n")
    
    tdata = [
        ["A", "B", "C", "D"], 
        ["1", "Al", "123", "Good"],
        ["2", "Bob", "122", "Bad"],
        ["3", "Cat", "111", "Good"],
        ["4", "Dan", "93", "Bad"],
        ["5", "Ed", "41", "Good"]
    ]

    t2data = []
    for theme in ["ocean", "forest", "minimalist"]:
        t2data.append([
            f"\"{theme}\"\n" + Vistab(tdata).apply_theme(f"{theme}").draw(),
            f"\"{theme}-index\"\n" + Vistab(tdata).apply_theme(f"{theme}-index").draw(),
            f"\"{theme}-cols\"\n" + Vistab(tdata).apply_theme(f"{theme}-cols").draw(),
            f"\"{theme}-cols-index\"\n" + Vistab(tdata).apply_theme(f"{theme}-cols-index").draw(),
            f"\"{theme}-solid\"\n" + Vistab(tdata).apply_theme(f"{theme}-solid").draw(),
            f"\"{theme}-solid-index\"\n" + Vistab(tdata).apply_theme(f"{theme}-solid-index").draw()
        ])

    demo_tb = Vistab(t2data, header=False, style="light", padding=0)
    demo_tb.set_table_wrap(False)
    print(demo_tb.draw())
    print()

def main():
    import argparse
    import sys
    import csv
    import json
    import os
    
    if sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    # Enable global theme resolution cleanly mapping native OS layers
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "vistab")
    themes_file = os.path.join(config_dir, "themes.json")
    if os.path.exists(themes_file):
        try:
            with open(themes_file, "r", encoding="utf8") as f:
                Vistab.THEMES.update(json.load(f))
        except Exception: pass
        
    usage_str = (
        "vistab [options] [files ...]\n"
        "       cat data.csv | vistab -t ocean -w 120\n\n"
        "       vistab --help            (standard table formatting options)\n"
        "       vistab --help-colors     (target-specific color coordinates)\n"
        "       vistab --help-advanced   (streams and jagged data matrices)\n"
        "       vistab --demo {styles|colors|capabilities|anatomy|themes}"
    )

    parser = argparse.ArgumentParser(
        prog="vistab",
        usage=usage_str,
        add_help=False,
        description="A lightweight Python utility for rendering rich terminal tables with ANSI color awareness.",
        epilog=(
            "Notes on Extensibility:\n"
            "  * Vistab gracefully uses standard built-in libraries safely.\n"
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

    diag_grp = parser.add_argument_group("Diagnostic & Demo Operations")
    diag_grp.add_argument("--demo", type=str, choices=["styles", "colors", "capabilities", "anatomy", "themes"], help=b_help("Run built-in demonstrations"))
    diag_grp.add_argument("--help-colors", action="store_true", help=b_help("Show advanced coordinate-based color parameters (-0, -E, -b, etc.)"))
    diag_grp.add_argument("--help-advanced", action="store_true", help=b_help("Show advanced streaming, sorting, and jagged matrix behaviors"))

    data_grp = parser.add_argument_group("Data Ingestion & Parsing Logic")
    data_grp.add_argument("-i", "--input", type=str, help=b_help("Auto-detect and format a delimited structural file (CSV, TSV, etc.)"))
    data_grp.add_argument("--csv-dialect", type=str, help=a_help("Enforce explicit CSV dialect mechanically without sniffing (e.g. 'excel-tab')."))
    data_grp.add_argument("--sort-by", type=int, help=a_help("Column index (0-indexed) to buffer and sort standard input (Caveat Emptor: memory intensive over streams)."))
    data_grp.add_argument("--sort-reverse", action="store_true", help=a_help("Reverse the sorting order."))
    data_grp.add_argument("--stream", action="store_true", help=a_help("Force infinite memoryless streaming output explicitly over buffer allocations."))
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
    layout_grp.add_argument("-d", "--dtype", type=str, help=b_help("Column datatypes string (e.g. 'tfi')"))
    layout_grp.add_argument("-P", "--precision", type=int, help=b_help("Float decimal precision mapping globally"))

    visual_grp = parser.add_argument_group("Visual Elements & Toggles")
    visual_grp.add_argument("-N", "--title", type=str, help=b_help("Table title string rendered centered above output"))
    visual_grp.add_argument("-s", "--style", type=str, default="light", help=b_help("Override the visual rendering style (default: 'light')"))
    visual_grp.add_argument("-t", "--theme", type=str, help=b_help("Apply a dynamic color theme matrix to the input data (e.g. 'forest-cols')"))
    visual_grp.add_argument("-H", "--no-header", action="store_true", help=b_help("Bypass popping the first row as the table header"))
    visual_grp.add_argument("-B", "--no-borders", action="store_true", help=b_help("Disable the outer table border"))
    visual_grp.add_argument("-X", "--no-hlines", action="store_true", help=b_help("Disable horizontal lines iteratively between rows"))
    visual_grp.add_argument("-V", "--no-vlines", action="store_true", help=b_help("Disable vertical lines strictly between columns"))
    visual_grp.add_argument("-U", "--no-header-line", action="store_true", help=b_help("Disable the horizontal divider below the header"))

    color_grp = parser.add_argument_group("Coordinate-Based Targeting (Colors)")
    color_grp.add_argument("--mark-abnormal", type=str, metavar="COLOR", help=a_help("Highlight skipped strings mutated implicitly dynamically."))
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
        print("Tip: Run 'vistab -L' to view a rendered matrix of all available layout stylings.", file=sys.stderr)
        sys.exit(1)
        
    if getattr(args, 'theme', None) and args.theme not in Vistab.THEMES:
        print(f"\033[1;31m[ERROR]\033[0m Unknown color theme '{args.theme}'", file=sys.stderr)
        print(f"Available themes: {', '.join(sorted(Vistab.THEMES.keys()))}", file=sys.stderr)
        print("Tip: Run 'vistab -M' to view a rendered matrix of all available color themes.", file=sys.stderr)
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
            with open(args.create_config, "w", encoding="utf8") as f:
                f.write(config_content)
            print(f"[\033[32mSUCCESS\033[0m] Generated Vistab config template at: {args.create_config}")
        except Exception as e:
            print(f"[\033[1;31mERROR\033[0m] Could not create config: {e}")
            sys.exit(1)
        # Exit cleanly without disrupting
        sys.exit(0)

    if args.demo == "styles":
        print_styles_list()
        _printed_anything = True
        
    if args.demo == "colors":
        print_colors_list()
        _printed_anything = True
        
    if args.demo == "themes":
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_themes_demo()
        _printed_anything = True
    if args.demo == "capabilities":
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_test_demo()
        _printed_anything = True
        
    if args.demo == "anatomy":
        if _printed_anything:
            print("\n" + "="*40 + "\n")
        print_coordinate_styles_demo()
        _printed_anything = True
        
    if _printed_anything:
        sys.exit(0)
        
    # Process inputs (backwards compatible with -i)
    target_files = getattr(args, 'files', [])
    if args.input and args.input not in target_files:
        target_files.append(args.input)
        
    streams_to_parse = [("file", fp) for fp in target_files]
            
    # Grab STDIN securely if terminal is executing a piped stream smoothly
    is_config_only = getattr(args, 'save_theme', None) or getattr(args, 'show_code', False)
    
    if not is_config_only and not sys.stdin.isatty() and not target_files:
        streams_to_parse.append(("stdin", "STDIN Stream"))
            
    # Validation fallback cleanly
    if not streams_to_parse:
        if is_config_only:
            streams_to_parse.append(("dummy", "Config Mapping"))
        elif not _printed_anything:
            parser.print_usage(sys.stderr)
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
        # Parse CSV payload structurally securely efficiently
        peek_stream = LinePeekableStream(f_stream)
        
        try:
            if getattr(args, 'csv_dialect', None):
                reader = csv.reader(peek_stream, dialect=args.csv_dialect)
            else:
                dialect = csv.Sniffer().sniff(peek_stream.sample(), delimiters=",\t|;")
                reader = csv.reader(peek_stream, dialect)
        except csv.Error:
            reader = csv.reader(peek_stream)
            
        is_streaming = args.stream or (source_type == "stdin")
        if getattr(args, 'sort_by', None) is not None:
            # Caveat Emptor boundary: Implicit streaming is bypassed globally explicitly ensuring matrix loads physically into RAM for proper sort evaluations.
            is_streaming = False
            
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
                print(f"[\033[33mWARN\033[0m] The parsed stream '{source_name}' is physically mathematically empty.")
                return

        # Instantiate physical mapping structure cleanly
        table = Vistab(
            style=args.style,
            max_width=args.width,
            padding=args.padding
        )
        
        # Apply jagged logic mapped seamlessly constraints
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
            
            # Buffer structurally explicitly if memory fallback mapped
            if rows is not None:
                table.set_rows(rows, header=not args.no_header)
            
            # Apply custom decorations cleanly and naturally
            deco = Vistab.BORDER | Vistab.HEADER | Vistab.HLINES | Vistab.VLINES
            if args.no_borders:
                deco &= ~Vistab.BORDER
            if args.no_hlines:
                deco &= ~Vistab.HLINES
            if args.no_vlines:
                deco &= ~Vistab.VLINES
            if args.no_header_line:
                deco &= ~Vistab.HEADER
            table.set_decorations(deco)
            
            # Proceed with applying explicit dimension mapping arrays natively
            if args.align:
                table.set_cols_align(args.align)
                
            if args.valign:
                table.set_cols_valign(args.valign)
                
            if args.dtype:
                table.set_cols_dtype(args.dtype)
                
            if args.col_widths:
                string_array = args.col_widths.split(",")
                table.set_cols_width(string_array)
                
            # Dynamically apply title logic cleanly
            if args.title:
                table.set_title(args.title)
            elif len(target_files) > 1 and source_type == "file":
                table.set_title(f"[ {source_name} ]") # Add implicit filename title smoothly mapping arrays natively
                
            if args.precision is not None:
                table.set_precision(args.precision)
                
            if args.theme:
                table.apply_theme(args.theme)
                
                # Ensure explicit command-line style or padding flag overrides theme defaults natively
                if "-s" in sys.argv or "--style" in sys.argv:
                    table.set_style(args.style)
                if "-p" in sys.argv or "--padding" in sys.argv:
                    table.set_padding(args.padding)
                    
            if getattr(args, 'sort_by', None) is not None:
                table.sort_by(args.sort_by, reverse=getattr(args, 'sort_reverse', False))
                    
            # Native helper to seamlessly map CLI string states to API logic dropping keys explicitly if "none"
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
                
            # Evaluate save-theme and show-code intercept logic cleanly referencing active state
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
                    os.makedirs(config_dir, exist_ok=True)
                    if not os.path.exists(themes_file):
                        with open(themes_file, "w") as f: json.dump({}, f)
                    try:
                        with open(themes_file, "r") as f: tdb = json.load(f)
                    except Exception: tdb = {}
                    tdb[args.save_theme] = compiled_theme
                    with open(themes_file, "w", encoding="utf8") as f: json.dump(tdb, f, indent=4)
                    print(f"[\033[32mSUCCESS\033[0m] Saved layout globally as '{args.save_theme}' in {themes_file}")
                    
                if getattr(args, 'show_code', False):
                    print("import vistab\n")
                    print("custom_theme = " + json.dumps(compiled_theme, indent=4) + "\n")
                    print("table = vistab.Vistab().apply_theme(custom_theme)")
                    
                    has_geometry = any([
                        getattr(args, 'col_widths', None), getattr(args, 'align', None), 
                        getattr(args, 'valign', None), getattr(args, 'dtype', None), 
                        getattr(args, 'precision', None) is not None, getattr(args, 'title', None), 
                        getattr(args, 'width', 0) > 0, getattr(args, 'max_rows', 0) > 0, getattr(args, 'max_cols', 0) > 0
                    ])
                    
                    if has_geometry:
                        print("\n# Data-specific parameters are mapped explicitly outside the theme registry")
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
                        
                    print("\n# ... map inputs cleanly and execute drawing natively")
                    print("print(table.draw())")
                    
                sys.exit(0)
                
            if is_streaming:
                for line in table.stream(reader, sample_size=args.stream_probe):
                    print(line)
            else:
                drawn = table.draw()
                if drawn: print(drawn)
                
            _printed_anything = True
            
        except Exception as eval_err:
            print(f"\n\033[1;31m[COMMAND-LINE FORMAT ERROR]\033[0m within stream '{source_name}'")
            print(f"Details: {eval_err}\n")
            print("Tip: Ensure your formatting inputs perfectly map to your CSV column lengths!")
            print("--align:  l (left), c (center), r (right)                   | e.g., 'lrc'")
            print("--valign: t (top), m (middle), b (bottom)                   | e.g., 'tmb'")
            print("--dtype:  t (text), f (float), i (int), e (exp), a (auto)   | e.g., 'ttfi'")
            print("--col-widths: Comma-separated integers                      | e.g., '40,10,15'")
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
