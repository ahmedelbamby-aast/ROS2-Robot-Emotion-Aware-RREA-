import json
import socket
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .common import load_project_config, send_json_line


def route_incoming_topic(topic):
    if topic == "/camera/image_raw":
        return "/camera/emotion"
    if topic == "/audio/raw":
        return "/audio/emotion"
    if topic in {"/odom", "/tf", "/robot/status", "/speech/text"}:
        return "/speech/text"
    return None


class LaptopGatewayNode(Node):
    def __init__(self):
        super().__init__("laptop_gateway_node")
        cfg = load_project_config()
        self.port = int(cfg["gateway"]["port"])
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", self.port))
        self.server.listen(1)
        self.conn = None
        self.conn_lock = threading.Lock()

        self.pub_cam = self.create_publisher(String, "/camera/emotion", 10)
        self.pub_audio = self.create_publisher(String, "/audio/emotion", 10)
        self.pub_text = self.create_publisher(String, "/speech/text", 10)

        self.create_subscription(String, "/emotion/final", lambda m: self.send("/emotion/final", m.data), 10)
        self.create_subscription(String, "/robot/response", lambda m: self.send("/robot/response", m.data), 10)
        self.create_subscription(String, "/robot/say", lambda m: self.send("/robot/say", m.data), 10)
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def accept_loop(self):
        self.get_logger().info(f"laptop gateway listening on :{self.port}")
        while rclpy.ok():
            conn, _ = self.server.accept()
            with self.conn_lock:
                self.conn = conn
            self.get_logger().info("robot connected")
            f = conn.makefile("r", encoding="utf-8")
            for line in f:
                msg = json.loads(line.strip())
                topic = msg.get("topic")
                data = msg.get("data", "")
                dst = route_incoming_topic(topic)
                if not dst:
                    continue
                out = String()
                out.data = data
                if dst == "/camera/emotion":
                    self.pub_cam.publish(out)
                elif dst == "/audio/emotion":
                    self.pub_audio.publish(out)
                elif dst == "/speech/text":
                    self.pub_text.publish(out)

    def send(self, topic, data):
        with self.conn_lock:
            if not self.conn:
                return
            send_json_line(self.conn, {"topic": topic, "data": data})


def main():
    rclpy.init()
    node = LaptopGatewayNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
