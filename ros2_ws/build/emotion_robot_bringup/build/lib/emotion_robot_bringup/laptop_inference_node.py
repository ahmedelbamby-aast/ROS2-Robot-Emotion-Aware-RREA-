import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class LaptopInferenceNode(Node):
    def __init__(self):
        super().__init__("laptop_inference_node")
        self.last_cam = "neutral"
        self.last_audio = "neutral"
        self.create_subscription(String, "/camera/emotion", self.on_cam, 10)
        self.create_subscription(String, "/audio/emotion", self.on_audio, 10)
        self.create_subscription(String, "/speech/text", self.on_text, 10)
        self.pub_final = self.create_publisher(String, "/emotion/final", 10)
        self.pub_response = self.create_publisher(String, "/robot/response", 10)
        self.pub_say = self.create_publisher(String, "/robot/say", 10)

    def on_cam(self, msg):
        self.last_cam = "alert" if "x" in msg.data else "neutral"

    def on_audio(self, msg):
        self.last_audio = "calm" if "bytes=" in msg.data else "neutral"

    def on_text(self, msg):
        text = msg.data.lower()
        mood = "supportive"
        if "sad" in text or "stress" in text:
            mood = "comforting"
        elif "happy" in text:
            mood = "joyful"
        final = String()
        final.data = f"{mood}|cam={self.last_cam}|audio={self.last_audio}"
        response = String()
        response.data = f"inference response for input: {msg.data[:80]}"
        say = String()
        say.data = "I understand. Let's take the next step together."
        self.pub_final.publish(final)
        self.pub_response.publish(response)
        self.pub_say.publish(say)


def main():
    rclpy.init()
    node = LaptopInferenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
