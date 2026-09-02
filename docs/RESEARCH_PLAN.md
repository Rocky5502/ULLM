# Research Plan — The Imperfective Uncertainty in Large Language Models

## Core thesis

The original ImperfectiveNLI benchmark exposes **semantic indeterminacy** in ambiguous telic progressive events: the event outcome is under-specified, but the correct NLI decision is determinately **Unknown**. This creates a clean test of whether an LLM can distinguish (i) uncertainty in the described world from (ii) uncertainty in its own prediction.

A well-behaved model should be *confidently uncertain about the event*: high probability on the NLI label `Unknown`, not a diffuse label distribution and not confident `True` completion.

## Three locked RQs

**RQ1 — Uncertainty Recognition.** Do frontier API LLMs correctly recognize semantic uncertainty in imperfective telic events, and how well calibrated are their True/False/Unknown confidence distributions across Groups A–D?

**RQ2 — Uncertainty Faithfulness.** Which black-box uncertainty signals—verbalized label probabilities or repeated-sampling disagreement—best identify aspectual reasoning errors, teleological completion bias, and overconfidence?

**RQ3 — Uncertainty-Aware Control.** Can selective prediction (defer/recheck the riskiest cases) reduce teleological completion errors at useful coverage and API cost without the broad atelic-performance collapse induced by aggressive counterfactual prompting in the reference study?

## Primary hypotheses (pre-register before seeing results)

- H1: Group C will show a disproportionate rate of confidently wrong `True` predictions (teleological overconfidence), even for strong frontier APIs.
- H2: Sampling disagreement will rank errors more reliably than single-pass self-reported confidence on semantically ambiguous cases.
- H3: Selective control will lower error/TBR at high coverage while retaining Group-D entailment accuracy better than a global aggressive prompt intervention.

## Experimental panel

Five cross-family API models through one OpenAI-compatible gateway: GPT-5.4, Claude Sonnet 5, DeepSeek V4 Pro, Qwen 3.8 Max, and Llama 4 Maverick. Freeze exact model IDs and gateway availability in `results/raw/manifest.json` at run time.

## Primary metrics

Keep the original study's group accuracy, Teleological Bias Rate (TBR), and Aspectual Awareness Gap (ΔAA), then add:

- multiclass Brier score, NLL, ECE;
- **SUR** (Semantic Uncertainty Recognition): mean `P(Unknown)` on Group C;
- **TOR@0.80** (Teleological Overconfidence Rate): Group-C fraction with `P(True) >= .80`;
- **ADG** (Ambiguity Discrimination Gap): mean `P(Unknown|C) - P(Unknown|A,B,D)`;
- sampling variation ratio / label entropy;
- selective risk–coverage and AURC.

All new names are working metrics and must be presented as proposed in this paper, not established community metrics.

## Statistical protocol

Use paired/clustered resampling by lexical verb rather than treating every generated pair as independent. Report 95% bootstrap CIs (10,000 resamples) for primary contrasts. Use Holm correction for families of multi-model hypothesis tests. Do not select thresholds on the final test examples; either sweep risk–coverage or tune on verb-disjoint calibration folds.

## IASEAI safety framing

This is an evaluation-and-risk-quantification paper. In safety-critical assistants/agents, confusing an action *in progress* with a completed safeguard, repair, verification, shutdown, audit, or remediation step can produce unsafe downstream state assumptions. The paper should clearly separate this motivation from what ImperfectiveNLI directly measures; it is a controlled semantic diagnostic, not itself a deployment-safety benchmark.
