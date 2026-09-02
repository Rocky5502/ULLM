from __future__ import annotations

from .schemas import Example

SYSTEM_PROMPT = """You are a strict natural-language-inference evaluator.
Judge only what the premise logically supports. Do not assume that an intended,
ongoing, typical, or likely event reached its endpoint unless the premise licenses it.
Return ONLY valid JSON with exactly these keys:
{"label":"True|False|Unknown","probabilities":{"True":0.0,"False":0.0,"Unknown":0.0},"reason_short":"..."}
The three probabilities must be finite numbers in [0,1] and sum to 1 (within rounding).
Use True when the hypothesis is entailed, False when contradicted, and Unknown when
neither entailment nor contradiction is warranted. Keep reason_short to one sentence."""

VERIFIER_SYSTEM_PROMPT = """You are an aspect-sensitive NLI verifier.
First determine whether the event predicate is goal-bounded (telic) or homogeneous
(atelic). A progressive telic event describes a process toward an endpoint but does not
by itself assert endpoint attainment. An atelic activity can license occurrence from a
nonzero subinterval. Explicit interruption or cancellation must be respected.
Return ONLY the same JSON schema as requested by the user, with calibrated probabilities."""


def make_user_prompt(ex: Example) -> str:
    return (
        f"Premise: {ex.premise}\n"
        f"Hypothesis: {ex.hypothesis}\n\n"
        "Classify the relation as True, False, or Unknown and give your probability "
        "distribution over all three labels."
    )
