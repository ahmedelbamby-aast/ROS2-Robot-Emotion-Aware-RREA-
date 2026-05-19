import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from emotion_robot_bringup.common import load_project_config, resolve_gateway_target, send_json_line


class TestCommonHelpers(unittest.TestCase):
    def test_load_project_config_uses_env_path_when_present(self):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "project.yaml"
            expected = {"gateway": {"transport": "local_tcp", "local_host": "127.0.0.1", "port": 9000}, "ngrok": {"reserved_tcp_addr": ""}}
            with open(cfg_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(expected, f, sort_keys=False)

            with patch.dict(os.environ, {"PROJECT_CONFIG_PATH": str(cfg_path)}, clear=False):
                cfg = load_project_config()

            self.assertEqual(cfg["gateway"]["port"], 9000)
            self.assertEqual(cfg["gateway"]["local_host"], "127.0.0.1")

    def test_resolve_gateway_target_prefers_local_tcp(self):
        cfg = {"gateway": {"transport": "local_tcp", "local_host": "192.168.1.2", "port": 8765}, "ngrok": {"reserved_tcp_addr": ""}}
        host, port = resolve_gateway_target(cfg)
        self.assertEqual((host, port), ("192.168.1.2", 8765))

    def test_resolve_gateway_target_uses_env_ngrok_when_set(self):
        cfg = {"gateway": {"transport": "ngrok_tcp", "local_host": "unused", "port": 0}, "ngrok": {"reserved_tcp_addr": "reserved.example.com:1234"}}
        with patch.dict(os.environ, {"NGROK_HOST": "ephemeral.example.com", "NGROK_PORT": "443"}, clear=False):
            host, port = resolve_gateway_target(cfg)
        self.assertEqual((host, port), ("ephemeral.example.com", 443))

    def test_resolve_gateway_target_uses_ngrok_env_file(self):
        cfg = {"gateway": {"transport": "ngrok_tcp", "local_host": "unused", "port": 0}, "ngrok": {"reserved_tcp_addr": ""}}
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "ngrok.env"
            env_path.write_text("NGROK_HOST=file.example.com\nNGROK_PORT=5555\n", encoding="utf-8")
            with patch.dict(os.environ, {"NGROK_ENV_FILE": str(env_path)}, clear=False):
                host, port = resolve_gateway_target(cfg)
        self.assertEqual((host, port), ("file.example.com", 5555))

    def test_send_json_line_writes_newline_terminated_json(self):
        captured = []

        class FakeSocket:
            def sendall(self, raw):
                captured.append(raw)

        send_json_line(FakeSocket(), {"emotion": "happy", "score": 0.8})
        self.assertEqual(len(captured), 1)
        data = captured[0].decode("utf-8")
        self.assertTrue(data.endswith("\n"))
        self.assertEqual(json.loads(data.strip()), {"emotion": "happy", "score": 0.8})


if __name__ == "__main__":
    unittest.main()
