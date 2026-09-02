from __future__ import annotations

from .schemas import Example

JSON_SCHEMA_INSTRUCTION = """Return ONLY valid JSON with exactly these keys:
{"label":"True|False|Unknown","probabilities":{"True":0.0,"False":0.0,"Unknown":0.0},"reason_short":"..."}
The three probabilities must be finite numbers in [0,1] and sum to 1 (within rounding).
Use True when the hypothesis is entailed, False when contradicted, and Unknown when
neither entailment nor contradiction is warranted. Keep reason_short to one sentence."""

PROMPTS: dict[str, str] = {
    # Primary condition. Deliberately avoids teaching the model the telicity rule.
    # This measures whether uncertainty/aspectual reasoning is present without a
    # benchmark-specific hint.
    "neutral": (
        "You are a natural-language-inference evaluator. Judge whether the hypothesis "
        "is supported by the premise. Use only the information in the premise and the "
        "ordinary meanings of the words. Do not add unstated facts.\n" + JSON_SCHEMA_INSTRUCTION
    ),
    # Comparable to the reference paper's strict-logic framing. It prohibits pragmatic
    # completion assumptions but still does not explicitly provide the telicity rule.
    "strict_logic": (
        "You are a strict natural-language-inference evaluator. Judge only what the "
        "premise logically supports. Do not assume that an intended, ongoing, typical, "
        "or likely event reached its endpoint unless the premise licenses it.\n" + JSON_SCHEMA_INSTRUCTION
    ),
    # Robustness / knowledge-application condition, not the primary result condition.
    "definition_aware": (
        "You are an aspect-aware natural-language-inference evaluator. Activities are "
        "homogeneous/atelic events whose occurrence can be licensed by a nonzero "
        "subinterval. Accomplishments are telic events with an inherent culmination: "
        "a progressive accomplishment describes progress toward the endpoint but does "
        "not by itself assert that the endpoint was reached. Explicit interruption or "
        "cancellation must be respected.\n" + JSON_SCHEMA_INSTRUCTION
    ),
    # Used only by the selective recheck policy in RQ3.
    "verifier": (
        "You are an independent aspect-sensitive NLI verifier. First identify whether "
        "the event is telic (goal-bounded) or atelic (homogeneous). Then determine "
        "whether the premise licenses the hypothesis. A progressive telic event does "
        "not by itself assert culmination; an atelic activity can license occurrence "
        "from a nonzero subinterval; explicit cancellation must be respected. Do not "
        "defer to a previous model answer.\n" + JSON_SCHEMA_INSTRUCTION
    ),
}


def get_system_prompt(prompt_type: str) -> str:
    try:
        return PROMPTS[prompt_type]
    except KeyError as exc:
        raise ValueError(f"Unknown prompt_type={prompt_type!r}; choose from {sorted(PROMPTS)}") from exc


def make_user_prompt(ex: Example, *, label_order: tuple[str, str, str] = ("True", "False", "Unknown")) -> str:
    labels = ", ".join(label_order)
    return (
        f"Premise: {ex.premise}\n"
        f"Hypothesis: {ex.hypothesis}\n\n"
        f"Classify the relation as one of [{labels}] and give a probability distribution "
        "over True, False, and Unknown. The label must equal the highest-probability class "
        "unless an exact tie makes that impossible."
    )
