import sys
import unittest
import os
from pathlib import Path
from types import ModuleType

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

if "rclpy" not in sys.modules:
    rclpy_stub = ModuleType("rclpy")
    rclpy_stub.ok = lambda: True
    node_mod = ModuleType("rclpy.node")

    class _Node:
        pass

    node_mod.Node = _Node
    sys.modules["rclpy"] = rclpy_stub
    sys.modules["rclpy.node"] = node_mod

if "std_msgs.msg" not in sys.modules:
    std_msgs_mod = ModuleType("std_msgs")
    std_msgs_msg_mod = ModuleType("std_msgs.msg")

    class _String:
        pass

    class _UInt8MultiArray:
        pass

    std_msgs_msg_mod.String = _String
    std_msgs_msg_mod.UInt8MultiArray = _UInt8MultiArray
    sys.modules["std_msgs"] = std_msgs_mod
    sys.modules["std_msgs.msg"] = std_msgs_msg_mod

from emotion_robot_bringup.stt_node import (
    resolve_stt_backend,
    resolve_topic_name as resolve_stt_topic,
    resolve_whisper_language,
    resolve_whisper_model_dir,
    resolve_whisper_model_size,
    resolve_whisper_task,
)
from emotion_robot_bringup.tts_node import resolve_topic_name as resolve_tts_topic
from emotion_robot_bringup.tts_node import resolve_tts_engine


class TestSttTtsParamResolution(unittest.TestCase):
    def test_stt_backend_prefers_backend_param(self):
        self.assertEqual(resolve_stt_backend("speech_recognition", "none"), "speech_recognition")

    def test_stt_backend_falls_back_to_model_backend(self):
        self.assertEqual(resolve_stt_backend("", "speech_recognition"), "speech_recognition")

    def test_stt_backend_accepts_whisper_alias(self):
        self.assertEqual(resolve_stt_backend("", "openai_whisper"), "openai_whisper")

    def test_stt_topic_uses_primary_when_set(self):
        self.assertEqual(resolve_stt_topic("/custom/text", "/speech/text"), "/custom/text")

    def test_stt_topic_falls_back_when_primary_empty(self):
        self.assertEqual(resolve_stt_topic(" ", "/speech/text"), "/speech/text")

    def test_whisper_model_size_prefers_new_param(self):
        self.assertEqual(resolve_whisper_model_size("base", "tiny"), "base")

    def test_whisper_model_size_uses_legacy_param_when_new_empty(self):
        self.assertEqual(resolve_whisper_model_size("", "small"), "small")

    def test_whisper_model_size_defaults_to_tiny(self):
        self.assertEqual(resolve_whisper_model_size("", ""), "tiny")

    def test_whisper_language_prefers_new_param(self):
        self.assertEqual(resolve_whisper_language("ar", "en"), "ar")

    def test_whisper_language_uses_legacy_param_when_new_empty(self):
        self.assertEqual(resolve_whisper_language("", "de"), "de")

    def test_whisper_language_defaults_to_en(self):
        self.assertEqual(resolve_whisper_language("", ""), "en")

    def test_whisper_model_dir_prefers_direct_param(self):
        self.assertEqual(resolve_whisper_model_dir("/models/dir", "/cache/dir"), "/models/dir")

    def test_whisper_model_dir_uses_cache_param(self):
        self.assertEqual(resolve_whisper_model_dir("", "/cache/dir"), "/cache/dir")

    def test_whisper_model_dir_uses_env_fallback(self):
        old = os.environ.get("WHISPER_MODEL_DIR")
        os.environ["WHISPER_MODEL_DIR"] = "/env/models"
        try:
            self.assertEqual(resolve_whisper_model_dir("", ""), "/env/models")
        finally:
            if old is None:
                os.environ.pop("WHISPER_MODEL_DIR", None)
            else:
                os.environ["WHISPER_MODEL_DIR"] = old

    def test_whisper_task_valid_and_fallback(self):
        self.assertEqual(resolve_whisper_task("translate"), "translate")
        self.assertEqual(resolve_whisper_task("bad-task"), "transcribe")

    def test_tts_engine_prefers_backend_param(self):
        self.assertEqual(resolve_tts_engine("pyttsx3", "other"), "pyttsx3")

    def test_tts_engine_falls_back_to_engine(self):
        self.assertEqual(resolve_tts_engine("", "pyttsx3"), "pyttsx3")

    def test_tts_topic_uses_primary_when_set(self):
        self.assertEqual(resolve_tts_topic("/robot/response", "/robot/say"), "/robot/response")

    def test_tts_topic_falls_back_when_primary_empty(self):
        self.assertEqual(resolve_tts_topic("", "/robot/say"), "/robot/say")


if __name__ == "__main__":
    unittest.main()
