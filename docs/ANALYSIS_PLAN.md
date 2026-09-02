# Analysis Plan

## RQ1 — recognition
Primary strict-protocol deterministic run. Compute Acc A–D, TBR, ΔAA, SUR, TOR@0.80, ADG, ECE, classwise ECE, Brier, NLL, and exact A/C + B/D pair consistency. Report verb-cluster 95% bootstrap CIs. Compare strict vs bare only after the primary table is frozen.

## RQ2 — faithfulness
Compare four black-box uncertainty signals: `1-maxprob`, normalized entropy of the verbal distribution, sampling variation ratio, and normalized sampling label entropy. Report error AUROC, error AUPRC, and AURC. Repeat for Group C separately and inspect telic subclasses. Explicitly count *confidently consistent errors*: low sampling disagreement with an incorrect modal label.

## RQ3 — control
Sort by each uncertainty score and evaluate the full risk–coverage curve. At coverages 1.0/0.9/0.8/0.7/0.5, report selective risk, Group-C TBR, Group-D retention, and number deferred. Recheck is a secondary policy using the aspect-sensitive verifier prompt. Report the additional token/call cost.

## Inference
Resample whole verb clusters (10,000 replicates). Prefer paired contrasts for A/C and B/D. Use Holm adjustment for families of multi-model hypothesis tests. Report effects and intervals; do not turn marginal p-values into narrative claims. Any optimized threshold must be chosen on verb-disjoint calibration folds.

## Robustness
1. Strict vs bare prompt.
2. Parse-failure sensitivity.
3. Telic semantic subclasses.
4. A/C and B/D pair transitions.
5. K=10 Group-C sensitivity only if K=5 is unstable.
6. Provider drift check from requested vs returned model IDs.

## Prohibited analysis behavior
Do not invent values, select thresholds after test-set inspection, drop failed API calls without accounting, silently switch model IDs, or phrase exploratory findings as pre-registered hypotheses.
