import sys
import unittest
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from emotion_robot_bringup.speech_helpers import choose_fallback_text, decode_audio_bytes, extract_text_from_audio_payload


class TestSpeechHelpers(unittest.TestCase):
    def test_decode_audio_bytes_handles_list(self):
        self.assertEqual(decode_audio_bytes([65, 66, 67]), b"ABC")

    def test_decode_audio_bytes_rejects_invalid_values(self):
        self.assertEqual(decode_audio_bytes(["x"]), b"")

    def test_extract_text_prefers_top_level_keys(self):
        raw = '{"text":"hello world","meta":{"text":"ignored"}}'
        self.assertEqual(extract_text_from_audio_payload(raw), "hello world")

    def test_extract_text_uses_meta_when_needed(self):
        raw = '{"meta":{"transcript":"from meta"}}'
        self.assertEqual(extract_text_from_audio_payload(raw), "from meta")

    def test_extract_text_returns_empty_for_bad_json(self):
        self.assertEqual(extract_text_from_audio_payload("not-json"), "")

    def test_choose_fallback_text_obeys_threshold_and_cooldown(self):
        self.assertIsNone(choose_fallback_text(200, 500, "fallback", 0, 1_000_000_000, 1_000_000_000))
        self.assertEqual(choose_fallback_text(800, 500, "fallback", 0, 3_000_000_000, 1_000_000_000), "fallback")
        self.assertIsNone(choose_fallback_text(800, 500, "fallback", 2_500_000_000, 3_000_000_000, 1_000_000_000))


if __name__ == "__main__":
    unittest.main()
