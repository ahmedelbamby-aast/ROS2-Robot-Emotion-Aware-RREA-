from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .emotion_policy import normalize_emotion


@dataclass
class VisionResult:
    emotion: str
    face_found: bool
    backend: str


def map_deepface_emotion(value: str) -> str:
    v = (value or "").strip().lower()
    if v in {"happy"}:
        return "happy"
    if v in {"sad", "fear"}:
        return "sad"
    if v in {"angry", "disgust"}:
        return "angry"
    return "neutral"


def image_msg_to_bgr(msg: Any, cv2_module: Any) -> Optional[np.ndarray]:
    try:
        width = int(msg.width)
        height = int(msg.height)
        if width <= 0 or height <= 0:
            return None
        raw = np.frombuffer(msg.data, dtype=np.uint8)
        encoding = (getattr(msg, "encoding", "") or "").lower()
        if encoding == "mono8":
            if raw.size < width * height:
                return None
            gray = raw[: width * height].reshape((height, width))
            return cv2_module.cvtColor(gray, cv2_module.COLOR_GRAY2BGR)
        if encoding in {"rgb8", "bgr8"}:
            if raw.size < width * height * 3:
                return None
            frame = raw[: width * height * 3].reshape((height, width, 3))
            if encoding == "rgb8":
                frame = cv2_module.cvtColor(frame, cv2_module.COLOR_RGB2BGR)
            return frame
    except Exception:
        return None
    return None


def detect_largest_face_bgr(
    frame_bgr: np.ndarray, cv2_module: Any, cascade_path: Optional[str] = None
) -> Optional[Tuple[int, int, int, int]]:
    try:
        gray = cv2_module.cvtColor(frame_bgr, cv2_module.COLOR_BGR2GRAY)
        resolved_cascade = cascade_path or (cv2_module.data.haarcascades + "haarcascade_frontalface_default.xml")
        cascade = cv2_module.CascadeClassifier(resolved_cascade)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        if faces is None or len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda f: int(f[2]) * int(f[3]))
        return int(x), int(y), int(w), int(h)
    except Exception:
        return None


def _extract_deepface_label(
    result: Any, min_score: float = 35.0, min_margin: float = 8.0
) -> Optional[str]:
    if isinstance(result, list):
        if not result:
            return None
        result = result[0]
    if not isinstance(result, dict):
        return None
    dominant = result.get("dominant_emotion")
    if isinstance(dominant, str):
        return dominant
    emotions = result.get("emotion")
    if isinstance(emotions, dict) and emotions:
        ranked = sorted(((str(k), float(v)) for k, v in emotions.items()), key=lambda kv: kv[1], reverse=True)
        top_label, top_score = ranked[0]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        if top_score < float(min_score) or (top_score - second_score) < float(min_margin):
            return None
        return top_label
    return None


def classify_camera_emotion(
    msg: Any,
    cv2_module: Any,
    deepface_cls: Any = None,
    use_deepface: bool = True,
    cascade_path: Optional[str] = None,
    deepface_detector_backend: str = "opencv",
    deepface_min_score: float = 35.0,
    deepface_min_margin: float = 8.0,
) -> VisionResult:
    if cv2_module is None:
        return VisionResult("neutral", False, "none")

    frame = image_msg_to_bgr(msg, cv2_module)
    if frame is None:
        return VisionResult("neutral", False, "opencv")

    face = detect_largest_face_bgr(frame, cv2_module, cascade_path=cascade_path)
    if face is None:
        return VisionResult("neutral", False, "opencv")

    if not use_deepface or deepface_cls is None:
        return VisionResult("neutral", True, "opencv")

    x, y, w, h = face
    try:
        face_roi = frame[y : y + h, x : x + w]
        result: Dict[str, Any] = deepface_cls.analyze(
            face_roi,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend=(deepface_detector_backend or "opencv"),
        )
        label = _extract_deepface_label(
            result,
            min_score=deepface_min_score,
            min_margin=deepface_min_margin,
        )
        return VisionResult(normalize_emotion(map_deepface_emotion(label or "")), True, "deepface")
    except Exception:
        return VisionResult("neutral", True, "opencv")
