import json
from typing import Any, Optional


def decode_audio_bytes(payload: Any) -> bytes:
    if payload is None:
        return b""
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload)
    if isinstance(payload, list):
        try:
            return bytes(int(x) & 0xFF for x in payload)
        except (TypeError, ValueError):
            return b""
    return b""


def extract_text_from_audio_payload(raw: str) -> str:
    """Parse best-effort text from JSON-encoded audio payload.

    Fallback chain:
    1) explicit `text`
    2) metadata/transcript fields
    3) empty string
    """
    if not raw:
        return ""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""

    for key in ("text", "transcript", "utterance"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    meta = payload.get("meta")
    if isinstance(meta, dict):
        for key in ("text", "transcript", "utterance"):
            value = meta.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return ""


def choose_fallback_text(
    audio_size_bytes: int,
    min_audio_bytes: int,
    fallback_text: str,
    last_emit_ns: int,
    now_ns: int,
    cooldown_ns: int,
) -> Optional[str]:
    if audio_size_bytes < min_audio_bytes:
        return None
    if now_ns - last_emit_ns < cooldown_ns:
        return None
    text = fallback_text.strip()
    if not text:
        return None
    return text
