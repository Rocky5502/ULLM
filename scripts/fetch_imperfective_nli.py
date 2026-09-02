#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://raw.githubusercontent.com/boleima/ImperfectiveParadox/main/data/imperfectiveNLI.json"
OUT = Path("data/imperfectiveNLI.json")
LOCAL_MANIFEST = Path("data/MANIFEST.local.json")
EXPECTED_GIT_BLOB = "e20112c9de1f8c8ab27a8e2b969699b23dcdb186"
EXPECTED_BYTES = 100970
EXPECTED_N = 400
REQUIRED = {"id", "group", "verb_class", "verb", "premise", "hypothesis", "label"}


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def main() -> None:
    req = Request(URL, headers={"User-Agent": "ULLM-research-artifact/0.2"})
    with urlopen(req, timeout=60) as response:
        payload = response.read()

    blob = git_blob_sha1(payload)
    if blob != EXPECTED_GIT_BLOB:
        raise RuntimeError(f"Upstream artifact changed: expected git blob {EXPECTED_GIT_BLOB}, got {blob}")
    if len(payload) != EXPECTED_BYTES:
        raise RuntimeError(f"Unexpected byte count: expected {EXPECTED_BYTES}, got {len(payload)}")

    rows = json.loads(payload.decode("utf-8"))
    if len(rows) != EXPECTED_N or any(not REQUIRED.issubset(row) for row in rows):
        raise RuntimeError("Unexpected ImperfectiveNLI schema or example count")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(payload)
    sha256 = hashlib.sha256(payload).hexdigest()
    LOCAL_MANIFEST.write_text(
        json.dumps(
            {
                "downloaded_utc": datetime.now(timezone.utc).isoformat(),
                "source_url": URL,
                "path": str(OUT),
                "bytes": len(payload),
                "examples": len(rows),
                "git_blob_sha1": blob,
                "sha256": sha256,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows)} exact upstream examples to {OUT}")
    print(f"git_blob_sha1={blob}")
    print(f"sha256={sha256}")


if __name__ == "__main__":
    main()
