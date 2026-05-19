import sys
import unittest
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from emotion_robot_bringup.inference_logic import (  # noqa: E402
    compute_emotion_policy,
    parse_audio_payload,
    parse_camera_payload,
    parse_text_payload,
)


class TestInferenceLogic(unittest.TestCase):
    def test_parse_camera_payload_json(self):
        out = parse_camera_payload('{"kind":"camera","width":640,"height":480,"label":"neutral"}')
        self.assertEqual(out["width"], 640)
        self.assertEqual(out["height"], 480)
        self.assertEqual(out["label"], "neutral")

    def test_parse_camera_payload_legacy_string(self):
        out = parse_camera_payload("320x240")
        self.assertEqual((out["width"], out["height"]), (320, 240))

    def test_parse_audio_payload_json(self):
        out = parse_audio_payload('{"kind":"audio","bytes":1024,"label":"calm"}')
        self.assertEqual(out["bytes"], 1024)
        self.assertEqual(out["label"], "calm")

    def test_parse_audio_payload_legacy_string(self):
        out = parse_audio_payload("bytes=55")
        self.assertEqual(out["bytes"], 55)
        self.assertEqual(out["label"], "calm")

    def test_parse_text_payload_json(self):
        out = parse_text_payload('{"kind":"status","text":"I feel stressed","source":"status"}')
        self.assertEqual(out, {"text": "I feel stressed", "source": "status"})

    def test_compute_policy_comforting(self):
        out = compute_emotion_policy("I feel very stressed today", "neutral", "calm")
        self.assertEqual(out["emotion"], "comforting")
        self.assertIn("policy=comforting", out["response"])

    def test_compute_policy_joyful(self):
        out = compute_emotion_policy("I am happy with progress", "neutral", "calm")
        self.assertEqual(out["emotion"], "joyful")
        self.assertIn("policy=joyful", out["response"])


if __name__ == "__main__":
    unittest.main()
