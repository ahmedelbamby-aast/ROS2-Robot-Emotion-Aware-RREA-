import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray

from .speech_helpers import choose_fallback_text, decode_audio_bytes, extract_text_from_audio_payload


class SttNode(Node):
    def __init__(self):
        super().__init__("stt_node")
        self.declare_parameter("use_microphone", False)
        self.declare_parameter("model_backend", "none")
        self.declare_parameter("fallback_enabled", True)
        self.declare_parameter("fallback_text", "I heard audio, but speech recognition is unavailable.")
        self.declare_parameter("min_audio_bytes", 1600)
        self.declare_parameter("fallback_cooldown_sec", 2.0)

        self._use_microphone = bool(self.get_parameter("use_microphone").value)
        self._model_backend = str(self.get_parameter("model_backend").value).strip().lower()
        self._fallback_enabled = bool(self.get_parameter("fallback_enabled").value)
        self._fallback_text = str(self.get_parameter("fallback_text").value)
        self._min_audio_bytes = int(self.get_parameter("min_audio_bytes").value)
        self._fallback_cooldown_ns = int(float(self.get_parameter("fallback_cooldown_sec").value) * 1_000_000_000)
        self._last_emit_ns = 0

        self._pub_text = self.create_publisher(String, "/speech/text", 10)
        self._pub_status = self.create_publisher(String, "/speech/stt_status", 10)

        self.create_subscription(UInt8MultiArray, "/audio/raw", self.on_audio_raw, 10)
        self.create_subscription(String, "/audio/raw_text", self.on_audio_text_payload, 10)

        self._recognizer = None
        self._microphone = None
        self._backend_ready = False
        self._init_backend()

        if self._use_microphone:
            self.create_timer(0.5, self._poll_microphone)

    def _init_backend(self):
        if self._model_backend != "speech_recognition":
            self._publish_status(f"backend=none fallback={str(self._fallback_enabled).lower()}")
            return
        try:
            import speech_recognition as sr

            self._recognizer = sr.Recognizer()
            if self._use_microphone:
                self._microphone = sr.Microphone()
            self._backend_ready = True
            self._publish_status("backend=speech_recognition ready=true")
        except Exception as exc:
            self._publish_status(f"backend=speech_recognition ready=false error={exc}")

    def _publish_status(self, text: str):
        msg = String()
        msg.data = text
        self._pub_status.publish(msg)
        self.get_logger().info(text)

    def _publish_text(self, text: str):
        out = String()
        out.data = text
        self._pub_text.publish(out)

    def _maybe_publish_fallback(self, audio_size: int):
        if not self._fallback_enabled:
            return
        now_ns = time.time_ns()
        chosen = choose_fallback_text(
            audio_size_bytes=audio_size,
            min_audio_bytes=self._min_audio_bytes,
            fallback_text=self._fallback_text,
            last_emit_ns=self._last_emit_ns,
            now_ns=now_ns,
            cooldown_ns=self._fallback_cooldown_ns,
        )
        if chosen:
            self._last_emit_ns = now_ns
            self._publish_text(chosen)

    def on_audio_raw(self, msg: UInt8MultiArray):
        audio = decode_audio_bytes(msg.data)
        if not audio:
            return
        self._maybe_publish_fallback(len(audio))

    def on_audio_text_payload(self, msg: String):
        parsed = extract_text_from_audio_payload(msg.data)
        if parsed:
            self._publish_text(parsed)
            return
        self._maybe_publish_fallback(len(msg.data.encode("utf-8")))

    def _poll_microphone(self):
        if not (self._backend_ready and self._recognizer and self._microphone):
            return
        try:
            import speech_recognition as sr

            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.1)
                audio = self._recognizer.listen(source, timeout=0.5, phrase_time_limit=2.0)
            try:
                text = self._recognizer.recognize_sphinx(audio)
            except sr.UnknownValueError:
                text = ""
            if text.strip():
                self._publish_text(text.strip())
            else:
                self._maybe_publish_fallback(2000)
        except Exception:
            self._maybe_publish_fallback(2000)


def main():
    rclpy.init()
    node = SttNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
