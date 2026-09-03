# Live execution record — 2026-09-03

This file records execution/provenance facts for the IASEAI'27 study **The Imperfective Uncertainty in Large Language Models**. It is not a Results section and does not interpret scientific outcomes.

## Frozen execution lineage

- Stage-5 deterministic data were originally collected under the V4 compatibility freeze and preserved under adjudication A1 after observing decision–distribution inconsistencies.
- Continuation and analysis semantics use `experiment-ready-v5` at `d17d118709d5f6c6f3f9752fc757db86f0ac38ce`.
- Adjudication A1 preserves the provider-emitted explicit `label` as the discrete decision and the emitted probability vector as the continuous uncertainty report. Label/probability disagreements are retained as an exploratory consistency diagnostic; they are not repaired, relabeled, or selectively retried.

## Completed live stages

### Stage 5 — neutral deterministic
- Planned calls: 2,000 = 400 items × 5 routes.
- Audit under A1: PASS.
- Completion-budget audit: 2,000 checked; 0 exhausted.
- Model-control audit: 2,000 checked; 0 override mismatches; 0 reasoning violations.
- Checksum seal: PASS; six files; 6,495,443 bytes.
- Decision–distribution inconsistencies: Claude 10/400, Qwen 8/400, total 18/2,000. GPT, DeepSeek, and Gemini: 0/400 in this stage.
- Gemini had 31 successful rows requiring more than one HTTP attempt.

### Stage 6 — neutral repeated sampling, K=5
- Planned calls: 10,000 = 400 items × 5 repeats × 5 routes.
- Initial audit found eight Claude parse failures. The raw pre-retry directory was checksum sealed before recovery.
- Recovery used the frozen `--resume --retry-failures` path and purged/replaced only those eight failed `(example_id, repeat)` rows. No valid row was reissued.
- Final audit under A1: PASS.
- Completion-budget audit: 10,000 checked; 0 exhausted.
- Model-control audit: 10,000 checked; 0 override mismatches; 0 reasoning violations.
- Final checksum seal: PASS; six files; 31,660,732 bytes.
- Preserved decision–distribution inconsistencies: Claude 46/2,000; DeepSeek 9/2,000; Qwen 60/2,000; GPT and Gemini 0 in this stage.
- Gemini had 44 successful rows requiring more than one HTTP attempt.

### Stage 7 — strict-logic robustness
- Planned calls: 600 = 120 items × 5 routes.
- Final audit under A1: PASS.
- Completion-budget audit: 600 checked; 0 exhausted.
- Model-control audit: 600 checked; 0 override mismatches; 0 reasoning violations.
- Checksum seal: PASS; six files; 1,660,782 bytes.
- Gemini had one successful row requiring more than one HTTP attempt.

### Stage 8 — definition-aware robustness
- Planned calls: 600 = 120 items × 5 routes.
- Final audit under A1: PASS.
- Completion-budget audit: 600 checked; 0 exhausted.
- Model-control audit: 600 checked; 0 override mismatches; 0 reasoning violations.
- Checksum seal: PASS; six files; 1,737,302 bytes.
- Qwen had one preserved decision–distribution inconsistency.

### Stage 9 — reversed-label-order robustness
- Planned calls: 600 = 120 items × 5 routes.
- Final audit under A1: PASS.
- Completion-budget audit: 600 checked; 0 exhausted.
- Model-control audit: 600 checked; 0 override mismatches; 0 reasoning violations.
- Checksum seal: PASS; six files; 1,676,224 bytes.
- Preserved decision–distribution inconsistencies: Claude 3/120; Qwen 1/120.
- Gemini had one successful row requiring more than one HTTP attempt.

### Stage 10 — cached aspect-sensitive verifier
- Planned calls: 2,000 = 400 items × 5 routes.
- Initial audit found one Claude parse failure. The raw pre-retry directory was checksum sealed before recovery.
- Recovery used the frozen `--resume --retry-failures` path and purged/replaced only that one failed row.
- Final audit under A1: PASS.
- Completion-budget audit: 2,000 checked; 0 exhausted.
- Model-control audit: 2,000 checked; 0 override mismatches; 0 reasoning violations.
- Final checksum seal: PASS; six files; 5,730,218 bytes.
- Preserved decision–distribution inconsistencies: Claude 4/400; Qwen 1/400.
- Gemini had two successful rows requiring more than one HTTP attempt.

## Paid study completion status

All six scientific live stages are now collected and PASS-audited under the frozen A1 adjudication policy. The planned study contains 15,800 main-study calls before retries. Recovery calls were limited to the eight audited Stage-6 Claude parse failures and the one audited Stage-10 Claude parse failure; no valid response was selectively replaced.

No empirical claim should be written from this execution log. Scientific interpretation must come only from the frozen analysis pipeline over the PASS-audited artifacts, followed by the evidence/manuscript gates.
