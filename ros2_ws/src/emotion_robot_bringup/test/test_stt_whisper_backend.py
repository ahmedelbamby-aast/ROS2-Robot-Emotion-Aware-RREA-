import sys
import unittest
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

from emotion_robot_bringup.stt_node import SttNode


class _WhisperModelOK:
    def __init__(self):
        self.calls = []

    def transcribe(self, path, **kwargs):
        if not path.endswith(".wav"):
            raise RuntimeError("unexpected file type")
        self.calls.append({"path": path, **kwargs})
        return {"text": " hello whisper "}


class _WhisperModelFail:
    def transcribe(self, path, **kwargs):
        _ = (path, kwargs)
        raise RuntimeError("transcribe failed")


class TestSttWhisperBackend(unittest.TestCase):
    def _make_node(self):
        node = SttNode.__new__(SttNode)
        node._whisper_sample_rate = 16000
        node._whisper_channels = 1
        node._whisper_sample_width = 2
        node._whisper_language = "en"
        node._whisper_task = "transcribe"
        node._whisper_fp16 = False
        node._whisper_temperature = -1.0
        node._status = []
        node._publish_status = lambda text: node._status.append(text)
        return node

    def test_transcribe_whisper_returns_text(self):
        node = self._make_node()
        model = _WhisperModelOK()
        node._whisper_model = model
        text = node._transcribe_whisper(b"\x00\x00" * 3200)
        self.assertEqual(text, "hello whisper")
        self.assertEqual(model.calls[-1]["language"], "en")
        self.assertEqual(node._status, [])

    def test_transcribe_whisper_passes_runtime_kwargs(self):
        class _WhisperModelArgs:
            def __init__(self):
                self.kwargs = None

            def transcribe(self, _path, **kwargs):
                self.kwargs = kwargs
                return {"text": "ok"}

        node = self._make_node()
        model = _WhisperModelArgs()
        node._whisper_model = model
        node._whisper_task = "translate"
        node._whisper_fp16 = True
        node._whisper_temperature = 0.15
        text = node._transcribe_whisper(b"\x00\x00" * 3200)
        self.assertEqual(text, "ok")
        self.assertEqual(model.kwargs["language"], "en")
        self.assertEqual(model.kwargs["task"], "translate")
        self.assertTrue(model.kwargs["fp16"])
        self.assertEqual(model.kwargs["temperature"], 0.15)

    def test_transcribe_whisper_handles_runtime_error(self):
        node = self._make_node()
        node._whisper_model = _WhisperModelFail()
        text = node._transcribe_whisper(b"\x00\x00" * 800)
        self.assertEqual(text, "")
        self.assertTrue(any("transcribe_error=" in entry for entry in node._status))

    def test_transcribe_whisper_handles_invalid_audio_params(self):
        node = self._make_node()
        node._whisper_model = _WhisperModelOK()
        node._whisper_sample_rate = 0
        text = node._transcribe_whisper(b"\x00\x00" * 800)
        self.assertEqual(text, "")
        self.assertIn("backend=whisper invalid_audio_params=true", node._status)


if __name__ == "__main__":
    unittest.main()
