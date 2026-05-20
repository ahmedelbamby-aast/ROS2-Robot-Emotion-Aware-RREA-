import time
import tempfile
import wave
import os
from typing import Dict

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray

from .speech_helpers import choose_fallback_text, decode_audio_bytes, extract_text_from_audio_payload


def resolve_stt_backend(backend: str, model_backend: str) -> str:
    backend_clean = str(backend or "").strip().lower()
    if backend_clean:
        return backend_clean
    return str(model_backend or "").strip().lower()


def resolve_topic_name(primary: str, fallback: str) -> str:
    primary_clean = str(primary or "").strip()
    if primary_clean:
        return primary_clean
    return str(fallback or "").strip()


def resolve_whisper_model_size(model_size: str, whisper_model: str) -> str:
    model_size_clean = str(model_size or "").strip()
    if model_size_clean:
        return model_size_clean
    whisper_model_clean = str(whisper_model or "").strip()
    if whisper_model_clean:
        return whisper_model_clean
    return "tiny"


def resolve_whisper_language(language: str, whisper_language: str) -> str:
    language_clean = str(language or "").strip()
    if language_clean:
        return language_clean
    whisper_language_clean = str(whisper_language or "").strip()
    if whisper_language_clean:
        return whisper_language_clean
    return "en"


def resolve_optional_text(value: str) -> str | None:
    clean = str(value or "").strip()
    return clean or None


def resolve_whisper_model_dir(model_dir: str, model_cache_dir: str) -> str | None:
    direct = resolve_optional_text(model_dir)
    if direct:
        return direct
    cache = resolve_optional_text(model_cache_dir)
    if cache:
        return cache
    return resolve_optional_text(os.getenv("WHISPER_MODEL_DIR", ""))


def resolve_whisper_task(task: str) -> str:
    task_clean = str(task or "").strip().lower()
    if task_clean in {"transcribe", "translate"}:
        return task_clean
    return "transcribe"


class SttNode(Node):
    def __init__(self):
        super().__init__("stt_node")
        self.declare_parameter("enabled", True)
        self.declare_parameter("use_microphone", True)
        self.declare_parameter("backend", "")
        self.declare_parameter("model_backend", "whisper")
        self.declare_parameter("transcript_topic", "")
        self.declare_parameter("audio_topic", "")
        self.declare_parameter("audio_text_topic", "")
        self.declare_parameter("status_topic", "")
        self.declare_parameter("whisper_model_size", "")
        self.declare_parameter("whisper_model", "")
        self.declare_parameter("whisper_language", "")
        self.declare_parameter("language", "")
        self.declare_parameter("whisper_sample_rate", 16000)
        self.declare_parameter("whisper_channels", 1)
        self.declare_parameter("whisper_sample_width", 2)
        self.declare_parameter("whisper_model_dir", "")
        self.declare_parameter("whisper_model_cache_dir", "")
        self.declare_parameter("whisper_device", "")
        self.declare_parameter("whisper_task", "transcribe")
        self.declare_parameter("whisper_fp16", False)
        self.declare_parameter("whisper_temperature", -1.0)
        self.declare_parameter("fallback_enabled", True)
        self.declare_parameter("fallback_text", "I heard audio, but speech recognition is unavailable.")
        self.declare_parameter("min_audio_bytes", 1600)
        self.declare_parameter("fallback_cooldown_sec", 2.0)

        self._enabled = bool(self.get_parameter("enabled").value)
        self._use_microphone = bool(self.get_parameter("use_microphone").value)
        self._model_backend = resolve_stt_backend(
            backend=str(self.get_parameter("backend").value),
            model_backend=str(self.get_parameter("model_backend").value),
        )
        transcript_topic = resolve_topic_name(
            primary=str(self.get_parameter("transcript_topic").value),
            fallback="/speech/text",
        )
        audio_topic = resolve_topic_name(
            primary=str(self.get_parameter("audio_topic").value),
            fallback="/audio/raw",
        )
        audio_text_topic = resolve_topic_name(
            primary=str(self.get_parameter("audio_text_topic").value),
            fallback="/audio/raw_text",
        )
        status_topic = resolve_topic_name(
            primary=str(self.get_parameter("status_topic").value),
            fallback="/speech/stt_status",
        )
        self._fallback_enabled = bool(self.get_parameter("fallback_enabled").value)
        self._fallback_text = str(self.get_parameter("fallback_text").value)
        self._min_audio_bytes = int(self.get_parameter("min_audio_bytes").value)
        self._fallback_cooldown_ns = int(float(self.get_parameter("fallback_cooldown_sec").value) * 1_000_000_000)
        self._whisper_model_size = resolve_whisper_model_size(
            model_size=str(self.get_parameter("whisper_model_size").value),
            whisper_model=str(self.get_parameter("whisper_model").value),
        )
        self._whisper_language = resolve_whisper_language(
            language=str(self.get_parameter("language").value),
            whisper_language=str(self.get_parameter("whisper_language").value),
        )
        self._whisper_sample_rate = int(self.get_parameter("whisper_sample_rate").value)
        self._whisper_channels = int(self.get_parameter("whisper_channels").value)
        self._whisper_sample_width = int(self.get_parameter("whisper_sample_width").value)
        self._whisper_model_dir = resolve_whisper_model_dir(
            model_dir=str(self.get_parameter("whisper_model_dir").value),
            model_cache_dir=str(self.get_parameter("whisper_model_cache_dir").value),
        )
        self._whisper_device = resolve_optional_text(str(self.get_parameter("whisper_device").value))
        self._whisper_task = resolve_whisper_task(str(self.get_parameter("whisper_task").value))
        self._whisper_fp16 = bool(self.get_parameter("whisper_fp16").value)
        self._whisper_temperature = float(self.get_parameter("whisper_temperature").value)
        self._last_emit_ns = 0

        self._pub_text = self.create_publisher(String, transcript_topic, 10)
        self._pub_status = self.create_publisher(String, status_topic, 10)

        self.create_subscription(UInt8MultiArray, audio_topic, self.on_audio_raw, 10)
        self.create_subscription(String, audio_text_topic, self.on_audio_text_payload, 10)

        self._recognizer = None
        self._microphone = None
        self._whisper = None
        self._whisper_model = None
        self._backend_ready = False
        if self._enabled:
            self._init_backend()
        else:
            self._publish_status("stt disabled")

        if self._enabled and self._use_microphone:
            self.create_timer(0.5, self._poll_microphone)

    def _init_backend(self):
        if self._model_backend in ("whisper", "openai_whisper"):
            try:
                import whisper

                self._whisper = whisper
                load_kwargs: Dict[str, str] = {}
                if self._whisper_model_dir:
                    load_kwargs["download_root"] = self._whisper_model_dir
                if self._whisper_device:
                    load_kwargs["device"] = self._whisper_device
                self._whisper_model = whisper.load_model(self._whisper_model_size, **load_kwargs)
                self._backend_ready = True
                self._publish_status(
                    f"backend=whisper ready=true model={self._whisper_model_size} "
                    f"language={self._whisper_language} device={self._whisper_device or 'auto'} "
                    f"model_dir={self._whisper_model_dir or 'default'}"
                )
            except Exception as exc:
                self._publish_status(f"backend=whisper ready=false error={exc}")
            return
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
        if not self._enabled or not self._fallback_enabled:
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
        if not self._enabled:
            return
        audio = decode_audio_bytes(msg.data)
        if not audio:
            return
        if self._model_backend in ("whisper", "openai_whisper") and self._backend_ready:
            text = self._transcribe_whisper(audio)
            if text:
                self._publish_text(text)
                return
        self._maybe_publish_fallback(len(audio))

    def on_audio_text_payload(self, msg: String):
        if not self._enabled:
            return
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

    def _transcribe_whisper(self, audio_bytes: bytes) -> str:
        if not self._whisper_model:
            return ""
        if self._whisper_sample_rate <= 0 or self._whisper_channels <= 0 or self._whisper_sample_width <= 0:
            self._publish_status("backend=whisper invalid_audio_params=true")
            return ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                with wave.open(tmp.name, "wb") as wav_file:
                    wav_file.setnchannels(self._whisper_channels)
                    wav_file.setsampwidth(self._whisper_sample_width)
                    wav_file.setframerate(self._whisper_sample_rate)
                    wav_file.writeframes(audio_bytes)
                transcribe_kwargs = {
                    "language": self._whisper_language,
                    "task": self._whisper_task,
                    "fp16": self._whisper_fp16,
                }
                if self._whisper_temperature >= 0.0:
                    transcribe_kwargs["temperature"] = self._whisper_temperature
                result = self._whisper_model.transcribe(tmp.name, **transcribe_kwargs)
            text = str((result or {}).get("text", "")).strip()
            return text
        except Exception as exc:
            self._publish_status(f"backend=whisper transcribe_error={exc}")
            return ""


def main():
    rclpy.init()
    node = SttNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
