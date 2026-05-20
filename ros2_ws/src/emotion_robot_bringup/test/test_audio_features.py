import unittest

import numpy as np

from emotion_robot_bringup.audio_features import classify_audio_emotion, extract_audio_features
import emotion_robot_bringup.audio_features as af


def _tone_bytes(freq_hz: float, amp: float, seconds: float = 0.5, sr: int = 16000) -> bytes:
    t = np.arange(int(sr * seconds), dtype=np.float32) / float(sr)
    wave = amp * np.sin(2.0 * np.pi * freq_hz * t)
    pcm = np.clip(wave * 32767.0, -32768.0, 32767.0).astype(np.int16)
    return pcm.tobytes()


class TestAudioFeatures(unittest.TestCase):
    def test_extract_empty(self):
        f = extract_audio_features(b"")
        self.assertEqual(f["backend"], "none")
        self.assertEqual(f["rms"], 0.0)
        self.assertEqual(f["pitch"], 0.0)
        self.assertEqual(f["zcr"], 0.0)

    def test_extract_fallback_backend_when_lib_missing(self):
        old = af.librosa
        af.librosa = None
        try:
            data = _tone_bytes(freq_hz=220.0, amp=0.25)
            f = extract_audio_features(data)
            self.assertEqual(f["backend"], "fallback")
            self.assertGreater(f["pitch"], 100.0)
            self.assertGreater(f["rms"], 0.0)
        finally:
            af.librosa = old

    def test_classify_happy(self):
        label = classify_audio_emotion({"energy": 0.004, "rms": 0.09, "pitch": 170.0, "zcr": 0.16})
        self.assertEqual(label, "happy")

    def test_classify_angry(self):
        label = classify_audio_emotion({"energy": 0.012, "rms": 0.16, "pitch": 210.0, "zcr": 0.28})
        self.assertEqual(label, "angry")

    def test_classify_sad(self):
        label = classify_audio_emotion({"energy": 0.0003, "rms": 0.02, "pitch": 90.0, "zcr": 0.05})
        self.assertEqual(label, "sad")

    def test_classify_neutral(self):
        label = classify_audio_emotion({"energy": 0.0015, "rms": 0.05, "pitch": 110.0})
        self.assertEqual(label, "neutral")

    def test_classify_with_linear_model_profile(self):
        profile = {
            "model_type": "linear_v1",
            "labels": ["sad", "neutral", "happy", "angry"],
            "feature_order": ["energy", "rms", "pitch", "zcr"],
            "weights": {
                "sad": [-1.0, -1.0, -0.001, -0.5],
                "neutral": [0.0, 0.0, 0.0, 0.0],
                "happy": [0.6, 0.8, 0.002, 0.5],
                "angry": [0.7, 0.9, 0.001, 0.9],
            },
            "bias": {"happy": -0.02, "angry": -0.01},
        }
        label = classify_audio_emotion(
            {"energy": 0.006, "rms": 0.09, "pitch": 210.0, "zcr": 0.23},
            profile=profile,
        )
        self.assertEqual(label, "happy")

    def test_classify_with_invalid_linear_profile_falls_back(self):
        profile = {"model_type": "linear_v1", "labels": ["happy"]}
        label = classify_audio_emotion(
            {"energy": 0.004, "rms": 0.09, "pitch": 170.0, "zcr": 0.16},
            profile=profile,
        )
        self.assertEqual(label, "happy")


if __name__ == "__main__":
    unittest.main()
