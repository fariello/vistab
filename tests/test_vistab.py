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


if __name__ == '__main__':
    unittest.main()
