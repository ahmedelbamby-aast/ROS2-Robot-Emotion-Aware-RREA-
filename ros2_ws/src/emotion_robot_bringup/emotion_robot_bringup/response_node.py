import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .emotion_policy import build_response, normalize_emotion


class ResponseNode(Node):
    def __init__(self):
        super().__init__("response_node")
        self.pub_response = self.create_publisher(String, "/robot/response", 10)
        self.pub_say = self.create_publisher(String, "/robot/say", 10)
        self.create_subscription(String, "/emotion/final", self.on_emotion, 10)
        self.create_subscription(String, "/speech/text", self.on_text, 10)
        self.latest_text = ""

    def on_text(self, msg: String):
        self.latest_text = msg.data

    def on_emotion(self, msg: String):
        final_emotion = normalize_emotion(msg.data)
        payload = build_response(final_emotion, self.latest_text)
        out_response = String()
        out_response.data = payload["response"]
        out_say = String()
        out_say.data = payload["say"]
        self.pub_response.publish(out_response)
        self.pub_say.publish(out_say)


def main():
    rclpy.init()
    node = ResponseNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
