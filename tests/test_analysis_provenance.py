from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_analysis_provenance_noncanonical_smoke(tmp_path: Path) -> None:
    raw = tmp_path / "raw" / "synthetic-run"
    raw.mkdir(parents=True)
    (raw / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": "synthetic-run",
                "execution_mode": "live",
                "git_commit": "raw-synthetic-sha",
                "dataset_sha256": "dataset-sha",
                "config_sha256": "config-sha",
                "models_sha256": "models-sha",
                "prompt_type": "neutral",
                "mode": "deterministic",
                "selected_n": 1,
            }
        ),
        encoding="utf-8",
    )
    (raw / "model.jsonl").write_text('{"synthetic": true}\n', encoding="utf-8")

    processed = tmp_path / "processed"
    figures = tmp_path / "figures"
    tables = tmp_path / "tables"
    processed.mkdir()
    figures.mkdir()
    tables.mkdir()
    (processed / "summary.csv").write_text("x\n1\n", encoding="utf-8")
    (processed / "audit_synthetic.json").write_text(
        '{"status":"PASS"}\n', encoding="utf-8"
    )
    (figures / "figure.pdf").write_bytes(b"synthetic-pdf-placeholder")
    (tables / "table.tex").write_text("% synthetic\n", encoding="utf-8")
    out = processed / "analysis_manifest.json"

    subprocess.run(
        [
            sys.executable,
            "scripts/freeze_analysis_provenance.py",
            "--raw-dir",
            str(raw),
            "--processed-dir",
            str(processed),
            "--figures-dir",
            str(figures),
            "--paper-generated-dir",
            str(tables),
            "--out",
            str(out),
            "--allow-noncanonical",
        ],
        cwd=ROOT,
        check=True,
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    assert payload["evidence_class"] == "synthetic/non-evidence"
    assert payload["scientific_tree_dirty"] is False
    assert payload["analysis_git_commit"]
    assert [row["run_id"] for row in payload["raw_runs"]] == ["synthetic-run"]
    assert payload["raw_runs"][0]["raw_execution_git_commit"] == "raw-synthetic-sha"
