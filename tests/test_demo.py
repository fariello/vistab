import unittest
import subprocess
import os
from pathlib import Path

class TestVistabDemo(unittest.TestCase):
    """
    Validation framework specifically capturing the diagnostic demo matrices.
    """
    
    def setUp(self):
        self.tests_dir = Path(__file__).parent.absolute()
        self.fixtures_dir = self.tests_dir / "fixtures"
        self.cli_path = self.tests_dir.parent / "src" / "vistab.py"
        
        # Ensure fixtures directory exists
        os.makedirs(self.fixtures_dir, exist_ok=True)

    def _run_cli(self, args: list) -> str:
        """Executes the CLI and returns the unified STDOUT."""
        cmd = ["python", str(self.cli_path)] + args
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        # Force HOME to map locally to prevent picking up the user's global config.toml
        temp_home = self.tests_dir / "temp_home"
        os.makedirs(temp_home, exist_ok=True)
        env["HOME"] = str(temp_home)
        env["USERPROFILE"] = str(temp_home)
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding="utf-8",
            env=env
        )
        return result.stdout + result.stderr

    def _assert_against_fixture(self, name: str, output: str):
        """
        Validates output against a saved fixture. 
        If the fixture does not exist, it bootstraps it.
        """
        fixture_path = self.fixtures_dir / f"{name}.txt"
        
        # If the fixture does not exist, save the new output
        if not fixture_path.exists():
            with open(fixture_path, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Bootstrapped new fixture: {name}.txt")
            return
            
        with open(fixture_path, "r", encoding="utf-8") as f:
            expected = f.read()

        output_lines = tuple(output.splitlines())
        expected_lines = tuple(expected.splitlines())
        
        if output_lines != expected_lines:
            for i in range(min(len(output_lines), len(expected_lines))):
                if output_lines[i] != expected_lines[i]:
                    print(f"MISMATCH AT LINE {i}:")
                    print(f"EXPECTED: {expected_lines[i]!r}")
                    print(f"ACTUAL:   {output_lines[i]!r}")
                    break
            self.assertEqual(output_lines, expected_lines, f"Fixture {name}.txt mismatch.")

    def test_demo_styles(self):
        """Test the --demo styles output."""
        out = self._run_cli(["--demo", "styles"])
        self._assert_against_fixture("regression_demo_styles", out)

    def test_demo_colors(self):
        """Test the --demo colors output."""
        out = self._run_cli(["--demo", "colors"])
        self._assert_against_fixture("regression_demo_colors", out)

    def test_demo_capabilities(self):
        """Test the --demo capabilities output."""
        out = self._run_cli(["--demo", "capabilities"])
        self._assert_against_fixture("regression_demo_capabilities", out)

    def test_demo_anatomy(self):
        """Test the --demo anatomy output."""
        out = self._run_cli(["--demo", "anatomy"])
        self._assert_against_fixture("regression_demo_anatomy", out)

    def test_demo_themes(self):
        """Test the --demo themes output."""
        out = self._run_cli(["--demo", "themes"])
        self._assert_against_fixture("regression_diagnostic_matrix", out)

if __name__ == "__main__":
    unittest.main()
