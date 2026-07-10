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
        
        # Overwrite non-empty cell raises ValueError
        with self.assertRaises(ValueError):
            table2.set_header_span(0, 2)
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


if __name__ == '__main__':
    unittest.main()
