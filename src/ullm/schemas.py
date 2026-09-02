from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LABELS = ("True", "False", "Unknown")


@dataclass(frozen=True)
class Example:
    id: str
    group: str
    verb_class: str
    verb: str
    premise: str
    hypothesis: str
    label: str

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "Example":
        return cls(**{k: row[k] for k in cls.__annotations__})
