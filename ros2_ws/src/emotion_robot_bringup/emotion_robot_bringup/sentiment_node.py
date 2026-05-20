import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .emotion_policy import normalize_sentiment
from .sentiment_logic import classify_text_sentiment


class SentimentNode(Node):
    def __init__(self):
        super().__init__("sentiment_node")
        self.pub = self.create_publisher(String, "/text/sentiment", 10)
        self.create_subscription(String, "/speech/text", self.on_text, 10)

    def on_text(self, msg: String):
        sentiment = classify_text_sentiment(msg.data)
        out = String()
        out.data = normalize_sentiment(sentiment)
        self.pub.publish(out)


def main():
    rclpy.init()
    node = SentimentNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
