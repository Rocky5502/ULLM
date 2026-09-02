from __future__ import annotations

import json
import math
import re
from typing import Any

from .schemas import LABELS


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Some gateways/models wrap an otherwise valid object in prose or fences.
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in model response")
        return json.loads(match.group(0))


def parse_prediction(text: str) -> dict[str, Any]:
    obj = _extract_json(text)
    label = str(obj.get("label", "")).strip().title()
    if label not in LABELS:
        raise ValueError(f"Invalid label: {label!r}")
    probs_in = obj.get("probabilities")
    if not isinstance(probs_in, dict):
        raise ValueError("Missing probabilities object")
    try:
        probs_raw = {label_: float(probs_in[label_]) for label_ in LABELS}
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Malformed probabilities object: {probs_in!r}") from exc
    if any((not math.isfinite(v)) or v < 0 or v > 1 for v in probs_raw.values()):
        raise ValueError(f"Invalid probabilities: {probs_raw}")
    total = sum(probs_raw.values())
    if total <= 0:
        raise ValueError("Probability mass is zero")
    probs = {k: v / total for k, v in probs_raw.items()}
    max_value = max(probs.values())
    argmax_labels = {k for k, v in probs.items() if abs(v - max_value) <= 1e-12}
    return {
        "label": label,
        "probabilities": probs,
        "reason_short": str(obj.get("reason_short", "")).strip(),
        "probability_sum_raw": total,
        "normalization_delta": abs(total - 1.0),
        "argmax_consistent": label in argmax_labels,
    }
