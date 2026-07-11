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

class TestCLIVerbs(unittest.TestCase):
    """Validation framework for the natural-language subject/verb/object subcommands."""

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'show', 'styles'])
    def test_show_styles(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("Available Styles", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'show', 'colors'])
    def test_show_colors(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("Foreground Colors", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'show', 'caps'])
    def test_show_caps_alias(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("ansi color", mock_stdout.getvalue().lower())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'show'])
    def test_bare_show_verb(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("Usage: vistab show", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'show', 'bogus'])
    def test_invalid_show_subject(self, mock_stderr):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 2)
        self.assertIn("Unknown show subject 'bogus'", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'help', 'colors'])
    def test_help_colors(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("--border-color COLOR", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'help', 'bogus'])
    def test_invalid_help_subject(self, mock_stderr):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 2)
        self.assertIn("Unknown help subject 'bogus'", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'demo', 'span'])
    def test_demo_span(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("Column Spanning (Colspan) Demonstration", mock_stdout.getvalue())
        self.assertIn("Example code:", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'demo', 'rowspan'])
    def test_demo_rowspan_alias(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("Column Spanning (Colspan) Demonstration", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', '--demo', 'colspan'])
    def test_demo_flag_alias(self, mock_stdout):
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("Column Spanning (Colspan) Demonstration", mock_stdout.getvalue())

    # --- Release-review 20260711-122840 gap coverage ---

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'show', 'span'])
    def test_show_span_parity(self, mock_stdout):
        """show span (verb parity added this batch) must render the span demo (T1)."""
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("Column Spanning (Colspan) Demonstration", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'show', 'spans'])
    def test_show_spans_alias(self, mock_stdout):
        """show spans alias resolves to the span demo (T1)."""
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        self.assertIn("Column Spanning (Colspan) Demonstration", mock_stdout.getvalue())


    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['vistab', 'show', 'showcase'])
    def test_show_showcase(self, mock_stdout):
        """show showcase renders the curated colspan+theme+CJK hero table (exit 0)."""
        import vistab
        with self.assertRaises(SystemExit) as e:
            vistab.main()
        self.assertEqual(e.exception.code, 0)
        out = mock_stdout.getvalue()
        self.assertIn("showcase", out)
        self.assertIn("Contact", out)      # the colspan header group
        self.assertIn("关羽", out)          # CJK content rendered

    def test_showcase_width_within_80(self):
        """The hero table must fit within 80 visible columns (screenshot legibility)."""
        import subprocess, os
        from vistab import StringLengthCalculator
        e = dict(os.environ); e.pop("NO_COLOR", None)
        cli = os.path.join(os.path.dirname(__file__), "..", "src", "vistab.py")
        out = subprocess.run([sys.executable, cli, "show", "showcase"],
                             capture_output=True, text=True, env=e).stdout
        widest = max((StringLengthCalculator.len(l) for l in out.splitlines()), default=0)
        self.assertLessEqual(widest, 80)


class TestCLINoColor(unittest.TestCase):
    """Release-review 20260711-122840 gap coverage for --no-color / NO_COLOR (T2)."""

    ANSI = None

    def _run(self, argv, env=None):
        import re, subprocess, os
        e = dict(os.environ); e.pop("NO_COLOR", None)
        if env:
            e.update(env)
        cli = os.path.join(os.path.dirname(__file__), "..", "src", "vistab.py")
        r = subprocess.run([sys.executable, cli] + argv, capture_output=True, text=True,
                           input="A,B\n1,2\n", env=e)
        return r.stdout, r.stderr, r.returncode

    def _has_ansi(self, s):
        import re
        return re.search(r'\x1b\[[0-9;]*[A-Za-z]', s) is not None

    def test_no_color_flag_themed_render_has_no_escapes(self):
        out, _, rc = self._run(["-t", "ocean", "--no-color"])
        self.assertEqual(rc, 0)
        self.assertFalse(self._has_ansi(out))

    def test_no_color_env_themed_render_has_no_escapes(self):
        out, _, rc = self._run(["-t", "ocean"], env={"NO_COLOR": "1"})
        self.assertEqual(rc, 0)
        self.assertFalse(self._has_ansi(out))

    def test_show_colors_no_color_warns_and_is_monochrome(self):
        # show colors --no-color: stdout escape-free, warning on stderr naming the trigger.
        import subprocess, os
        e = dict(os.environ); e.pop("NO_COLOR", None)
        cli = os.path.join(os.path.dirname(__file__), "..", "src", "vistab.py")
        r = subprocess.run([sys.executable, cli, "show", "colors", "--no-color"],
                           capture_output=True, text=True, env=e)
        self.assertFalse(self._has_ansi(r.stdout))
        self.assertIn("colors turned off", r.stderr)

    def test_show_showcase_no_color_monochrome_and_warns(self):
        import subprocess, os
        e = dict(os.environ); e.pop("NO_COLOR", None)
        cli = os.path.join(os.path.dirname(__file__), "..", "src", "vistab.py")
        r = subprocess.run([sys.executable, cli, "show", "showcase", "--no-color"],
                           capture_output=True, text=True, env=e)
        self.assertFalse(self._has_ansi(r.stdout))     # fully monochrome (content ANSI stripped)
        self.assertIn("colors turned off", r.stderr)


class TestSetColorLibrary(unittest.TestCase):
    """Library-level set_color(False) suppresses vistab styling escapes (T2)."""

    def _has_ansi(self, s):
        import re
        return re.search(r'\x1b\[[0-9;]*[A-Za-z]', s) is not None

    def test_set_color_false_no_styling_escapes(self):
        t = Vistab(style="light")
        t.set_theme("ocean")
        t.add_rows([["A", "B"], ["1", "2"]])
        t.set_color(False)
        self.assertFalse(self._has_ansi(t.draw()))

    def test_set_color_true_default_still_colored(self):
        t = Vistab(style="light")
        t.set_theme("ocean")
        t.add_rows([["A", "B"], ["1", "2"]])
        self.assertTrue(self._has_ansi(t.draw()))  # default: color on

    def test_set_color_false_preserves_user_content_ansi(self):
        t = Vistab(style="light")
        t.add_row(["\033[31mred\033[0m"])
        t.set_color(False)
        self.assertIn("\033[31m", t.draw())  # user content ANSI is not stripped


if __name__ == '__main__':
    unittest.main()
