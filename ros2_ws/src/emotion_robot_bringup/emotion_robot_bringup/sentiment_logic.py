import re
from typing import Iterable, List


POSITIVE_TERMS = {
    "happy",
    "great",
    "good",
    "awesome",
    "thanks",
    "thank",
    "love",
    "excellent",
    "glad",
    "relieved",
}
NEGATIVE_TERMS = {
    "sad",
    "angry",
    "bad",
    "upset",
    "hate",
    "stress",
    "stressed",
    "worried",
    "frustrated",
    "anxious",
    "overwhelmed",
}
NEGATORS = {"not", "no", "never", "hardly", "scarcely", "without"}

_TOKEN_RE = re.compile(r"[a-z']+")


def _tokens(text: str) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _has_recent_negator(tokens: Iterable[str]) -> bool:
    return any(tok in NEGATORS for tok in tokens)


def classify_text_sentiment(text: str) -> str:
    toks = _tokens(text)
    if not toks:
        return "neutral"

    score = 0.0
    for idx, token in enumerate(toks):
        base = 0.0
        if token in POSITIVE_TERMS:
            base = 1.0
        elif token in NEGATIVE_TERMS:
            base = -1.0
        if base == 0.0:
            continue
        if _has_recent_negator(toks[max(0, idx - 2) : idx]):
            base *= -0.8
        score += base

    if score >= 1.0:
        return "positive"
    if score <= -1.0:
        return "negative"
    return "neutral"
