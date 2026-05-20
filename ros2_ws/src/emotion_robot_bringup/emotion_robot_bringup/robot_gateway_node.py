import json
import socket
import threading
import time

import rclpy
from diagnostic_msgs.msg import DiagnosticArray
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String, UInt8MultiArray
from tf2_msgs.msg import TFMessage

from .common import load_project_config, resolve_gateway_target, send_json_line


def route_robot_incoming_topic(topic):
    if topic == "/emotion/final":
        return "emotion"
    if topic == "/robot/response":
        return "response"
    if topic == "/robot/say":
        return "say"
    return None


def shape_camera_payload(msg, stamp_ns):
    return {
        "kind": "camera",
        "width": int(msg.width),
        "height": int(msg.height),
        "encoding": msg.encoding,
        "stamp_ns": int(stamp_ns),
        "label": "neutral",
    }


def shape_audio_payload(msg, stamp_ns):
    return {
        "kind": "audio",
        "bytes": int(len(msg.data)),
        "stamp_ns": int(stamp_ns),
        "label": "calm",
    }


def shape_odom_payload(msg, stamp_ns):
    return {
        "kind": "odom",
        "x": round(float(msg.pose.pose.position.x), 3),
        "y": round(float(msg.pose.pose.position.y), 3),
        "stamp_ns": int(stamp_ns),
    }


def shape_tf_payload(msg, stamp_ns):
    return {
        "kind": "tf",
        "frames": int(len(msg.transforms)),
        "stamp_ns": int(stamp_ns),
    }


def shape_status_payload(msg, stamp_ns):
    return {
        "kind": "status",
        "status": msg.status[0].name if msg.status else "ok",
        "level": int(msg.status[0].level) if msg.status else 0,
        "stamp_ns": int(stamp_ns),
    }


class RobotGatewayNode(Node):
    def __init__(self):
        super().__init__("robot_gateway_node")
        cfg = load_project_config()
        self.host, self.port = resolve_gateway_target(cfg)
        self.sock = None
        self.lock = threading.Lock()
        self.pub_emotion = self.create_publisher(String, "/emotion/final", 10)
        self.pub_response = self.create_publisher(String, "/robot/response", 10)
        self.pub_say = self.create_publisher(String, "/robot/say", 10)

        self.create_subscription(Image, "/camera/image_raw", self.on_image, 10)
        self.create_subscription(UInt8MultiArray, "/audio/raw", self.on_audio, 10)
        self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.create_subscription(TFMessage, "/tf", self.on_tf, 10)
        self.create_subscription(DiagnosticArray, "/robot/status", self.on_status, 10)
        self.create_subscription(String, "/speech/text", self.on_speech_text, 10)
        self.connect_and_start()

    def connect_and_start(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
        # Use blocking mode for the long-lived reader loop after initial connect.
        self.sock.settimeout(None)
        threading.Thread(target=self.reader, daemon=True).start()
        self.get_logger().info(f"connected to laptop gateway at {self.host}:{self.port}")

    def reader(self):
        try:
            f = self.sock.makefile("r", encoding="utf-8")
            for line in f:
                if not line.strip():
                    continue
                msg = json.loads(line.strip())
                out = String()
                out.data = msg.get("data", "")
                route = route_robot_incoming_topic(msg.get("topic"))
                if route == "emotion":
                    self.pub_emotion.publish(out)
                elif route == "response":
                    self.pub_response.publish(out)
                elif route == "say":
                    self.pub_say.publish(out)
        except Exception as exc:
            self.get_logger().warning(f"gateway reader stopped: {exc}")

    def send(self, topic, data):
        if not self.sock:
            return
        with self.lock:
            send_json_line(self.sock, {"topic": topic, "data": data})

    def on_image(self, msg):
        payload = shape_camera_payload(msg, time.time_ns())
        self.send("/camera/image_raw", json.dumps(payload, separators=(",", ":")))

    def on_audio(self, msg):
        payload = shape_audio_payload(msg, time.time_ns())
        self.send("/audio/raw", json.dumps(payload, separators=(",", ":")))

    def on_odom(self, msg):
        payload = shape_odom_payload(msg, time.time_ns())
        self.send("/odom", json.dumps(payload, separators=(",", ":")))

    def on_tf(self, msg):
        payload = shape_tf_payload(msg, time.time_ns())
        self.send("/tf", json.dumps(payload, separators=(",", ":")))

    def on_status(self, msg):
        payload = shape_status_payload(msg, time.time_ns())
        self.send("/robot/status", json.dumps(payload, separators=(",", ":")))

    def on_speech_text(self, msg):
        self.send("/speech/text", msg.data)


def main():
    rclpy.init()
    node = RobotGatewayNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
