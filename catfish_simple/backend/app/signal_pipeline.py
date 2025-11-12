import hashlib
import io
import json
from typing import List, Dict, Any

import numpy as np
from PIL import Image, ImageFilter, ExifTags
from urllib.parse import urlparse
from sqlalchemy.orm import Session

from .models import Upload
from .providers import MockReverseImageProvider, ReverseImageProvider

SEVERITY_POINTS = {"low": 5, "med": 15, "high": 30}
ADVICE = [
    "Request a live selfie with today's date",
    "Schedule a quick video call",
    "Never send money or gift cards to new online contacts",
]
SCAM_KEYWORDS = [
    "oil rig",
    "widowed engineer",
    "crypto wallet",
    "urgent surgery",
    "gift card",
    "western union",
    "whatsapp",
]
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl"}
THROWAWAY_DOMAINS = {"mailinator.com", "yopmail.com", "guerrillamail.com"}

reverse_provider: ReverseImageProvider = MockReverseImageProvider()


def _dhash(image: Image.Image, hash_size: int = 8) -> str:
    img = image.convert("L").resize((hash_size + 1, hash_size), Image.LANCZOS)
    pixels = np.array(img)
    diff = pixels[:, 1:] > pixels[:, :-1]
    bits = "".join("1" if v else "0" for v in diff.flatten())
    return hex(int(bits, 2))[2:].zfill(len(bits) // 4)


def _hamming_distance(hash1: str, hash2: str) -> int:
    return sum(ch1 != ch2 for ch1, ch2 in zip(hash1, hash2))


def _extract_exif(image: Image.Image) -> Dict[str, Any]:
    exif_data = image.getexif() or {}
    parsed = {}
    for tag_id, value in exif_data.items():
        tag = ExifTags.TAGS.get(tag_id, str(tag_id))
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", errors="ignore")
            except Exception:
                value = value.hex()
        parsed[tag] = value
    return parsed


def _exif_signals(exif: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals = []
    if not exif:
        signals.append({"type": "exif_missing", "severity": "med", "details": {}})
        return signals
    required = ["DateTime", "Model"]
    missing = [field for field in required if field not in exif]
    if missing:
        signals.append(
            {
                "type": "exif_incomplete",
                "severity": "low",
                "details": {"missing": missing},
            }
        )
    return signals


def _ai_signals(image: Image.Image) -> List[Dict[str, Any]]:
    gray = image.convert("L")
    arr = np.array(gray, dtype=np.float32) / 255.0
    smoothness = 1.0 - float(np.std(arr))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_score = float(np.mean(np.array(edges) / 255.0))
    fft = np.fft.fft2(arr)
    freq = np.abs(fft)
    center = max(1, freq.shape[0] // 4)
    focus_region = freq[center:-center or None, center:-center or None]
    high_freq_ratio = float(np.mean(focus_region) / (np.mean(freq) + 1e-6)) if focus_region.size else 0.5
    quantized = (arr * 16).round() / 16
    quant_error = float(np.mean(np.abs(arr - quantized)))
    confidence = min(1.0, (smoothness + edge_score + high_freq_ratio + quant_error) / 4)
    signals = []
    if confidence > 0.55:
        signals.append(
            {
                "type": "ai_gen_suspect",
                "severity": "high",
                "details": {
                    "confidence": round(confidence, 2),
                    "smoothness": round(smoothness, 3),
                    "edge_score": round(edge_score, 3),
                },
            }
        )
    else:
        signals.append(
            {
                "type": "ai_metrics",
                "severity": "low",
                "details": {
                    "smoothness": round(smoothness, 3),
                    "edge_score": round(edge_score, 3),
                    "high_freq_ratio": round(high_freq_ratio, 3),
                },
            }
        )
    return signals


def _text_signals(
    profile_url: str | None,
    notes: str | None,
    profile_bio: str | None,
    conversation_text: str | None,
) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []
    combined_text = " ".join(filter(None, [notes, profile_bio, conversation_text]))
    notes_lower = combined_text.lower()
    for keyword in SCAM_KEYWORDS:
        if keyword in notes_lower:
            signals.append(
                {
                    "type": "text_flag",
                    "severity": "med",
                    "details": {"keyword": keyword},
                }
            )
    if profile_url:
        url = profile_url.lower()
        parsed = urlparse(url if url.startswith("http") else f"http://{url}")
        domain = parsed.netloc or parsed.path
        if any(short in domain for short in SHORTENERS):
            signals.append(
                {
                    "type": "link_shortener",
                    "severity": "med",
                    "details": {"url": profile_url},
                }
            )
        if any(throw in domain for throw in THROWAWAY_DOMAINS):
            signals.append(
                {
                    "type": "throwaway_domain",
                    "severity": "high",
                    "details": {"domain": domain},
                }
            )
    return signals


def _reverse_image_signals(image_bytes: bytes) -> List[Dict[str, Any]]:
    matches = reverse_provider.search(image_bytes)
    signals: List[Dict[str, Any]] = []
    for match in matches:
        severity = "high" if match.similarity >= 0.8 else "med"
        signals.append(
            {
                "type": "reverse_image_match",
                "severity": severity,
                "details": {
                    "similarity": match.similarity,
                    "source_url": match.source_url,
                    "description": match.description,
                },
            }
        )
    return signals


def _duplicate_signals(phash: str, session: Session) -> List[Dict[str, Any]]:
    threshold = 8  # smaller distance = more similar
    signals: List[Dict[str, Any]] = []
    existing = session.query(Upload).filter(Upload.phash.isnot(None)).all()
    for item in existing:
        if not item.phash:
            continue
        distance = _hamming_distance(phash, item.phash)
        if distance <= threshold:
            signals.append(
                {
                    "type": "possible_reuse",
                    "severity": "high",
                    "details": {"match_id": item.id, "distance": distance},
                }
            )
            break
    return signals


def aggregate(signals: List[Dict[str, Any]]) -> tuple[int, float, List[str]]:
    if not signals:
        return 5, 0.2, ADVICE
    raw = sum(SEVERITY_POINTS.get(sig.get("severity"), 5) for sig in signals)
    score = max(0, min(100, raw))
    confidence = max(0.2, min(1.0, 0.2 + 0.15 * len(signals)))
    return score, confidence, ADVICE


def analyze_upload(
    data: bytes,
    profile_url: str | None,
    notes: str | None,
    profile_bio: str | None,
    conversation_text: str | None,
    session: Session,
) -> Dict[str, Any]:
    image = Image.open(io.BytesIO(data)).convert("RGB")
    sha = hashlib.sha256(data).hexdigest()
    phash = _dhash(image)
    exif = _extract_exif(image)

    signals: List[Dict[str, Any]] = []
    signals += _duplicate_signals(phash, session)
    signals += _exif_signals(exif)
    signals += _ai_signals(image)
    signals += _text_signals(profile_url, notes, profile_bio, conversation_text)
    signals += _reverse_image_signals(data)

    risk_score, confidence, advice = aggregate(signals)

    return {
        "sha256": sha,
        "phash": phash,
        "signals": signals,
        "risk_score": risk_score,
        "confidence": confidence,
        "advice": ADVICE.copy(),
        "exif": exif,
    }
