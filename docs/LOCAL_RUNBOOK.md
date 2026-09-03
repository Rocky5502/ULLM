# Local frozen-run runbook

This runbook is the handoff from the completed no-API preparation phase to the later local paid execution. It is intentionally operational and should be followed in order.

## 0. Ground rules

- Run from a clean clone of `Rocky5502/ULLM` on the commit you intend to evaluate.
- Do not edit `configs/experiment.yaml`, `configs/models.yaml`, `configs/preregistered_hypotheses.yaml`, or prompt definitions after the first paid call without starting a new protocol version.
- Keep `ZZZ_API_KEY` only in the shell environment. Never paste it into source files, notebooks, logs, issues, or commits.
- Raw API outputs remain under ignored `results/raw/` directories. Back them up separately after the run.

## 1. Create the tested environment

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-frozen.txt
python -m pip check
$env:PYTHONPATH = "src"
```

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-frozen.txt
python -m pip check
export PYTHONPATH=src
```

`requirements.txt` remains the compatibility range used by broad CI. `requirements-frozen.txt` is the tested environment snapshot for the frozen experiment.

## 2. Fetch and validate the exact benchmark

```bash
python scripts/fetch_imperfective_nli.py
python scripts/validate_dataset.py data/imperfectiveNLI.json
python scripts/preflight.py
```

Expected properties:

- upstream source commit: `8845a732d04a0b49e154fbf0db334d48d895b11f`
- upstream Git blob: `e20112c9de1f8c8ab27a8e2b969699b23dcdb186`
- bytes: `100970`
- examples: `400`
- groups: 100 each A/B/C/D
- main-study budget: `15,800` calls before retries

The downloader writes `data/MANIFEST.local.json`. Preflight refuses to proceed if its SHA-256 does not match the local dataset.

## 3. Rehearse the complete study without an API key

```bash
python scripts/offline_rehearsal.py
```

This constructs and audits all six planned main-study request sets:

- neutral deterministic: 2,000
- neutral K=5 sampling: 10,000
- strict-logic robustness: 600
- definition-aware robustness: 600
- reversed-label-order robustness: 600
- verifier cache: 2,000

Total: **15,800 planned requests, zero provider calls**.

The script writes a local snapshot under `artifacts/local/` and individual request-plan manifests under ignored `results/raw/offline-*` directories.

## 4. Set the API key only after offline gates pass

### Windows PowerShell

```powershell
$env:ZZZ_API_KEY = "<your-local-key>"
```

### Linux/macOS

```bash
export ZZZ_API_KEY='<your-local-key>'
```

Do not echo or commit the credential.

## 5. Freeze the live gateway catalogue

```bash
python scripts/check_models.py
```

Inspect the saved catalogue snapshot and confirm that all five configured gateway IDs are available:

- `gpt-5.6-sol`
- `claude-sonnet-5`
- `deepseek-v4-pro`
- `qwen3.8-max`
- `gemini-3.7-flash`

If an ID is absent or maps unexpectedly, **stop**. Do not silently substitute another model after paid execution begins. Record any protocol change in Git first and regenerate the offline rehearsal.

## 6. Use the guarded frozen runner

### Windows

```powershell
.\scripts\run_frozen.ps1
```

### POSIX

```bash
bash scripts/run_frozen.sh
```

The runner must stop before paid chat-completion calls and ask for the explicit token `SMOKE`. That authorizes only the 100-call smoke test.

After the smoke test finishes:

1. allow its audit to complete;
2. inspect routing identifiers, parse failures, probability schema, usage metadata and representative raw responses;
3. do not continue if the audit fails or endpoint routing is suspicious;
4. type `RUN` only when the smoke stage is acceptable.

`RUN` authorizes the 15,800-call frozen main study before retries.

## 7. Failure recovery

Do not manually edit JSONL output files.

For compatible interrupted stages, use the same run ID with `--resume`. For request or parse failures, use `--resume --retry-failures`; the runner atomically removes failed rows before replacement so `(example_id, repeat)` keys remain unique.

The run manifest rejects unsafe resume if frozen scientific fields differ.

## 8. Preserve raw evidence immediately after execution

Before analysis or manuscript editing, make an immutable backup of:

- all `results/raw/<run-id>/manifest.json` files;
- all raw JSONL files;
- live model-catalogue snapshot;
- `data/MANIFEST.local.json`;
- the exact Git commit SHA;
- the local Python/package environment (`python --version`, `pip freeze`);
- any gateway billing/usage export available for cost reconciliation.

Recommended: archive the raw directory and generate SHA-256 checksums before moving or copying it.

## 9. Audit first, analyze second

The canonical frozen scripts already invoke audits around the experiment. If running analysis manually, never bypass `scripts/audit_run.py`.

After all manifests pass, run the complete analysis script:

### Windows

```powershell
.\scripts\analyze_frozen.ps1
```

### POSIX

```bash
bash scripts/analyze_frozen.sh
```

The analysis should produce processed CSVs, bootstrap intervals, vector PDF/SVG figures, and generated LaTeX tables.

## 10. Manuscript update rule

Only audited real outputs may replace `TBD`.

The intended flow is:

`raw JSONL -> audit -> processed CSV -> generated vector figures/tables -> manuscript`

Do not copy individual numbers from terminal output into `paper/main.tex` when a generated artifact exists.

After empirical tables are generated, rebuild the manuscript and run citation/layout checks. Then rewrite Results, Discussion, limitations and Conclusion to match the observed evidence, including null or negative findings.

## 11. Final submission gate

Before IASEAI'27 submission:

- re-check the official 2027 formatting/template instructions;
- migrate away from the provisional AAAI layout if required;
- confirm anonymity requirements;
- verify page count under the official format;
- verify every result claim against generated artifacts;
- verify all references and venue metadata;
- preserve the frozen code/data/results snapshot used for the submitted PDF.
