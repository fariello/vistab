#!/usr/bin/env python3
"""
csvforge.py

Generate CSV files from a compact column specification language.

Recommended script name:
    csvforge.py

Overview
========
This script accepts one or more column specifications and produces a CSV file
with headers:

    col1, col2, ... colX

where X is the number of supplied column specifications.

Supported column specifications
===============================

d[n]
    Ascending index sequence.
    Starts at 1 by default unless n is specified.

    Examples:
        d       -> 1, 2, 3, ...
        d0      -> 0, 1, 2, ...
        d5      -> 5, 6, 7, ...

D[n]
    Descending index sequence.
    Starts at n and counts down.
    If omitted, defaults to 1.

    Examples:
        D       -> 1, 0, -1, ...
        D12     -> 12, 11, 10, ...

i[n[-m]]
    Random integer.
    If neither n nor m is specified, range is 1..9.
    If only n is specified, range is 0..n.
    If n-m is specified, range is n..m inclusive.

    Examples:
        i       -> 1..9
        i12     -> 0..12
        i34-49  -> 34..49

f[[n[-m]]:decimals]
    Random float.
    If neither n nor m is specified, range is 1..9.
    If only n is specified, range is 0..n.
    If n-m is specified, range is n..m inclusive.
    Decimals is optional and defaults to 2.

    Examples:
        f         -> 1..9 with 2 decimals
        f12       -> 0..12 with 2 decimals
        f34-49    -> 34..49 with 2 decimals
        f:3       -> 1..9 with 3 decimals
        f10:4     -> 0..10 with 4 decimals
        f3-7:1    -> 3..7 with 1 decimal

l[[a[-z]]:[[i]-j]]]
    Random lowercase letters.
    The optional leading range defines which letters may be used.
    The optional length portion defines how many letters to generate.

    Letter range behavior:
        l         -> a-z
        la        -> a-z
        la-n      -> a-n
        ln-m      -> n-m

    Length behavior:
        l         -> exactly 1 letter
        l:3       -> exactly 3 letters
        l:2-5     -> 2 to 5 letters
        la-f:3    -> 3 letters chosen from a-f

u[[a[-z]]:[[i]-j]]]
    Same as lowercase letter generation, but uppercase.

    Examples:
        u         -> one uppercase letter A-Z
        u:4       -> 4 uppercase letters A-Z
        ua-f:2-4  -> 2 to 4 uppercase letters A-F

X[n]
    Random alphanumeric string of exactly n characters.
    Default is 1.

    Examples:
        X         -> 1 alphanumeric character
        X8        -> 8 alphanumeric characters

Z[n]
    Random alphanumeric string with length from 1 to n inclusive.
    Default is 1.

    Examples:
        Z         -> length 1
        Z12       -> length 1..12

F
    Random first name selected from a list of 100+ internationally friendly names.

L
    Random last name selected from a list of 100+ internationally friendly names.

N
    Random full name built from the first-name and last-name lists.

T[n]
    Random nonsense text up to n characters long.
    Default is 40.

    Examples:
        T         -> text up to 40 characters
        T80       -> text up to 80 characters

Examples
========

Using a single comma-separated spec string:
    python csvforge.py output.csv --rows 20 --spec "d,F,L,i18,f10-20:3,T60"

Using repeated --col arguments:
    python csvforge.py output.csv --rows 20 --col d --col F --col L --col i18 --col f10-20:3 --col T60

Using positional rows for backward compatibility:
    python csvforge.py output.csv 20 --spec "d,F,L,u:3,X8,T40"

Notes
=====
- --rows is the preferred way to specify the row count.
- A positional rows argument is still supported for backward compatibility.
- If both are provided, --rows takes precedence.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import string
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple


FIRST_NAMES: List[str] = [
    "Aarav", "Aaliyah", "Adam", "Adriana", "Aiko", "Aisha", "Alejandro", "Alex",
    "Alina", "Amara", "Amir", "Ana", "Andre", "Anika", "Aria", "Ariya", "Arjun",
    "Asher", "Aya", "Bao", "Beatriz", "Bilal", "Camila", "Carlos", "Carmen",
    "Chloe", "Daniel", "Daria", "David", "Diego", "Elias", "Elena", "Eli",
    "Ella", "Emil", "Emma", "Ethan", "Eva", "Farah", "Fatima", "Felix", "Gabriel",
    "Grace", "Hana", "Hassan", "Hiro", "Hugo", "Ibrahim", "Ines", "Isaac", "Isla",
    "Ivan", "Jamal", "Javier", "Jiho", "Jonah", "Joseph", "Julia", "Kai", "Karim",
    "Katarina", "Kenji", "Laila", "Leila", "Leo", "Liam", "Lina", "Lucia", "Luca",
    "Luis", "Maja", "Malik", "Mara", "Mateo", "Maya", "Mei", "Mia", "Mila",
    "Mina", "Mira", "Mohamed", "Naomi", "Nathan", "Nia", "Nina", "Noah", "Nora",
    "Omar", "Oscar", "Pavel", "Priya", "Rafael", "Rania", "Ravi", "Rei", "Rina",
    "Roman", "Sami", "Sara", "Sofia", "Sora", "Stefan", "Talia", "Theo", "Tomoko",
    "Valentina", "Victor", "Yara", "Yasmin", "Yousef", "Zara", "Zoe", "Amina",
    "Noemi", "Rosa", "Elio", "Samir", "Layla", "Nikolai", "Adele", "Leonie"
]

LAST_NAMES: List[str] = [
    "Abadi", "Ahmed", "Alonso", "Anders", "Aoki", "Baba", "Bakker", "Barbieri",
    "Basu", "Becker", "Bennett", "Bianchi", "Borges", "Brown", "Cabrera", "Cano",
    "Castro", "Chen", "Costa", "Cruz", "Davis", "Diaz", "Dlamini", "Dubois",
    "Edwards", "Elahi", "Fabbri", "Farah", "Fernandes", "Fischer", "Flores",
    "Garcia", "Gonzalez", "Gupta", "Haddad", "Hansen", "Hasan", "Hernandez",
    "Hossain", "Ibrahim", "Ivanov", "Jaber", "Jackson", "Jensen", "Johansson",
    "Kaur", "Khan", "Kim", "Kovacs", "Kowalski", "Kumar", "Lam", "Larsen",
    "Lee", "Lopez", "Martin", "Martinez", "Meyer", "Miller", "Mohamed", "Morales",
    "Mori", "Muller", "Nakamura", "Nguyen", "Nielsen", "Okafor", "Oliveira",
    "Omar", "Ortega", "Patel", "Pereira", "Petrov", "Popov", "Rahman", "Ramos",
    "Reyes", "Rossi", "Sanchez", "Sato", "Schmidt", "Shah", "Silva", "Singh",
    "Soto", "Tanaka", "Taylor", "Thomas", "Torres", "Usman", "Valdez", "Vega",
    "Wagner", "Wang", "Weber", "Williams", "Wong", "Yamada", "Yilmaz", "Young",
    "Zhang", "Ali", "Souza", "Marin", "Nowak", "Bauer", "Klein",
    "Navarro", "Pires", "Romero", "Saidi", "Tahiri", "Vieira", "Yoon", "Zoric"
]

WORDS: List[str] = [
    "amber", "apple", "atlas", "bamboo", "banner", "beacon", "berry", "blue",
    "bridge", "breeze", "candle", "cedar", "circle", "cloud", "comet", "copper",
    "coral", "crystal", "dawn", "delta", "echo", "ember", "field", "forest",
    "garden", "glow", "gold", "grain", "harbor", "horizon", "island", "jade",
    "jungle", "lake", "lantern", "leaf", "linen", "lunar", "marble", "meadow",
    "melon", "mist", "morning", "mosaic", "mountain", "nova", "oak", "ocean",
    "olive", "opal", "orchard", "paper", "pearl", "pine", "planet", "plaza",
    "pond", "prairie", "quartz", "quiet", "rain", "raven", "river", "rose",
    "saffron", "sage", "sand", "shadow", "silver", "sky", "snow", "solar",
    "song", "spring", "star", "stone", "stream", "summer", "sunset", "tea",
    "thunder", "tiger", "timber", "violet", "wave", "willow", "wind", "winter",
    "wood", "yard", "zen", "aurora", "cobalt", "drift", "elm", "fable", "gale"
]


@dataclass
class ColumnGenerator:
    """
    Represent a compiled generator for one column spec.

    Attributes:
        spec: The original column specification string.
        generator: A callable that accepts the zero-based row index and
            returns the generated cell value as a string.
    """

    spec: str
    generator: Callable[[int], str]


def parse_int(value: str) -> int:
    """
    Convert a string to an integer.

    Args:
        value: A string representing an integer.

    Returns:
        The parsed integer.

    Example:
        parse_int("12") -> 12
    """
    return int(value)


def split_csv_spec(spec_string: str) -> List[str]:
    """
    Split a comma-separated spec string into individual trimmed specs.

    Args:
        spec_string: A comma-separated list of column specs.

    Returns:
        A list of non-empty, stripped specification strings.

    Example:
        split_csv_spec("d,F,L,i10")
        -> ["d", "F", "L", "i10"]
    """
    parts: List[str] = [part.strip() for part in spec_string.split(",")]
    return [part for part in parts if part]


def parse_letter_range(part: Optional[str]) -> Tuple[str, str]:
    """
    Parse the optional letter range used by lowercase or uppercase letter specs.

    Supported forms:
        None     -> a-z
        a        -> a-z
        n        -> n-z
        a-f      -> a-f
        n-m      -> n-m

    Args:
        part: The optional letter-range fragment.

    Returns:
        A tuple of (start_letter, end_letter), both lowercase.

    Raises:
        ValueError: If the letter range is invalid.

    Examples:
        parse_letter_range(None)   -> ("a", "z")
        parse_letter_range("a")    -> ("a", "z")
        parse_letter_range("n")    -> ("n", "z")
        parse_letter_range("c-f")  -> ("c", "f")
    """
    if not part:
        return "a", "z"

    normalized: str = part.lower()

    if "-" in normalized:
        left, right = normalized.split("-", 1)
        if len(left) != 1 or len(right) != 1 or not left.isalpha() or not right.isalpha():
            raise ValueError(f"Invalid letter range: {part}")
        return left, right

    if len(normalized) == 1 and normalized.isalpha():
        return normalized, "z"

    raise ValueError(f"Invalid letter range: {part}")


def parse_length_range(part: Optional[str], default_exact: int = 1) -> Tuple[int, int]:
    """
    Parse the optional length component used in letter specs.

    Supported forms:
        None   -> default_exact, default_exact
        3      -> 3, 3
        2-5    -> 2, 5

    Args:
        part: The optional length fragment after ':'.
        default_exact: Exact default length when omitted.

    Returns:
        A tuple of (min_length, max_length).

    Raises:
        ValueError: If the parsed length values are invalid.

    Examples:
        parse_length_range(None)    -> (1, 1)
        parse_length_range("3")     -> (3, 3)
        parse_length_range("2-5")   -> (2, 5)
    """
    if not part:
        return default_exact, default_exact

    if "-" in part:
        left, right = part.split("-", 1)
        min_len: int = parse_int(left)
        max_len: int = parse_int(right)
    else:
        min_len = parse_int(part)
        max_len = min_len

    if min_len < 1 or max_len < 1 or min_len > max_len:
        raise ValueError(f"Invalid length range: {part}")

    return min_len, max_len


def random_letters(start: str, end: str, min_len: int, max_len: int, uppercase: bool = False) -> str:
    """
    Generate a random sequence of letters from an inclusive letter range.

    Args:
        start: Starting letter, inclusive.
        end: Ending letter, inclusive.
        min_len: Minimum number of letters to generate.
        max_len: Maximum number of letters to generate.
        uppercase: Whether to uppercase the generated result.

    Returns:
        A string of random letters.

    Raises:
        ValueError: If the letter range is invalid.

    Examples:
        random_letters("a", "f", 3, 3) -> "bce"
        random_letters("n", "z", 2, 4, uppercase=True) -> "QW"
    """
    start_ord: int = ord(start.lower())
    end_ord: int = ord(end.lower())

    if start_ord > end_ord:
        raise ValueError(f"Invalid letter range: {start}-{end}")

    alphabet: List[str] = [chr(code) for code in range(start_ord, end_ord + 1)]
    length: int = random.randint(min_len, max_len)
    result: str = "".join(random.choice(alphabet) for _ in range(length))

    if uppercase:
        return result.upper()
    return result


def random_alnum(length: int) -> str:
    """
    Generate a random alphanumeric string of exact length.

    Args:
        length: Exact number of characters to generate.

    Returns:
        A random alphanumeric string.

    Raises:
        ValueError: If length is less than 1.

    Example:
        random_alnum(5) -> "A9x2Q"
    """
    if length < 1:
        raise ValueError("Alphanumeric length must be at least 1")

    chars: str = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def random_text(max_chars: int) -> str:
    """
    Generate nonsense text up to a maximum number of characters.

    The function combines simple word fragments until enough content exists,
    then trims the result to a random target length from 1 to max_chars.

    Args:
        max_chars: Maximum allowed output length.

    Returns:
        A random text string whose length is between 1 and max_chars.

    Raises:
        ValueError: If max_chars is less than 1.

    Example:
        random_text(20) -> "cedar echo mist"
    """
    if max_chars < 1:
        raise ValueError("Text length must be at least 1")

    target_len: int = random.randint(1, max_chars)
    pieces: List[str] = []

    while len(" ".join(pieces)) < target_len:
        pieces.append(random.choice(WORDS))

    candidate: str = " ".join(pieces)[:target_len].rstrip()

    if not candidate:
        candidate = random.choice(WORDS)[:target_len]

    return candidate


def build_generator(spec: str) -> ColumnGenerator:
    """
    Compile a single column spec into a row-aware generator function.

    Args:
        spec: The column specification string.

    Returns:
        A ColumnGenerator object containing the original spec and a callable.

    Raises:
        ValueError: If the specification is not recognized or invalid.

    Examples:
        build_generator("d")
        build_generator("i10")
        build_generator("u:4")
        build_generator("N")
    """
    cleaned_spec: str = spec.strip()

    if not cleaned_spec:
        raise ValueError("Empty column spec is not allowed")

    if cleaned_spec == "F":
        return ColumnGenerator(
            spec=cleaned_spec,
            generator=lambda _row: random.choice(FIRST_NAMES),
        )

    if cleaned_spec == "L":
        return ColumnGenerator(
            spec=cleaned_spec,
            generator=lambda _row: random.choice(LAST_NAMES),
        )

    if cleaned_spec == "N":
        return ColumnGenerator(
            spec=cleaned_spec,
            generator=lambda _row: f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        )

    match: Optional[re.Match[str]]

    match = re.fullmatch(r"d(\d+)?", cleaned_spec)
    if match:
        start_value: int = 1 if match.group(1) is None else parse_int(match.group(1))

        def generate_ascending(row_index: int, start: int = start_value) -> str:
            """
            Generate an ascending numeric sequence value for the given row.

            Args:
                row_index: Zero-based row index.
                start: Starting sequence value.

            Returns:
                The generated sequence value as a string.
            """
            return str(start + row_index)

        return ColumnGenerator(spec=cleaned_spec, generator=generate_ascending)

    match = re.fullmatch(r"D(\d+)?", cleaned_spec)
    if match:
        start_value = 1 if match.group(1) is None else parse_int(match.group(1))

        def generate_descending(row_index: int, start: int = start_value) -> str:
            """
            Generate a descending numeric sequence value for the given row.

            Args:
                row_index: Zero-based row index.
                start: Starting sequence value.

            Returns:
                The generated sequence value as a string.
            """
            return str(start - row_index)

        return ColumnGenerator(spec=cleaned_spec, generator=generate_descending)

    match = re.fullmatch(r"i(?:(\d+)(?:-(\d+))?)?", cleaned_spec)
    if match:
        if match.group(1) is None:
            min_value: int = 1
            max_value: int = 9
        elif match.group(2) is None:
            min_value = 0
            max_value = parse_int(match.group(1))
        else:
            min_value = parse_int(match.group(1))
            max_value = parse_int(match.group(2))

        if min_value > max_value:
            raise ValueError(f"Invalid integer range in spec: {cleaned_spec}")

        def generate_integer(_row: int, low: int = min_value, high: int = max_value) -> str:
            """
            Generate a random integer string.

            Args:
                _row: Unused row index.
                low: Inclusive lower bound.
                high: Inclusive upper bound.

            Returns:
                A random integer as a string.
            """
            return str(random.randint(low, high))

        return ColumnGenerator(spec=cleaned_spec, generator=generate_integer)

    match = re.fullmatch(r"f(?:(\d+)(?:-(\d+))?)?(?::(\d+))?", cleaned_spec)
    if match:
        if match.group(1) is None:
            min_value_f: float = 1.0
            max_value_f: float = 9.0
        elif match.group(2) is None:
            min_value_f = 0.0
            max_value_f = float(parse_int(match.group(1)))
        else:
            min_value_f = float(parse_int(match.group(1)))
            max_value_f = float(parse_int(match.group(2)))

        if min_value_f > max_value_f:
            raise ValueError(f"Invalid float range in spec: {cleaned_spec}")

        decimals: int = 2 if match.group(3) is None else parse_int(match.group(3))
        if decimals < 0:
            raise ValueError(f"Invalid decimal precision in spec: {cleaned_spec}")

        def generate_float(
            _row: int,
            low: float = min_value_f,
            high: float = max_value_f,
            decimal_places: int = decimals
        ) -> str:
            """
            Generate a formatted random float string.

            Args:
                _row: Unused row index.
                low: Inclusive lower bound.
                high: Inclusive upper bound.
                decimal_places: Number of decimal places to render.

            Returns:
                A formatted float string.
            """
            value: float = random.uniform(low, high)
            return f"{value:0.{decimal_places}f}"

        return ColumnGenerator(spec=cleaned_spec, generator=generate_float)

    match = re.fullmatch(r"l([a-z](?:-[a-z])?)?(?::(\d+(?:-\d+)?))?", cleaned_spec, flags=re.IGNORECASE)
    if match:
        letter_part: Optional[str] = match.group(1)
        length_part: Optional[str] = match.group(2)
        start_letter, end_letter = parse_letter_range(letter_part)
        min_len, max_len = parse_length_range(length_part, default_exact=1)

        def generate_lowercase_letters(
            _row: int,
            start: str = start_letter,
            end: str = end_letter,
            min_length: int = min_len,
            max_length: int = max_len
        ) -> str:
            """
            Generate random lowercase letters.

            Args:
                _row: Unused row index.
                start: Inclusive start letter.
                end: Inclusive end letter.
                min_length: Minimum number of letters.
                max_length: Maximum number of letters.

            Returns:
                A lowercase random-letter string.
            """
            return random_letters(start, end, min_length, max_length, uppercase=False)

        return ColumnGenerator(spec=cleaned_spec, generator=generate_lowercase_letters)

    match = re.fullmatch(r"u([a-z](?:-[a-z])?)?(?::(\d+(?:-\d+)?))?", cleaned_spec, flags=re.IGNORECASE)
    if match:
        letter_part = match.group(1)
        length_part = match.group(2)
        start_letter, end_letter = parse_letter_range(letter_part)
        min_len, max_len = parse_length_range(length_part, default_exact=1)

        def generate_uppercase_letters(
            _row: int,
            start: str = start_letter,
            end: str = end_letter,
            min_length: int = min_len,
            max_length: int = max_len
        ) -> str:
            """
            Generate random uppercase letters.

            Args:
                _row: Unused row index.
                start: Inclusive start letter.
                end: Inclusive end letter.
                min_length: Minimum number of letters.
                max_length: Maximum number of letters.

            Returns:
                An uppercase random-letter string.
            """
            return random_letters(start, end, min_length, max_length, uppercase=True)

        return ColumnGenerator(spec=cleaned_spec, generator=generate_uppercase_letters)

    match = re.fullmatch(r"X(\d+)?", cleaned_spec)
    if match:
        length_x: int = 1 if match.group(1) is None else parse_int(match.group(1))

        def generate_fixed_alnum(_row: int, length: int = length_x) -> str:
            """
            Generate a fixed-length alphanumeric string.

            Args:
                _row: Unused row index.
                length: Exact output length.

            Returns:
                A random alphanumeric string.
            """
            return random_alnum(length)

        return ColumnGenerator(spec=cleaned_spec, generator=generate_fixed_alnum)

    match = re.fullmatch(r"Z(\d+)?", cleaned_spec)
    if match:
        max_length_z: int = 1 if match.group(1) is None else parse_int(match.group(1))

        def generate_variable_alnum(_row: int, max_length: int = max_length_z) -> str:
            """
            Generate a variable-length alphanumeric string.

            Args:
                _row: Unused row index.
                max_length: Maximum output length.

            Returns:
                A random alphanumeric string with length in the range 1..max_length.
            """
            chosen_length: int = random.randint(1, max_length)
            return random_alnum(chosen_length)

        return ColumnGenerator(spec=cleaned_spec, generator=generate_variable_alnum)

    match = re.fullmatch(r"T(\d+)?", cleaned_spec)
    if match:
        max_chars_t: int = 40 if match.group(1) is None else parse_int(match.group(1))

        def generate_text(_row: int, max_chars: int = max_chars_t) -> str:
            """
            Generate random nonsense text up to the given character limit.

            Args:
                _row: Unused row index.
                max_chars: Maximum allowed output length.

            Returns:
                A random text fragment.
            """
            return random_text(max_chars)

        return ColumnGenerator(spec=cleaned_spec, generator=generate_text)

    raise ValueError(f"Unrecognized column spec: {cleaned_spec}")


def write_csv(output_path: str, row_count: int, generators: Sequence[ColumnGenerator]) -> None:
    """
    Write generated CSV data to disk.

    Args:
        output_path: Destination path for the CSV file.
        row_count: Number of data rows to generate.
        generators: Sequence of compiled column generators.

    Returns:
        None

    Example:
        write_csv("sample.csv", 10, generators)
    """
    headers: List[str] = [f"col{index}" for index in range(1, len(generators) + 1)]

    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)

        for row_index in range(row_count):
            row: List[str] = [generator.generator(row_index) for generator in generators]
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Preferred usage:
        python csvforge.py output.csv --rows 100 --spec "d,F,L,i10"

    Backward-compatible usage:
        python csvforge.py output.csv 100 --spec "d,F,L,i10"

    Returns:
        Parsed argparse namespace.
    """
    parser = argparse.ArgumentParser(
        description="Generate a CSV file from a compact column specification."
    )

    parser.add_argument(
        "output",
        help="Path to the output CSV file."
    )

    parser.add_argument(
        "rows_positional",
        nargs="?",
        type=int,
        help="Optional positional row count. Retained for backward compatibility."
    )

    parser.add_argument(
        "--rows",
        dest="rows_option",
        type=int,
        help="Preferred row-count option."
    )

    parser.add_argument(
        "--col",
        action="append",
        default=[],
        help="Add one column spec. May be used multiple times."
    )

    parser.add_argument(
        "--spec",
        help='Comma-separated column spec string, for example: "d,F,L,i10,f2-5:3,T40"'
    )

    parser.add_argument(
        "--seed",
        type=int,
        help="Optional random seed for reproducible output."
    )

    return parser.parse_args()


def resolve_row_count(args: argparse.Namespace) -> int:
    """
    Resolve the effective row count from CLI arguments.

    Resolution order:
        1. --rows
        2. positional rows
        3. default of 10

    Args:
        args: Parsed CLI arguments.

    Returns:
        Effective row count.

    Raises:
        ValueError: If the resolved row count is negative.

    Example:
        If --rows 25 is given, returns 25.
        If only positional 25 is given, returns 25.
        If neither is given, returns 10.
    """
    if args.rows_option is not None:
        row_count: int = args.rows_option
    elif args.rows_positional is not None:
        row_count = args.rows_positional
    else:
        row_count = 10

    if row_count < 0:
        raise ValueError("Row count must be 0 or greater")

    return row_count


def collect_specs(args: argparse.Namespace) -> List[str]:
    """
    Collect all requested column specs from --spec and repeated --col options.

    Args:
        args: Parsed CLI arguments.

    Returns:
        A list of column spec strings.

    Raises:
        ValueError: If no column specs were provided.

    Example:
        --spec "d,F,L" --col i10
        -> ["d", "F", "L", "i10"]
    """
    specs: List[str] = []

    if args.spec:
        specs.extend(split_csv_spec(args.spec))

    if args.col:
        specs.extend([item.strip() for item in args.col if item.strip()])

    if not specs:
        raise ValueError("You must provide at least one column spec using --col and/or --spec")

    return specs


def main() -> int:
    """
    Program entry point.

    This function:
    1. Parses arguments
    2. Resolves the row count
    3. Seeds the random generator if requested
    4. Compiles the column specs
    5. Writes the CSV file

    Returns:
        Process exit code 0 on success.

    Example:
        python csvforge.py output.csv --rows 20 --spec "d,F,L,u:3,T40"
    """
    args = parse_args()
    row_count: int = resolve_row_count(args)

    if args.seed is not None:
        random.seed(args.seed)

    specs: List[str] = collect_specs(args)
    generators: List[ColumnGenerator] = [build_generator(spec) for spec in specs]

    write_csv(args.output, row_count, generators)

    print(f"Wrote {row_count} rows and {len(generators)} columns to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
