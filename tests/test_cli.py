import unittest
from unittest.mock import patch, MagicMock
import sys
import io
import os
from vistab import Vistab

class TestCLI(unittest.TestCase):
    def setUp(self):
        # Create a dummy CSV file to test with
        self.test_csv = "dummy_test_data.csv"
        with open(self.test_csv, "w", encoding="utf-8") as f:
            f.write("Name,Age,Score\nGabriel,25,99\nAlice,30,88\nBob,40,77\n")

    def tearDown(self):
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)
        if os.path.exists("dummy_config.toml"):
            os.remove("dummy_config.toml")

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'dummy_test_data.csv'])
    def test_basic_file_parsing(self, mock_stdout):
        import vistab
        vistab.main()
        output = mock_stdout.getvalue()
        self.assertIn("Name", output)
        self.assertIn("Gabriel", output)
        self.assertIn("Alice", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'dummy_test_data.csv', '--style', 'ascii', '--padding', '0'])
    def test_cli_styling_arguments(self, mock_stdout):
        import vistab
        vistab.main()
        output = mock_stdout.getvalue()
        self.assertIn("+-", output)  # ascii border char
        # Check padding mapping
        self.assertIn("|Name|Age|Score|", output.replace(" ", ""))

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'dummy_test_data.csv', '--style', 'invalid_style_name'])
    def test_cli_invalid_style_exit(self, mock_stderr):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 1)
        self.assertIn("Unknown layout style", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'dummy_test_data.csv', '--align', 'l'])
    def test_cli_invalid_format_mapping(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 1)
        self.assertIn("[COMMAND-LINE FORMAT ERROR]", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'dummy_test_data.csv', '--sort-by', '1', '--sort-reverse'])
    def test_cli_sorting_logic(self, mock_stdout):
        import vistab
        vistab.main()
        output = mock_stdout.getvalue()
        # Ensure age 40 comes before 25 and 30 visually
        lines = output.splitlines()
        bob_idx, alice_idx, gab_idx = -1, -1, -1
        for i, line in enumerate(lines):
            if "Bob" in line: bob_idx = i
            elif "Alice" in line: alice_idx = i
            elif "Gabriel" in line: gab_idx = i
        
        self.assertTrue(bob_idx < alice_idx < gab_idx)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.stdin', io.StringIO("A,B\n1,2\n3,4"))
    @patch('sys.argv', ['vistab', '--stream'])
    def test_cli_streaming(self, mock_stdout):
        import vistab
        # Monkeypatch sys.stdin.isatty to False so vistab thinks it's a pipe
        with patch('sys.stdin.isatty', return_value=False):
            vistab.main()
        
        output = mock_stdout.getvalue()
        self.assertIn("A", output)
        self.assertIn("3", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', '--create-config', 'dummy_config.toml'])
    def test_cli_create_config(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertTrue(os.path.exists('dummy_config.toml'))
        with open('dummy_config.toml', 'r') as f:
            content = f.read()
            self.assertIn("padding = 1", content)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'dummy_test_data.csv', '--show-code'])
    def test_cli_show_code(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("import vistab", output)
        self.assertIn("custom_theme =", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'dummy_test_data.csv', '--dtype', 't,f2,f4'])
    def test_cli_dtype_precisions(self, mock_stdout):
        # We know "dummy_test_data.csv" -> ["Gabriel", "25", "99"]
        # Column 0: (t) Text -> 'Gabriel'
        # Column 1: (f2) Float mapped to 2 decimals -> '25.00'
        # Column 2: (f4) Float mapped to 4 decimals -> '99.0000'
        import vistab
        vistab.main()
        output = mock_stdout.getvalue()
        self.assertIn("Gabriel", output)
        self.assertIn("25.00", output)
        self.assertNotIn("25.000", output)
        self.assertIn("99.0000", output)

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab']) # No valid input string
    def test_cli_empty_stream_exit(self, mock_stderr):
        import vistab
        # If sys.stdin.isatty() is True, it will exit
        if sys.stdin.isatty():
            with self.assertRaises(SystemExit) as e:
                vistab.main()
            self.assertEqual(e.exception.code, 1)
            self.assertIn("No tabular dataset found", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'dummy_test_data.csv', '--style', 'round-header', '--save-theme', 'testing_theme_temp'])
    def test_cli_save_theme(self, mock_stdout):
        import vistab
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.path.expanduser', return_value=tmpdir):
                with self.assertRaises(SystemExit) as e:
                    vistab.main()
                self.assertEqual(e.exception.code, 0)
                
            output = mock_stdout.getvalue()
            self.assertIn("Saved layout globally as 'testing_theme_temp'", output)
            
            themes_path = os.path.join(tmpdir, ".config", "vistab", "themes.json")
            self.assertTrue(os.path.exists(themes_path))
            
            import json
            with open(themes_path, "r") as f:
                data = json.load(f)
            self.assertIn("testing_theme_temp", data)
            self.assertEqual(data["testing_theme_temp"]["style"], "round-header") # Default style

if __name__ == '__main__':
    unittest.main()
