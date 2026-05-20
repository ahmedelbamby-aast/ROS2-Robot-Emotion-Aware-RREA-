import unittest

from emotion_robot_bringup.emotion_policy import (
    build_response,
    fuse_emotions,
    normalize_emotion,
    sentiment_to_emotion,
)


class TestEmotionPolicy(unittest.TestCase):
    def test_normalize_emotion_aliases(self):
        self.assertEqual(normalize_emotion("joyful"), "happy")
        self.assertEqual(normalize_emotion("distressed"), "sad")
        self.assertEqual(normalize_emotion("frustrated"), "angry")
        self.assertEqual(normalize_emotion("unknown"), "neutral")

    def test_sentiment_to_emotion(self):
        self.assertEqual(sentiment_to_emotion("positive"), "happy")
        self.assertEqual(sentiment_to_emotion("negative"), "sad")
        self.assertEqual(sentiment_to_emotion("neutral"), "neutral")

    def test_fuse_emotions_prefers_weighted_result(self):
        out = fuse_emotions("happy", "angry", "positive")
        self.assertEqual(out, "happy")

    def test_fuse_emotions_conflict_uses_deterministic_vector(self):
        out = fuse_emotions("happy", "angry", "negative")
        self.assertEqual(out, "angry")

    def test_fuse_emotions_conflict_matrix(self):
        vectors = [
            ("happy", "sad", "neutral", "happy"),
            ("happy", "angry", "neutral", "happy"),
            ("sad", "angry", "positive", "angry"),
            ("sad", "happy", "negative", "sad"),
            ("neutral", "happy", "negative", "sad"),
            ("neutral", "angry", "positive", "happy"),
            ("happy", "neutral", "negative", "happy"),
            ("sad", "neutral", "positive", "sad"),
            ("angry", "neutral", "negative", "sad"),
            ("neutral", "neutral", "positive", "neutral"),
            ("neutral", "neutral", "negative", "neutral"),
            ("neutral", "neutral", "neutral", "neutral"),
        ]
        for camera, audio, sentiment, expected in vectors:
            self.assertEqual(
                fuse_emotions(camera, audio, sentiment),
                expected,
                msg=f"camera={camera} audio={audio} sentiment={sentiment}",
            )

    def test_build_response_by_emotion(self):
        sad = build_response("sad", "I feel down")
        self.assertIn("supportive", sad["response"])
        self.assertTrue(sad["say"])
        angry = build_response("angry", "")
        self.assertIn("calming", angry["response"])


if __name__ == "__main__":
    unittest.main()
