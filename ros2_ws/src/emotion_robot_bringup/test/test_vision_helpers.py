import sys
import unittest
from pathlib import Path

import numpy as np

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from emotion_robot_bringup.vision_helpers import (  # noqa: E402
    VisionResult,
    _extract_deepface_label,
    classify_camera_emotion,
    map_deepface_emotion,
)


class FakeImage:
    def __init__(self, width, height, encoding, data):
        self.width = width
        self.height = height
        self.encoding = encoding
        self.data = data


class FakeDeepFace:
    @staticmethod
    def analyze(_roi, actions=None, enforce_detection=False, detector_backend="opencv"):
        _ = (actions, enforce_detection, detector_backend)
        return {"dominant_emotion": "happy"}


class FakeDeepFaceScores:
    @staticmethod
    def analyze(_roi, actions=None, enforce_detection=False, detector_backend="opencv"):
        _ = (actions, enforce_detection, detector_backend)
        return {"emotion": {"happy": 60, "sad": 40}}


class TestVisionHelpers(unittest.TestCase):
    def test_map_deepface_emotion(self):
        self.assertEqual(map_deepface_emotion("happy"), "happy")
        self.assertEqual(map_deepface_emotion("fear"), "sad")
        self.assertEqual(map_deepface_emotion("disgust"), "angry")
        self.assertEqual(map_deepface_emotion("surprise"), "neutral")

    def test_extract_deepface_label(self):
        self.assertEqual(_extract_deepface_label({"dominant_emotion": "angry"}), "angry")
        self.assertEqual(
            _extract_deepface_label({"emotion": {"sad": 20, "happy": 95, "angry": 10}}),
            "happy",
        )
        self.assertIsNone(_extract_deepface_label({"emotion": {"happy": 31, "sad": 29}}))
        self.assertIsNone(_extract_deepface_label({}))

    def test_classify_returns_neutral_without_cv2(self):
        msg = FakeImage(8, 8, "bgr8", bytes(8 * 8 * 3))
        out = classify_camera_emotion(msg, cv2_module=None, deepface_cls=None, use_deepface=True)
        self.assertEqual(out, VisionResult("neutral", False, "none"))

    def test_classify_with_face_and_no_deepface_is_neutral_face_found(self):
        class Cv2Stub:
            COLOR_GRAY2BGR = 1
            COLOR_RGB2BGR = 2
            COLOR_BGR2GRAY = 3

            class data:
                haarcascades = "/tmp/"

            @staticmethod
            def cvtColor(arr, _code):
                return arr

            class CascadeClassifier:
                def __init__(self, _path):
                    pass

                def detectMultiScale(self, _gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)):
                    _ = (scaleFactor, minNeighbors, minSize)
                    return np.array([[0, 0, 6, 6]])

        msg = FakeImage(8, 8, "bgr8", bytes(8 * 8 * 3))
        out = classify_camera_emotion(msg, cv2_module=Cv2Stub, deepface_cls=None, use_deepface=True)
        self.assertEqual(out.emotion, "neutral")
        self.assertTrue(out.face_found)
        self.assertEqual(out.backend, "opencv")

    def test_classify_with_deepface_maps_happy(self):
        class Cv2Stub:
            COLOR_GRAY2BGR = 1
            COLOR_RGB2BGR = 2
            COLOR_BGR2GRAY = 3

            class data:
                haarcascades = "/tmp/"

            @staticmethod
            def cvtColor(arr, _code):
                return arr

            class CascadeClassifier:
                def __init__(self, _path):
                    pass

                def detectMultiScale(self, _gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)):
                    _ = (scaleFactor, minNeighbors, minSize)
                    return np.array([[0, 0, 6, 6]])

        msg = FakeImage(8, 8, "bgr8", bytes(8 * 8 * 3))
        out = classify_camera_emotion(msg, cv2_module=Cv2Stub, deepface_cls=FakeDeepFace, use_deepface=True)
        self.assertEqual(out.emotion, "happy")
        self.assertTrue(out.face_found)
        self.assertEqual(out.backend, "deepface")

    def test_classify_with_deepface_uses_score_thresholds(self):
        class Cv2Stub:
            COLOR_GRAY2BGR = 1
            COLOR_RGB2BGR = 2
            COLOR_BGR2GRAY = 3

            class data:
                haarcascades = "/tmp/"

            @staticmethod
            def cvtColor(arr, _code):
                return arr

            class CascadeClassifier:
                def __init__(self, _path):
                    pass

                def detectMultiScale(self, _gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)):
                    _ = (scaleFactor, minNeighbors, minSize)
                    return np.array([[0, 0, 6, 6]])

        msg = FakeImage(8, 8, "bgr8", bytes(8 * 8 * 3))
        out = classify_camera_emotion(
            msg,
            cv2_module=Cv2Stub,
            deepface_cls=FakeDeepFaceScores,
            use_deepface=True,
            deepface_min_score=35.0,
            deepface_min_margin=25.0,
        )
        self.assertEqual(out.emotion, "neutral")
        self.assertTrue(out.face_found)
        self.assertEqual(out.backend, "deepface")


if __name__ == "__main__":
    unittest.main()
