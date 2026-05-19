import json
import socket
import threading

import rclpy
from diagnostic_msgs.msg import DiagnosticArray
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String, UInt8MultiArray
from tf2_msgs.msg import TFMessage

from .common import load_project_config, resolve_gateway_target, send_json_line


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
        self.connect_and_start()

    def connect_and_start(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
        threading.Thread(target=self.reader, daemon=True).start()
        self.get_logger().info(f"connected to laptop gateway at {self.host}:{self.port}")

    def reader(self):
        f = self.sock.makefile("r", encoding="utf-8")
        for line in f:
            msg = json.loads(line.strip())
            out = String()
            out.data = msg.get("data", "")
            topic = msg.get("topic")
            if topic == "/emotion/final":
                self.pub_emotion.publish(out)
            elif topic == "/robot/response":
                self.pub_response.publish(out)
            elif topic == "/robot/say":
                self.pub_say.publish(out)

    def send(self, topic, data):
        if not self.sock:
            return
        with self.lock:
            send_json_line(self.sock, {"topic": topic, "data": data})

    def on_image(self, msg):
        self.send("/camera/image_raw", f"{msg.width}x{msg.height}")

    def on_audio(self, msg):
        self.send("/audio/raw", f"bytes={len(msg.data)}")

    def on_odom(self, msg):
        self.send("/odom", f"x={msg.pose.pose.position.x:.3f},y={msg.pose.pose.position.y:.3f}")

    def on_tf(self, msg):
        self.send("/tf", f"frames={len(msg.transforms)}")

    def on_status(self, msg):
        self.send("/robot/status", f"status={msg.status[0].name if msg.status else 'ok'}")


def main():
    rclpy.init()
    node = RobotGatewayNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
