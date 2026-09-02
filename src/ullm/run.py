from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .client import OpenAICompatibleClient
from .parsing import parse_prediction
from .prompts import SYSTEM_PROMPT, make_user_prompt
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


async def run_model(
    client: OpenAICompatibleClient,
    model: str,
    examples: list[Example],
    output: Path,
    temperature: float,
    repeats: int,
    concurrency: int,
    seed: int,
) -> None:
    sem = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()

    async def one(ex: Example, rep: int) -> None:
        async with sem:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": make_user_prompt(ex)},
            ]
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
            record: dict[str, Any] = {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "model_requested": model,
                "model_returned": result.model_returned,
                "temperature": temperature,
                "repeat": rep,
                "example": ex.__dict__,
                "prediction": parsed,
                "parse_error": parse_error,
                "raw_text": result.text,
                "usage": result.usage,
                "raw_response": result.raw,
            }
            async with lock:
                with output.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

    await asyncio.gather(
        *(one(ex, rep) for ex in examples for rep in range(repeats))
    )


async def main_async(args: argparse.Namespace) -> None:
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    model_cfg = yaml.safe_load(Path(args.models).read_text(encoding="utf-8"))
    models = [m["id"] for m in model_cfg["models"]]
    if args.model:
        models = [m for m in models if m in args.model]
    if not models:
        raise SystemExit("No configured models matched --model.")

    input_path = Path(config["input_file"])
    examples = load_examples(input_path)
    random.Random(config["seed"]).shuffle(examples)
    if args.limit:
        examples = examples[: args.limit]

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

    manifest = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": sha256(input_path),
        "dataset_path": str(input_path),
        "models": models,
        "config": config,
        "limit": args.limit,
    }
    (outdir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    mode = config[args.mode]
    for model in models:
        safe = model.replace("/", "_")
        output = outdir / f"{safe}__{args.mode}.jsonl"
        if output.exists() and not args.resume:
            raise SystemExit(f"Output already exists: {output}")
        print(f"Running {model} -> {output}")
        await run_model(
            client,
            model,
            examples,
            output,
            temperature=float(mode["temperature"]),
            repeats=int(mode["samples_per_item"]),
            concurrency=int(config["max_concurrency"]),
            seed=int(config["seed"]),
        )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/experiment.yaml")
    p.add_argument("--models", default="configs/models.yaml")
    p.add_argument(
        "--mode", choices=["deterministic", "sampling"], default="deterministic"
    )
    p.add_argument(
        "--model",
        action="append",
        help="Run only a listed model ID; repeat flag for multiple models",
    )
    p.add_argument(
        "--limit", type=int, default=0, help="Smoke-test a shuffled subset of N examples"
    )
    p.add_argument("--run-id", help="Stable run directory name; defaults to UTC timestamp")
    p.add_argument(
        "--resume",
        action="store_true",
        help="Append to an existing run directory intentionally",
    )
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
