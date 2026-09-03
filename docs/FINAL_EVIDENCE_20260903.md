# Final statistical evidence — 2026-09-03

This record is written after the paid main study and the completed 12-step audited base analysis. It uses the checksum-matching Stage-5 deterministic-neutral raw records, Stage-10 verifier raw records, the processed analysis handoff, and post-run numerical adjudication A2. No new API calls are introduced here.

## RQ1 / H1 — semantic uncertainty recognition

All five routed endpoints have positive ADG with verb-cluster 95% CIs above zero. The predeclared one-sided A/C randomization test (10,000 permutations) yields raw p=0.00010 for each endpoint; Holm-adjusted p=0.00050 for each.

- Claude Sonnet 5: ADG .440 [.394,.482]
- DeepSeek V4 Pro: ADG .318 [.265,.372]
- Gemini 3.7 Flash: ADG .532 [.494,.567]
- GPT-5.6 Sol: ADG .733 [.675,.785]
- Qwen 3.8 Max: ADG .386 [.339,.434]

H1 therefore receives formal directional evidence for 5/5 endpoints under the preregistered rule.

H2 remains descriptive by design. TOR@.80 is Claude .070, DeepSeek .340, Gemini .040, GPT .050, Qwen .220.

## RQ2 / H3 — uncertainty faithfulness

Across the full 400-item benchmark, every endpoint has at least one uncertainty signal whose verb-cluster AUROC interval lies entirely above random (.5). DeepSeek's two verbal signals include .5, while its two sampling signals are above .5; the other four endpoints show above-random full-benchmark ranking for all four signals.

The main finding is conditional on the critical Group-C ambiguous-telic examples:

| endpoint | 1-maxprob AUROC [95% CI] | sampling variation AUROC [95% CI] |
|---|---:|---:|
| Claude | .013 [.000,.045] | .822 [.643,.965] |
| DeepSeek | .002 [.000,.007] | .498 [.389,.608] |
| Gemini | .001 [.000,.008] | .742 [.485,1.000] |
| GPT | .404 [.151,.636] | .887 [.657,1.000] |
| Qwen | .000 [.000,.000] | .603 [.509,.705] |

Predictive entropy follows the same qualitative pattern as 1-maxprob after numerical adjudication A2. Thus verbal probability uncertainty is inverse for four endpoints and non-diagnostic for GPT inside Group C, while sampling disagreement is clearly above random for Claude, GPT, and Qwen and directionally high but interval-uncertain for Gemini.

## RQ3 / H4 — preregistered control

At the frozen `1-maxprob >= .20` selective-recheck operating point, overall risk decreases for all five endpoints and Group-D accuracy is preserved or improves. However, Group-C TBR is unchanged for Claude, DeepSeek, GPT, and Qwen and increases by .03 for Gemini. H4 is therefore mixed/negative for its targeted teleological-bias objective rather than a clean success.

Blanket verification can remove TBR for some endpoints but may sharply damage valid Group-D entailments (Claude .91->.64; DeepSeek .99->.57; Qwen 1.00->.91), demonstrating the over-skepticism trade-off.

## Exploratory mechanism check — not confirmatory

A post-hoc, outcome-independent K=5 rule that rechecks any item with sampling variation ratio >= .20 reduces TBR for Claude (.08->.04), DeepSeek (.34->.12), GPT (.05->.04), and Qwen (.22->.16), with Gemini unchanged (.04). Recheck rates range from 5.3% to 31.5%. This supports the RQ2 mechanism but does not replace the preregistered H4 test.

## Interpretation lock

The manuscript should foreground the recognition-versus-faithfulness dissociation, report the negative H4 result, keep the sampling router explicitly exploratory, retain all five endpoint results, and describe the systems as gateway-routed endpoints rather than immutable vendor checkpoints. Smoke outputs remain excluded from evidence.