#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://raw.githubusercontent.com/boleima/ImperfectiveParadox/main/data/imperfectiveNLI.json"
OUT = Path("data/imperfectiveNLI.json")
req = Request(URL, headers={"User-Agent": "ULLM-research-artifact/0.1"})
with urlopen(req, timeout=60) as response:
    payload = response.read()
rows = json.loads(payload.decode("utf-8"))
required = {"id", "group", "verb_class", "verb", "premise", "hypothesis", "label"}
if not rows or any(not required.issubset(row) for row in rows):
    raise RuntimeError("Unexpected ImperfectiveNLI schema")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(payload)
sha = hashlib.sha256(payload).hexdigest()
print(f"Wrote {len(rows)} examples to {OUT}; sha256={sha}")
