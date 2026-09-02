# The Imperfective Uncertainty in Large Language Models

Research artifact for an IASEAI'27 main-conference paper. The project extends the ACL 2026 Best Paper **“The Imperfective Paradox in Large Language Models”** by asking a different question: *when event completion is semantically underdetermined, do LLMs know that the correct inference is Unknown, and can their uncertainty be used to control risk?*

## Locked research questions

1. **Uncertainty Recognition:** Do frontier API LLMs correctly recognize semantic uncertainty in imperfective telic events, and are their confidence distributions calibrated across the four ImperfectiveNLI conditions?
2. **Uncertainty Faithfulness:** Which black-box uncertainty signals—verbalized probabilities or repeated-sampling disagreement—best identify teleological reasoning errors and overconfidence?
3. **Uncertainty-Aware Control:** Can selective prediction/rechecking reduce teleological completion errors at useful coverage and API cost without degrading valid atelic entailments?

## Models (API only; no large local LLMs)

The initial cross-family panel is `gpt-5.4`, `claude-sonnet-5`, `deepseek-v4-pro`, `qwen3.8-max`, and `llama-4-maverick`, all through `https://api.zhizengzeng.com/v1`. Because aggregator catalogs can change, `scripts/check_models.py` must be run immediately before the frozen experiment.

## Why this is not a clone of the reference paper

The reference paper studies teleological bias, prompting, scaling, semantic subclasses, and representation-vs-inference. This project treats **semantic uncertainty vs predictive uncertainty** as the central object. In Group C the world outcome is under-specified, yet the NLI label is determinately `Unknown`; an ideal reasoner should therefore be *confidently uncertain about the event*. We evaluate calibrated confidence, black-box sampling uncertainty, teleological overconfidence, and selective risk control.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_imperfective_nli.py
# set ZZZ_API_KEY in your shell, not in Git
python scripts/check_models.py
PYTHONPATH=src python -m ullm.run --mode deterministic --model gpt-5.4 --limit 8
pytest -q
```

## Repository map

- `src/ullm/` — API client, prompts, parsing, metrics, runner
- `configs/` — frozen model and experiment settings
- `data/README.md` — upstream dataset and license notes
- `docs/` — research plan and experiment protocol
- `paper/` — AAAI-2027-style provisional IASEAI manuscript with editable TikZ figures and TBD result tables
- `results/` — generated raw/processed outputs (large raw outputs are gitignored)

## Data and attribution

ImperfectiveNLI is from Bolei Ma and Yusuke Miyao, *The Imperfective Paradox in Large Language Models*, ACL 2026. The paper states that the dataset is released under CC BY-NC 4.0 for research use. This repo downloads the upstream artifact rather than silently re-licensing it.

## Status

**Stage 1 complete:** study design, API harness, metrics, manuscript skeleton, and figure sources. **Results remain intentionally TBD** until the API experiment is run.
