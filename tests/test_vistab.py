import unittest
from vistab import Vistab, StringLengthCalculator, ColorAwareWrapper

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

if __name__ == '__main__':
    unittest.main()
