# Contract adjudication A1 — Stage-5 decision/distribution inconsistency

Date: 2026-09-03

This amendment was created **after the complete 2,000-call neutral deterministic Stage 5 was collected, but before the 10,000-call K=5 sampling stage and before any prompt-robustness or verifier runs**. It is triggered by a response-contract phenomenon, not by a favorable/unfavorable benchmark score.

## Observed trigger

The original strict audit required the explicit discrete `label` to belong to the set of maximum-probability classes in the same response. Stage 5 produced schema-valid, complete responses in which this serialization/faithfulness contract was violated for 10/400 Claude rows and 8/400 Qwen rows. GPT, DeepSeek, and Gemini had zero such violations in Stage 5. The raw Stage-5 directory was sealed before adjudication.

These are **not parse failures** and are not missing data. The model supplied all three probabilities, a valid label, and a reason. Re-issuing only these calls would condition data collection on an observed model behavior and could selectively replace difficult items. Repairing or silently changing the label would alter the provider output. Both are disallowed.

## Frozen adjudication rule

1. The explicit `label` is preserved as the model's **primary discrete decision**. It is used for discrete accuracy, TBR/Delta-AA, paired correctness, error targets, repeated-sampling label disagreement, prompt/order label flips, and verifier decisions.
2. The reported `probabilities` vector is preserved as the model's **continuous uncertainty report**. It is used for SUR, TOR, ADG, Brier, NLL, classwise calibration, 1-maxprob, predictive entropy, JSD, and selective-risk scoring.
3. No response is repaired, deleted, relabeled, or selectively retried merely because the stated label disagrees with its own probability argmax.
4. Label/probability disagreement is retained and quantified as an **exploratory decision–distribution inconsistency diagnostic**. It is not retroactively promoted to a preregistered hypothesis.
5. The original strict audit remains the default. An explicit adjudication flag may convert only this one contract condition from fatal failure to a recorded warning. Request errors, parse errors, malformed probability vectors, large probability-sum deviations, missing required reasons, manifest drift, incomplete K, completion-budget exhaustion, and model-control violations remain fatal.

## Why this is the least biased rule

The rule is independent of whether the stated label or the probability argmax is closer to the benchmark gold label. It therefore does not choose the representation that improves accuracy on a given item. Both provider-emitted signals are preserved exactly as observed and their disagreement is reported instead of selecting a winner after seeing outcomes.

## Analysis note

The preregistered phrase “top-label ECE” is interpreted literally as calibration of the **probability argmax class**. Discrete-decision metrics remain based on the explicit `label`. The manuscript must state this distinction and report the decision–distribution inconsistency rate.

## Provenance

- Stage-5 run ID: `frozen-det-neutral-v1`
- Stage-5 calls: 2,000 = 400 items × 5 routes
- Pre-adjudication checksum manifest: `results/raw/frozen-det-neutral-v1.checksums.predecision.json`
- Pre-adjudication checksum status: PASS; 6 files; 6,495,443 bytes
- Observed strict-audit contract violations: Claude 10/400; Qwen 8/400; total 18/2,000
- Group distribution: Claude A/C/D = 2/5/3; Qwen A/B = 7/1
- This amendment changes **audit/adjudication and analysis semantics only**. It does not change the dataset, prompts, configured model routes, temperatures, K, robustness subsets, verifier prompt, thresholds, bootstrap plan, or API request construction.
