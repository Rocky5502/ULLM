# Adversarial reviewer red-team checklist

Use this document after the real frozen experiment and before submission. The goal is to attack the paper's strongest claims before external reviewers do. A concern is closed only by evidence, narrower wording, or an explicit limitation—not by rhetorical confidence.

## 1. Novelty versus the ImperfectiveNLI paper

**Attack:** This is just the same benchmark on newer model aliases.

**Required defense:** Keep the contribution centered on the semantic-uncertainty versus predictive-uncertainty distinction, black-box uncertainty faithfulness, paired probability updates, calibration/ranking separation, and selective control. Report the original benchmark metrics for comparability, but do not present accuracy replication as the main novelty. Explicitly attribute dataset construction, teleological bias, and the original prompting findings.

**Failure condition:** If the real results reduce to a model leaderboard without meaningful uncertainty/control evidence, narrow the paper rather than overselling novelty.

## 2. Benchmark contamination / memorization

**Attack:** New API models may have seen the ACL paper, benchmark repository, examples, or discussions during training/post-training.

**Required response:** State that benchmark contamination cannot be ruled out for closed/routed APIs. Avoid claiming the experiment measures unaided acquisition of lexical-aspect theory. Emphasize observed deployment-time behavior on controlled semantic contrasts. Use A↔C/B↔D paired probability shifts, prompt/order robustness, and failure patterns as behavioral evidence, not as proof of unseen generalization.

**Optional exploratory follow-up:** If time/budget permits after the frozen primary analysis, create a clearly labeled paraphrase or held-out lexical stress test under a separately versioned protocol. Do not retrofit it into the preregistered primary study.

## 3. Are verbalized probabilities meaningful?

**Attack:** Asked-for probabilities are performative text, not a model posterior.

**Required defense:** Never call them internal probabilities. Call them structured verbalized/elicited probabilities. Evaluate them behaviorally using proper scoring, calibration, error ranking, prompt sensitivity, and repeated-sampling disagreement. If verbalized confidence is weak while sampling works, that is a valid finding; if both are weak, report the negative result.

## 4. Is “semantic uncertainty” being confused with class uncertainty?

**Attack:** Group C has a deterministic benchmark label `Unknown`, so why call it uncertainty at all?

**Required defense:** Preserve the two-level distinction. The described world outcome (culmination) is semantically under-specified, whereas the NLI decision is determinately `Unknown`. Correct behavior is therefore concentrated probability on `Unknown`, not maximal class entropy. Uniform class uncertainty is a negative control, not success.

## 5. Calibration methodology

**Attack:** ECE is bin-dependent and can be misleading on 400 examples.

**Required defense:** Do not rely on ECE alone. Report Brier and NLL, Unknown-class calibration, ranking metrics, and verb-cluster intervals. Treat ECE as one descriptive diagnostic. Avoid fine-grained calibration claims unsupported by sample size.

## 6. K=5 sampling is small

**Attack:** Five samples give coarse disagreement estimates and many ties.

**Required defense:** State this limitation explicitly. Use tie-aware AURC/coverage, variation ratio and normalized three-label entropy, and do not imply precise posterior estimation. K=5 is an operational black-box budget choice, not a claim of convergence.

## 7. Pseudo-replication and templated dependence

**Attack:** There are 400 rows but not 400 independent semantic phenomena.

**Required defense:** Bootstrap by lexical verb, exploit paired A↔C/B↔D structure, and avoid IID language. Report uncertainty intervals accordingly. Do not inflate power by treating every template row as an unrelated observation.

## 8. Multiple comparisons / researcher degrees of freedom

**Attack:** Five models × many metrics × prompts × thresholds permits cherry-picking.

**Required defense:** Keep the three RQs fixed, distinguish primary from descriptive metrics, use Holm correction for declared test families, show full threshold sweeps, retain the predeclared compact RQ3 operating point, and label any post-hoc analysis exploratory.

## 9. Prompt sensitivity

**Attack:** The uncertainty result could be an artifact of one wording.

**Required defense:** Neutral remains primary. Strict-logic, definition-aware, and reversed-label-order conditions are robustness checks. Report all fixed robustness results, including failures. Never choose whichever prompt produces the best model behavior as the headline result.

## 10. Gateway validity

**Attack:** A third-party gateway alias does not prove an immutable vendor checkpoint.

**Required defense:** Claims attach to routed endpoints on the recorded execution date. Preserve live catalogue snapshot, requested and returned IDs, timestamps, request IDs when available, decoding parameters, and raw responses. Stop the experiment if routing is suspicious rather than silently substituting a model.

## 11. Reproducibility of closed APIs

**Attack:** Exact numerical reproduction may be impossible later.

**Required defense:** Separate computational reproducibility of our pipeline from provider reproducibility. Preserve raw responses, manifests, catalogue snapshot, exact Git commit, dependency/environment snapshot, dataset provenance, checksums, and generated analysis artifacts. State that closed endpoint behavior may drift.

## 12. Selective control is circular

**Attack:** The verifier is just another prompt to the same model; improvement may reflect stronger prompting rather than uncertainty.

**Required defense:** Blanket verifier is the control. The RQ3 contribution is whether uncertainty can route that intervention selectively, preserving Group-D valid entailments while lowering Group-C teleological error and reducing recheck cost. If blanket verification dominates selective verification at acceptable utility/cost, say so.

## 13. Fixed selective threshold

**Attack:** `1-maxprob >= 0.20` may be arbitrary.

**Required defense:** Full threshold/risk–coverage sweeps are primary. The fixed threshold exists only as a predeclared compact table operating point. Do not optimize it on the final test set. Any optimized threshold requires a verb-disjoint calibration split and separate held-out evaluation.

## 14. Safety relevance is overstated

**Attack:** A linguistic NLI benchmark does not demonstrate safer AI systems.

**Required defense:** Keep the safety claim narrow: event-state completion assumptions can be relevant to monitoring/agents, and the benchmark provides a controlled evaluation/risk-quantification probe. Never claim that lower TBR proves safe deployment, alignment, or robustness in the broad sense.

## 15. External validity

**Attack:** English aspect on short templated sentences may not transfer to realistic operational language or other languages.

**Required response:** State this directly. Frame the benchmark as a diagnostic test case, not a universal estimate. Future work can extend to multilingual aspect marking, discourse, tool-use state reports, and domain-specific processes.

## 16. Model-panel wording

**Attack:** “Frontier” is vague and may be inaccurate for mutable gateway aliases.

**Required response:** Prefer “five cross-family API LLM endpoints” or “gateway-routed API endpoints” in final wording unless the exact evaluated models and contemporaneous evidence justify a stronger descriptor.

## 17. Cost and latency claims

**Attack:** Public price tables may not match gateway billing, and retries distort cost.

**Required defense:** Report observed call counts and provider/gateway usage metadata where available. Distinguish planned calls, successful calls, retries, tokens, and simulated selective-verifier incremental cost. Do not reconstruct precise monetary cost from stale pricing if billing evidence is unavailable.

## 18. Qualitative examples are cherry-picked

**Attack:** A few vivid rationales are anecdotal.

**Required defense:** Use the prestratified qualitative protocol by model/group/confidence/class. Report coding counts before illustrative examples. Do not substitute model rationales for quantitative evidence or treat short explanations as hidden chain-of-thought.

## 19. Negative or null results

**Attack:** The hypotheses are not supported, so the paper has no contribution.

**Required response:** A well-audited negative finding can still establish that verbalized/sampling uncertainty does not reliably expose the imperfection, or that selective verification fails to preserve utility. Rewrite claims around what the experiment actually rules out. Never change metrics/prompts after seeing null results simply to recover a positive story.

## 20. Double-blind artifact leakage

**Attack:** The public repository or supplementary archive reveals the authors.

**Required response:** Re-check the official IASEAI'27 policy. Do not link identity-bearing Git history in a double-blind manuscript. Use `docs/ANONYMITY_PLAN.md` and `scripts/package_anonymous_artifact.py` if anonymous supplementary code is allowed, then manually inspect the archive. Decide public-repository visibility before submission rather than assuming no hyperlink is enough.

## Final red-team pass criteria

The paper is submission-ready only when every major empirical sentence can be traced to an audited artifact, all null/negative results are represented fairly, the exact provider/routing limitations are disclosed, anonymity/template requirements have been re-checked, generated tables/figures match the processed data, and the post-run manuscript evidence gate passes.
