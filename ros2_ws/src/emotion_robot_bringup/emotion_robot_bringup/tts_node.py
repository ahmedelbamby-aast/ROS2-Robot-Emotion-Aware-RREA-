import queue
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TtsNode(Node):
    def __init__(self):
        super().__init__("tts_node")
        self.declare_parameter("engine", "pyttsx3")
        self.declare_parameter("enabled", True)
        self.declare_parameter("log_only_when_unavailable", True)

        self._engine_name = str(self.get_parameter("engine").value).strip().lower()
        self._enabled = bool(self.get_parameter("enabled").value)
        self._log_only_when_unavailable = bool(self.get_parameter("log_only_when_unavailable").value)

        self._pub_status = self.create_publisher(String, "/speech/tts_status", 10)
        self.create_subscription(String, "/robot/say", self.on_say, 10)

        self._q = queue.Queue(maxsize=20)
        self._tts_engine = None
        self._ready = False
        self._init_engine()

        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _publish_status(self, text: str):
        msg = String()
        msg.data = text
        self._pub_status.publish(msg)
        self.get_logger().info(text)

    def _init_engine(self):
        if not self._enabled:
            self._publish_status("tts disabled")
            return
        if self._engine_name != "pyttsx3":
            self._publish_status("tts fallback=log_only reason=unsupported_engine")
            return
        try:
            import pyttsx3

            self._tts_engine = pyttsx3.init()
            self._ready = True
            self._publish_status("tts backend=pyttsx3 ready=true")
        except Exception as exc:
            self._publish_status(f"tts backend=pyttsx3 ready=false error={exc}")

    def on_say(self, msg: String):
        text = msg.data.strip()
        if not text:
            return
        try:
            self._q.put_nowait(text)
        except queue.Full:
            self.get_logger().warning("tts queue full; dropping message")

    def _worker_loop(self):
        while rclpy.ok():
            text = self._q.get()
            if self._ready and self._tts_engine:
                try:
                    self._tts_engine.say(text)
                    self._tts_engine.runAndWait()
                    continue
                except Exception:
                    self._ready = False
                    self._publish_status("tts runtime error; switching to fallback log mode")
            if self._log_only_when_unavailable:
                self.get_logger().info(f"[TTS fallback] {text}")


def main():
    rclpy.init()
    node = TtsNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
