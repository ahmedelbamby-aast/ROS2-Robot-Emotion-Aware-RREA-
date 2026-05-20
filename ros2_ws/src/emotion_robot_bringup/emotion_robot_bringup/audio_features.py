from __future__ import annotations

from typing import Optional

import numpy as np

try:
    import librosa  # type: ignore
except Exception:  # pragma: no cover - exercised via tests with monkeypatching
    librosa = None


def pcm16_from_bytes(data: bytes) -> np.ndarray:
    if not data:
        return np.array([], dtype=np.float32)
    if len(data) % 2 == 1:
        data = data[:-1]
    if not data:
        return np.array([], dtype=np.float32)
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    return samples / 32768.0


def _safe_pitch_proxy(samples: np.ndarray, sr: int) -> float:
    if samples.size < int(sr * 0.1):
        return 0.0
    windowed = samples * np.hanning(samples.size)
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(windowed.size, d=1.0 / float(sr))
    if spectrum.size < 3:
        return 0.0
    spectrum[0] = 0.0
    peak_idx = int(np.argmax(spectrum))
    peak_hz = float(freqs[peak_idx])
    if peak_hz < 50.0 or peak_hz > 500.0:
        return 0.0
    return peak_hz


def extract_audio_features(data: bytes, sample_rate: int = 16000) -> dict:
    samples = pcm16_from_bytes(data)
    if samples.size == 0:
        return {"energy": 0.0, "rms": 0.0, "pitch": 0.0, "zcr": 0.0, "backend": "none"}

    energy = float(np.mean(np.square(samples)))
    rms = float(np.sqrt(max(energy, 0.0)))
    zcr = float(np.mean(np.abs(np.diff(np.signbit(samples).astype(np.int8))))) if samples.size > 1 else 0.0

    if librosa is not None:
        try:
            frame_rms = librosa.feature.rms(y=samples)
            rms = float(np.mean(frame_rms))
            pitches, magnitudes = librosa.piptrack(y=samples, sr=sample_rate)
            if pitches.size and magnitudes.size:
                idx = np.argmax(magnitudes, axis=0)
                chosen = pitches[idx, np.arange(pitches.shape[1])]
                chosen = chosen[chosen > 0]
                if chosen.size:
                    return {
                        "energy": energy,
                        "rms": rms,
                        "pitch": float(np.median(chosen)),
                        "zcr": zcr,
                        "backend": "librosa",
                    }
        except Exception:
            pass

    return {
        "energy": energy,
        "rms": rms,
        "pitch": _safe_pitch_proxy(samples, sample_rate),
        "zcr": zcr,
        "backend": "fallback",
    }


def classify_audio_emotion(features: dict, profile: Optional[dict] = None) -> str:
    model_type = str((profile or {}).get("model_type", "")).strip().lower()
    if model_type == "linear_v1":
        predicted = _classify_with_linear_model(features, profile or {})
        if predicted:
            return predicted

    energy = float(features.get("energy", 0.0))
    rms = float(features.get("rms", 0.0))
    pitch = float(features.get("pitch", 0.0))
    zcr = float(features.get("zcr", 0.0))
    cfg = profile or {}
    sad_energy_max = float(cfg.get("sad_energy_max", 0.0008))
    sad_rms_max = float(cfg.get("sad_rms_max", 0.03))
    sad_zcr_max = float(cfg.get("sad_zcr_max", 0.2))
    angry_rms_min = float(cfg.get("angry_rms_min", 0.11))
    angry_pitch_min = float(cfg.get("angry_pitch_min", 190.0))
    angry_loud_rms_min = float(cfg.get("angry_loud_rms_min", 0.14))
    angry_loud_energy_min = float(cfg.get("angry_loud_energy_min", 0.008))
    angry_zcr_rms_min = float(cfg.get("angry_zcr_rms_min", 0.13))
    angry_zcr_min = float(cfg.get("angry_zcr_min", 0.25))
    happy_rms_min = float(cfg.get("happy_rms_min", 0.07))
    happy_pitch_min = float(cfg.get("happy_pitch_min", 130.0))
    happy_zcr_min = float(cfg.get("happy_zcr_min", 0.08))

    if energy < sad_energy_max and rms < sad_rms_max and zcr < sad_zcr_max:
        return "sad"
    if (rms > angry_rms_min and pitch > angry_pitch_min) or (
        rms > angry_loud_rms_min and energy > angry_loud_energy_min
    ) or (rms > angry_zcr_rms_min and zcr > angry_zcr_min):
        return "angry"
    if rms > happy_rms_min and pitch > happy_pitch_min and zcr > happy_zcr_min:
        return "happy"
    return "neutral"


def _classify_with_linear_model(features: dict, profile: dict) -> Optional[str]:
    labels = profile.get("labels")
    feature_order = profile.get("feature_order")
    weights = profile.get("weights")
    if not isinstance(labels, list) or not labels:
        return None
    if not isinstance(feature_order, list) or not feature_order:
        return None
    if not isinstance(weights, dict) or not weights:
        return None

    best_label = None
    best_score = None
    for label in labels:
        label_name = str(label).strip().lower()
        if label_name not in {"happy", "sad", "angry", "neutral"}:
            continue
        coeffs = weights.get(label_name)
        if not isinstance(coeffs, list) or len(coeffs) != len(feature_order):
            continue
        score = float(profile.get("bias", {}).get(label_name, 0.0)) if isinstance(profile.get("bias"), dict) else 0.0
        valid = True
        for idx, feature_name in enumerate(feature_order):
            try:
                value = float(features.get(str(feature_name), 0.0))
                coef = float(coeffs[idx])
            except (TypeError, ValueError):
                valid = False
                break
            score += value * coef
        if not valid:
            continue
        if best_score is None or score > best_score:
            best_label = label_name
            best_score = score

    return best_label
