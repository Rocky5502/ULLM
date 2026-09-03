# Post-run numerical adjudication A2

## Trigger

After the paid study and the first complete Windows analysis, the final handoff was independently recomputed from the checksum-matching Stage-5 raw files on Linux. All RQ1 quantities, `1-maxprob`, sampling-disagreement scores, labels, and raw records matched. A small discrepancy appeared only for predictive-entropy error ranking on several endpoints.

The cause is numerical, not scientific: `normalized_entropy()` summed `prob.values()` with ordinary floating-point addition. Many elicited three-way probability vectors are permutations of the same coarse decimal values. Their entropies are mathematically identical, but platform/libm and summation-order differences can perturb the last floating-point bits. Rank-based AUROC then treats those micro-differences as an ordering rather than a tie.

## Frozen resolution

For final analysis only, predictive entropy is computed in canonical label order with `math.fsum` and rounded to 12 decimal places before rank-based metrics. Twelve decimals are far below the precision of the elicited probability reports and serve only to make mathematically equal entropy values ties. No model response, explicit label, probability vector, prompt, threshold, example, or other uncertainty signal is changed.

This rule was fixed before final manuscript interpretation and is applied to every endpoint, group, and predictive-entropy comparison. It is not selected because it improves any result. All four predeclared RQ2 signals remain reported.

## Consequence

The correction changes only tiny predictive-entropy ranking values; the qualitative scientific pattern is unchanged. In particular, the Group-C reversal remains: verbal probability uncertainty is inverse or non-diagnostic for the critical completion errors, whereas repeated-sampling disagreement is substantially more informative for several endpoints.

## Provenance rule

The final evidence package must record both the frozen raw-execution commit(s) and the final analysis commit containing A2. The original Windows processed CSV is retained as an execution artifact; the manuscript uses the A2-stabilized reranking artifact for predictive-entropy rank metrics.