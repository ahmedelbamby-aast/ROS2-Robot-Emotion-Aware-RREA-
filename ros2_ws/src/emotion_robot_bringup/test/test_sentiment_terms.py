import unittest

from emotion_robot_bringup.sentiment_logic import NEGATIVE_TERMS, POSITIVE_TERMS, classify_text_sentiment


class TestSentimentTerms(unittest.TestCase):
    def test_positive_terms_include_common_words(self):
        self.assertIn("happy", POSITIVE_TERMS)
        self.assertIn("good", POSITIVE_TERMS)

    def test_negative_terms_include_common_words(self):
        self.assertIn("sad", NEGATIVE_TERMS)
        self.assertIn("angry", NEGATIVE_TERMS)

    def test_classify_text_sentiment(self):
        self.assertEqual(classify_text_sentiment("I am very happy today"), "positive")
        self.assertEqual(classify_text_sentiment("I feel stressed"), "negative")
        self.assertEqual(classify_text_sentiment("hello"), "neutral")
        self.assertEqual(classify_text_sentiment("This is not good"), "neutral")
        self.assertEqual(classify_text_sentiment("I am not sad anymore"), "neutral")

    def test_classify_text_sentiment_case_and_punctuation(self):
        self.assertEqual(classify_text_sentiment("THANKS!!! This is AWESOME."), "positive")
        self.assertEqual(classify_text_sentiment("I am... FRUSTRATED!!!"), "negative")
        self.assertEqual(classify_text_sentiment("???!"), "neutral")


if __name__ == "__main__":
    unittest.main()
