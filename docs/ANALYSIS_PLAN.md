# Analysis Plan

## Non-negotiable order of operations

1. Validate the exact ImperfectiveNLI artifact and write the local SHA-256 manifest.
2. Freeze the gateway model catalogue and execute the predeclared calls.
3. Run `scripts/audit_run.py` on every result file. Stop on duplicate/missing records, request/parse failures, mixed prompt hashes/orders, or incomplete sampling K.
4. Produce processed CSVs.
5. Produce figures/tables directly from processed CSVs.
6. Only then replace manuscript `TBD` values.

## RQ1 — Uncertainty Recognition

Primary evidence comes from the **neutral-prompt deterministic full run**. Compute:

- Acc A–D, TBR-C, ΔAA;
- SUR, TOR@0.80, ADG;
- multiclass Brier and NLL;
- top-label ECE plus separate True/False/Unknown classwise ECE;
- exact A/C and B/D both-correct pair consistency;
- probability profiles by group and telic semantic subclass.

Primary uncertainty intervals are 95% verb-cluster bootstrap intervals with 10,000 resamples. Do not replace Group-C semantic recognition with entropy: the desired Group-C target is concentrated `P(Unknown)`.

## RQ2 — Uncertainty Faithfulness

Compare four black-box uncertainty signals:

1. `1-maxprob` from verbalized probabilities;
2. normalized predictive entropy of the verbal distribution;
3. K=5 sampling variation ratio;
4. K=5 normalized sampling label entropy.

For each signal report error-detection AUROC and AUPRC. Calibration and failure ranking are distinct claims and must be discussed separately.

### Paired semantics

Use the benchmark's matched structure rather than treating rows as independent:

- A→C: report ΔP(Unknown), ΔP(True), label transitions, and semantic-subclass splits;
- B→D: report P(True) stability and label transitions.

### Prompt/order robustness

On the fixed balanced 120-example subset compare canonical neutral `[True,False,Unknown]` with:

- `strict_logic`;
- `definition_aware`;
- neutral with `[Unknown,False,True]` label order.

Report label flip rate, accuracy change, mean JSD, ΔP(Unknown), and ΔP(True). These runs are robustness analyses, not alternative primary protocols selected after seeing results.

## RQ3 — Uncertainty-Aware Control

For every uncertainty score, order examples from least to most uncertain and report:

- full risk–coverage curve;
- AURC and empirical excess AURC;
- risk at coverages 1.0/0.9/0.8/0.7/0.5;
- coverage achievable at target risk 0.10 and 0.05 where possible;
- Group-C TBR and coverage at matched operating points;
- Group-D coverage and retained accuracy.

Then compare base neutral, blanket verifier, and selective cached-verifier policies. Report accuracy/risk, TBR-C, Group-D accuracy, recheck rate/calls, and incremental verifier tokens. A control does not count as successful merely because it abstains on or rejects most progressive inputs.

## Statistical inference

- Resample whole verb pairs/clusters, 10,000 replicates, 95% percentile CIs.
- Prefer paired contrasts for A/C and B/D.
- Use Holm adjustment for families of multi-model hypothesis tests.
- Report effects and intervals; avoid narrative claims based only on marginal p-values.
- Any optimized decision threshold must be selected on a 25% verb-disjoint calibration split and evaluated on held-out verbs. Predeclared threshold/coverage sweeps do not require optimization.

## Sanity baselines

Include always-True, always-Unknown, and uniform three-way probability outputs as interpretation controls. In particular, a uniform distribution has maximal predictive entropy but is not correct semantic uncertainty recognition.

## Qualitative analysis

Prestratify examples by model × group × confidence regime × semantic class. Candidate codes are endpoint-completion prior, cancellation neglect, over-skepticism, telicity confusion, and probability/label inconsistency. Do not cherry-pick anecdotes to create a result absent from aggregate data.

## Prohibited analysis behavior

Do not invent values, tune prompts/models on test performance, select thresholds after test-set inspection, drop failed API calls without accounting, silently switch model IDs, change K after seeing instability, or phrase exploratory findings as preregistered hypotheses.
