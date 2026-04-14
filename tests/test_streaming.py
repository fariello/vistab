import unittest
from vistab import Vistab, ArraySizeError
from typing import Iterator

class TestVistabStreamAndJagged(unittest.TestCase):
    
    def test_jagged_arrays_default(self):
        """Test that default jagged array handling appropriately pads and truncates."""
        table = Vistab(header=False)
        table.has_header = False
        table.on_short_row = "pad"
        table.on_long_row = "truncate"
        
        # Row 1 determines width mapping
        table.add_row(["Col1", "Col2", "Col3"])
        
        # Row 2 is short
        table.add_row(["A", "B"])
        
        # Row 3 is long
        table.add_row(["X", "Y", "Z", "EXTRA1", "EXTRA2"])
        
        metrics = table.get_structural_metrics()
        self.assertEqual(metrics["padded"], 1)
        self.assertEqual(metrics["truncated"], 1)
        
        out = table.draw()
        
        # Ensure row 2 padded. Since it has 3 structural cells, drawing doesn't fail.
        self.assertTrue(bool(out))
        
    def test_strict_grid_error(self):
        """Test strict grid mappings raising."""
        table = Vistab(header=False)
        table.has_header = False
        table.on_short_row = "raise"
        table.on_long_row = "raise"
        
        table.add_row(["A", "B"])
        
        with self.assertRaises(ArraySizeError):
            table.add_row(["1"])
            
    def test_native_stream(self):
        """Test yielding infinite string loop mechanically."""
        table = Vistab(header=False)
        table.has_header = False
        iterable = [
            ["Row1A", "Row1B"],
            ["Row2A", "Row2B"],
            ["Row3A", "Row3B"]
        ]
        
        lines = list(table.stream(iterable, sample_size=1))
        
        # Stream contains top border, 3 rows (which may have separating hlines mapped)
        output = "\n".join(lines)
        self.assertIn("Row1A", output)
        self.assertIn("Row3B", output)
        
    def test_stream_max_rows(self):
        """Test parsing infinite iterables capping correctly with max-rows."""
        def infinite_generator():
            i = 0
            while True:
                yield [f"Data{i}", f"Info{i}"]
                i += 1
                
        table = Vistab(header=False)
        table.has_header = False
        table.set_max_rows(5)
        
        lines = list(table.stream(infinite_generator(), sample_size=2))
        
        output = "\n".join(lines)
        
        # Output should truncate iterating
        self.assertIn("Data4", output)
        self.assertNotIn("Data5", output)
        
if __name__ == '__main__':
    unittest.main()
