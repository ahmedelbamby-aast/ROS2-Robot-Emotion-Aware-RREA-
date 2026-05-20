import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .emotion_policy import build_response, fuse_emotions, normalize_emotion
from .inference_logic import parse_audio_payload, parse_camera_payload, parse_text_payload
from .sentiment_logic import classify_text_sentiment


class LaptopInferenceNode(Node):
    def __init__(self):
        super().__init__("laptop_inference_node")
        self.last_cam = {"label": "neutral"}
        self.last_audio = {"label": "neutral"}
        self.last_text = ""
        self.create_subscription(String, "/camera/emotion", self.on_cam, 10)
        self.create_subscription(String, "/audio/emotion", self.on_audio, 10)
        self.create_subscription(String, "/speech/text", self.on_text, 10)
        self.pub_sentiment = self.create_publisher(String, "/text/sentiment", 10)
        self.pub_final = self.create_publisher(String, "/emotion/final", 10)
        self.pub_response = self.create_publisher(String, "/robot/response", 10)
        self.pub_say = self.create_publisher(String, "/robot/say", 10)

    def on_cam(self, msg):
        self.last_cam = parse_camera_payload(msg.data)

    def on_audio(self, msg):
        self.last_audio = parse_audio_payload(msg.data)

    def on_text(self, msg):
        parsed = parse_text_payload(msg.data)
        text = parsed["text"]
        self.last_text = text
        sentiment = classify_text_sentiment(text)
        sentiment_msg = String()
        sentiment_msg.data = sentiment
        self.pub_sentiment.publish(sentiment_msg)

        final_emotion = fuse_emotions(
            normalize_emotion(self.last_cam.get("label", "neutral")),
            normalize_emotion(self.last_audio.get("label", "neutral")),
            sentiment,
        )
        policy = build_response(final_emotion, text)

        final = String()
        final.data = final_emotion
        response = String()
        response.data = policy["response"]
        say = String()
        say.data = policy["say"]
        self.pub_final.publish(final)
        self.pub_response.publish(response)
        self.pub_say.publish(say)


def main():
    rclpy.init()
    node = LaptopInferenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
