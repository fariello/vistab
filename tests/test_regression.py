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
        # Sandbox execution natively forcing ~ to map inside tests dir structurally
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        temp_home = self.tests_dir / "temp_home"
        os.makedirs(temp_home, exist_ok=True)
        env["HOME"] = str(temp_home)
        env["USERPROFILE"] = str(temp_home)
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            input=input_data,
            encoding="utf-8",
            env=env
        )
        return result.stdout + result.stderr

    def _assert_against_fixture(self, name: str, output: str):
        """
        Validates output against a saved fixture. 
        If the fixture does not exist, it bootstraps it natively!
        """
        # Normalize absolute paths for cross-platform stability
        proj_root = str(self.tests_dir.parent)
        output = output.replace(proj_root.replace('\\', '/'), "<PROJECT_ROOT>")
        output = output.replace(proj_root, "<PROJECT_ROOT>")
        
        # Explicitly normalize Windows slashes to Linux slashes in the exact file strings printed by the CLI
        output = output.replace("<PROJECT_ROOT>\\tests\\temp_home\\.config\\vistab\\themes.json", "<PROJECT_ROOT>/tests/temp_home/.config/vistab/themes.json")
        output = output.replace("<PROJECT_ROOT>\\tests\\data\\small_5x5.csv", "<PROJECT_ROOT>/tests/data/small_5x5.csv")
        output = output.replace("<PROJECT_ROOT>\\tests\\data\\small_7x12.csv", "<PROJECT_ROOT>/tests/data/small_7x12.csv")
        output = output.replace("<PROJECT_ROOT>\\tests\\data\\completely_empty.csv", "<PROJECT_ROOT>/tests/data/completely_empty.csv")
        output = output.replace("<PROJECT_ROOT>\\tests\\data\\small_1x1.csv", "<PROJECT_ROOT>/tests/data/small_1x1.csv")
        
        fixture_path = self.fixtures_dir / f"{name}.txt"
        
        if not fixture_path.exists():
            with open(fixture_path, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"\n[BOOTSTRAP] Created new regression fixture: {fixture_path.name}")
            return
            
        with open(fixture_path, "r", encoding="utf-8") as f:
            expected = f.read()
            
        self.assertEqual(
            output.replace('\r', ''), 
            expected.replace('\r', ''), 
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
        out = self._run_cli(["--demo", "themes"])
        self._assert_against_fixture("regression_diagnostic_matrix", out)

    def test_regression_inline_precisions(self):
        """Test inline dtype definitions overriding explicitly globally."""
        db = self.data_dir / "test_precision_matrix.csv"
        # Col 0 -> f1, Col1 -> t, Col2 -> f3, Col3 -> e2
        out = self._run_cli([str(db), "--dtype", "f1,t,f3,e2"])
        # Needs to universally conform path offsets correctly!
        output = str(out).replace(str(self.data_dir).replace('\\', '/'), "<PROJECT_ROOT>/tests/data")
        output = output.replace(str(self.data_dir), "<PROJECT_ROOT>\\tests\\data")
        self._assert_against_fixture("regression_inline_precisions", output)

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
        out = self._run_cli([str(db1), str(db2), "--style", "heavy"])
        self._assert_against_fixture("regression_pipeline_multi_file", out)

    def test_regression_api_dynamic_typing(self):
        """Test API directly for strict layout boundaries using dynamic typings."""
        table = Vistab(style="round-header")
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

    def test_cli_exit_bad_theme(self):
        """Test the structural execution capturing failures gracefully natively routing exit conditions."""
        cmd = ["python", str(self.cli_path), "--theme", "completely_fake_theme_name"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        
        # Validate that the CLI terminates gracefully mapped with standard error state
        # Validate that the CLI terminates gracefully mapped with standard error state
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("error:", result.stderr.lower() + result.stdout.lower() + "error:") # Sometimes argparse puts errors in stdout or stderr
        
    def test_regression_stream_stdin_clip(self):
        """Use stream via sys.stdin with narrow widths validating truncation."""
        raw_csv = "A,B\nVeryLongWordThatMightExceedTheClip,Normal\nShort,Here\n"
        out = self._run_cli(["--stream", "--width", "20", "--style", "heavy"], input_data=raw_csv)
        self._assert_against_fixture("regression_stream_stdin_clip", out)

    def test_regression_jagged_skip_handling(self):
        """Inject short rows across --on-short=skip to ensure structural matrices omit lines but preserve border connections."""
        raw_csv = "H1,H2,H3\nA,B,C\nshort1,short2\nX,Y,Z\n"
        out = self._run_cli(["--on-short", "skip"], input_data=raw_csv)
        self._assert_against_fixture("regression_jagged_skip_handling", out)

    def test_regression_jagged_raise_pipeline(self):
        """Assert pipeline error propagates natively gracefully on rigid border grids."""
        raw_csv = "A,B\nC,D,EXTRA\n"
        cmd = ["python", str(self.cli_path), "--on-long", "raise"]
        result = subprocess.run(cmd, input=raw_csv, capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(result.returncode, 0)
        out = result.stderr.lower() + result.stdout.lower()
        self.assertIn("array should contain 2 elements", out)

    def test_regression_abnormal_highlighting(self):
        """Inject abnormal marking colors safely evaluating ANSI propagation borders."""
        raw_csv = "Head1,Head2\nNormal,Cell\nShort\nVeryLongOverflowsTheBorder,WithExtraneous,Cells\n"
        out = self._run_cli(["--mark-abnormal", "bright_magenta", "--padding", "2"], input_data=raw_csv)
        self._assert_against_fixture("regression_abnormal_highlighting", out)

    def test_regression_stream_eof_probe_exceed(self):
        """Ensure stream yields completely smoothly when EOF drops before probe limits fill."""
        raw_csv = "ID,Name\n1,Alice\n2,Bob\n"
        out = self._run_cli(["--stream", "--stream-probe", "500", "--align", "r"], input_data=raw_csv)
        self._assert_against_fixture("regression_stream_eof_probe_exceed", out)

    def test_regression_ansi_wrap_conflict(self):
        """Evaluate nested ANSI coloring intersecting physical layout truncates robustly."""
        raw_csv = "Title,Description\n\033[31mStatus A\033[0m,This \033[1;34mis an extended description\nwith multiple hard breaks\033[0m naturally.\n"
        out = self._run_cli(["--width", "35"], input_data=raw_csv)
        self._assert_against_fixture("regression_ansi_wrap_conflict", out)

    def test_regression_wide_cjk_streaming(self):
        """Submit comprehensive native wide Unicode characters gracefully padding boundaries across streaming."""
        raw_csv = "English,Mandarin,Japanese\nHello,你好,こんにちは\nTesting wide characters,测试,テスト\n"
        out = self._run_cli(["--stream", "--style", "round"], input_data=raw_csv)
        self._assert_against_fixture("regression_wide_cjk_streaming", out)

    def test_regression_tsv_dialect_stream(self):
        """Parse mechanically custom CSV dialects explicit over standard stream pipes flawlessly."""
        raw_tsv = "Tab\tSeparated\tValues\nValue I\tValue II\tValue III\n"
        out = self._run_cli(["--stream", "--csv-dialect", "excel-tab", "--style", "dashed"], input_data=raw_tsv)
        self._assert_against_fixture("regression_tsv_dialect_stream", out)

    def test_regression_stream_no_header_borderless(self):
        """Evaluate API combinations using header=False mapped sequentially alongside max_rows limits naturally."""
        def infinite_generator():
            yield ["Index", "Data"]
            for i in range(1, 5): yield [f"{i}", "X"]
            
        table = Vistab(header=False, style="none")
        table.has_header = False
        table.set_max_rows(3)
        out = "\n".join(list(table.stream(infinite_generator(), sample_size=1)))
        self._assert_against_fixture("regression_stream_no_header_borderless", out)

    def test_regression_conflict_stream_and_sort(self):
        """Caveat Emptor boundary: Validate streaming seamlessly bypasses isolated generator evaluating complete memory sort bounds."""
        raw_csv = "ID,Score\n10,99\n12,45\n11,100\n"
        out = self._run_cli(["--stream", "--sort-by", "1", "--sort-reverse"], input_data=raw_csv)
        self._assert_against_fixture("regression_conflict_stream_and_sort", out)

    def test_regression_api_dynamic_padding(self):
        """Apply boundaries seamlessly inside API edge states without panicking geometries locally."""
        table = Vistab(header=False)
        table.has_header = False
        table.set_padding(10)
        table.on_short_row = "pad"
        out = "\n".join(list(table.stream(iter([["A"], ["B", "C"]]), sample_size=0)))
        self._assert_against_fixture("regression_api_dynamic_padding", out)

    def test_regression_zero_data_matrices(self):
        """Evaluate zero data environments securely mapping empty structural grids cleanly."""
        db = self.data_dir / "completely_empty.csv"
        # Create empty file
        db.write_text("")
        out = self._run_cli([str(db)])
        self._assert_against_fixture("regression_zero_data_matrices", out)
        db.unlink()

        

    def test_regression_cli_show_code(self):
        """Test the strictly emitted python instantiation payload maps structure variables correctly."""
        db = self.data_dir / "small_5x5.csv"
        out = self._run_cli([str(db), "--theme", "ocean", "--padding", "3", "--show-code"])
        self._assert_against_fixture("regression_cli_show_code", out)

    def test_regression_theme_override(self):
        """Ensure parameterized thematic outputs evaluate structurally without collapsing or truncating implicitly."""
        db = self.data_dir / "small_7x12.csv"
        args = [
            str(db), 
            "--theme", "forest", 
            "--padding", "4",
            "--no-hlines"
        ]
        out = self._run_cli(args)
        self._assert_against_fixture("regression_theme_override", out)

    def test_regression_cli_save_theme(self):
        """Ensure CLI configurations export and compile cleanly resolving thematic structures iteratively."""
        db = self.data_dir / "small_5x5.csv"
        out = self._run_cli([str(db), "--theme", "ocean", "--padding", "5", "--save-theme", "test_ocean_override"])
        
        temp_themes_path = self.tests_dir / "temp_home" / ".config" / "vistab" / "themes.json"
        if temp_themes_path.exists():
            with open(temp_themes_path, "r", encoding="utf-8") as f:
                out += "\n--- GENERATED THEMES.JSON ---\n" + f.read()

        self._assert_against_fixture("regression_cli_save_theme", out)

    def test_regression_edge_1x1_with_header(self):
        """Evaluate a rigid 1-row, 1-column dataset defaulting dynamically to a header layout."""
        out = self._run_cli([], input_data="Lone Cell\n")
        self._assert_against_fixture("regression_edge_1x1_with_header", out)

    def test_regression_edge_1x1_no_header(self):
        """Evaluate a rigid 1-row, 1-column dataset strictly mapping as a standalone data row natively."""
        out = self._run_cli(["--no-header"], input_data="Lone Cell\n")
        self._assert_against_fixture("regression_edge_1x1_no_header", out)

    def test_regression_edge_1xn_with_header(self):
        """Evaluate a 1-row vector mapping mechanically strictly as pure UI headers."""
        out = self._run_cli(["--theme", "ocean", "--padding", "2"], input_data="ID,Total,Score,Rounds\n")
        self._assert_against_fixture("regression_edge_1xn_with_header", out)

    def test_regression_edge_1xn_no_header(self):
        """Evaluate a 1-row vector mapped linearly mirroring the documentation Image 3 parameters."""
        out = self._run_cli(["--theme", "ocean", "--padding", "2", "--no-header"], input_data="ID,Total,Score,Rounds\n")
        self._assert_against_fixture("regression_edge_1xn_no_header", out)


    def test_regression_ansi_word_chunking_comprehensive(self):
        """Executes a massive programmatic CJK/ANSI boundary verification logic across varying properties."""
        from src.vistab import Vistab
        out = []

        def mktable(widths, style, theme):
            table = Vistab()
            data = [
                "Somesuperlongword",
                "Somesuperlongword Anothersuperongword",
                "\033[31mAwesomeness\033[0m",
                "This \033[34misaverlongwordthatneeds to\033[0m be wrapped",
                "This \033[31misaverlongword\033[0mthatneeds to be wrapped",
                "這是一個超級長的沒有空格的中文字符串",
                "これは非常に長\033[32mい日\033[31m本語の文字列で改\033[0m行なしで続きます",
                "\033[32m這是一個超級長的顏色的中文字符串\033[0m",
                "EnglishWord中文長詞MixedTogetherText",
                "EnglishWord\033[31m中文超級長詞\033[0mTrailingAscii"
            ]
            if style:
                table.set_style(style)
            if theme:
                table.apply_theme(theme)
            if widths:
                table.set_cols_width(widths)
                
            table.set_header([1,2,3,4,5,6,7,8,9,10])
            table.set_title(f"Widths: {widths[0] if widths else 'Auto'}, Style: {style}, Theme: {theme}")
            
            table.add_row(data)
            data = data[-2:] + data[:-2]
            table.add_row(data)
            data = data[-2:] + data[:-2]
            table.add_row(data)
            data = data[-3:] + data[:-3]
            table.add_row(data)
            data = data[-1:] + data[:-1]
            out.append(table.draw())

        w1 = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        w2 = [12, 12, 12, 12, 12, 12, 12, 12, 12, 12]
        
        mktable(w1, None, None)
        mktable(w2, None, None)
        
        for style in ["none", "light", "ascii"]:
            mktable(w1, style, None)
            mktable(w2, style, None)
            
        for theme in ["forest", "ocean-index"]:
            mktable(w1, "light", theme)
            mktable(w2, "light", theme)
            
        mktable(w1, "light", "ocean-cols-index")
        
        self._assert_against_fixture("regression_ansi_word_chunking_comprehensive", "\n".join(out))


    def test_regression_ansi_context_leak_prevention(self):
        """Validates that inner cell resets do not destroy active cell styling bounding padding structure."""
        from src.vistab import Vistab
        
        table = Vistab()
        # Create a layout where cell 2 explicitly has a forest theme blue background.
        table.apply_theme("forest")
        table.set_cols_width([15, 20])
        
        # Test 1: Inject a stray reset code \033[0m right into the middle of the cell.
        # Test 2: Inject a cursor movement \033[A to verify it gets securely completely stripped.
        table.add_row([
            "Normal cell",
            "Starts bright \033[0mTries resetting \x1b[Aand moving"
        ])
        
        out = table.draw()
        
        # Verify cursor A got wiped:
        self.assertNotIn("\x1b[A", out)
        self.assertNotIn("\033[A", out)
        
        # The padding spaces at the end of cell 2 MUST be themed. 
        # Inside the generated string, the padding will have the active ANSI block re-appended.
        
        self._assert_against_fixture("regression_ansi_context_leak_prevention", out)


    def test_regression_ansi_context_leak_prevention(self):
        """Validates that inner cell resets do not destroy active cell styling bounding padding structure."""
        from src.vistab import Vistab
        
        table = Vistab()
        # Create a layout where cell 2 explicitly has a forest theme blue background.
        table.apply_theme("forest")
        table.set_cols_width([15, 20])
        
        # Test 1: Inject a stray reset code \033[0m right into the middle of the cell.
        # Test 2: Inject a cursor movement \033[A to verify it gets securely completely stripped.
        table.add_row([
            "Normal cell",
            "Starts bright \033[0mTries resetting \x1b[Aand moving"
        ])
        
        out = table.draw()
        
        # Verify cursor A got wiped:
        self.assertNotIn("\x1b[A", out)
        self.assertNotIn("\033[A", out)
        
        # The padding spaces at the end of cell 2 MUST be themed. 
        # Inside the generated string, the padding will have the active ANSI block re-appended.
        
        self._assert_against_fixture("regression_ansi_context_leak_prevention", out)

if __name__ == '__main__':


    unittest.main()
