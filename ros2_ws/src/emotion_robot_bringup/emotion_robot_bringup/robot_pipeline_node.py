import rclpy
from diagnostic_msgs.msg import DiagnosticArray
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String, UInt8MultiArray

from .inference_logic import compute_emotion_policy
from .robot_pipeline_policy import (
    normalize_audio_state,
    normalize_camera_state,
    normalize_status_state,
    should_publish_policy,
)


class RobotPipelineNode(Node):
    def __init__(self):
        super().__init__("robot_pipeline_node")
        self.pub_emotion = self.create_publisher(String, "/emotion/final", 10)
        self.pub_response = self.create_publisher(String, "/robot/response", 10)
        self.pub_say = self.create_publisher(String, "/robot/say", 10)

        self.create_subscription(Image, "/camera/image_raw", self.on_camera, 10)
        self.create_subscription(UInt8MultiArray, "/audio/raw", self.on_audio, 10)
        self.create_subscription(DiagnosticArray, "/robot/status", self.on_status, 10)

        self._camera = {"label": "neutral"}
        self._audio = {"label": "neutral"}
        self._status = {"text": ""}
        self._last_policy = {}

    def on_camera(self, msg: Image):
        new_state = normalize_camera_state(msg.width, msg.height, msg.encoding)
        if new_state != self._camera:
            self._camera = new_state
            self._recompute_and_publish()

    def on_audio(self, msg: UInt8MultiArray):
        new_state = normalize_audio_state(len(msg.data))
        if new_state != self._audio:
            self._audio = new_state
            self._recompute_and_publish()

    def on_status(self, msg: DiagnosticArray):
        if not msg.status:
            new_state = normalize_status_state("ok", "", 0)
        else:
            first = msg.status[0]
            new_state = normalize_status_state(first.name, first.message, first.level)
        if new_state != self._status:
            self._status = new_state
            self._recompute_and_publish()

    def _recompute_and_publish(self):
        policy = compute_emotion_policy(
            self._status.get("text", ""),
            self._camera.get("label", "neutral"),
            self._audio.get("label", "neutral"),
        )
        if not should_publish_policy(self._last_policy, policy):
            return
        self._last_policy = policy

        emotion_msg = String()
        emotion_msg.data = policy["emotion"]
        response_msg = String()
        response_msg.data = policy["response"]
        say_msg = String()
        say_msg.data = policy["say"]

        self.pub_emotion.publish(emotion_msg)
        self.pub_response.publish(response_msg)
        self.pub_say.publish(say_msg)


def main():
    rclpy.init()
    node = RobotPipelineNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
