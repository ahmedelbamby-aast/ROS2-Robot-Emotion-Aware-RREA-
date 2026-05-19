import sys
import unittest
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from emotion_robot_bringup.robot_pipeline_policy import (  # noqa: E402
    normalize_audio_state,
    normalize_camera_state,
    normalize_status_state,
    should_publish_policy,
)


class TestRobotPipelinePolicy(unittest.TestCase):
    def test_normalize_camera_state_marks_engaged_with_dimensions(self):
        out = normalize_camera_state(640, 480, "rgb8")
        self.assertEqual(out["label"], "engaged")
        self.assertEqual(out["width"], 640)
        self.assertEqual(out["height"], 480)
        self.assertEqual(out["encoding"], "rgb8")

    def test_normalize_camera_state_marks_neutral_when_empty(self):
        out = normalize_camera_state(0, 480, "rgb8")
        self.assertEqual(out["label"], "neutral")

    def test_normalize_audio_state_calm_with_bytes(self):
        out = normalize_audio_state(12)
        self.assertEqual(out, {"bytes": 12, "label": "calm"})

    def test_normalize_status_state_builds_text(self):
        out = normalize_status_state("battery", "low", 1)
        self.assertEqual(out["text"], "battery low")
        self.assertEqual(out["level"], 1)

    def test_should_publish_policy_only_on_change(self):
        prev = {"emotion": "supportive", "response": "a", "say": "b"}
        next_same = {"emotion": "supportive", "response": "a", "say": "b"}
        next_changed = {"emotion": "joyful", "response": "c", "say": "d"}
        self.assertFalse(should_publish_policy(prev, next_same))
        self.assertTrue(should_publish_policy(prev, next_changed))
        self.assertFalse(should_publish_policy(prev, {}))


if __name__ == "__main__":
    unittest.main()
