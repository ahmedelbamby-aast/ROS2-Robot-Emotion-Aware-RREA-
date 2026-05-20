from typing import Dict, Tuple


EMOTIONS = ("happy", "sad", "angry", "neutral")
SENTIMENTS = ("positive", "negative", "neutral")
EMOTION_VECTORS: Dict[str, Tuple[float, float]] = {
    "happy": (0.85, 0.55),
    "sad": (-0.75, -0.45),
    "angry": (-0.85, 0.85),
    "neutral": (0.0, 0.0),
}


def normalize_emotion(value: str) -> str:
    v = (value or "").strip().lower()
    if v in EMOTIONS:
        return v
    if v in {"joyful", "excited"}:
        return "happy"
    if v in {"comforting", "supportive", "distressed", "worried", "anxious"}:
        return "sad"
    if v in {"tense", "frustrated", "mad"}:
        return "angry"
    return "neutral"


def normalize_sentiment(value: str) -> str:
    v = (value or "").strip().lower()
    if v in SENTIMENTS:
        return v
    return "neutral"


def sentiment_to_emotion(sentiment: str) -> str:
    s = normalize_sentiment(sentiment)
    if s == "positive":
        return "happy"
    if s == "negative":
        return "sad"
    return "neutral"


def _dist2(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def fuse_emotions(camera: str, audio: str, sentiment: str) -> str:
    cam = normalize_emotion(camera)
    aud = normalize_emotion(audio)
    txt = sentiment_to_emotion(sentiment)

    weights: Dict[str, float] = {"happy": 0.0, "sad": 0.0, "angry": 0.0, "neutral": 0.0}
    weights[cam] += 0.4
    weights[aud] += 0.3
    weights[txt] += 0.3

    # Resolve high-conflict scenarios with a deterministic valence/arousal vector.
    conflict = len({cam, aud, txt}) == 3 or ("happy" in {cam, aud, txt} and "angry" in {cam, aud, txt})
    if conflict:
        mix = [0.0, 0.0]
        for emo, w in ((cam, 0.4), (aud, 0.3), (txt, 0.3)):
            vec = EMOTION_VECTORS[emo]
            mix[0] += vec[0] * w
            mix[1] += vec[1] * w
        v = (mix[0], mix[1])
        non_neutral_count = sum(1 for emo in (cam, aud, txt) if emo != "neutral")
        candidates = ("happy", "sad", "angry") if non_neutral_count >= 2 else EMOTIONS
        # Prefer closest vector, then higher direct vote weight, then input priority text->camera->audio.
        best = min(
            candidates,
            key=lambda e: (
                _dist2(EMOTION_VECTORS[e], v),
                -weights[e],
                e != txt,
                e != cam,
                e != aud,
            ),
        )
        return best

    # Default weighted vote with deterministic priority text->camera->audio.
    best = max(weights.items(), key=lambda item: (item[1], item[0] == txt, item[0] == cam, item[0] == aud))
    return best[0]


def build_response(final_emotion: str, latest_text: str) -> Dict[str, str]:
    e = normalize_emotion(final_emotion)
    spoken = (latest_text or "").strip()

    if e == "sad":
        say = "I am here with you. We can take this step by step."
        response = "Detected sadness. Responding with a supportive tone."
    elif e == "angry":
        say = "I understand. Let us slow down and solve this calmly."
        response = "Detected anger. Responding with a calming tone."
    elif e == "happy":
        say = "That is great to hear. Let us keep this positive energy."
        response = "Detected happiness. Responding with an encouraging tone."
    else:
        say = "I am ready to help. Tell me what you need."
        response = "Detected neutral emotion. Responding with a general assistant tone."

    if spoken:
        response = f"{response} Last speech: {spoken[:120]}"

    return {"response": response, "say": say}
