from __future__ import annotations

import json

from ullm.run import _critical_manifest_fields, write_request_plan
from ullm.schemas import Example


def example() -> Example:
    return Example(
        id="C_001",
        group="C_Ambiguous_Accomplishment",
        verb_class="Creation",
        verb="build",
        premise="The carpenter was building a gazebo.",
        hypothesis="The carpenter built a gazebo.",
        label="Unknown",
    )


def test_write_request_plan_is_exact_and_content_minimized(tmp_path):
    path = tmp_path / "plan.jsonl"
    n = write_request_plan(
        path,
        models=["model-a", "model-b"],
        examples=[example()],
        temperature=0.7,
        repeats=3,
        seed=42,
        max_tokens=220,
        prompt_type="neutral",
        label_order=("True", "False", "Unknown"),
    )
    assert n == 6

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 6
    assert {(r["model_requested"], r["repeat"]) for r in rows} == {
        ("model-a", 0),
        ("model-a", 1),
        ("model-a", 2),
        ("model-b", 0),
        ("model-b", 1),
        ("model-b", 2),
    }
    assert {r["seed_requested"] for r in rows} == {42, 43, 44}
    assert {r["example_id"] for r in rows} == {"C_001"}
    assert {r["group"] for r in rows} == {"C_Ambiguous_Accomplishment"}
    assert all(len(r["messages_sha256"]) == 64 for r in rows)
    assert all(len(r["prompt_sha256"]) == 64 for r in rows)

    # The request-plan artifact is intended to prove construction/counts without
    # duplicating benchmark text or provider content.
    forbidden = {"messages", "premise", "hypothesis", "raw_text", "raw_response"}
    assert all(not (forbidden & set(r)) for r in rows)


def test_execution_mode_is_resume_critical():
    dry = {
        "dataset_sha256": "a",
        "dataset_n": 400,
        "selected_n": 400,
        "selected_ids": ["A_001"],
        "models": ["model-a"],
        "mode": "deterministic",
        "execution_mode": "dry_run",
        "prompt_type": "neutral",
        "prompt_sha256": "b",
        "label_order": ["True", "False", "Unknown"],
        "config_sha256": "c",
        "models_sha256": "d",
        "git_commit": "e",
        "max_tokens": 220,
    }
    live = dict(dry, execution_mode="live")
    assert _critical_manifest_fields(dry) != _critical_manifest_fields(live)
