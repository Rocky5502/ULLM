# ULLM: Uncertainty Understanding in Large Language Models

Research artifact for an IASEAI'27 main-conference submission.

ULLM studies a core reliability question for large language models:

> When semantic interpretation is underdetermined, do LLMs represent uncertainty faithfully, does uncertainty align with actual failures, and can uncertainty signals support safer decision control?

The project investigates uncertainty as a reliability mechanism rather than only a confidence score. ULLM connects semantic ambiguity, uncertainty representation, calibration, error awareness, and selective verification.

---

## Overview

Large language models increasingly operate in settings where the underlying world state may be incomplete, ambiguous, or difficult to determine. ULLM evaluates whether models can distinguish:

- uncertainty about the world state;
- uncertainty about their own prediction;
- uncertainty that is useful for downstream risk control.

The artifact provides the experimental protocol, analysis tools, validation scripts, and reproducibility infrastructure used for the study.

---

## Research Foundation

ULLM is inspired by previous work on semantic interpretation in large language models, including **The Imperfective Paradox in Large Language Models**. Instead of reproducing that evaluation objective, ULLM focuses on uncertainty representation, calibration, and uncertainty-aware control.

---

## Artifact Components

| Component | Status |
|---|---|
| Benchmark protocol | Frozen |
| Experiment configuration | Released |
| Validation pipeline | Released |
| Audit tools | Released |
| Analysis scripts | Released |
| Raw private model responses | Not included |

---

## Evaluation Pipeline

ULLM evaluates uncertainty through:

1. controlled semantic ambiguity;
2. deterministic prediction analysis;
3. repeated sampling consistency;
4. robustness evaluation;
5. selective verification.

The artifact preserves reproducibility information while excluding private credentials and restricted execution logs.

---

## Repository Structure

```text
ULLM/
├── assets/        Research figures for documentation
├── src/           Core implementation
├── scripts/       Execution and analysis utilities
├── configs/       Experiment configurations
├── docs/          Protocol and reproducibility documents
├── tests/         Automated validation
└── results/       Generated local outputs
```

---

## Reproducibility

Install dependencies:

```bash
pip install -r requirements.txt
```

Validate installation:

```bash
python scripts/validate_project.py
pytest -q
```

The repository supports protocol verification and analysis without exposing API keys or private model credentials.

---

## Documentation Figures

### Motivation: semantic uncertainty and predictive uncertainty

The first figure illustrates the distinction between uncertainty about the underlying event state and uncertainty in model prediction.

### Evaluation framework

The second figure presents the black-box evaluation pipeline, including protocol freezing, uncertainty measurement, robustness testing, and audit-controlled analysis.

---

## Data and License

The repository uses the MIT License for original code. Third-party datasets and resources remain subject to their respective licenses. Raw API outputs and private execution artifacts are intentionally excluded.

---

## Citation

If you use this artifact, please cite the associated IASEAI'27 paper after publication.
