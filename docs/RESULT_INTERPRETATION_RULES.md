# Pre-results interpretation rules

These rules are frozen before the paid main study. Their purpose is to stop the narrative from changing after model outputs are visible. They govern how H1–H4 and the three RQs are described in the manuscript; they do not add new experimental conditions.

## General language

- Use **estimate**, **interval**, **directional evidence**, **mixed evidence**, or **no clear evidence** unless a formal test is actually implemented and reported.
- Never use “proved,” “solved,” “safe,” or “aligned” for this diagnostic study.
- A model leaderboard is not a contribution by itself. Interpret results through semantic recognition, uncertainty faithfulness, and selective control.
- Report all five configured endpoints. Do not omit an endpoint because its result weakens the story.
- Report all four RQ2 uncertainty signals. Do not headline only the best post-hoc signal.
- Negative/null findings are valid outcomes and must remain in Results/Discussion.
- Distinguish **gateway-routed endpoint behavior on the execution date** from claims about immutable vendor checkpoints.

## H1 — semantic uncertainty recognition

Primary metric: ADG. Companion evidence: SUR, Group-C accuracy, Group-C P(Unknown), and paired A→C probability updates.

- `analyze_hypotheses.py` performs the predeclared one-sided A/C paired-label randomization test for ADG while retaining B/D as the non-C baseline.
- The five model-wise H1 p-values are Holm adjusted as one family.
- A model may be described as showing **formal directional H1 evidence** only when the Holm-adjusted p-value is < .05 and the observed ADG is positive.
- The verb-cluster 95% interval is always reported alongside the test. If the interval crosses zero, describe the magnitude as uncertain even if a randomization test happens to cross a threshold.
- Panel-level language should state the count/pattern across five endpoints (for example, “three of five endpoints show…”). Do not invent a pooled “all models support H1” test after seeing results.

## H2 — teleological overconfidence severity

Primary diagnostic: TOR@0.80. Companion evidence: TBR, Group-C P(True), error confidence distribution.

- H2 remains **descriptive by design**; the threshold was fixed before results.
- High TOR means many ambiguous telic examples receive high completion confidence. Low TOR does not by itself prove uncertainty is faithful; a model could be uncertain or confidently wrong in another class.
- Never tune the `.80` threshold after seeing results. Threshold curves may be reported as descriptive sensitivity analysis.

## H3 — uncertainty faithfulness for error ranking

Primary statistic: error-detection AUROC for all four fixed uncertainty signals. Companion metrics: AUPRC, AURC/E-AURC, Group-C-only ranking, and prompt/order robustness.

- Compare the verb-cluster 95% AUROC interval with random ranking (0.5).
- `CI entirely > 0.5` → **directional evidence that the signal ranks errors above random** for that endpoint.
- `CI includes 0.5` → **no clear interval-based evidence versus random**.
- `CI entirely < 0.5` → **inverse/misleading ranking evidence**.
- Do not treat the four signals as four chances to declare success. Report the complete model × signal matrix and summarize consistency, disagreement, or failure.
- Sampling K=5 is coarse. Ties and discrete disagreement values are expected; use the tie-aware risk code and do not overstate small differences between signals.

## H4 — uncertainty-aware control

Primary evidence: full risk–coverage behavior and verifier trade-offs. Compact predeclared operating point: `1-maxprob >= 0.20`.

For each endpoint report, separately:

1. risk change versus the base neutral model;
2. Group-C TBR change versus base;
3. Group-D accuracy/retention change versus base;
4. Group-D performance versus blanket verification;
5. recheck rate/calls;
6. incremental token overhead.

Do **not** collapse these into an unregistered weighted score. A selective policy is useful only to the extent that the trade-off is visible. The fixed operating point is for compact comparison; the full threshold sweep remains primary and must be shown even if `.20` looks unattractive.

If blanket verification performs better on both safety-relevant error and benign utility at acceptable cost, report that selective routing did not add value. If selective routing lowers TBR but destroys Group-D entailment, describe it as an over-skepticism trade-off rather than a success.

## Prompt and label-order robustness

Neutral remains the primary scientific condition. Strict-logic, definition-aware, and reversed-label-order results answer robustness questions only.

- Do not replace the neutral headline result with a robustness prompt because it performs better.
- If results change materially across benign wording/order variants, lower the strength of uncertainty-faithfulness claims and discuss prompt dependence explicitly.
- If the definition-aware condition improves Group C but harms Group D, connect this to the calibration/over-correction trade-off rather than reporting only the improvement.

## Statistical reporting

- Use lexical verb as the bootstrap cluster.
- Report 95% intervals and the number of lexical clusters.
- Holm correction is used only for a declared family of formal p-value tests; it is not applied cosmetically to descriptive metrics.
- Do not convert percentile bootstrap intervals into unplanned p-values after seeing results.
- Do not treat 400 templated rows as 400 independent semantic phenomena.

## Qualitative examples

Qualitative examples may illustrate a quantitative pattern but may not establish one.

- Select examples using the prestratified protocol rather than manually choosing the most dramatic rationale.
- Treat `reason_short` as an observed short explanation, not privileged chain-of-thought or proof of internal reasoning.
- Include counterexamples when they materially qualify the dominant pattern.

## Scope of claims

Permitted framing: the benchmark is a controlled diagnostic of whether endpoint-completion under-specification is recognized, whether black-box uncertainty exposes errors, and whether uncertainty can support selective oversight in this setting.

Not permitted from this experiment alone: claims that an endpoint is generally safe, aligned, trustworthy across tasks, robust to real-world agents, or universally calibrated.

## Post-run manuscript gate

Before removing the last `TBD`, all six raw-run audits must PASS, canonical processed artifacts must exist, the preregistered hypothesis evidence table must exist, and `analysis_manifest.json` must bind the raw run hashes to the analysis Git commit. The final manuscript should then pass `python scripts/manuscript_evidence_gate.py --mode post`.
