import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml


def _load_lib_config_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "lib_config.py"
    spec = importlib.util.spec_from_file_location("lib_config", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestLibConfig(unittest.TestCase):
    def setUp(self):
        self.lib_config = _load_lib_config_module()

    def test_get_nested_key_prints_scalar_value(self):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "project.yaml"
            cfg_path.write_text("gateway:\n  port: 8765\n", encoding="utf-8")

            with patch.object(self.lib_config, "CFG", cfg_path), patch("sys.argv", ["lib_config.py", "get", "gateway.port"]):
                out = io.StringIO()
                with redirect_stdout(out):
                    rc = self.lib_config.main()

            self.assertEqual(rc, 0)
            self.assertEqual(out.getvalue().strip(), "8765")

    def test_set_nested_key_casts_int_and_persists(self):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "project.yaml"
            cfg_path.write_text("gateway:\n  port: 8765\n", encoding="utf-8")

            with patch.object(self.lib_config, "CFG", cfg_path), patch("sys.argv", ["lib_config.py", "set", "gateway.port", "9999"]):
                rc = self.lib_config.main()

            self.assertEqual(rc, 0)
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            self.assertEqual(cfg["gateway"]["port"], 9999)

    def test_set_audio_stt_tts_keys_persist_with_type_casting(self):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "project.yaml"
            cfg_path.write_text(
                (
                    "audio:\n"
                    "  sample_rate_hz: 16000\n"
                    "stt:\n"
                    "  enabled: false\n"
                    "tts:\n"
                    "  enabled: false\n"
                ),
                encoding="utf-8",
            )

            with patch.object(self.lib_config, "CFG", cfg_path):
                with patch("sys.argv", ["lib_config.py", "set", "audio.sample_rate_hz", "22050"]):
                    rc1 = self.lib_config.main()
                with patch("sys.argv", ["lib_config.py", "set", "stt.enabled", "true"]):
                    rc2 = self.lib_config.main()
                with patch("sys.argv", ["lib_config.py", "set", "tts.enabled", "true"]):
                    rc3 = self.lib_config.main()

            self.assertEqual(rc1, 0)
            self.assertEqual(rc2, 0)
            self.assertEqual(rc3, 0)

            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            self.assertEqual(cfg["audio"]["sample_rate_hz"], 22050)
            self.assertTrue(cfg["stt"]["enabled"])
            self.assertTrue(cfg["tts"]["enabled"])


if __name__ == "__main__":
    unittest.main()
