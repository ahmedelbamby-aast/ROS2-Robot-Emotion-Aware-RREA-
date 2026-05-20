import json
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray

from .audio_features import classify_audio_emotion, extract_audio_features
from .emotion_policy import normalize_emotion


class AudioEmotionNode(Node):
    def __init__(self):
        super().__init__("audio_emotion_node")
        self.sample_rate = int(self.declare_parameter("sample_rate", 16000).value)
        self.input_topic = str(self.declare_parameter("input_topic", "/audio/raw").value or "/audio/raw")
        self.output_topic = str(self.declare_parameter("output_topic", "/audio/emotion").value or "/audio/emotion")
        self.model_profile_path = str(self.declare_parameter("model_profile_path", "").value or "").strip()
        self._profile = self._load_profile(self.model_profile_path)
        self.pub = self.create_publisher(String, self.output_topic, 10)
        self.create_subscription(UInt8MultiArray, self.input_topic, self.on_audio, 10)

    def on_audio(self, msg: UInt8MultiArray):
        data = bytes(msg.data)
        label = self._classify(data)
        out = String()
        out.data = normalize_emotion(label)
        self.pub.publish(out)

    def _classify(self, data: bytes) -> str:
        features = extract_audio_features(data, sample_rate=self.sample_rate)
        return classify_audio_emotion(features, profile=self._profile)

    def _load_profile(self, profile_path: str):
        if not profile_path:
            return None
        path = Path(profile_path)
        if not path.exists():
            self.get_logger().warning(f"Audio model profile path not found: {profile_path}")
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return raw
            self.get_logger().warning(f"Audio model profile at {profile_path} is not a JSON object")
            return None
        except Exception as exc:
            self.get_logger().warning(f"Failed to load audio model profile at {profile_path}: {exc}")
            return None


def main():
    rclpy.init()
    node = AudioEmotionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
