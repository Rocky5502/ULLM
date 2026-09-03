from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.audit_model_controls import reasoning_content
from ullm.run import _validate_model_request_overrides


def test_deepseek_non_thinking_override_is_frozen_before_main_results():
    config = yaml.safe_load(Path("configs/experiment.yaml").read_text(encoding="utf-8"))
    assert config["model_request_overrides"] == {
        "deepseek-v4-pro": {"thinking": {"type": "disabled"}}
    }
    assert config["deterministic"]["temperature"] == 0.0
    assert config["sampling"]["temperature"] == 0.7
    assert config["sampling"]["samples_per_item"] == 5


def test_model_request_overrides_cannot_replace_common_controls():
    config = {"model_request_overrides": {"deepseek-v4-pro": {"temperature": 0.0}}}
    with pytest.raises(SystemExit, match="may not replace common controls"):
        _validate_model_request_overrides(config, ["deepseek-v4-pro"])


def test_reasoning_content_reader_detects_provider_cot():
    row = {
        "raw_response": {
            "choices": [{"message": {"content": "{}", "reasoning_content": "hidden cot"}}]
        }
    }
    assert reasoning_content(row) == "hidden cot"
    row["raw_response"]["choices"][0]["message"]["reasoning_content"] = None
    assert reasoning_content(row) == ""
