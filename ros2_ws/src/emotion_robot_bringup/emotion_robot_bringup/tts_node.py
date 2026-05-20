import queue
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def resolve_tts_engine(backend: str, engine: str) -> str:
    backend_clean = str(backend or "").strip().lower()
    if backend_clean:
        return backend_clean
    return str(engine or "").strip().lower()


def resolve_topic_name(primary: str, fallback: str) -> str:
    primary_clean = str(primary or "").strip()
    if primary_clean:
        return primary_clean
    return str(fallback or "").strip()


class TtsNode(Node):
    def __init__(self):
        super().__init__("tts_node")
        self.declare_parameter("backend", "pyttsx3")
        self.declare_parameter("engine", "pyttsx3")
        self.declare_parameter("enabled", True)
        self.declare_parameter("output_topic", "")
        self.declare_parameter("say_topic", "/robot/say")
        self.declare_parameter("status_topic", "")
        self.declare_parameter("log_only_when_unavailable", True)

        self._engine_name = resolve_tts_engine(
            backend=str(self.get_parameter("backend").value),
            engine=str(self.get_parameter("engine").value),
        )
        self._enabled = bool(self.get_parameter("enabled").value)
        input_topic = resolve_topic_name(
            primary=str(self.get_parameter("output_topic").value),
            fallback=str(self.get_parameter("say_topic").value),
        )
        status_topic = resolve_topic_name(
            primary=str(self.get_parameter("status_topic").value),
            fallback="/speech/tts_status",
        )
        self._log_only_when_unavailable = bool(self.get_parameter("log_only_when_unavailable").value)

        self._pub_status = self.create_publisher(String, status_topic, 10)
        self.create_subscription(String, input_topic, self.on_say, 10)

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
