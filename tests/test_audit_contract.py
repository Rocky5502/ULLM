from __future__ import annotations

import json

from scripts.audit_run import audit_file


def row(
    *,
    normalization_delta: float = 0.0,
    reason: str = "one sentence",
    argmax_consistent: bool = True,
) -> dict:
    return {
        "model_requested": "m",
        "model_returned": "m",
        "temperature": 0.0,
        "max_tokens_requested": 220,
        "repeat": 0,
        "prompt_type": "neutral",
        "prompt_sha256": "p",
        "messages_sha256": "a" * 64,
        "label_order": ["True", "False", "Unknown"],
        "example": {"id": "C_001"},
        "prediction": {
            "label": "Unknown",
            "probabilities": {"True": 0.55, "False": 0.05, "Unknown": 0.40}
            if not argmax_consistent
            else {"True": 0.1, "False": 0.1, "Unknown": 0.8},
            "reason_short": reason,
            "normalization_delta": normalization_delta,
            "argmax_consistent": argmax_consistent,
        },
        "request_error": None,
        "parse_error": None,
        "usage": {"total_tokens": 12},
        "latency_s": 0.1,
        "request_id": "r",
        "http_status": 200,
        "attempts_used": 1,
    }


def manifest(*, execution_mode: str = "live") -> dict:
    return {
        "execution_mode": execution_mode,
        "selected_ids": ["C_001"],
        "selected_n": 1,
        "models": ["m"],
        "samples_per_item": 1,
        "prompt_type": "neutral",
        "prompt_sha256": "p",
        "label_order": ["True", "False", "Unknown"],
        "max_tokens": 220,
        "temperature": 0.0,
    }


def write(path, payload):
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_valid_row_passes(tmp_path):
    path = tmp_path / "run.jsonl"
    write(path, row())
    report = audit_file(path, expected_k=1, manifest=manifest())
    assert report["status"] == "PASS"
    assert report["retry_rows"] == 0


def test_argmax_inconsistency_still_fails_under_strict_policy(tmp_path):
    path = tmp_path / "run.jsonl"
    write(path, row(argmax_consistent=False))
    report = audit_file(path, expected_k=1, manifest=manifest())
    assert report["status"] == "FAIL"
    assert report["argmax_inconsistencies"] == 1
    assert report["argmax_inconsistency_policy"] == "strict-fail"


def test_argmax_inconsistency_can_be_preserved_as_observed_behavior(tmp_path):
    path = tmp_path / "run.jsonl"
    write(path, row(argmax_consistent=False))
    report = audit_file(
        path,
        expected_k=1,
        manifest=manifest(),
        allow_argmax_inconsistency=True,
    )
    assert report["status"] == "PASS"
    assert report["argmax_inconsistencies"] == 1
    assert report["argmax_inconsistency_policy"] == "preserve-and-warn"
    assert any("preserved as observed" in msg for msg in report["warnings"])


def test_large_probability_sum_deviation_is_failure(tmp_path):
    path = tmp_path / "run.jsonl"
    write(path, row(normalization_delta=0.05))
    report = audit_file(path, expected_k=1, manifest=manifest())
    assert report["status"] == "FAIL"
    assert report["normalization_contract_failures"] == 1


def test_missing_short_reason_is_failure(tmp_path):
    path = tmp_path / "run.jsonl"
    write(path, row(reason=""))
    report = audit_file(path, expected_k=1, manifest=manifest())
    assert report["status"] == "FAIL"
    assert report["empty_reason_failures"] == 1


def test_dry_run_manifest_cannot_be_audited_as_live_evidence(tmp_path):
    path = tmp_path / "run.jsonl"
    write(path, row())
    report = audit_file(path, expected_k=1, manifest=manifest(execution_mode="dry_run"))
    assert report["status"] == "FAIL"
    assert any("execution_mode=live" in msg for msg in report["failures"])
