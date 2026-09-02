#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys

import httpx
import yaml

base = os.getenv("ZZZ_BASE_URL", "https://api.zhizengzeng.com/v1").rstrip("/")
key = os.getenv("ZZZ_API_KEY")
if not key:
    sys.exit("ZZZ_API_KEY is not set")
wanted = [x["id"] for x in yaml.safe_load(open("configs/models.yaml", encoding="utf-8"))["models"]]
r = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {key}"}, timeout=30)
r.raise_for_status()
data = r.json()
available = {m.get("id") for m in data.get("data", [])}
print(json.dumps({"wanted": wanted, "available": {m: m in available for m in wanted}}, indent=2))
