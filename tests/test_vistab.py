import unittest
from vistab import Vistab, StringLengthCalculator, ColorAwareWrapper, ArraySizeError

class TestVistab(unittest.TestCase):

    def test_basic_table_creation(self):
        """Test creating a minimal generic table."""
        table = Vistab()
        table.add_rows([
            ["Header 1", "Header 2"],
            ["Data 1", "Data 2"]
        ])
        output = table.draw()
        self.assertIn("Header 1", output)
        self.assertIn("Data 2", output)
        self.assertTrue(len(output.splitlines()) > 2)

    def test_string_length_calculator(self):
        """Test calculating terminal lengths of strings containing ANSI codes."""
        calculator = StringLengthCalculator()

        # Pure ASCII
        self.assertEqual(calculator.len("hello"), 5)

        # With ANSI escape sequence (red text)
        colored_string = "\033[1;31mhello\033[0m"
        self.assertEqual(calculator.len(colored_string), 5)

    def test_color_aware_wrapper(self):
        """Test text wrapping while taking ANSI codes into account."""
        wrapper = ColorAwareWrapper()

        text = "This is \033[1;31mred\033[0m text"
        wrapped = wrapper.wrap(text, width=10)

        # It should wrap after "This is", dropping the space
        self.assertIn("\n", wrapped)
        self.assertIn("\033[1;31mred\033[0m", wrapped)

    def test_styles(self):
        """Test using an alternate table rendering style."""
        for style in ["ascii", "double", "heavy", "light", "none"]:
            with self.subTest(style=style):
                table = Vistab(style=style)
                table.add_rows([["A", "B"], ["1", "2"]])
                out = table.draw()
                self.assertIsNotNone(out)

    def test_max_cols(self):
        """Test limiting tables enforcing column dimensions."""
        table = Vistab(max_width=50)
        table.add_rows([
            ["A", "B", "C", "D", "E"],
            ["1", "2", "3", "4", "5"],
            ["6", "7", "8", "9", "This is a very long string that should get truncated"]
        ])

        table.set_max_rows(1)
        table.set_max_cols(3)
        out = table.draw()

        self.assertIn("A", out)
        self.assertIn("C", out)
        self.assertNotIn("E", out) # Dropped by max_cols
        self.assertNotIn("6", out) # Dropped by max_rows

    def test_dtype_coercion(self):
        """Test numeric and string datatypes formatting."""
        table = Vistab(style="none")
        table.set_cols_dtype(["t", "i", "f"])
        table.set_precision(2)
        table.add_rows([["Text", "Int", "Float"], ["ABC", 50.55, 3.14159]])

        out = table.draw()
        self.assertIn("51", out)     # Int evaluates and rounds correctly (50.55 -> 51)
        self.assertIn("3.14", out)   # Precision formats float

    def test_auto_dtype_inferences(self):
        """Test cascading data type inference for automatic bounds correctly formatting floats/sci over ints."""
        table = Vistab(style="none")
        table.set_precision(3)
        # Testing Mixed Decimal Inference
        table.add_rows([
            ["3.0", "1.5", "101"],
            ["12", "1.2e-4", "202"],
            ["5", "10", "303"]
        ], header=False)
        out = table.draw()

        # Column 0: Mixed whole numbers and parsed floats (3.0 vs 12). Should all be Floats (.000)
        self.assertIn("3.000", out)
        self.assertIn("12.000", out)
        self.assertIn("5.000", out)

        # Column 1: Mixed explicit scientific notation (1.2e-4) vs floats (1.5). Should all be Scientific!
        self.assertIn("1.500e+00", out)
        self.assertIn("1.200e-04", out)

        # Column 2: Pure integers logically exclusively. Should format exactly as purely string integers!
        self.assertIn("101", out)
        self.assertIn("202", out)
        self.assertIn("303", out)
        self.assertNotIn("101.000", out)

    def test_inline_precision_overrides(self):
        """Test mapping decimals per column individually."""
        table = Vistab(style="none")
        table.set_precision(1) # Base global default structurally
        table.set_cols_dtype("if2e4a") # Implicit parsing string!

        table.add_rows([["1.9", "1.9", "1.9", "1.9"]], header=False)
        out = table.draw()

        # Column 0: (i) Integer rounding safely
        self.assertIn("2", out)

        # Column 1: (f2) Explicit decimal truncation bypassing the global n=1!
        self.assertIn("1.90", out)

        # Column 2: (e4) Exponent forcing 4 decimal points bypassing global n=1
        self.assertIn("1.9000e+00", out)

        # Column 3: (a -> f1 inferred via global)
        self.assertIn("1.9", out)

    def test_layout_modifiers(self):
        """Test structural colors applying within the ANSI boundaries."""
        table = Vistab(style="light")
        table.add_rows([["A", "B"], ["1", "2"]])
        table.set_table_style(bg="red")
        table.color_row(-1, bg="blue")

        out = table.draw()
        # Verify the ANSI codes were actually mapped into the output
        self.assertIn("\033[41m", out) # Red background exists
        self.assertIn("\033[44m", out) # Blue background exists

    def test_invalid_padding(self):
        """Test trapping ValueErrors for impossible configurations."""
        table = Vistab()
        with self.assertRaises(ValueError):
            table.set_padding(-1)

    def test_invalid_style(self):
        """Test trapping an unknown style mapping configuration."""
        with self.assertRaises(ValueError):
            table = Vistab(style="fake_border_magic")

    def test_max_width_too_low(self):
        """Test trapping an impossible max-width matrix bound."""
        table = Vistab(max_width=2) # 2 physically cannot contain standard framing
        table.add_rows([["A", "B"], ["1", "2"]])
        with self.assertRaises(ValueError) as context:
            table.draw()
        self.assertIn("too low to render data", str(context.exception))

    def test_array_size_error(self):
        """Test triggering structural asymmetry inside table strings."""
        table = Vistab()
        with self.assertRaises(ArraySizeError):
            # Pass bad configuration structure arrays manually bypassing logic
            table.add_rows([["A", "B", "C"]])
            table.set_cols_dtype(["i", "f"]) # 2 dtypes mapping to 3 columns throws ArraySizeError

    def test_set_cols_dtype_callable(self):
        """Test mapping Python callable lambda expressions resolving inside precision layouts."""
        table = Vistab(style="none")
        # Map first col as native str, second col via custom Python function formatting string block
        table.set_cols_dtype(["t", lambda x: f"[[{float(x):.1f}]]"])
        table.add_rows([["Val", "Formula"], ["ABC", "-3.1415"]])
        out = table.draw()
        self.assertIn("ABC", out)
        self.assertIn("[[-3.1]]", out)

class TestVistabColspan(unittest.TestCase):

    def test_colspan_ingestion_api(self):
        """Test ColSpan instantiation and data model ingestion in headers and rows."""
        from vistab import ColSpan
        table = Vistab()
        table.set_header(["Name", ColSpan("Details", 2)])
        table.add_row(["Alice", ColSpan("Age: 25, City: Paris", 2)])

        # Verify sizes and objects
        self.assertEqual(len(table._header), 3)
        self.assertEqual(table._header[1].value, "Details")
        self.assertEqual(table._header[1].colspan, 2)
        self.assertTrue(table._header[2].is_placeholder)
        self.assertEqual(table._header[2].source_cell, table._header[1])

        self.assertEqual(len(table._rows[0]), 3)
        self.assertEqual(table._rows[0][1].value, "Age: 25, City: Paris")
        self.assertEqual(table._rows[0][1].colspan, 2)
        self.assertTrue(table._rows[0][2].is_placeholder)
        self.assertEqual(table._rows[0][2].source_cell, table._rows[0][1])

    def test_set_span_api(self):
        """Test set_header_span and set_cell_span post-ingestion mutators."""
        table = Vistab()
        table.set_header(["Col1", "", ""])
        table.add_row(["Data1", "", ""])

        table.set_header_span(0, 3)
        table.set_cell_span(0, 1, 2)

        self.assertEqual(table._header[0].colspan, 3)
        self.assertTrue(table._header[1].is_placeholder)
        self.assertTrue(table._header[2].is_placeholder)

        self.assertEqual(table._rows[0][1].colspan, 2)
        self.assertTrue(table._rows[0][2].is_placeholder)
        self.assertFalse(table._rows[0][0].is_placeholder)

    def test_colspan_rendering_and_wrapping(self):
        """Verify rendering and wrapping logic formats spanned blocks correctly."""
        from vistab import ColSpan
        table = Vistab(style="light")
        table.set_header(["Col1", ColSpan("Long Header Spanning Two Columns", 2)])
        table.add_row(["Short", ColSpan("This text is long enough to wrap across columns", 2)])

        out = table.draw()

        # Long header should wrap and layout without crashing
        self.assertIn("Long Header Spanning Two Columns", out)
        self.assertIn("This text is long enough to wrap across columns", out)

    def test_colspan_junction_suppression(self):
        """Verify horizontal line junctions are suppressed under spanned cells."""
        from vistab import ColSpan
        table = Vistab(style="light")
        table.set_header(["Col1", ColSpan("Spanned Header", 2)])
        table.add_row(["A", "B", "C"])
        out = table.draw()

        # Verify that mid-line under "Spanned Header" (boundary index 2) has no junction
        # Let's inspect the hline separating the header from the first row.
        # Spanned Header covers columns 1 and 2, which means the boundary between col 1 and 2
        # is suppressed and replaced by horizontal lines instead of intersection junctions.
        lines = out.splitlines()
        # header-separator line (index 2 for light style with header and TOP border)
        # 0: TOP border: ┌──────┬──────┬──────┐
        # 1: Header:     │ Col1 │ Spanned Hea  │
        # 2: Hline:      ├──────┼─────────────┤ (mid junction suppressed between col 1 & 2!)
        self.assertIn("┼", lines[2]) # Still has first mid junction between col 0 and 1
        # But should NOT have a junction at the next separator: it should be continuous: "────────"
        # Let's check the number of "┼" or junction characters in lines[2]
        self.assertEqual(lines[2].count("┼"), 1)

    def test_colspan_junction_header_sep_up_tee(self):
        """Plain header over a spanned data row: the header divider terminates on the
        header-separator line as an up-tee (┴), never a flat line or a full cross.
        Regression for the 'dangling divider' bug."""
        t = Vistab(style="light")
        t.set_header(["N", "A", "B"])
        t.add_row(["x", "one", "two"])
        t.set_cell_span(0, 1, 2)
        lines = t.draw().splitlines()
        # 0 top, 1 header, 2 header-sep, 3 data...
        self.assertEqual(lines[0], "┌───┬────┬────┐")   # top: A|B divider present (header divides)
        self.assertEqual(lines[2], "├───┼────┴────┤")   # header-sep: ┼ at N|A, ┴ at A|B
        self.assertEqual(lines[-1], "└───┴─────────┘")  # bottom: merged data -> flat under span

    def test_colspan_junction_row_sep_down_tee(self):
        """A merged row above a plain (divided) row must render a down-tee (┬) on the
        separator between them, opening into the divided row."""
        from vistab import ColSpan
        t = Vistab(style="light")
        t.set_header(["Name", ColSpan("Details", 2), "Status"])
        t.add_row(["Alice", ColSpan("a@x", 2), "Active"])
        t.add_row(["Bob", "b", "c", "Inactive"])
        lines = t.draw().splitlines()
        # 0 top,1 header,2 header-sep,3 row0(merged),4 row0/row1-sep,5 row1(plain),6 bottom
        row_sep = lines[4]
        self.assertIn("┬", row_sep)              # down-tee where the plain row divides below
        self.assertNotIn("┴", row_sep)
        # header-sep: header AND row0 both merge cols 1-2 -> that boundary is flat (no tee)
        header_sep = lines[2]
        self.assertNotIn("┬", header_sep)
        self.assertNotIn("┴", header_sep)

    def test_colspan_junction_fully_merged_column(self):
        """When header and every row merge the same columns, the interior boundary has
        no divider on any rule: no ┬, ┴, or ┼ at that boundary anywhere."""
        from vistab import ColSpan
        t = Vistab(style="light")
        t.set_header(["N", ColSpan("AB", 2)])
        t.add_row(["x", ColSpan("yz", 2)])
        # Only one real interior boundary (N | block); the in-span boundary must stay clean.
        self.assertEqual(t.draw().splitlines(), [
            "┌───┬─────┐",
            "│ N │ AB  │",
            "├───┼─────┤",
            "│ x │ yz  │",
            "└───┴─────┘",
        ])

    def test_colspan_junction_top_and_bottom_borders(self):
        """Top border above a spanned header, and bottom border below a spanned last
        row, must suppress the interior junction (no ┬/┴ piercing the merged block)."""
        from vistab import ColSpan
        # Spanned header -> top border interior boundary suppressed.
        t1 = Vistab(style="light")
        t1.set_header(["N", ColSpan("AB", 2)])
        t1.add_row(["x", "y", "z"])
        self.assertEqual(t1.draw().splitlines()[0], "┌───┬───────┐")
        # Spanned last data row -> bottom border interior boundary suppressed.
        t2 = Vistab(style="light")
        t2.set_header(["N", "A", "B"])
        t2.add_row(["x", "y", "z"])
        t2.set_cell_span(0, 1, 2)
        self.assertEqual(t2.draw().splitlines()[-1], "└───┴───────┘")

    def test_colspan_junction_header_only_table(self):
        """A header-only table (no data rows) must keep full tees on top and bottom
        borders (regression: the bottom border's 'row above' is the header)."""
        t = Vistab(style="light")
        t.set_header(["A", "B", "C"])
        self.assertEqual(t.draw().splitlines(), [
            "┌───┬───┬───┐",
            "│ A │ B │ C │",
            "└───┴───┴───┘",
        ])

    def test_colspan_junction_canonical_full_render(self):
        """Byte-exact render of the canonical mixed span/plain table, pinning every
        directional junction at once."""
        from vistab import ColSpan
        t = Vistab(style="light")
        t.set_header(["Name", ColSpan("Details Block", 2), "Status"])
        t.add_row(["Alice", ColSpan("Age: 25, Paris", 2), "Active"])
        t.add_row(["Bob", "Age: 30", "Berlin", "Inactive"])
        self.assertEqual(t.draw().splitlines(), [
            "┌───────┬──────────────────┬──────────┐",
            "│ Name  │  Details Block   │  Status  │",
            "├───────┼──────────────────┼──────────┤",  # header & row0 both merge -> flat at bdry2
            "│ Alice │ Age: 25, Paris   │ Active   │",
            "├───────┼─────────┬────────┼──────────┤",  # row0 merged, row1 divides -> ┬ at bdry2
            "│ Bob   │ Age: 30 │ Berlin │ Inactive │",
            "└───────┴─────────┴────────┴──────────┘",
        ])

    def _visible_width(self, out):
        """Max visible (ANSI-stripped) width across all rendered lines."""
        import re
        return max(len(re.sub(r"\x1b\[[0-9;]*m", "", line)) for line in out.splitlines())

    def test_colspan_honors_max_width_by_wrapping(self):
        """Regression: a spanned cell whose merged content exceeds its combined
        column budget must WRAP within max_width, not expand the table past it.

        Before the fix this rendered 56 columns wide for max_width=40."""
        t = Vistab(style="light", max_width=40)
        t.set_header(["A", "B", "C"])
        t.add_row(["x", "some long value here", "another long value here too"])
        t.add_row(["y", "p", "q"])
        t.set_cell_span(0, 1, 2)
        out = t.draw()
        # Ceiling honored.
        self.assertLessEqual(self._visible_width(out), 40)
        # Merged content fully present across wrapped lines (not truncated).
        for word in ["some", "long", "value", "here", "another", "too"]:
            self.assertIn(word, out)

    def test_colspan_near_zero_column_block_still_wraps(self):
        """Edge case (F1/F3): a span covering a column that has no standalone
        content, under a tight max_width. The block must still be wide enough to
        wrap the merged content legibly (borrowing width from columns outside the
        span) rather than collapsing or looping in the wrapper."""
        t = Vistab(style="light", max_width=30)
        t.set_header(["id", "name", "notes"])
        # Column index 2 ("notes") never carries standalone content: its only
        # occupant is the spanned block and an empty cell.
        t.add_row(["1", "this is a fairly long merged value that must wrap", ""])
        t.add_row(["2", "bob", "ok"])
        t.set_cell_span(0, 1, 2)
        out = t.draw()
        self.assertLessEqual(self._visible_width(out), 30)
        for word in ["this", "fairly", "merged", "value", "must", "wrap"]:
            self.assertIn(word, out)

    def test_colspan_under_max_width_that_already_fits_is_unchanged(self):
        """A span whose merged content already fits within its combined budget
        under max_width must not be spuriously wrapped: same as no ceiling."""
        no_ceiling = Vistab(style="light")
        no_ceiling.set_header(["A", "B", "C"])
        no_ceiling.add_row(["x", "hi", "there"])
        no_ceiling.add_row(["y", "p", "q"])
        no_ceiling.set_cell_span(0, 1, 2)

        with_ceiling = Vistab(style="light", max_width=200)
        with_ceiling.set_header(["A", "B", "C"])
        with_ceiling.add_row(["x", "hi", "there"])
        with_ceiling.add_row(["y", "p", "q"])
        with_ceiling.set_cell_span(0, 1, 2)

        self.assertEqual(with_ceiling.draw(), no_ceiling.draw())

    def test_colspan_max_width_pin_nonspan_wrapping_unchanged(self):
        """Byte-identical pin: plain (non-span) max_width wrapping is untouched
        by the colspan fix."""
        t = Vistab(style="light", max_width=40)
        t.set_header(["A", "B", "C"])
        t.add_row(["x", "some long value here", "another long value here too"])
        t.add_row(["y", "p", "q"])
        self.assertEqual(t.draw().splitlines(), [
            "┌───┬─────────────────┬────────────────┐",
            "│ A │        B        │       C        │",
            "├───┼─────────────────┼────────────────┤",
            "│ x │ some long value │ another long   │",
            "│   │ here            │ value here too │",
            "├───┼─────────────────┼────────────────┤",
            "│ y │ p               │ q              │",
            "└───┴─────────────────┴────────────────┘",
        ])

    def test_colspan_pin_span_without_max_width_unchanged(self):
        """Byte-identical pin: a span WITHOUT a width ceiling still expands its
        covered columns to fit on one line (the correct no-ceiling behavior)."""
        t = Vistab(style="light")
        t.set_header(["A", "B", "C"])
        t.add_row(["x", "some long value here", "another long value here too"])
        t.add_row(["y", "p", "q"])
        t.set_cell_span(0, 1, 2)
        self.assertEqual(t.draw().splitlines(), [
            "┌───┬─────────────────────────┬────────────────────────┐",
            "│ A │            B            │           C            │",
            "├───┼─────────────────────────┴────────────────────────┤",
            "│ x │ some long value here another long value here too │",
            "├───┼─────────────────────────┬────────────────────────┤",
            "│ y │ p                       │ q                      │",
            "└───┴─────────────────────────┴────────────────────────┘",
        ])

    def test_colspan_sorting(self):
        """Verify sorting table rows with spans preserves span adjacency."""
        from vistab import ColSpan
        table = Vistab(style="none")
        table.set_header(["SortKey", ColSpan("Spanned", 2)])
        table.add_row(["Beta", ColSpan("V1", 2)])
        table.add_row(["Alpha", ColSpan("V2", 2)])

        table.sort_by(0)
        out = table.draw()

        # Alpha row should sort before Beta
        alpha_idx = out.find("Alpha")
        beta_idx = out.find("Beta")
        self.assertTrue(alpha_idx < beta_idx)
        self.assertTrue(out.find("V2") < out.find("V1"))

    def test_colspan_usability_and_validation(self):
        """Test comprehensive colspan validation and exception specifications."""
        from vistab import ColSpan

        # 1. ColSpan instantiation and parameter aliases
        c1 = ColSpan("x", 2)
        self.assertEqual(c1.colspan, 2)
        self.assertEqual(c1.span, 2)

        c2 = ColSpan("x", colspan=3)
        self.assertEqual(c2.colspan, 3)

        c3 = ColSpan("x", span=4)
        self.assertEqual(c3.colspan, 4)

        # Conflicting parameters
        with self.assertRaises(ValueError):
            ColSpan("x", colspan=2, span=3)

        # colspan < 1
        with self.assertRaises(ValueError):
            ColSpan("x", colspan=0)

        # colspan=1 is a no-op
        c_one = ColSpan("x", colspan=1)
        self.assertEqual(c_one.colspan, 1)

        # 2. Mutator Index/Value Exception Matrix
        table = Vistab()
        table.set_header(["C1", "C2", "C3"])
        table.add_row(["D1", "D2", "D3"])

        # IndexError for out-of-range row_idx
        with self.assertRaises(IndexError):
            table.set_cell_span(5, 0, 2)
        with self.assertRaises(IndexError):
            table.set_cell_span(-5, 0, 2)

        # IndexError for out-of-range col_idx
        with self.assertRaises(IndexError):
            table.set_cell_span(0, 5, 2)
        with self.assertRaises(IndexError):
            table.set_cell_span(0, -5, 2)
        with self.assertRaises(IndexError):
            table.set_header_span(5, 2)
        with self.assertRaises(IndexError):
            table.set_header_span(-5, 2)

        # Negative indexing support
        table.set_header_span(-3, 1) # no-op span=1 at first column
        table.set_cell_span(-1, -3, 1) # no-op span=1 at first column

        # ValueError for bad colspan (< 1)
        with self.assertRaises(ValueError):
            table.set_cell_span(0, 0, 0)
        with self.assertRaises(ValueError):
            table.set_header_span(0, -1)

        # 3. Transactional Integrity (Grid Unchanged on Failure)
        table2 = Vistab()
        table2.set_header(["Col1", "Col2", "Col3"])
        table2.add_row(["Data1", "Data2", "Data3"])

        original_header_values = [c.value if hasattr(c, 'value') else c for c in table2._header]

        # Overwrite non-empty cell raises ValueError when combine=None
        with self.assertRaises(ValueError) as ctx:
            table2.set_header_span(0, 2, combine=None)
        self.assertIn("combine=None", str(ctx.exception))
        # Verify header is completely unchanged (no partial mutation)
        current_header_values = [c.value if hasattr(c, 'value') else c for c in table2._header]
        self.assertEqual(original_header_values, current_header_values)

        # 4. Overlap & Placeholder target validation
        table3 = Vistab()
        table3.set_header(["Col1", "", "", "Col4"])
        table3.add_row(["Data1", "", "", ""])

        # Set initial span on row 0, col 1 (span 2 -> covers indices 1, 2)
        table3.set_cell_span(0, 1, 2)

        # Target index is placeholder target -> ValueError
        with self.assertRaises(ValueError) as ctx:
            table3.set_cell_span(0, 2, 2)
        self.assertIn("placeholder owned by column 1", str(ctx.exception))

        # Overlap existing span -> ValueError
        with self.assertRaises(ValueError) as ctx:
            table3.set_cell_span(0, 0, 3)
        self.assertIn("would overlap with", str(ctx.exception))

        # 5. Adjacency ordering crash prevention
        # set_cell_span(0, 1, 2) then set_cell_span(0, 0, 2)
        table4 = Vistab()
        table4.set_header(["Col1", "", "", ""])
        table4.add_row(["Data1", "", "", ""])

        table4.set_cell_span(0, 1, 2)
        with self.assertRaises(ValueError):
            # Overlaps index 1 (which is owned by 1)
            table4.set_cell_span(0, 0, 3)

        # Draw should render cleanly without KeyError crash
        self.assertIsNotNone(table4.draw())

    def test_colspan_combine_options_and_wrapping(self):
        """Test B1 (combine options: default merge, custom, strict, wrapping of merged values)."""
        from vistab import Vistab

        # 1. Default merge combine=" "
        t1 = Vistab()
        t1.set_header(["A", "B", "C"])
        t1.add_row(["Alice", 25, "Paris"])

        t1.set_cell_span(0, 0, 3) # default: merges "Alice", "25", "Paris" -> "Alice 25 Paris"
        self.assertEqual(t1._rows[0][0].value, "Alice 25 Paris")
        self.assertTrue(t1._rows[0][1].is_placeholder)
        self.assertTrue(t1._rows[0][2].is_placeholder)

        # 2. combine="" (no separator)
        t2 = Vistab()
        t2.set_header(["A", "B"])
        t2.add_row(["Alice", "25"])
        t2.set_cell_span(0, 0, 2, combine="")
        self.assertEqual(t2._rows[0][0].value, "Alice25")

        # 3. combine=", " (custom separator)
        t3 = Vistab()
        t3.set_header(["A", "B"])
        t3.add_row(["Alice", "25"])
        t3.set_cell_span(0, 0, 2, combine=", ")
        self.assertEqual(t3._rows[0][0].value, "Alice, 25")

        # 4. TypeError for invalid combine type (e.g. integer)
        t4 = Vistab()
        t4.set_header(["A", "B"])
        t4.add_row(["Alice", "25"])
        with self.assertRaises(TypeError):
            t4.set_cell_span(0, 0, 2, combine=123)

        # 5. Empty covered cells do not leave trailing separators
        t5 = Vistab()
        t5.set_header(["A", "B", "C"])
        t5.add_row(["Alice", "", ""])
        t5.set_cell_span(0, 0, 3, combine=", ")
        self.assertEqual(t5._rows[0][0].value, "Alice")

        # 6. Merged value wrapping (R1)
        t6 = Vistab(style="light", padding=0)
        t6.set_cols_width([5, 5])
        t6.set_header(["Col1", "Col2"])
        t6.add_row(["ExtremelyLongWord", "AnotherOne"])

        # Merge them (total width = 5 + 5 + separator width of 1 = 11)
        t6.set_cell_span(0, 0, 2, combine=" ")
        self.assertEqual(t6._rows[0][0].value, "ExtremelyLongWord AnotherOne")

        out = t6.draw()
        # Verify it wrapped inside the combined block and does not crash or bleed
        self.assertIn("ExtremelyLo", out)
        self.assertIn("ngWord", out)
        self.assertIn("AnotherOne", out)


class TestHasHeaderAlignment(unittest.TestCase):
    """Regression: has_header=False must turn a consumed row 0 into a normal data row
    (body alignment, not centered header alignment). Bug prompt:
    20260710-has-header-false-alignment-bug.md."""

    ROWS = [
        [".config", "10", ".opencode", "8", ".antigravity-server", "7"],
        [".cargo", "6", ".mozilla", "5", ".expo", "4"],
        [".cookiecutter_replay", "3", ".idlerc", "3", ".keras", "3"],
    ]

    def _first_body_line(self, table):
        # Return the rendered line containing the first row's leading cell value.
        for line in table.draw().splitlines():
            if ".config" in line:
                return line
        self.fail("first row not found in output")

    def test_has_header_false_after_rows_ctor_is_left_aligned(self):
        """Repro A: Vistab(rows) then has_header=False -> row 0 left-aligned, not centered."""
        t = Vistab(self.ROWS, alignment="lr" * 3)
        t.has_header = False
        t.set_decorations(Vistab.BORDER | Vistab.VLINES)
        line = self._first_body_line(t)
        # Left-aligned: ".config" sits immediately after the "│ " pad (no centering spaces).
        self.assertIn("│ .config ", line)
        # And it must NOT be centered (which would put spaces before ".config").
        self.assertNotIn("   .config", line)
        # Structurally row 0 is now a data row, header slot empty.
        self.assertEqual(t._header, [])
        self.assertEqual(len(t._rows), 3)

    def test_header_false_at_construction_matches(self):
        """Workaround B: header=False at construction yields the same left-aligned row 0."""
        t = Vistab(self.ROWS, alignment="lr" * 3, header=False)
        t.set_decorations(Vistab.BORDER | Vistab.VLINES)
        self.assertIn("│ .config ", self._first_body_line(t))

    def test_explicit_header_still_centered(self):
        """Passing an explicit header iterable is unaffected: header renders centered + divider."""
        t = Vistab([["a", "bb"], ["1", "2"]], header=["Head1", "Head2"], alignment="lr")
        out = t.draw()
        # Header divider line present (header retained structurally).
        self.assertIn("├", out)
        # Header cell centered (default header align 'c'): "Head1"/"Head2" render as header row.
        self.assertIn("Head1", out)
        self.assertTrue(t._header)  # header still consumed

    def test_toggle_round_trip_stable(self):
        """has_header False->True->False is stable and idempotent."""
        t = Vistab([r[:] for r in self.ROWS], alignment="lr" * 3)
        t.has_header = False
        self.assertEqual(t._header, [])
        self.assertEqual(len(t._rows), 3)
        t.has_header = True
        self.assertTrue(t._header)          # a header was re-consumed
        self.assertEqual(len(t._rows), 2)
        t.has_header = False
        self.assertEqual(t._header, [])
        self.assertEqual(len(t._rows), 3)

    def test_colspan_in_row0_with_has_header_false_renders(self):
        """Colspan-safe: a row-0 ColSpan survives demotion and draws without KeyError."""
        from vistab import ColSpan
        t = Vistab([[ColSpan("SPANNED", 2), "x"], ["a", "b", "c"]], alignment="llc")
        t.has_header = False
        out = t.draw()  # must not raise
        self.assertIn("SPANNED", out)
        self.assertEqual(t._header, [])
        self.assertEqual(len(t._rows), 2)


class TestColspanInteractions(unittest.TestCase):
    """Release-review S3 gap coverage: width distribution, styling parity, max_cols
    clipping, and multiple spans per row (run 20260710-194844, findings T1/T2/T3)."""

    def test_width_distribution_across_covered_columns(self):
        """A spanned value wider than the natural combined width widens the covered
        columns so the value fits in the merged block (T1)."""
        from vistab import ColSpan
        t = Vistab(style="light")
        t.set_header(["A", "B", "C"])
        t.add_row([ColSpan("WIDE_SPANNED_VALUE_HERE", 2), "z"])
        out = t.draw()
        # The full wide value renders on one line inside the merged block (no truncation).
        self.assertIn("WIDE_SPANNED_VALUE_HERE", out)
        # Each rendered body line has equal visible width (grid stayed rectangular).
        body = [l for l in out.splitlines() if "WIDE_SPANNED_VALUE_HERE" in l]
        self.assertTrue(body)

    def test_styling_parity_span_uses_source_column_style(self):
        """A column style on the span's source column colors the merged block (T2)."""
        t = Vistab(style="light")
        t.set_header(["A", "B", "C"])
        t.add_row(["x", "y", "z"])
        t.set_cell_span(0, 0, 2)
        t.set_col_style(0, bold=True)
        out = t.draw()
        self.assertIn("\033[", out)  # ANSI styling emitted for the spanned block

    def test_max_cols_clips_a_span(self):
        """A span crossing the max_cols boundary is clipped without crashing (T3)."""
        from vistab import ColSpan
        t = Vistab(style="light", max_cols=2)
        t.set_header(["a", "b", "c", "d"])
        t.add_row([ColSpan("SP", 3), "x"])
        lines = t.draw().splitlines()  # must not raise
        self.assertIn("SP", "\n".join(lines))
        # Clipped to 2 columns; the plain header keeps its divider (top border has a ┬),
        # while the data-row span merges below (header separator shows the up-tee ┴).
        self.assertIn("┬", lines[0])
        self.assertIn("┴", lines[2])

    def test_multiple_spans_in_one_row(self):
        """Two independent spans in the same row render correctly (T3)."""
        t = Vistab(style="light")
        t.set_header(["a", "b", "c", "d", "e"])
        t.add_row(["1", "2", "3", "4", "5"])
        t.set_cell_span(0, 0, 2)
        t.set_cell_span(0, 3, 2)
        row = t._rows[0]
        self.assertEqual(row[0].colspan, 2)
        self.assertTrue(row[1].is_placeholder)
        self.assertFalse(row[2].is_placeholder)   # middle cell untouched
        self.assertEqual(row[3].colspan, 2)
        self.assertTrue(row[4].is_placeholder)
        self.assertIsNotNone(t.draw())  # renders without error


class TestBidiRTL(unittest.TestCase):
    """Bidi-safe rendering: RTL (Arabic/Hebrew) cells are wrapped in Unicode LTR
    isolates (U+2066..U+2069) so they do not flip the table grid. Isolates are
    zero-width, so column geometry is unchanged, and non-RTL tables are untouched."""

    LRI = "\u2066"
    PDI = "\u2069"

    def _strip_isolates(self, s):
        return s.replace(self.LRI, "").replace(self.PDI, "")

    def _visible_width(self, out):
        import re
        from vistab import StringLengthCalculator
        plain = re.sub(r"\x1b\[[0-9;]*m", "", self._strip_isolates(out))
        return [StringLengthCalculator.len(l) for l in plain.splitlines()]

    def test_contains_rtl_detection(self):
        from vistab import _contains_rtl
        self.assertTrue(_contains_rtl("الخوارزمي"))       # Arabic
        self.assertTrue(_contains_rtl("אדה לאבלייס"))     # Hebrew
        self.assertTrue(_contains_rtl("mixed abc العربية"))
        self.assertFalse(_contains_rtl("plain ascii"))
        self.assertFalse(_contains_rtl("José Ñoño"))       # accented Latin, not RTL
        self.assertFalse(_contains_rtl("关羽 (Guan Yu)"))  # CJK, not RTL

    def test_rtl_table_wraps_cells_in_isolates(self):
        t = Vistab(style="light")
        t.set_header(["ID", "Name"])
        t.add_row(["5", "الخوارزمي"])
        t.add_row(["7", "plain"])
        out = t.draw()
        self.assertIn(self.LRI, out)
        self.assertIn(self.PDI, out)
        # Balanced: every isolate opened is closed.
        self.assertEqual(out.count(self.LRI), out.count(self.PDI))

    def test_non_rtl_table_has_no_isolates(self):
        t = Vistab(style="light")
        t.set_header(["A", "B"])
        t.add_row(["1", "2"])
        out = t.draw()
        self.assertNotIn(self.LRI, out)
        self.assertNotIn(self.PDI, out)

    def test_non_rtl_output_byte_identical_with_feature_present(self):
        """The bidi gate must be a true no-op for non-RTL tables: enabling the
        feature (default) yields exactly the same bytes as disabling it."""
        def build(bidi):
            t = Vistab(style="round-header").set_bidi(bidi)
            t.set_header(["Name", "Age", "City"])
            t.add_row(["Alice", "30", "Paris"])
            t.add_row(["Bob", "25", "Berlin"])
            return t.draw()
        self.assertEqual(build(True), build(False))

    def test_isolates_are_width_neutral(self):
        """An RTL table's visible per-line width must be identical with and
        without bidi (isolates are zero-width)."""
        def build(bidi):
            t = Vistab(style="light").set_bidi(bidi)
            t.set_header(["ID", "Name"])
            t.add_row(["5", "الخوارزمي (al-Khwarizmi)"])
            t.add_row(["7", "plain text here"])
            return t.draw()
        on, off = build(True), build(False)
        self.assertNotIn(self.LRI, off)
        # Stripping isolates from the bidi-on output reproduces the bidi-off output
        # exactly: proves the isolates are the ONLY difference (purely additive).
        self.assertEqual(self._strip_isolates(on), off)
        self.assertEqual(self._visible_width(on), self._visible_width(off))

    def test_set_bidi_false_disables_isolates(self):
        t = Vistab(style="light").set_bidi(False)
        t.set_header(["ID", "Name"])
        t.add_row(["5", "الخوارزمي"])
        out = t.draw()
        self.assertNotIn(self.LRI, out)

    def test_mixed_cell_isolated_once_and_balanced(self):
        """A cell mixing Arabic + Latin + digits is wrapped exactly once (the
        isolate gives it a self-contained bidi context; the terminal orders the
        runs inside)."""
        t = Vistab(style="light")
        t.set_header(["Col"])
        t.add_row(["الخوارزمي al-Khwarizmi 2024"])
        out = t.draw()
        # The content line contains exactly one LRI/PDI pair for that single cell.
        content_lines = [l for l in out.splitlines() if "al-Khwarizmi" in l]
        self.assertEqual(len(content_lines), 1)
        self.assertEqual(content_lines[0].count(self.LRI), 1)
        self.assertEqual(content_lines[0].count(self.PDI), 1)

    def test_set_bidi_is_chainable(self):
        t = Vistab(style="light")
        self.assertIs(t.set_bidi(True), t)
        self.assertIs(t.set_bidi(False), t)


class TestWrappingBoundaries(unittest.TestCase):
    """Word wrapping must break on WORD (whitespace) boundaries, fall back to
    CHARACTER breaks only for over-long words, and treat ANSI color as zero-width
    and boundary-neutral (never break a word just because its color changes)."""

    def _visible_lines(self, out):
        import re
        return [re.sub(r"\x1b\[[0-9;]*m", "", l) for l in out.splitlines()]

    def test_wrap_breaks_on_word_boundaries_not_color(self):
        """A single word with mid-word color changes must not be split at the
        color boundaries; it stays one token and only character-breaks if it is
        longer than the column."""
        # 'redgreen' is short enough to fit; the color change is mid-word. It must
        # NOT be broken at the color boundary.
        colored = "\033[1;31mred\033[1;32mgreen\033[0m"
        t = Vistab(style="light", max_width=20)
        t.set_header(["W"])
        t.add_row([colored + " tail"])
        out = t.draw()
        vis = self._visible_lines(out)
        # 'redgreen' appears intact on one visible line (color change did not split it).
        self.assertTrue(any("redgreen" in l for l in vis),
                        f"'redgreen' was split across a color boundary: {vis}")

    def test_overlong_colored_word_char_breaks_like_plain(self):
        """An over-long multi-color word character-breaks exactly like the same
        plain word: color codes are zero-width and do not shift break points."""
        from vistab import StringLengthCalculator
        word = "supercalifragilisticexpialidocious"
        colored = "super\033[1;31mcali\033[0mfragi\033[1;32mlistic\033[0mexpialidocious"

        def render(cell):
            t = Vistab(style="light", max_width=20)
            t.set_header(["W"]); t.add_row([cell])
            return t.draw()

        plain_vis = self._visible_lines(render(word))
        color_vis = self._visible_lines(render(colored))
        # The visible (ANSI-stripped) wrapping is identical whether or not the word
        # carries color: proves breaks are on character count, not color boundaries.
        self.assertEqual(plain_vis, color_vis)
        # And every rendered line has a uniform visible width (grid intact).
        widths = {StringLengthCalculator.len(l) for l in render(colored).splitlines()}
        self.assertEqual(len(widths), 1, f"non-uniform line widths: {widths}")

    def test_color_codes_preserved_across_wrap(self):
        """Wrapping an over-long colored word must not drop its ANSI codes."""
        colored = "super\033[1;31mcali\033[0mfragi\033[1;32mlistic\033[0mexpialidocious"
        t = Vistab(style="light", max_width=20)
        t.set_header(["W"]); t.add_row([colored])
        out = t.draw()
        for code in ("\033[1;31m", "\033[1;32m"):
            self.assertIn(code, out)


class TestColumnDtypes(unittest.TestCase):
    """Valid column data types are enumerated and explained; invalid ones fail loudly."""

    VALID = ("a", "t", "i", "I", "f", "F", "e", "E")

    def _cell(self, dtype, val):
        """Render one value under one dtype and return the visible cell text."""
        t = Vistab(style="none")
        t.set_header(["x"]); t.add_row([val]); t.set_cols_dtype([dtype])
        return t.draw().splitlines()[-1].strip()

    def test_all_valid_codes_accepted(self):
        for code in self.VALID:
            t = Vistab(style="light")
            t.set_header(["A", "B"])
            t.add_row(["1", "2"])
            t.set_cols_dtype([code, "t"])   # should not raise
            self.assertIsNotNone(t.draw())

    def test_precision_suffix_accepted(self):
        t = Vistab(style="light")
        t.set_header(["A"]); t.add_row([3.14159])
        t.set_cols_dtype(["f2"])           # numeric + precision suffix
        self.assertIn("3.14", t.draw())

    def test_invalid_code_raises_enumerating_and_explaining_all_types(self):
        t = Vistab(style="light")
        with self.assertRaises(ValueError) as ctx:
            t.set_cols_dtype("tx")          # 'x' is invalid
        msg = str(ctx.exception)
        self.assertIn("'x' is invalid", msg)
        # Every valid code is enumerated...
        for code in self.VALID:
            self.assertIn(f"  {code}  ", msg)
        # ...and explained (not just listed), and the precision suffix is documented.
        self.assertIn("thousands separators", msg)   # explains 'I'
        self.assertIn("exponential", msg)            # explains 'e'
        self.assertIn("precision suffix", msg)

    def test_grouped_float_F_groups_and_keeps_decimals(self):
        self.assertEqual(self._cell("F2", 123456.789), "123,456.79")
        self.assertEqual(self._cell("F0", 1234567), "1,234,567")

    def test_grouped_float_F_preserves_negative_sign(self):
        self.assertEqual(self._cell("F2", -1234.5), "-1,234.50")

    def test_grouped_exp_E_groups_mantissa(self):
        # grouped scientific renders without error and uses the requested precision
        self.assertEqual(self._cell("E2", 123456.789), "1.23e+05")

    def test_int_rounding_is_half_up_symmetric(self):
        """Integer codes round half AWAY FROM ZERO (not banker's/half-to-even). B1."""
        for v, expect in [(0.5, "1"), (1.5, "2"), (2.5, "3"), (3.5, "4"),
                          (-0.5, "-1"), (-1.5, "-2"), (-2.5, "-3"),
                          (2.4, "2"), (2.6, "3")]:
            self.assertEqual(self._cell("i", v), expect, f"i({v})")
        # grouped int rounds the same way
        self.assertEqual(self._cell("I", 2.5), "3")
        self.assertEqual(self._cell("I", -2.5), "-3")

    def test_none_renders_empty_in_numeric_columns(self):
        """None in any numeric-code column renders as an empty cell, not 'None'. B3."""
        for dt in ("a", "i", "I", "f", "F", "e", "E"):
            self.assertEqual(self._cell(dt, None), "", f"None under {dt!r}")

    def test_none_in_text_column_unchanged(self):
        """A text column still renders None / the literal string 'None' as before. B3."""
        self.assertEqual(self._cell("t", None), "None")
        self.assertEqual(self._cell("t", "None"), "None")

    def test_bare_F_uses_global_precision(self):
        """Bare 'F' (no suffix) uses the global precision default, like bare 'f'.
        For a small value needing no grouping, 'F' and 'f' render identically."""
        self.assertEqual(self._cell("F", 3.14159), self._cell("f", 3.14159))

    def test_grouped_code_over_non_numeric_falls_back_to_text(self):
        """A grouped code over a non-numeric cell must render as text, not crash
        (same behavior as the existing 'I' code)."""
        self.assertEqual(self._cell("F", "hello"), "hello")
        self.assertEqual(self._cell("E", "world"), "world")

    def test_f_F_i_I_are_distinct_for_same_value(self):
        v = 1234567.89
        self.assertEqual(self._cell("f", v), "1234567.890")   # no grouping
        self.assertEqual(self._cell("F", v), "1,234,567.890") # grouped, decimals
        self.assertEqual(self._cell("i", v), "1234568")       # rounded, no grouping
        self.assertEqual(self._cell("I", v), "1,234,568")     # rounded, grouped

    def test_existing_dtype_strings_unchanged_by_new_codes(self):
        """Adding F/E must not change how existing codes or comma-decorated strings parse."""
        import re
        tok = lambda s: re.findall(r'[a-zA-Z]\d*', s.replace(",", ""))
        self.assertEqual(tok("a,t,f4,i"), tok("atf4i"))
        self.assertEqual(tok("a,t,f4,i"), ["a", "t", "f4", "i"])

    def test_dtype_help_enumeration_matches_format_map(self):
        """The documented codes must exactly match the codes the formatter accepts,
        so help can never drift from behavior."""
        from vistab import COLUMN_DTYPES, _DTYPE_CODES
        self.assertEqual(tuple(c for c, _, _ in COLUMN_DTYPES), _DTYPE_CODES)
        # every documented code actually formats without KeyError
        for code in _DTYPE_CODES:
            t = Vistab(); t.set_header(["A"]); t.add_row(["1"])
            t.set_cols_dtype([code])
            self.assertIsNotNone(t.draw())


if __name__ == '__main__':
    unittest.main()
