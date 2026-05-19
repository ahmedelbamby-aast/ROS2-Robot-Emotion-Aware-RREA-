def normalize_camera_state(width: int, height: int, encoding: str) -> dict:
    has_frame = int(width) > 0 and int(height) > 0
    return {
        "width": int(width),
        "height": int(height),
        "encoding": str(encoding or ""),
        "label": "engaged" if has_frame else "neutral",
    }


def normalize_audio_state(byte_count: int) -> dict:
    size = int(byte_count)
    return {"bytes": size, "label": "calm" if size > 0 else "neutral"}


def normalize_status_state(name: str, message: str, level: int) -> dict:
    status_name = str(name or "ok")
    status_message = str(message or "")
    text = " ".join(p for p in (status_name, status_message) if p).strip()
    return {"name": status_name, "message": status_message, "level": int(level), "text": text}


def should_publish_policy(previous_policy: dict, next_policy: dict) -> bool:
    if not next_policy:
        return False
    return previous_policy != next_policy
