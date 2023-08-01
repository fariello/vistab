#!/usr/bin/env python
# -*- coding: utf-8 -*-
# texttable - module for creating simple ASCII tables
# Copyright (C) 2003-2019 Gerome Fournier <jef(at)foutaise.org>

r"""module for creating simple ASCII tables.

Example:

    table = UniTable()
    table.set_cols_align(["l", "r", "c"])
    table.set_cols_valign(["t", "m", "b"])
    table.add_rows([["Name", "Age", "Nickname"],
                    ["Mr\\nXavier\\nHuon", 32, "Xav'"],
                    ["Mr\\nBaptiste\\nClement", 1, "Baby"],
                    ["Mme\\nLouise\\nBourgeau", 28, "Lou\\n\\nLoue"]])
    print table.draw() + "\\n"

    table = UniTable()
    table.set_decorations(UniTable.HEADER)
    table.set_cols_dtype(['t',  # text
                          'f',  # float (decimal)
                          'e',  # float (exponent)
                          'i',  # integer
                          'a']) # automatic
    table.set_cols_align(["l", "r", "r", "r", "l"])
    table.add_rows([["text",    "float", "exp", "int", "auto"],
                    ["abcd",    "67",    654,   89,    128.001],
                    ["efghijk", 67.5434, .654,  89.6,  12800000000000000000000.00023],
                    ["lmn",     5e-78,   5e-78, 89.4,  .000000000000128],
                    ["opqrstu", .023,    5e+78, 92.,   12800000000000000000000]])
    print table.draw()

Result:

    +----------+-----+----------+
    |   Name   | Age | Nickname |
    +==========+=====+==========+
    | Mr       |     |          |
    | Xavier   |  32 |          |
    | Huon     |     |   Xav'   |
    +----------+-----+----------+
    | Mr       |     |          |
    | Baptiste |   1 |          |
    | Clement  |     |   Baby   |
    +----------+-----+----------+
    | Mme      |     |   Lou    |
    | Louise   |  28 |          |
    | Bourgeau |     |   Loue   |
    +----------+-----+----------+

    text   float       exp      int     auto
    ===========================================
    abcd   67.000   6.540e+02   89    128.001
    efgh   67.543   6.540e-01   90    1.280e+22
    ijkl   0.000    5.000e-78   89    0.000
    mnop   0.023    5.000e+78   92    1.280e+22
"""

from __future__ import division
from wcwidth import wcswidth
import re
import sys
from typing import List, Optional, Iterable, Any
from functools import reduce

__all__ = ["UniTable", "ArraySizeError", "StringLengthCalculator"]

__author__ = 'Gerome Fournier <jef(at)foutaise.org>'
__license__ = 'MIT'
__version__ = '1.6.2'
__credits__ = """\
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

gfariello:
    - Added unicode box border options, made errors more informative, corrected typos
"""

# define a text wrapping function to wrap some text
# to a specific width:
# - use cjkwrap if available (better CJK support)
# - fallback to textwrap otherwise
try:
    import cjkwrap

    def textwrapper(txt, width):
        return cjkwrap.wrap(txt, width)
except ImportError:
    try:
        import textwrap

        def textwrapper(txt, width):
            return textwrap.wrap(txt, width)
    except ImportError:
        sys.stderr.write("Can't import textwrap module!\n")
        raise


class StringLengthCalculator:
    """
    A class to calculate the visible length of a string, excluding ANSI escape sequences.

    Example:
    --------
    ```
    calculator = StringLengthCalculator()
    colored_string = "\033[1;31mRed text\033[0m"
    length = calculator.visible_length(colored_string)
    print(length)  # Outputs: 8
    ```
    """
    def __init__(self):
        # Regular expression to match ANSI escape sequences
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def len(self, string: str) -> int:
        """
        Calculate the visible length of a string, excluding ANSI escape sequences.

        Args:
        s (str): The string whose visible length should be calculated.

        Returns:
        int: The visible length of the string.
        """
        # Remove ANSI escape sequences
        visible_string = self.ansi_escape.sub('', string)

        # Return the length of the visible string
        return wcswidth(visible_string)

    pass


class ColorAwareWrapper:
    """
    Class to wrap text to a specified width, excluding ANSI escape sequences.
    """
    def __init__(self):
        self.calculator = StringLengthCalculator()

    def wrap(self, text: str, width: int) -> str:
        """
        Wraps text to the specified width, ignoring ANSI escape sequences.
        """
        # Split the text into words
        words = text.split()

        # Initialize an empty line and an empty result
        line, result = [], []

        # Iterate over the words
        for word in words:
            # Calculate the length of the current line and the next word
            line_length = self.calculator.visible_length(' '.join(line))
            word_length = self.calculator.visible_length(word)

            # If adding the next word to the line would exceed the width...
            if line_length + word_length + len(line) > width:  # +len(line) for spaces
                # ...then add the current line to the result and start a new line
                result.append(' '.join(line))
                line = []

            # Add the word to the current line
            line.append(word)

        # If there are any words left in the line, add the line to the result
        if line:
            result.append(' '.join(line))

        # Join the lines in the result with line breaks
        return '\n'.join(result)

    pass


def obj2unicode(obj):
    """Return a unicode representation of a python object."""
    if isinstance(obj, str):
        return obj
    elif isinstance(obj, bytes):
        return obj.decode()
    return str(obj)


class ArraySizeError(Exception):
    """Exception raised when specified rows don't fit the required size."""

    def __init__(self, msg):
        """Init this."""
        self.msg = msg
        Exception.__init__(self, msg, '')
        pass

    def __str__(self):
        """Return string."""
        return self.msg
    pass


class FallbackToText(Exception):
    """Used for failed conversion to float."""

    pass


class UniTable:
    """
    A class that provides functionality for creating and manipulating ASCII tables.

    Example usage:
    ```
    table = UniTable()
    table.set_cols_align(["l", "r", "c"])
    table.add_rows([["Name", "Age"], ["Alice", 25], ["Bob", 30]])
    print(table.draw())
    ```
    """

    BORDER = 1
    HEADER = 1 << 1
    HLINES = 1 << 2
    VLINES = 1 << 3
    # --- gfariello -- Start -- Added to support new styles.
    TOP = 0
    MIDDLE = 1
    BOTTOM = 2
    STYLES = {
        "ascii": "-|+-",
        "ascii2": "-|+=",
        "bold": "━┃┏┓┗┛┣┫┳┻╋━┣┫╋",
        "double": "═║╔╗╚╝╠╣╦╩╬═╠╣╬",
        "light2": "─│┌┐└┘├┤┬┴┼═╞╡╪",
        "round": "─│╭╮╰╯├┤┬┴┼─├┤┼",
        "round2": "─│╭╮╰╯├┤┬┴┼═╞╡╪",
        "light": "─│┌┐└┘├┤┬┴┼─├┤┼",
        "none": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ],
        "none2": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ],
    }
    STYLE_MAPPER = {
        "heavy": {
            "---w": " ",
            "--e-": " ",
            "--ew": "━",
            "-s--": " ",
            "-s-w": "┓",
            "-se-": "┏",
            "-sew": "┳",
            "n---": " ",
            "n--w": "┛",
            "n-e-": "┗",
            "n-ew": "┻",
            "ns--": "┃",
            "ns-w": "┫",
            "nse-": "┣",
            "nsew": "╋",
        },
        "light2": {
            "---w": " ",
            "--e-": " ",
            "--ew": "-",
            "-s--": " ",
            "-s-w": "┐",
            "-se-": "┌",
            "-sew": "┬",
            "n---": " ",
            "n--w": "┘",
            "n-e-": "└",
            "n-ew": "┴",
            "ns--": "│",
            "ns-w": "┤",
            "nse-": "├",
            "nsew": "┼",
        },
        "round": {
            "---w": " ",
            "--e-": " ",
            "--ew": "-",
            "-s--": " ",
            "-s-w": "╮",
            "-se-": "╭",
            "-sew": "┬",
            "n---": " ",
            "n--w": "╯",
            "n-e-": "╰",
            "n-ew": "┴",
            "ns--": "│",
            "ns-w": "┤",
            "nse-": "├",
            "nsew": "┼",
        },
        "double": {
            "---w": " ",
            "--e-": " ",
            "--ew": "═",
            "-s--": " ",
            "-s-w": "╗",
            "-se-": "╔",
            "-sew": "╦",
            "n---": " ",
            "n--w": "╝",
            "n-e-": "╚",
            "n-ew": "╩",
            "ns--": "║",
            "ns-w": "╣",
            "nse-": "╠",
            "nsew": "╬",
        },
        "heavy:light": {
            "---w:--e-": "╾",
            "---w:-s--": "┑",
            "---w:-se-": "┲",
            "---w:n---": "┙",
            "---w:n-e-": "┺",
            "---w:ns--": "┥",
            "---w:nse-": "┽",
            "--e-:---w": "╼",
            "--e-:-s--": "┍",
            "--e-:-s-w": "┮",
            "--e-:n---": "┙",
            "--e-:n--w": "┶",
            "--e-:ns--": "┝",
            "--e-:ns-w": "┾",
            "--ew:-s--": "┰",
            "--ew:n---": "┸",
            "--ew:ns--": "┿",
            "-s--:---w": "┒",
            "-s--:--e-": "┎",
            "-s--:--ew": "┰",
            "-s--:n---": "╽",
            "-s--:n--w": "┧",
            "-s--:n-e-": "┟",
            "-s--:n-ew": "╁",
            "-s-w:--e-": "┱",
            "-s-w:n---": "┧",
            "-s-w:n-e-": "╅",
            "-se-:---w": "┲",
            "-se-:n---": "┢",
            "-se-:n--w": "╆",
            "-sew:n---": "╈",
            "n---:---w": "┖",
            "n---:--e-": "┚",
            "n---:--ew": "┸",
            "n---:-s--": "╿",
            "n---:-s-w": "┦",
            "n---:-se-": "┞",
            "n---:-sew": "╀",
            "n--w:--e-": "┹",
            "n--w:-s--": "┩",
            "n--w:-se-": "╃",
            "n-e-:---w": "┺",
            "n-e-:-s--": "┡",
            "n-e-:-s-w": "╄",
            "n-ew:-s--": "╇",
            "ns--:---w": "┨",
            "ns--:--e-": "┠",
            "ns--:--ew": "╂",
            "ns-w:--e-": "╉",
            "nse-:---w": "╊",
        }
    }

    def __init__(self, rows: Optional[Iterable[Iterable]] = None, max_width: int = 80,
                 style: str = 'light', padding: int = 1, alignment: str = None):
        """
        Initializes a new instance of the UniTable class.

        Args:
        rows (optional): An iterable containing rows to be added to the table.
                         Each row should be an iterable of cell values. Default is None.
        max_width (optional): The maximum width of the table. Default is 80. If this
                         is set to 0, no wrapping will occur.
        style (optional): The style of the table. Default is 'light' See set_style().
        padding (optional): The amount of padding (left and right) for the cells. The
                          default is 1. See set_padding()
        alignment (optional): Set the alignment. See set_cols_align()

        Example:
        --------
        ```
        # creates a new UniTable instance with initial rows and a maximum width of 100
        table = UniTable(rows=[["Name", "Age"], ["Alice", 25], ["Bob", 30]], max_width=100)
        print(table.draw())
        ```

        If no rows are provided during initialization, they can be added later using the `add_row` or `add_rows` methods.
        """
        self._has_border = True
        self._has_header = True
        self._has_hline_between_headers = True
        self._has_hline_header_2_cell = True
        self._has_hline_between_cells = True
        self._has_vline_between_headers = True
        self._has_vline_header_2_cell = True
        self._has_vline_between_cells = True
        self._vislen = StringLengthCalculator()
        self._cwrap = ColorAwareWrapper()
        self.reset()
        self._precision = 3
        # --- gfariello -- Start -- Added to support rows arg (i.e., adding
        # entire table definition in initilization). NOTE: This changed the
        # order (max_width is now one arg later) and therefore has a chance of
        # breaking older code that called UniTable(50) but not
        # UniTable(max_width=50). It felt less intuitive to have the rows
        # definition after the max_width, but if backwards compatibility is
        # more important, just swap the order of rows and max_width.
        if rows is not None:
            self.add_rows(rows)
            pass
        self.set_max_width(max_width)
        # --- gfariello -- End -- Added to support rows arg.
        # Match an ANSI reset sequence if it is not followed by a non-reset seqeunce
        self.no_end_reset = re.compile(r'\033\[0m(?!.*\033\[((?!0m)[0-?]*[ -/]*[@-~]))')
        self.non_reset_sequence = re.compile(r'\033\[((?!0m)[0-?]*[ -/]*[@-~])')
        self.non_reset_not_followed_by_reset = re.compile(r'(\033\[(?:(?!0m)[0-?]*[ -/]*[@-~]))(?!.*\033\[0m)')
        self.ansi_norm = "\033[0m"

        self._deco = UniTable.VLINES | UniTable.HLINES | UniTable.BORDER | \
            UniTable.HEADER
        self.set_style(style)
        self.set_padding(padding)
        if alignment is not None:
            self.set_cols_align(alignment)
            pass
        pass

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

        - reset rows and header
        """
        self._hline_string = None
        self._row_size = None
        self._header = []
        self._rows = []
        self._style = "light"
        return self

    @property
    def max_width(self):
        """Get the maximum width of the table. If 0, no max."""
        return self._max_width

    @max_width.setter
    def max_width(self, val):
        self.set_max_width(val)

    def set_max_width(self, max_width: int) -> 'UniTable':
        """Set the maximum width of the table.

        - max_width is an integer, specifying the maximum width of the table
        - if set to 0, size is unlimited, therefore cells won't be wrapped
        """
        self._max_width = max_width if max_width > 0 else False
        return self

    def set_style(self, style: str = "light") -> 'UniTable':
        """Set the characters used to draw lines between rows and columns to one of defined types.

        Examples:
            "light": Use unicode light box borders (─│┌┐└┘├┤┬┴┼)
            "bold":  Use unicode bold box borders (━┃┏┓┗┛┣┫┳┻╋)
            "double": Use unicode double box borders (═║╔╗╚╝╠╣╦╩╬)

        Default if none provided is "light"

        """
        self._style = style
        if style in UniTable.STYLES:
            self.set_table_lines(UniTable.STYLES[style])
            return self
        raise ValueError("style must be one of '%s' not '%s'" % ("', '".join(sorted(UniTable.STYLES.keys())), style))

    def _set_table_lines(self, table_lines: str) -> 'UniTable':
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

    def set_table_lines(self, table_lines: str) -> 'UniTable':
        """Set the characters used to draw lines between rows and columns.

        - the table_lines should contain either 4 fields or 15. For 4:

            [horizontal, vertical, corner, header]

        - default is set to (both are the same):

            "-|+="
            "-|+++++++++=+++"
        """
        if len(table_lines) == 15:
            return self._set_table_lines(table_lines)
        if len(table_lines) != 4:
            raise ArraySizeError("string/array should contain either 4 or 15 characters not %d as in '%s'" % (len(table_lines), table_lines))
        (hor, ver, cor, hea) = table_lines
        self._set_table_lines([hor, ver, cor, cor, cor, cor, cor, cor, cor, cor, cor, hea, cor, cor, cor])
        return self

    def set_decorations(self, decorations: int) -> 'UniTable':
        """Set the table decoration.

        - 'decorations' can be a combinasion of:

            UniTable.BORDER: Border around the table
            UniTable.HEADER: Horizontal line below the header
            UniTable.HLINES: Horizontal lines between rows
            UniTable.VLINES: Vertical lines between columns

           All of them are enabled by default

        - example:

            UniTable.BORDER | UniTable.HEADER
        """
        self._deco = decorations
        return self

    def set_header_align(self, array: str) -> 'UniTable':
        """Set the desired header alignment.

        - the elements of the array should be either "l", "c" or "r":

            * "l": column flushed left
            * "c": column centered
            * "r": column flushed right
        """
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._header_align = array
        return self

    def set_cols_align(self, array: str) -> 'UniTable':
        """Set the desired columns alignment.

        - the elements of the array should be either "l", "c" or "r":

            * "l": column flushed left
            * "c": column centered
            * "r": column flushed right
        """
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._align = array
        return self

    def set_cols_valign(self, array: str) -> 'UniTable':
        """Set the desired columns vertical alignment.

        - the elements of the array should be either "t", "m" or "b":

            * "t": column aligned on the top of the cell
            * "m": column aligned on the middle of the cell
            * "b": column aligned on the bottom of the cell
        """
        if isinstance(array, str):
            array = [c for c in array]
            pass
        self._check_row_size(array)
        self._valign = array
        return self

    def set_cols_dtype(self, array: str) -> 'UniTable':
        """
        Sets the data types for the columns in the table.

        Args:
        array (List[str]): A list of strings representing the data types for the columns.
                           Acceptable values are: 't' (text), 'f' (float, decimal),
                           'e' (float, exponent), 'i' (integer), and 'a' (automatic).

        Example usage:
        ```
        table = UniTable()
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

    def set_cols_width(self, array: str) -> 'UniTable':
        """Set the desired columns width.

        - the elements of the array should be integers, specifying the
          width of each column. For example:
                [10, 20, 5]
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

    def set_precision(self, width: int) -> 'UniTable':
        """Set the desired precision for float/exponential formats.

        - width must be an integer >= 0
        - default value is set to 3
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
    def padding(self, val: int) -> 'UniTable':
        """Set the amount of padding."""
        self.set_padding(val)
        return self

    def set_padding(self, amount: int) -> 'UniTable':
        """Set the amount of spaces to pad cells (right and left, we don't do top bottom padding).

        - width must be an integer >= 0
        - default value is set to 1
        """
        if not type(amount) is int or amount < 0:
            raise ValueError('padding must be an integer greater then 0')
        self._pad = amount
        return self

    def header(self, array: List[Any]) -> 'UniTable':
        """Specify the header of the table."""
        self._check_row_size(array)
        self._header = list(map(obj2unicode, array))
        return self

    def add_row(self, array: List[str]) -> 'UniTable':
        """Add a row in the rows stack.

        - cells can contain newlines and tabs
        """
        self._check_row_size(array)
        if not hasattr(self, "_dtype"):
            self._dtype = ["a"] * self._row_size
        cells = []
        for i, x in enumerate(array):
            cells.append(self._str(i, x))
        self._rows.append(cells)
        return self

    def add_rows(self, rows, header=True) -> 'UniTable':
        """Add several rows in the rows stack.

        - The 'rows' argument can be either an iterator returning arrays,
          or a by-dimensional array
        - 'header' specifies if the first row should be used as the header
          of the table
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

    def set_rows(self, rows, header=True) -> 'UniTable':
        """Replace all rows in the table with the provided rows."""
        self._rows = []
        return self.add_rows(rows, header)

    def draw(self):
        """Draw the table and return as string."""
        if not self._header and not self._rows:
            return
        self._compute_cols_width()
        self._check_align()
        out = ""
        if self.has_border:
            out += self._hline(location=UniTable.TOP)
        if self._header:
            out += self._draw_line(self._header, isheader=True)
            if self.has_header:
                out += self._hline_header(location=UniTable.MIDDLE)
                pass
            pass
        num = 0
        length = len(self._rows)
        for row in self._rows:
            num += 1
            out += self._draw_line(row)
            if self.has_hlines() and num < length:
                out += self._hline(location=UniTable.MIDDLE)
        if self._has_border:
            out += self._hline(location=UniTable.BOTTOM)
        return out[:-1]

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
        return self._deco & UniTable.VLINES > 0

    def has_hlines(self):
        """Return a boolean, if hlines are required or not."""
        return self._deco & UniTable.HLINES > 0

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
        if UniTable.TOP == location:
            left, mid, right = self._char_se, self._char_sew, self._char_sw
        elif UniTable.MIDDLE == location:
            if is_header:
                left, mid, right = self._char_hnse, self._char_hnsew, self._char_hnsw
            else:
                left, mid, right = self._char_nse, self._char_nsew, self._char_nsw
                pass
        elif UniTable.BOTTOM == location:
            # NOTE: This will not work as expected if the table is only headers.
            left, mid, right = self._char_ne, self._char_new, self._char_nw
        else:
            raise ValueError("Unknown location '%s'. Should be one of UniTable.TOP, UniTable.MIDDLE, or UniTable.BOTTOM." % (location))
        # compute cell separator
        cell_sep = "%s%s%s" % (horiz_char * self._pad, [horiz_char, mid][self.has_vlines()], horiz_char * self._pad)
        # build the line
        hline = cell_sep.join([horiz_char * n for n in self._width])
        # add border if needed
        if self.has_border:
            hline = "%s%s%s%s%s\n" % (left, horiz_char * self._pad, hline, horiz_char * self._pad, right)
        else:
            hline += "\n"
        return hline

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

    def _compute_cols_width(self):
        """Return an array with the width of each column.

        If a specific width has been specified, exit. If the total of the
        columns width exceed the table desired width, another width will be
        computed to fit, and cells will be wrapped.
        """
        if hasattr(self, "_width"):
            return
        maxi = []
        if self._header:
            maxi = [self._len_cell(x) for x in self._header]
        for row in self._rows:
            for cell, i in zip(row, list(range(len(row)))):
                try:
                    maxi[i] = max(maxi[i], self._len_cell(cell))
                except (TypeError, IndexError):
                    maxi.append(self._len_cell(cell))
        ncols = len(maxi)
        content_width = sum(maxi)
        deco_width = 3 * (ncols - 1) + [0, 4][self.has_border]
        if self._max_width and (content_width + deco_width) > self._max_width:
            # content too wide to fit the expected max_width
            # let's recompute maximum cell width for each cell
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

    def _check_align(self):
        """Check if alignment has been specified, set default one if not."""
        if not hasattr(self, "_header_align"):
            self._header_align = ["c"] * self._row_size
        if not hasattr(self, "_align"):
            self._align = ["l"] * self._row_size
        if not hasattr(self, "_valign"):
            self._valign = ["t"] * self._row_size

    def _draw_line(self, line, isheader=False):
        """Draw a line.

        Loop over a single cell length, over all the cells.
        """
        line = self._splitit(line, isheader)
        space = " "
        out = ""
        # topmost, leftmost = True, True
        for i in range(self.vislen(line[0])):
            if self.has_border:
                out += "%s%s" % (self._char_ns, " " * self._pad)
            length = 0
            for cell, width, align in zip(line, self._width, self._align):
                length += 1
                cell_line = cell[i]
                fill = width - self.vislen(cell_line)
                if isheader:
                    align = self._header_align[length - 1]
                if align == "r":
                    out += fill * space + cell_line
                elif align == "c":
                    out += (int(fill / 2) * space + cell_line + int(fill / 2 + fill % 2) * space)
                else:
                    out += cell_line + fill * space
                if length < self.vislen(line):
                    out += "%s%s%s" % (" " * self._pad, [space, self._char_ns][self.has_vlines()], " " * self._pad)
            out += "%s\n" % ['', " " * self._pad + self._char_ns][self.has_border]
        return out

    def _splitit(self, line, isheader):
        """Split each element of line to fit the column width.

        Each element is turned into a list, result of the wrapping of the
        string to the desired width.
        """
        line_wrapped = []
        for cell, width in zip(line, self._width):
            array = []
            for c in cell.split('\n'):
                if c.strip() == "":
                    array.append("")
                else:
                    array.extend(textwrapper(c, width))
            line_wrapped.append(array)
        max_cell_lines = reduce(max, list(map(len, line_wrapped)))
        for cell, valign in zip(line_wrapped, self._valign):
            if isheader:
                valign = "t"
            if valign == "m":
                missing = max_cell_lines - self.vislen(cell)
                cell[:0] = [""] * int(missing / 2)
                cell.extend([""] * int(missing / 2 + missing % 2))
            elif valign == "b":
                cell[:0] = [""] * (max_cell_lines - self.vislen(cell))
            else:
                cell.extend([""] * (max_cell_lines - self.vislen(cell)))
                pass
            pass
        return self._process_lines(line_wrapped)

    def _process_lines(self, lines_2d: List[List[str]]) -> List[List[str]]:
        """
        Process a list of lines to ensure all ANSI escape sequences are
        properly terminated and continued onto the next line if necessary.

        Parameters:
        lines (List[str]): The lines to process.

        Returns:
        List[str]: The processed lines.
        """
        # Initialize a variable to hold the last sequence
        unterminated_sequences = ""
        # print(f"START lines_2d={lines_2d}")
        for lines in lines_2d:
            for i in range(len(lines)):
                # If there was a non-reset sequence in the last line, prepend it to this line
                if unterminated_sequences:
                    lines[i] = unterminated_sequences + lines[i]
                    unterminated_sequences = ""
                    pass
                # Save any ANSI escape sequences that are not terminated by a reset sequence
                unterminated_sequences = "".join(self.non_reset_not_followed_by_reset.findall(lines[i]))
                if unterminated_sequences:
                    # print(f"unterminated_sequences={unterminated_sequences}")
                    # Add a reset sequence to the end of the line
                    lines[i] += "\033[0m"
                    pass
                pass
            pass
        # print(f"ENDS lines_2d={lines_2d}\033[0m")
        return lines_2d


def split_list(input_list, split_length, fill_value=None):
    """
    Split a list into sub-lists of a specified length.

    If the last sub-list is shorter than the specified length, it will be filled
    with the specified fill value.

    Parameters:
    input_list (list): The list to split.
    split_length (int): The length of the sub-lists.
    fill_value (optional): The value to fill the last sub-list with. Default is None.

    Returns:
    list: A list of sub-lists.
    """
    # Calculate the number of chunks
    num_chunks = (len(input_list) + split_length - 1) // split_length
    # Create the chunks
    chunks = [input_list[i*split_length:(i+1)*split_length] for i in range(num_chunks)]
    # Fill the last chunk if necessary
    if len(chunks[-1]) < split_length:
        chunks[-1] += [fill_value] * (split_length - len(chunks[-1]))
    return chunks


def example_table(style: str, padding: int = 1):
    return UniTable([["Hd1", "Hd2"], ["Ce1", "Ce2"], ["Ce3", "Ce4"], ], style=style, padding=padding).draw()


if __name__ == '__main__':
    print("\033[1m\033[1;31mANSI\033[0m\033[1m Color / Escape Sequence Aware Text-Based Tables\033[0m:")
    t1 = UniTable([
        ["Test 1", "Test 2", "Test 3", "Test 4"],
        [
            "This is some \033[1;31mRed text\033[0m to show the ability to wrap \033[38;5;226mcolored text\033[0m correctly.",
            "\033[4mThis text is underlined, \033[1mbold, and \033[34mblue.\033[0m This is not.",
            "This is some normal text in the middle to ensure that it is working properly.",
            "Some \033[1;31mRed mandarin: 这是一个 美好的世界！\033[0m for testing.",
        ]
    ])
    t1.set_max_width(80)
    print(t1.draw())
    import textwrap3
    width = 18
    print("-" * width)
    for line in textwrap3.wrap("This is some Red text to show the ability to wrap colored text correctly.", width):
        print(line)
        pass
    print("-" * width)
    for line in textwrap3.wrap("This is some \033[1;31mRed text\033[0m to show the ability to wrap \033[38;5;226mcolored text\033[0m correctly.", width):
        print(line)
        pass
    print()
    print("\033[1mAvailable Styles\033[0m (Note: the default is \"light\"):")
    style_list = sorted(UniTable.STYLES.keys())
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
                pass
            pass
        data.append(style_row)
        data.append(tables_row)
        data.append(["", "", "", ""])
        pass
    t1 = UniTable(data, max_width=120, style="none", alignment="cccc")
    print(t1.draw())
    exit()
