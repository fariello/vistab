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

    def test_dimensions_limit(self):
        """Test limiting tables dynamically explicitly enforcing dimensions."""
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
        """Test numeric and string datatypes formatting natively."""
        table = Vistab(style="none")
        table.set_cols_dtype(["t", "i", "f"])
        table.set_precision(2)
        table.add_rows([["Text", "Int", "Float"], ["ABC", 50.55, 3.14159]])
        
        out = table.draw()
        self.assertIn("51", out)     # Int evaluates and rounds correctly (50.55 -> 51)
        self.assertIn("3.14", out)   # Precision formats float
        
    def test_auto_dtype_inferences(self):
        """Test cascading data type inference for automatic bounds correctly formatting floats/sci explicitly over ints."""
        table = Vistab(style="none")
        table.set_precision(3)
        # Testing Mixed Decimal Inference
        table.add_rows([
            ["3.0", "1.5", "101"], 
            ["12", "1.2e-4", "202"], 
            ["5", "10", "303"]
        ], header=False)
        out = table.draw()
        
        # Column 0: Mixed whole numbers and explicitly parsed floats (3.0 vs 12). Should all be Floats (.000)
        self.assertIn("3.000", out)
        self.assertIn("12.000", out)
        self.assertIn("5.000", out)
        
        # Column 1: Mixed explicit scientific notation (1.2e-4) vs floats (1.5). Should all be Scientific!
        self.assertIn("1.500e+00", out)
        self.assertIn("1.200e-04", out)
        
        # Column 2: Pure integers logically exclusively. Should format exactly as purely string integers cleanly!
        self.assertIn("101", out)
        self.assertIn("202", out)
        self.assertIn("303", out)
        self.assertNotIn("101.000", out)
        
    def test_layout_modifiers(self):
        """Test structural colors applying cleanly within the ANSI boundaries."""
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

if __name__ == '__main__':
    unittest.main()
