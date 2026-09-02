# Research Plan — The Imperfective Uncertainty in Large Language Models

## Core thesis

The original ImperfectiveNLI benchmark exposes **semantic indeterminacy** in ambiguous telic progressive events: the event outcome is under-specified, but the correct NLI decision is determinately **Unknown**. This creates a clean test of whether an LLM can distinguish (i) uncertainty in the described world from (ii) uncertainty in its own prediction.

A well-behaved model should be *confidently uncertain about the event*: high probability on the NLI label `Unknown`, not a diffuse label distribution and not confident `True` completion. Therefore semantic uncertainty recognition is not equivalent to maximizing entropy.

## Exactly three locked RQs

**RQ1 — Uncertainty Recognition.** Do frontier API LLMs correctly recognize semantic uncertainty in imperfective telic events, and how well calibrated are their True/False/Unknown confidence distributions across Groups A–D?

**RQ2 — Uncertainty Faithfulness.** Which black-box uncertainty signals—verbalized label probabilities or repeated-sampling disagreement—best identify aspectual reasoning errors, teleological completion bias, and overconfidence?

**RQ3 — Uncertainty-Aware Control.** Can selective prediction or selective rechecking reduce teleological completion errors at useful coverage and API cost without inducing broad atelic-performance collapse?

## Predeclared hypotheses

The executable source of truth is `configs/preregistered_hypotheses.yaml`. The paper should not silently strengthen these statements after results.

- **H1 / RQ1:** If a model recognizes semantic under-specification, Group C should receive selectively higher `P(Unknown)` than A/B/D; primary diagnostic: positive ADG.
- **H2 / RQ1:** Teleological completion is operationally most concerning when it is confident; TOR@0.80 is therefore reported descriptively, with lower values preferred.
- **H3 / RQ2:** At least one predeclared black-box uncertainty score should rank incorrect predictions better than random (`error AUROC > .5`) if behavior exposes useful uncertainty.
- **H4 / RQ3:** As uncertain cases are selectively deferred/rechecked, risk and TBR should decrease while Group-D entailment is retained better than under a blanket skeptical/aspect-aware intervention.

## Novelty relative to the reference study

The paper is not a model-refresh replication. The reference study established teleological bias, prompt trade-offs, scaling behavior, semantic-class effects, and a representation/inference dissociation. Our new axis is **uncertainty as an observable reliability signal and control variable**:

1. separate event-level semantic uncertainty from model-level predictive uncertainty;
2. measure calibrated three-way verbal probabilities rather than only hard labels;
3. compare verbal uncertainty with repeated black-box sampling;
4. exploit A→C / B→D matched probability updates;
5. measure prompt/order robustness of uncertainty itself;
6. turn uncertainty into abstention/selective-verification policies with risk–coverage and cost analysis.

## Experimental panel

Five cross-family API models through one OpenAI-compatible gateway: GPT-5.4, Claude Sonnet 5, DeepSeek V4 Pro, Qwen 3.8 Max, and Llama 4 Maverick. Exact gateway availability is checked immediately before execution. Requested and returned model identifiers are recorded per call.

No large local LLM is required; provider-specific logits are not part of the primary analysis. This keeps the main methodology comparable across black-box APIs.

## Primary metrics

Retain group accuracy, Teleological Bias Rate (TBR), and Aspectual Awareness Gap (ΔAA), then add:

- multiclass Brier score and NLL;
- top-label ECE and one-vs-rest classwise ECE;
- **SUR**: mean `P(Unknown)` on Group C;
- **TOR@0.80**: Group-C fraction with `P(True) >= .80`;
- **ADG**: mean `P(Unknown|C) - P(Unknown|A,B,D)`;
- sampling variation ratio / normalized label entropy;
- error-detection AUROC and AUPRC;
- prompt/order JSD and label-flip rate;
- paired A→C / B→D probability updates and label transitions;
- risk–coverage, AURC/E-AURC, matched-coverage TBR and Group-D retention;
- recheck rate, API-call count, token usage, and latency/cost metadata.

SUR/TOR/ADG are explicitly proposed descriptive measures for this paper, not established community standards.

## Statistical protocol

Use paired/clustered resampling by lexical verb rather than treating every generated row as independent. Report 95% bootstrap CIs from 10,000 verb-cluster resamples for primary contrasts. Use Holm correction for families of multi-model hypothesis tests. Do not choose thresholds on final test examples; predeclared sweeps are primary, and any optimized threshold must be selected on a 25% verb-disjoint calibration split and evaluated on held-out verbs.

## IASEAI safety framing

This is an evaluation-and-risk-quantification paper with a lightweight control experiment. In assistants/agents, confusing an action *in progress* with a completed safeguard, repair, verification, shutdown, audit, or remediation step can create unsupported downstream state assumptions. The reverse failure—global skepticism that rejects valid activity occurrence—also harms utility. The manuscript must clearly separate this motivation from what ImperfectiveNLI directly measures: a controlled semantic diagnostic, not an end-to-end deployment-safety benchmark.

## Stop conditions

- No numerical result enters the manuscript without a frozen raw JSONL artifact, manifest, and PASS audit.
- No model is dropped because of poor performance if its gateway calls are valid.
- No prompt is promoted to primary because it scores better after inspection.
- No claim of safer deployment is made from benchmark TBR alone.
