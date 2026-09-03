from __future__ import annotations

import sys
from pathlib import Path

# Keep test imports deterministic under local runs and GitHub Actions regardless of
# PYTHONPATH overrides used for the src/ layout. This makes both the package code and
# research scripts importable without altering production execution semantics.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)
