from __future__ import annotations

import json

from scripts.analyze_contract_consistency import analyze


def write(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def base_row(example_id: str, label: str, probs: dict[str, float], gold: str = "Unknown") -> dict:
    return {
        "model_requested": "m",
        "prompt_type": "neutral",
        "example": {
            "id": example_id,
            "group": "C_Ambiguous_Accomplishment",
            "label": gold,
        },
        "prediction": {
            "label": label,
            "probabilities": probs,
            "argmax_consistent": label in [k for k, v in probs.items() if v == max(probs.values())],
        },
    }


def test_contract_consistency_preserves_and_counts_mismatch(tmp_path):
    path = tmp_path / "m.jsonl"
    write(
        path,
        [
            base_row("C_001", "Unknown", {"True": 0.55, "False": 0.05, "Unknown": 0.40}),
            base_row("C_002", "Unknown", {"True": 0.10, "False": 0.10, "Unknown": 0.80}),
        ],
    )
    summary, items = analyze(path)
    assert summary["n"] == 2
    assert summary["mismatch_n"] == 1
    assert summary["mismatch_rate"] == 0.5
    assert summary["mismatch_C_n"] == 1
    assert items[0]["id"] == "C_001"
    assert items[0]["stated_label"] == "Unknown"
    assert items[0]["argmax_label"] == "True"
    assert abs(items[0]["top2_gap"] - 0.15) < 1e-12
