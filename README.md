# ULLM: Uncertainty Understanding in Large Language Models

Research artifact for an IASEAI'27 main-conference submission.

ULLM studies a fundamental reliability question for large language models:

> When semantic interpretation is underdetermined, do LLMs represent uncertainty faithfully, does uncertainty align with actual errors, and can uncertainty signals support safer decision control?

The project evaluates uncertainty representation beyond simple accuracy by connecting semantic ambiguity, confidence calibration, error awareness, and selective verification.

---

## Research Overview

Large language models often produce confident predictions in situations where the underlying world state is incomplete or ambiguous. ULLM investigates whether models distinguish:

- uncertainty about the world state,
- uncertainty about their own prediction,
- and uncertainty useful for downstream decision making.

The study uses controlled semantic reasoning tasks based on imperfective interpretation phenomena and evaluates frontier LLM systems under reproducible protocols.

## Research Questions

**RQ1 — Uncertainty Recognition**  
Do LLMs recognize semantic under-specification and represent uncertainty appropriately?

**RQ2 — Uncertainty Faithfulness**  
Which uncertainty signals best identify model errors and overconfident failures?

**RQ3 — Uncertainty-Aware Control**  
Can uncertainty estimates enable selective verification and reduce risky predictions while maintaining useful coverage?

---

## Artifact Status

| Component | Status |
|---|---|
| Benchmark provenance | Frozen |
| Experiment protocol | Frozen |
| Request construction | Reproducible |
| Offline rehearsal | Supported |
| Audit pipeline | Released |
| Analysis pipeline | Released |
| Live empirical execution | Requires authorized model gateway |

This repository intentionally separates engineering readiness from scientific evidence. Final empirical claims are generated only from audited frozen runs.

---

## Models and Evaluation

The evaluation framework supports multiple routed LLM endpoints:

- GPT-5.6-sol
- Claude Sonnet 5
- Gemini 3.7 Flash
- DeepSeek V4 Pro
- Qwen 3.8 Max

Model identifiers represent recorded gateway endpoints used during execution. Scientific conclusions are attached only to observed audited runs.

---

## Experiment Design

The frozen evaluation protocol contains:

- deterministic uncertainty estimation;
- repeated sampling with K=5;
- semantic robustness conditions;
- label-order robustness testing;
- verifier-based selective control analysis.

The complete planned evaluation contains 15,800 main-study calls before retries:

| Stage | Calls |
|-|-:|
| Neutral deterministic | 2,000 |
| Neutral repeated sampling | 10,000 |
| Strict logic robustness | 600 |
| Definition-aware robustness | 600 |
| Label-order robustness | 600 |
| Verifier evaluation | 2,000 |

---

## Reproducibility

Install dependencies:

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

Run validation:

```bash
python scripts/validate_project.py
python scripts/synthetic_pipeline_smoke.py
pytest -q
```

Run the complete offline rehearsal:

```bash
python scripts/offline_rehearsal.py
```

No API credentials are required for protocol verification and pipeline testing.

---

## Repository Structure

```
ULLM/
├── paper/          Manuscript sources and figures
├── src/            Core experiment implementation
├── configs/        Frozen experiment configurations
├── scripts/        Execution, auditing, and analysis tools
├── docs/           Protocol and reproducibility documentation
├── tests/          Automated validation tests
└── results/        Generated outputs (local artifacts)
```

---

## Research Foundation

ULLM is informed by previous work on semantic interpretation and uncertainty evaluation in large language models, including **The Imperfective Paradox in Large Language Models**. ULLM extends this direction by focusing on uncertainty representation, calibration, and risk-aware control rather than reproducing the original evaluation objective.

---

## Citation

If you use this artifact, please cite the associated IASEAI'27 paper after publication.

---

## License and Data

Code and documentation follow the repository license. Third-party benchmark resources remain subject to their original terms. Raw API responses and private execution artifacts are not committed by default.

---

## Current Development Status

The repository is prepared as a research artifact release: frozen protocols, reproducibility scripts, auditing tools, manuscript integration, and analysis infrastructure are maintained under version control.
