from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import random
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .client import OpenAICompatibleClient
from .parsing import parse_prediction
from .prompts import PROMPTS, get_system_prompt, make_user_prompt
from .schemas import Example


def load_examples(path: Path) -> list[Example]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [Example.from_dict(row) for row in rows]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def balanced_subset(examples: list[Example], n: int, seed: int) -> list[Example]:
    """Deterministic A/B/C/D-balanced subset for smoke/robustness runs."""
    if n <= 0 or n >= len(examples):
        out = list(examples)
        random.Random(seed).shuffle(out)
        return out
    buckets: dict[str, list[Example]] = defaultdict(list)
    for ex in examples:
        buckets[ex.group[0]].append(ex)
    rng = random.Random(seed)
    for rows in buckets.values():
        rng.shuffle(rows)
    letters = [x for x in "ABCD" if x in buckets]
    out: list[Example] = []
    while len(out) < n:
        progressed = False
        for letter in letters:
            if buckets[letter] and len(out) < n:
                out.append(buckets[letter].pop())
                progressed = True
        if not progressed:
            break
    rng.shuffle(out)
    return out


def completed_keys(output: Path) -> set[tuple[str, int]]:
    """Read successful-or-recorded keys so --resume never duplicates API calls."""
    seen: set[tuple[str, int]] = set()
    if not output.exists():
        return seen
    for line in output.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            seen.add((row["example"]["id"], int(row["repeat"])))
        except Exception:
            # A truncated last line should not make the whole run unrecoverable.
            continue
    return seen


async def run_model(
    client: OpenAICompatibleClient,
    model: str,
    examples: list[Example],
    output: Path,
    *,
    temperature: float,
    repeats: int,
    concurrency: int,
    seed: int,
    prompt_type: str,
    label_order: tuple[str, str, str],
    resume: bool,
) -> None:
    sem = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()
    already = completed_keys(output) if resume else set()
    system_prompt = get_system_prompt(prompt_type)

    async def write_record(record: dict[str, Any]) -> None:
        async with lock:
            with output.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    async def one(ex: Example, rep: int) -> None:
        key = (ex.id, rep)
        if key in already:
            return
        async with sem:
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": make_user_prompt(ex, label_order=label_order),
                },
            ]
            base_record: dict[str, Any] = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "model_requested": model,
                "temperature": temperature,
                "repeat": rep,
                "prompt_type": prompt_type,
                "prompt_sha256": text_sha256(system_prompt),
                "label_order": list(label_order),
                "example": ex.__dict__,
            }
            try:
                result = await client.chat(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    seed=seed + rep,
                )
                try:
                    parsed = parse_prediction(result.text)
                    parse_error = None
                except Exception as exc:
                    parsed = None
                    parse_error = repr(exc)
                base_record.update(
                    {
                        "model_returned": result.model_returned,
                        "prediction": parsed,
                        "parse_error": parse_error,
                        "request_error": None,
                        "raw_text": result.text,
                        "usage": result.usage,
                        "latency_s": result.latency_s,
                        "request_id": result.request_id,
                        "raw_response": result.raw,
                    }
                )
            except Exception as exc:
                # Preserve the failed key in the audit trail. A later targeted retry can
                # be launched after filtering request_error records.
                base_record.update(
                    {
                        "model_returned": None,
                        "prediction": None,
                        "parse_error": None,
                        "request_error": repr(exc),
                        "raw_text": None,
                        "usage": None,
                        "latency_s": None,
                        "request_id": None,
                        "raw_response": None,
                    }
                )
            await write_record(base_record)

    await asyncio.gather(*(one(ex, rep) for ex in examples for rep in range(repeats)))


async def main_async(args: argparse.Namespace) -> None:
    config_path = Path(args.config)
    models_path = Path(args.models)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    model_cfg = yaml.safe_load(models_path.read_text(encoding="utf-8"))
    models = [m["id"] for m in model_cfg["models"]]
    if args.model:
        models = [m for m in models if m in args.model]
    if not models:
        raise SystemExit("No configured models matched --model.")

    input_path = Path(config["input_file"])
    examples_all = load_examples(input_path)
    examples = balanced_subset(examples_all, args.limit, int(config["seed"]))

    prompt_type = args.prompt or config.get("primary_prompt", "neutral")
    if prompt_type not in PROMPTS:
        raise SystemExit(f"Unknown --prompt={prompt_type}; choose from {sorted(PROMPTS)}")
    label_order = tuple(x.strip() for x in args.label_order.split(","))
    if sorted(label_order) != ["False", "True", "Unknown"] or len(label_order) != 3:
        raise SystemExit("--label-order must contain True,False,Unknown exactly once")

    client = OpenAICompatibleClient(
        base_url=config["base_url"],
        timeout_s=config["request_timeout_s"],
        max_retries=config["max_retries"],
    )

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = Path(config["output_dir"]) / run_id
    if outdir.exists() and not args.resume:
        raise SystemExit(
            f"Run directory already exists: {outdir}. Use --resume or choose --run-id."
        )
    outdir.mkdir(parents=True, exist_ok=True)

    system_prompt = get_system_prompt(prompt_type)
    manifest = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": sha256(input_path),
        "dataset_path": str(input_path),
        "dataset_n": len(examples_all),
        "selected_n": len(examples),
        "selected_ids": sorted(ex.id for ex in examples),
        "models": models,
        "mode": args.mode,
        "prompt_type": prompt_type,
        "prompt_sha256": text_sha256(system_prompt),
        "label_order": list(label_order),
        "config": config,
        "config_sha256": sha256(config_path),
        "models_sha256": sha256(models_path),
        "git_commit": git_commit(),
        "python": sys.version,
        "platform": platform.platform(),
    }
    (outdir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    mode = config[args.mode]
    try:
        for model in models:
            safe = model.replace("/", "_").replace(":", "_")
            output = outdir / f"{safe}__{args.mode}__{prompt_type}.jsonl"
            if output.exists() and not args.resume:
                raise SystemExit(f"Output already exists: {output}")
            print(f"Running {model} [{args.mode}/{prompt_type}] -> {output}")
            await run_model(
                client,
                model,
                examples,
                output,
                temperature=float(mode["temperature"]),
                repeats=int(mode["samples_per_item"]),
                concurrency=int(config["max_concurrency"]),
                seed=int(config["seed"]),
                prompt_type=prompt_type,
                label_order=label_order,  # type: ignore[arg-type]
                resume=args.resume,
            )
    finally:
        await client.aclose()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/experiment.yaml")
    p.add_argument("--models", default="configs/models.yaml")
    p.add_argument(
        "--mode", choices=["deterministic", "sampling"], default="deterministic"
    )
    p.add_argument(
        "--prompt",
        choices=sorted(PROMPTS),
        help="Prompt condition; defaults to configs/experiment.yaml primary_prompt",
    )
    p.add_argument(
        "--label-order",
        default="True,False,Unknown",
        help="Output-label order audit, e.g. Unknown,False,True",
    )
    p.add_argument(
        "--model",
        action="append",
        help="Run only a listed model ID; repeat flag for multiple models",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Balanced A/B/C/D smoke or robustness subset of N examples",
    )
    p.add_argument("--run-id", help="Stable run directory name; defaults to UTC timestamp")
    p.add_argument(
        "--resume",
        action="store_true",
        help="Resume an existing run without duplicating completed example/repeat keys",
    )
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
