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
        for style in ["ascii", "bold", "double", "light", "none"]:
            with self.subTest(style=style):
                table = Vistab(style=style)
                table.add_rows([["A", "B"], ["1", "2"]])
                out = table.draw()
                self.assertIsNotNone(out)

if __name__ == '__main__':
    unittest.main()
