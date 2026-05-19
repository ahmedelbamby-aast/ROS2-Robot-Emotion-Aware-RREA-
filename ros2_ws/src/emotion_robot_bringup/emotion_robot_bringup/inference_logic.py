import json
import re
from typing import Any, Dict


def _parse_json_object(raw: str) -> Dict[str, Any]:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def parse_camera_payload(raw: str) -> Dict[str, Any]:
    payload = _parse_json_object(raw)
    if payload:
        label = str(payload.get("label", payload.get("emotion", "neutral"))).lower()
        return {
            "label": label if label else "neutral",
            "width": int(payload.get("width", 0) or 0),
            "height": int(payload.get("height", 0) or 0),
            "confidence": float(payload.get("confidence", 0.0) or 0.0),
        }

    match = re.search(r"(\d+)\s*x\s*(\d+)", raw or "")
    if match:
        return {"label": "neutral", "width": int(match.group(1)), "height": int(match.group(2)), "confidence": 0.0}
    return {"label": "neutral", "width": 0, "height": 0, "confidence": 0.0}


def parse_audio_payload(raw: str) -> Dict[str, Any]:
    payload = _parse_json_object(raw)
    if payload:
        label = str(payload.get("label", "neutral")).lower()
        return {
            "label": label if label else "neutral",
            "bytes": int(payload.get("bytes", 0) or 0),
            "rms": float(payload.get("rms", 0.0) or 0.0),
        }

    match = re.search(r"bytes=(\d+)", raw or "")
    size = int(match.group(1)) if match else 0
    return {"label": "calm" if size > 0 else "neutral", "bytes": size, "rms": 0.0}


def parse_text_payload(raw: str) -> Dict[str, str]:
    payload = _parse_json_object(raw)
    if payload:
        text = str(payload.get("text", payload.get("data", "")))
        source = str(payload.get("source", payload.get("kind", "text")))
        return {"text": text, "source": source}
    return {"text": raw or "", "source": "text"}


def compute_emotion_policy(text: str, camera_label: str, audio_label: str) -> Dict[str, str]:
    t = (text or "").lower()
    cam = (camera_label or "neutral").lower()
    aud = (audio_label or "neutral").lower()

    distress_terms = ("sad", "stress", "anxious", "upset", "scared", "overwhelmed", "tired")
    positive_terms = ("happy", "great", "excited", "good", "awesome", "thank")

    if any(term in t for term in distress_terms):
        emotion = "comforting"
    elif any(term in t for term in positive_terms):
        emotion = "joyful"
    elif cam in {"sad", "distressed", "worried"} or aud in {"anxious", "tense"}:
        emotion = "supportive"
    else:
        emotion = "supportive"

    response = f"policy={emotion};cam={cam};audio={aud};text_len={len(t)}"

    if emotion == "comforting":
        say = "I hear you. Let's take one slow breath and handle this together."
    elif emotion == "joyful":
        say = "That is great to hear. Let's keep this positive momentum going."
    else:
        say = "I am here with you. Tell me what would help most right now."

    return {"emotion": emotion, "response": response, "say": say}
