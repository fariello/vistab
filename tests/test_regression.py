import unittest
import subprocess
import os
from pathlib import Path
from vistab import Vistab

class TestVistabRegression(unittest.TestCase):
    """
    Regression testing framework that captures CLI execution payloads
    and compares them against baseline gold-master ASCII structures.
    """
    
    def setUp(self):
        self.tests_dir = Path(__file__).parent.absolute()
        self.data_dir = self.tests_dir / "data"
        self.fixtures_dir = self.tests_dir / "fixtures"
        self.cli_path = self.tests_dir.parent / "src" / "vistab.py"
        
        # Ensure fixtures directory exists safely
        os.makedirs(self.fixtures_dir, exist_ok=True)

    def _run_cli(self, args: list, input_data: str = None) -> str:
        """Executes the CLI and returns the unified STDOUT."""
        cmd = ["python", str(self.cli_path)] + args
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            input=input_data,
            encoding="utf-8"
        )
        return result.stdout

    def _assert_against_fixture(self, name: str, output: str):
        """
        Validates output against a saved fixture. 
        If the fixture does not exist, it bootstraps it natively!
        """
        fixture_path = self.fixtures_dir / f"{name}.txt"
        
        if not fixture_path.exists():
            with open(fixture_path, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"\n[BOOTSTRAP] Created new regression fixture: {fixture_path.name}")
            return
            
        with open(fixture_path, "r", encoding="utf-8") as f:
            expected = f.read()
            
        self.assertEqual(
            output, 
            expected, 
            f"Regression failed! Output for '{name}' does not match the strict baseline."
        )

    def test_regression_small_default(self):
        """Test default output for a standard small dataset."""
        db = self.data_dir / "small_5x5.csv"
        out = self._run_cli([str(db)])
        self._assert_against_fixture("regression_small_default", out)

    def test_regression_complex_theme(self):
        """Test a heavily parameterized thematic dataset output."""
        db = self.data_dir / "small_7x12.csv"
        args = [
            str(db), 
            "--theme", "ocean-index", 
            "--align", "c",
            "--width", "60",
            "--table-bg-color", "bright_black"
        ]
        out = self._run_cli(args)
        self._assert_against_fixture("regression_complex_theme", out)
        
    def test_regression_diagnostic_matrix(self):
        """Safeguard structural matrix calculations implicitly testing rendering offsets natively."""
        out = self._run_cli(["-M"])
        self._assert_against_fixture("regression_diagnostic_matrix", out)

    def test_regression_pipeline_stdin(self):
        """Test the structural execution capturing datasets strictly through STDIN streams."""
        raw_csv_string = "ID,Name,Status\n101,Process A,Active\n102,Process B,Failed\n"
        out = self._run_cli(["--theme", "ocean", "--padding", "2"], input_data=raw_csv_string)
        self._assert_against_fixture("regression_pipeline_stdin", out)

    def test_regression_pipeline_multi_file(self):
        """Test the sequential CLI resolution targeting multiple physical files iteratively."""
        db1 = self.data_dir / "small_1x1.csv"
        db2 = self.data_dir / "small_5x5.csv"
        
        # Pass multiple paths explicitly
        out = self._run_cli([str(db1), str(db2), "--style", "bold"])
        self._assert_against_fixture("regression_pipeline_multi_file", out)

    def test_regression_api_dynamic_typing(self):
        """Test API directly for strict layout boundaries using dynamic typings."""
        table = Vistab(style="round2")
        table.set_title("API Regression Data")
        table.set_cols_dtype(["t", "f", "i", "e"])
        table.set_precision(3)
        table.set_cols_align(["l", "r", "c", "r"])
        
        table.add_rows([
            ["String", "Float", "Int", "Scientific"],
            ["Measurement A", 456.12356, 10.45, 0.0000000045],
            ["Measurement B", 12.3, 0.0, 4.2e-5]
        ])
        
        out = table.draw()
        self._assert_against_fixture("regression_api_dynamic_typing", out)

    def test_regression_api_theme_dictionary(self):
        """Test the explicit API custom_theme parameter structure natively."""
        custom_theme = {
            "style": "heavy",
            "padding": 2,
            "decorations": 11,
            "table": {"bg": "bright_black"},
            "col_0": {"bg": "blue"},
            "col_-1": {"bg": "red"},
            "row_-1": {"fg": "black", "bg": "white"}
        }
        
        table = Vistab().apply_theme(custom_theme)
        table.add_rows([
            ["Index", "Metric", "Status"],
            ["1", "45ms", "OK"],
            ["2", "120ms", "DELAY"],
            ["3", "12ms", "OK"]
        ])
        
        out = table.draw()
        self._assert_against_fixture("regression_api_theme_dictionary", out)

if __name__ == '__main__':
    unittest.main()
