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
    probs = {label_: float(probs_in[label_]) for label_ in LABELS}
    if any((not math.isfinite(v)) or v < 0 or v > 1 for v in probs.values()):
        raise ValueError(f"Invalid probabilities: {probs}")
    total = sum(probs.values())
    if total <= 0:
        raise ValueError("Probability mass is zero")
    probs = {k: v / total for k, v in probs.items()}
    return {"label": label, "probabilities": probs, "reason_short": str(obj.get("reason_short", "")).strip()}
