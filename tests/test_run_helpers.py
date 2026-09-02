import json
from collections import Counter

import pytest

from ullm.run import balanced_subset, prepare_resume_output, write_or_validate_manifest
from ullm.schemas import Example


def ex(group: str, i: int) -> Example:
    letter = group[0]
    return Example(
        id=f"{letter}_{i:03d}",
        group=group,
        verb_class="Activity" if letter in "BD" else "Creation",
        verb=f"v-{letter}-{i}",
        premise="p",
        hypothesis="h",
        label={"A": "False", "B": "True", "C": "Unknown", "D": "True"}[letter],
    )


def test_balanced_subset_is_balanced_and_reproducible():
    rows = []
    for letter, group in [
        ("A", "A_Interrupted_Accomplishment"),
        ("B", "B_Interrupted_Activity"),
        ("C", "C_Ambiguous_Accomplishment"),
        ("D", "D_Ambiguous_Activity"),
    ]:
        rows.extend(ex(group, i) for i in range(1, 11))
    a = balanced_subset(rows, 20, 42)
    b = balanced_subset(rows, 20, 42)
    assert [x.id for x in a] == [x.id for x in b]
    assert Counter(x.group[0] for x in a) == Counter({"A": 5, "B": 5, "C": 5, "D": 5})


def test_resume_manifest_rejects_critical_drift(tmp_path):
    path = tmp_path / "manifest.json"
    base = {
        "dataset_sha256": "d",
        "dataset_n": 400,
        "selected_n": 400,
        "selected_ids": ["A_001"],
        "models": ["m"],
        "mode": "deterministic",
        "prompt_type": "neutral",
        "prompt_sha256": "p",
        "label_order": ["True", "False", "Unknown"],
        "config_sha256": "c",
        "models_sha256": "mhash",
        "git_commit": "g",
        "max_tokens": 220,
        "created_utc": "first",
    }
    write_or_validate_manifest(path, base, resume=False)
    same = dict(base, created_utc="later")
    write_or_validate_manifest(path, same, resume=True)
    drifted = dict(base, max_tokens=999)
    with pytest.raises(RuntimeError, match="unsafe resume"):
        write_or_validate_manifest(path, drifted, resume=True)


def test_retry_failure_purge_preserves_only_successes(tmp_path):
    path = tmp_path / "out.jsonl"
    success = {
        "example": {"id": "A_001"},
        "repeat": 0,
        "prediction": {"label": "False"},
        "request_error": None,
    }
    failed = {
        "example": {"id": "A_002"},
        "repeat": 0,
        "prediction": None,
        "request_error": "boom",
    }
    path.write_text(json.dumps(success) + "\n" + json.dumps(failed) + "\n", encoding="utf-8")
    prepare_resume_output(path, retry_failures=True)
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    assert rows == [success]
