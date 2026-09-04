# ULLM Artifact Guide

This repository is the public code artifact for **The Imperfective Uncertainty in Large Language Models**. It is designed so that reviewers and researchers can inspect the complete protocol, validate the benchmark provenance, exercise the analysis stack without paid model access, and reproduce live runs when they have authorized gateway credentials.

## Public artifact boundary

The repository includes:

- frozen experiment and model configuration;
- immutable benchmark provenance metadata and validation tools;
- the core black-box runner and structured-output parser;
- deterministic, sampling, paired, robustness, calibration, selective-control, and bootstrap analyses;
- run-manifest, checksum, completion-budget, model-control, and decision/distribution audits;
- automated tests and zero-API end-to-end rehearsal tools; and
- reproducibility and protocol documentation.

The repository intentionally excludes:

- API keys, populated environment files, private keys, and local credential stores;
- downloaded third-party benchmark bytes;
- raw provider responses and request logs;
- processed empirical outputs and local environment snapshots;
- local virtual environments, editor state, archives, and machine-specific paths; and
- manuscript source/build products, which are maintained separately from this code artifact.

## Reproduce the public validation stack

Create an isolated environment and install the compatibility dependencies:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Fetch the benchmark from the pinned upstream revision and validate it:

```bash
python scripts/fetch_imperfective_nli.py
python scripts/validate_dataset.py data/imperfectiveNLI.json
python scripts/preflight.py
```

Exercise the complete protocol without making a model request:

```bash
python scripts/validate_project.py
python scripts/offline_rehearsal.py
python scripts/synthetic_pipeline_smoke.py
pytest -q
```

The offline rehearsal materializes and audits the full 15,800-request main-study plan without constructing an API client.

## Live execution

Live model calls are deliberately opt-in. The runner reads the gateway credential from the local environment at execution time; the credential value is never written to a manifest or committed file. Use `docs/LOCAL_RUNBOOK.md` for the frozen execution sequence rather than reconstructing commands ad hoc.

Before sharing or releasing a checkout, run:

```bash
python scripts/security_scan.py
```

GitHub Actions runs the same tracked-file security scan together with project validation and tests on every push and pull request.

## Evidence discipline

A live stage is not treated as evidence merely because requests completed. The artifact separates collection from interpretation through explicit audits of record coverage, request/parse failures, completion-budget exhaustion, model-specific controls, checksums, and the predeclared A1 decision/distribution policy. Generated summaries and figures are downstream of those gates.

See `docs/EXPERIMENT_PROTOCOL.md`, `docs/ANALYSIS_PLAN.md`, `docs/CONTRACT_ADJUDICATION_A1.md`, and `docs/REPRODUCIBILITY.md` for the scientific and engineering contracts.
