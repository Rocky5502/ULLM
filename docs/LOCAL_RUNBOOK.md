# Local frozen-run runbook

This runbook is the handoff from the completed no-API preparation phase to the later local paid execution. It is intentionally operational and should be followed in order.

## 0. Ground rules

- Run from a clean clone of `Rocky5502/ULLM` on the commit you intend to evaluate.
- Do not edit `configs/experiment.yaml`, `configs/models.yaml`, `configs/preregistered_hypotheses.yaml`, or prompt definitions after the first paid call without starting a new protocol version.
- Keep `ZZZ_API_KEY` only in the shell environment. Never paste it into source files, notebooks, logs, issues, or commits.
- Raw API outputs remain under ignored `results/raw/` directories. Back them up separately after the run.
- If `ZZZ_BASE_URL` is set in the environment, it must exactly match `configs/experiment.yaml`; `check_models.py` refuses to inspect a different gateway from the one the runner will call.

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

`requirements.txt` remains the compatibility range used by broad CI. `requirements-frozen.txt` is the exact tested environment snapshot for the frozen experiment.

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

The downloader writes `data/MANIFEST.local.json`; the structural validator writes `data/dataset_manifest.json`. Preflight requires both manifests to agree with the committed provenance record and the actual local bytes.

## 3. Freeze and rehearse the complete study without an API key

Create a machine-readable pre-API protocol snapshot:

```bash
python scripts/freeze_protocol.py
```

The snapshot records the current Git commit, model IDs, config/hypothesis/manuscript hashes, prompt hashes, dataset identity, seed/decoding settings, statistics/selective settings and call matrix. It explicitly records that no empirical result is claimed.

Then rehearse the exact request plan:

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

Finally record a credential-safe environment snapshot:

```bash
python scripts/environment_snapshot.py
```

It records only whether the API key exists, never its value. These local evidence files live under ignored `artifacts/local/`.

## 4. Set the API key only after offline gates pass

### Windows PowerShell

```powershell
$env:ZZZ_API_KEY = "<your-local-key>"
```

### Linux/macOS

```bash
export ZZZ_API_KEY='<your-local-key>'
```

Do not echo, screenshot, commit, or paste the credential into chat/issues/logs.

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

The snapshot includes catalogue hash, configured file hashes, request/timestamp metadata, and the raw catalogue response, but never the authorization header or API-key value.

If an ID is absent or maps unexpectedly, **stop**. Do not silently substitute another model after paid execution begins. Record any protocol change in Git first, then rerun preflight, protocol freeze and offline rehearsal.

## 6. Use the guarded frozen runner

### Windows

```powershell
.\scripts\run_frozen.ps1
```

### POSIX

```bash
bash scripts/run_frozen.sh
```

The canonical runner now repeats the critical no-API gates automatically before touching the live catalogue: preflight, machine-readable protocol freeze, complete 15,800-request offline rehearsal, and environment snapshot. It then performs the live `/models` check and stops before chat-completion calls.

The runner asks for the explicit token `SMOKE`. That authorizes only the 100-call smoke test.

After the smoke test finishes:

1. its hard audit must pass;
2. a SHA-256 evidence manifest is automatically generated for the raw smoke directory;
3. inspect requested/returned routing identifiers, parse failures, probability schema, usage metadata and representative raw responses;
4. do not continue if the audit fails or endpoint routing is suspicious;
5. type `RUN` only when the smoke stage is acceptable.

`RUN` authorizes the 15,800-call frozen main study before retries. Each completed main-study stage is audited and then automatically sealed with an external checksum manifest under `results/raw/<run-id>.checksums.json`.

## 7. Failure recovery

Do not manually edit JSONL output files.

For compatible interrupted stages, use the same run ID with `--resume`. For request or parse failures, use `--resume --retry-failures`; the runner atomically removes failed rows before replacement so `(example_id, repeat)` keys remain unique.

The run manifest rejects unsafe resume if frozen scientific fields differ. Dry-run and live manifests also cannot be mixed because `execution_mode` is resume-critical.

After any retry changes a raw run, rerun the audit and checksum sealing step; the canonical runner already does this automatically when resumed through it.

## 8. Preserve raw evidence immediately after execution

Before manuscript interpretation, copy the following to a separate read-only backup location:

- all `results/raw/<run-id>/manifest.json` files;
- all raw JSONL files;
- all `results/raw/<run-id>.checksums.json` files;
- live model-catalogue snapshot;
- `data/MANIFEST.local.json` and `data/dataset_manifest.json`;
- pre-API protocol freeze snapshot;
- pre/post-run environment snapshots;
- exact Git commit SHA;
- any gateway billing/usage export available for cost reconciliation.

If a run was executed outside the canonical script, seal it manually before copying:

```bash
python scripts/checksum_run.py results/raw/<run-id>
```

The checksum manifest is deliberately written outside the run directory it authenticates.

## 9. Audit first, analyze second

The canonical frozen scripts invoke audits around the experiment. If running analysis manually, never bypass `scripts/audit_run.py`.

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
- preserve the frozen code/data/results snapshot used for the submitted PDF;
- follow `docs/ARTIFACT_POLICY.md` before releasing any raw provider output or third-party data bytes.
