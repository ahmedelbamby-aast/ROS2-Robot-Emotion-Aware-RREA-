import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .emotion_policy import fuse_emotions, normalize_emotion, normalize_sentiment


class FusionNode(Node):
    def __init__(self):
        super().__init__("fusion_node")
        self.pub = self.create_publisher(String, "/emotion/final", 10)
        self.create_subscription(String, "/camera/emotion", self.on_camera, 10)
        self.create_subscription(String, "/audio/emotion", self.on_audio, 10)
        self.create_subscription(String, "/text/sentiment", self.on_sentiment, 10)
        self.camera = "neutral"
        self.audio = "neutral"
        self.sentiment = "neutral"
        self.last_final = ""

    def on_camera(self, msg: String):
        self.camera = normalize_emotion(msg.data)
        self._publish_if_changed()

    def on_audio(self, msg: String):
        self.audio = normalize_emotion(msg.data)
        self._publish_if_changed()

    def on_sentiment(self, msg: String):
        self.sentiment = normalize_sentiment(msg.data)
        self._publish_if_changed()

    def _publish_if_changed(self):
        final = fuse_emotions(self.camera, self.audio, self.sentiment)
        if final == self.last_final:
            return
        self.last_final = final
        out = String()
        out.data = final
        self.pub.publish(out)


def main():
    rclpy.init()
    node = FusionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
