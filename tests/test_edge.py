import unittest
import io
from vistab import Vistab, ArraySizeError

class TestEdge(unittest.TestCase):
    def test_on_short_pad(self):
        """Test missing element padding resolution."""
        table = Vistab()
        table.on_short_row = "pad"
        table.set_cols_dtype(['t', 'i', 't'])
        table.add_rows([
            ["A", "B", "C"],
            ["1", "2"] # Missing 3rd boundary
        ])
        
        table.add_row(["1"]) # Missing 2nd and 3rd boundaries
        out = table.draw()
        self.assertIn("A", out)

    def test_on_short_skip(self):
        """Test missing elements skipped entirely dropping physical rows."""
        table = Vistab()
        table.on_short_row = "skip"
        table.add_rows([
            ["A", "B", "C"],
            ["1", "2"] # Missing logic
        ])
        out = table.draw()
        self.assertNotIn("1", out) # Dropped by skip handler

    def test_on_short_raise(self):
        """Test missing elements raising errors."""
        table = Vistab()
        table.on_short_row = "raise"
        table.add_rows([["A", "B", "C"]])
        with self.assertRaises(ArraySizeError):
            table.add_rows([["1", "2"]])

    def test_on_long_truncate(self):
        """Test overflow elements truncated."""
        table = Vistab()
        table.on_long_row = "truncate"
        table.add_rows([
            ["A", "B"],
            ["1", "2", "3"]
        ])
        out = table.draw()
        self.assertNotIn("3", out) # 3 should be dropped because matrix is 2 cols 

    def test_on_long_skip(self):
        """Test overflow elements skipped."""
        table = Vistab()
        table.on_long_row = "skip"
        table.add_rows([
            ["A", "B"],
            ["1", "2", "3"]
        ])
        out = table.draw()
        self.assertNotIn("1", out) # Entire row dropped by skip
        
    def test_on_long_raise(self):
        """Test overflow elements raising bounds."""
        table = Vistab()
        table.on_long_row = "raise"
        table.add_rows([["A", "B"]])
        with self.assertRaises(ArraySizeError):
            table.add_rows([["1", "2", "3"]])

    def test_word_chunking_core(self):
        """Test mathematical break logic resolving huge contiguous block bounds safely."""
        from vistab import ColorAwareWrapper
        wrapper = ColorAwareWrapper()
        
        long_word = "AAAAAAAAAAAAAAAAAAAA" # length 20
        res = wrapper.wrap(long_word, width=5)
        self.assertEqual(len(res.splitlines()), 4)
        
        # Test ANSI chunking boundary mapping!
        ansi_long_word = "\033[1;31mAAAAA\033[0m\033[42mBBBBB\033[0m"
        res = wrapper.wrap(ansi_long_word, width=5)
        lines = res.splitlines()
        self.assertEqual(len(lines), 2)
        # Asserts inner sequences intercept context bounding closures
        self.assertIn("\033[0m", lines[0])
        self.assertIn("\033[42m", lines[1])

if __name__ == '__main__':
    unittest.main()
