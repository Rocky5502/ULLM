from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
from collections import Counter, defaultdict
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


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text_sha256(payload)


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


def _load_jsonl_strict(path: Path) -> list[dict[str, Any]]:
    """Load an existing output, tolerating only a truncated final non-empty line."""
    if not path.exists():
        return []
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            if i == len(lines) - 1:
                print(f"WARNING: dropping truncated final JSONL line in {path}")
                break
            raise RuntimeError(f"Malformed non-final JSONL line {i + 1} in {path}") from exc
    return rows


def prepare_resume_output(path: Path, *, retry_failures: bool) -> None:
    """Validate existing keys and optionally purge failed rows before a retry.

    Failed rows are removed atomically before retrying, so the replacement call keeps a
    unique (example_id, repeat) key rather than appending a duplicate that would later
    fail the audit gate. If the process dies after the purge, a normal --resume still
    sees those keys as missing and can safely fill them.
    """
    if not path.exists():
        return
    rows = _load_jsonl_strict(path)
    keys = [(r.get("example", {}).get("id"), int(r.get("repeat", 0))) for r in rows]
    duplicates = [key for key, n in Counter(keys).items() if n > 1]
    if duplicates:
        raise RuntimeError(f"Refusing to resume {path}: duplicate keys {duplicates[:10]}")
    if not retry_failures:
        return
    kept = [r for r in rows if not r.get("request_error") and r.get("prediction") is not None]
    if len(kept) == len(rows):
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for row in kept:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    print(f"Purged {len(rows) - len(kept)} failed rows from {path} for clean retry")


def completed_keys(output: Path) -> set[tuple[str, int]]:
    seen: set[tuple[str, int]] = set()
    for row in _load_jsonl_strict(output):
        seen.add((row["example"]["id"], int(row["repeat"])))
    return seen


def _critical_manifest_fields(manifest: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "dataset_sha256",
        "dataset_n",
        "selected_n",
        "selected_ids",
        "models",
        "mode",
        "execution_mode",
        "prompt_type",
        "prompt_sha256",
        "label_order",
        "config_sha256",
        "models_sha256",
        "git_commit",
        "max_tokens",
        "model_request_overrides",
    )
    return {key: manifest.get(key) for key in keys}


def write_or_validate_manifest(path: Path, candidate: dict[str, Any], *, resume: bool) -> None:
    if path.exists():
        if not resume:
            raise RuntimeError(f"Manifest already exists: {path}")
        existing = json.loads(path.read_text(encoding="utf-8"))
        old = _critical_manifest_fields(existing)
        new = _critical_manifest_fields(candidate)
        if old != new:
            diffs = [k for k in old if old[k] != new[k]]
            raise RuntimeError(
                "Refusing unsafe resume because frozen manifest differs in: "
                + ", ".join(diffs)
            )
        print(f"Resume manifest verified: {path}")
        return
    path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")


def _validate_model_request_overrides(
    config: dict[str, Any], models: list[str]
) -> dict[str, dict[str, Any]]:
    raw = config.get("model_request_overrides", {}) or {}
    if not isinstance(raw, dict):
        raise SystemExit("model_request_overrides must be a mapping keyed by model ID")
    unknown = sorted(set(str(k) for k in raw) - set(models))
    if unknown:
        raise SystemExit(f"model_request_overrides contains unknown model IDs: {unknown}")

    forbidden = {"model", "messages", "temperature", "max_tokens", "seed"}
    out: dict[str, dict[str, Any]] = {}
    for model in models:
        value = raw.get(model, {}) or {}
        if not isinstance(value, dict):
            raise SystemExit(f"model_request_overrides[{model!r}] must be a mapping")
        collisions = sorted(forbidden & set(value))
        if collisions:
            raise SystemExit(
                f"model_request_overrides[{model!r}] may not replace common controls: {collisions}"
            )
        # JSON round-trip gives an immutable, serializable copy for manifests/records.
        out[model] = json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return out


def write_request_plan(
    path: Path,
    *,
    models: list[str],
    examples: list[Example],
    temperature: float,
    repeats: int,
    seed: int,
    max_tokens: int,
    prompt_type: str,
    label_order: tuple[str, str, str],
    model_request_overrides: dict[str, dict[str, Any]] | None = None,
) -> int:
    """Materialize the exact planned request hashes without contacting any provider.

    The plan deliberately stores hashes and IDs rather than model outputs. It is a
    zero-API rehearsal artifact for checking call counts, seeds, prompts, label order,
    and per-example request construction before a paid run.
    """
    system_prompt = get_system_prompt(prompt_type)
    overrides = model_request_overrides or {model: {} for model in models}
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for model in models:
            request_overrides = overrides.get(model, {})
            for ex in examples:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": make_user_prompt(ex, label_order=label_order)},
                ]
                message_hash = canonical_sha256(messages)
                for rep in range(repeats):
                    record = {
                        "model_requested": model,
                        "example_id": ex.id,
                        "group": ex.group,
                        "repeat": rep,
                        "seed_requested": seed + rep,
                        "temperature": temperature,
                        "max_tokens_requested": max_tokens,
                        "request_overrides": request_overrides,
                        "prompt_type": prompt_type,
                        "prompt_sha256": text_sha256(system_prompt),
                        "messages_sha256": message_hash,
                        "label_order": list(label_order),
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
    return count


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
    max_tokens: int,
    request_overrides: dict[str, Any],
    prompt_type: str,
    label_order: tuple[str, str, str],
    resume: bool,
    retry_failures: bool,
) -> None:
    if resume:
        prepare_resume_output(output, retry_failures=retry_failures)
    sem = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()
    already = completed_keys(output) if resume else set()
    system_prompt = get_system_prompt(prompt_type)

    async def write_record(record: dict[str, Any]) -> None:
        async with lock:
            with output.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()

    async def one(ex: Example, rep: int) -> None:
        key = (ex.id, rep)
        if key in already:
            return
        async with sem:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": make_user_prompt(ex, label_order=label_order)},
            ]
            requested_seed = seed + rep
            base_record: dict[str, Any] = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "model_requested": model,
                "temperature": temperature,
                "max_tokens_requested": max_tokens,
                "request_overrides": request_overrides,
                "seed_requested": requested_seed,
                "repeat": rep,
                "prompt_type": prompt_type,
                "prompt_sha256": text_sha256(system_prompt),
                "messages_sha256": canonical_sha256(messages),
                "label_order": list(label_order),
                "example": ex.__dict__,
            }
            try:
                result = await client.chat(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    seed=requested_seed,
                    request_overrides=request_overrides,
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
                        "http_status": result.http_status,
                        "attempts_used": result.attempts_used,
                        "raw_response": result.raw,
                    }
                )
            except Exception as exc:
                # Preserve failed calls in the audit trail. --resume --retry-failures
                # atomically purges these rows before replacing them with retry calls.
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
                        "http_status": None,
                        "attempts_used": None,
                        "raw_response": None,
                    }
                )
            await write_record(base_record)

    await asyncio.gather(*(one(ex, rep) for ex in examples for rep in range(repeats)))


async def main_async(args: argparse.Namespace) -> None:
    if args.retry_failures and not args.resume:
        raise SystemExit("--retry-failures requires --resume")
    if args.dry_run and (args.resume or args.retry_failures):
        raise SystemExit("--dry-run is a fresh rehearsal and cannot be combined with resume flags")

    config_path = Path(args.config)
    models_path = Path(args.models)
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    model_cfg = yaml.safe_load(models_path.read_text(encoding="utf-8"))
    configured_models = [m["id"] for m in model_cfg["models"]]
    all_model_request_overrides = _validate_model_request_overrides(config, configured_models)

    models = list(configured_models)
    if args.model:
        models = [m for m in models if m in args.model]
    if not models:
        raise SystemExit("No configured models matched --model.")
    model_request_overrides = {m: all_model_request_overrides[m] for m in models}

    input_path = Path(config["input_file"])
    examples_all = load_examples(input_path)
    examples = balanced_subset(examples_all, args.limit, int(config["seed"]))

    prompt_type = args.prompt or config.get("primary_prompt", "neutral")
    if prompt_type not in PROMPTS:
        raise SystemExit(f"Unknown --prompt={prompt_type}; choose from {sorted(PROMPTS)}")
    label_order = tuple(x.strip() for x in args.label_order.split(","))
    if sorted(label_order) != ["False", "True", "Unknown"] or len(label_order) != 3:
        raise SystemExit("--label-order must contain True,False,Unknown exactly once")

    max_tokens = int(config["max_tokens"])
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = Path(config["output_dir"]) / run_id
    if outdir.exists() and not args.resume:
        raise SystemExit(f"Run directory already exists: {outdir}. Use --resume or choose --run-id.")
    outdir.mkdir(parents=True, exist_ok=True)

    system_prompt = get_system_prompt(prompt_type)
    mode = config[args.mode]
    manifest = {
        "schema_version": 4,
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "dry_run" if args.dry_run else "live",
        "dataset_sha256": sha256(input_path),
        "dataset_path": str(input_path),
        "dataset_n": len(examples_all),
        "selected_n": len(examples),
        "selected_ids": sorted(ex.id for ex in examples),
        "models": models,
        "mode": args.mode,
        "temperature": float(mode["temperature"]),
        "samples_per_item": int(mode["samples_per_item"]),
        "max_tokens": max_tokens,
        "model_request_overrides": model_request_overrides,
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
    write_or_validate_manifest(outdir / "manifest.json", manifest, resume=args.resume)

    if args.dry_run:
        plan_path = outdir / "request_plan.jsonl"
        planned = write_request_plan(
            plan_path,
            models=models,
            examples=examples,
            temperature=float(mode["temperature"]),
            repeats=int(mode["samples_per_item"]),
            seed=int(config["seed"]),
            max_tokens=max_tokens,
            prompt_type=prompt_type,
            label_order=label_order,  # type: ignore[arg-type]
            model_request_overrides=model_request_overrides,
        )
        expected = len(models) * len(examples) * int(mode["samples_per_item"])
        if planned != expected:
            raise RuntimeError(f"Dry-run plan count mismatch: expected {expected}, wrote {planned}")
        print(f"DRY RUN ONLY: wrote {planned:,} planned requests to {plan_path}")
        print("No API client was created and no network request was made.")
        return

    client = OpenAICompatibleClient(
        base_url=config["base_url"],
        timeout_s=config["request_timeout_s"],
        max_retries=config["max_retries"],
    )
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
                max_tokens=max_tokens,
                request_overrides=model_request_overrides[model],
                prompt_type=prompt_type,
                label_order=label_order,  # type: ignore[arg-type]
                resume=args.resume,
                retry_failures=args.retry_failures,
            )
    finally:
        await client.aclose()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/experiment.yaml")
    p.add_argument("--models", default="configs/models.yaml")
    p.add_argument("--mode", choices=["deterministic", "sampling"], default="deterministic")
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
        help="Resume a compatible frozen run without duplicating completed keys",
    )
    p.add_argument(
        "--retry-failures",
        action="store_true",
        help="With --resume, purge request/parse failures and replace them cleanly",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Write a manifest and exact request-hash plan without creating an API client",
    )
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
