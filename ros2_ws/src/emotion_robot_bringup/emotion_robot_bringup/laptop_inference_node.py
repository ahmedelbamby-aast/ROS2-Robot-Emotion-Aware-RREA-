import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .inference_logic import compute_emotion_policy, parse_audio_payload, parse_camera_payload, parse_text_payload


class LaptopInferenceNode(Node):
    def __init__(self):
        super().__init__("laptop_inference_node")
        self.last_cam = {"label": "neutral"}
        self.last_audio = {"label": "neutral"}
        self.create_subscription(String, "/camera/emotion", self.on_cam, 10)
        self.create_subscription(String, "/audio/emotion", self.on_audio, 10)
        self.create_subscription(String, "/speech/text", self.on_text, 10)
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
        policy = compute_emotion_policy(text, self.last_cam.get("label", "neutral"), self.last_audio.get("label", "neutral"))
        final = String()
        final.data = policy["emotion"]
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
