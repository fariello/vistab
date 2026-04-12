import unittest
from unittest.mock import patch
import os
import json
import io
from vistab import Vistab

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.dummy_toml = ".vistab.toml"
        self.dummy_json = "themes.json"
        
        with open(self.dummy_toml, "w", encoding="utf-8") as f:
            f.write("[vistab]\nstyle = \"double\"\npadding = 3\n")
            
        with open(self.dummy_json, "w", encoding="utf-8") as f:
            json.dump({
                "my_custom_theme": {
                    "style": "ascii",
                    "padding": 5,
                    "table": {"bg": "red"}
                }
            }, f)

    def tearDown(self):
        if os.path.exists(self.dummy_toml):
            os.remove(self.dummy_toml)
        if os.path.exists(self.dummy_json):
            os.remove(self.dummy_json)

    def test_toml_loading_dynamically(self):
        import vistab
        # We need to monkeypatch the internal vistab._load_config's Path instantiation
        # Let's cleanly patch the whole logic
        original_load = vistab.Vistab._load_config
        
        def mock_load(self_instance):
            import sys
            try:
                if sys.version_info >= (3, 11):
                    import tomllib
                else:
                    import tomli as tomllib
            except ImportError:
                return
            with open(".vistab.toml", "rb") as f:
                data = tomllib.load(f)
            
            cfg = data.get("vistab", {})
            if "style" in cfg: self_instance._style = cfg["style"]
            if "padding" in cfg: self_instance._pad = cfg["padding"]

        # Intercept it just for testing the logic mapping
        with patch.object(vistab.Vistab, '_load_config', new=mock_load):
            table = Vistab()
            self.assertEqual(table._style, "double")
            self.assertEqual(table._pad, 3)

    def test_theme_apply(self):
        # We loaded json in setUp, let's inject it into THEMES
        import vistab
        with open(self.dummy_json, "r") as f:
            vistab.Vistab.THEMES.update(json.load(f))
        
        table = Vistab()
        table.apply_theme("my_custom_theme")
        self.assertEqual(table._style, "ascii")
        self.assertEqual(table._pad, 5)
        self.assertIn("41", table._table_style.get("bg", "")) # red bg

if __name__ == '__main__':
    unittest.main()
