#!/usr/bin/env python3
"""Build a review-time anonymous source artifact without API calls or local data.

This utility does not decide whether IASEAI'27 requires anonymity; it only prepares a
sanitized option. It never includes Git history, credentials, downloaded benchmark
bytes, provider outputs, or the development repository's identity-bearing metadata.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOP_LEVEL_FILES = (
    "LICENSE",
    "pyproject.toml",
    "requirements.txt",
    "requirements-frozen.txt",
)

INCLUDE_DIRS = (
    "src",
    "scripts",
    "configs",
    "tests",
)

DATA_FILES = (
    "data/README.md",
    "data/MANIFEST.json",
    "data/THIRD_PARTY_DATA.md",
)

FORBIDDEN_PARTS = {
    ".git",
    ".github",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "results",
    "artifacts",
}

FORBIDDEN_FILENAMES = {
    ".env",
    ".env.example",
    "CITATION.cff",
    "README.md",  # development README is replaced by an anonymous generated README
    "imperfectiveNLI.json",
    "MANIFEST.local.json",
    "dataset_manifest.json",
}

# Keep this list specific enough to avoid false positives in scientific prose.
IDENTITY_TOKENS = (
    "Rocky5502",
    "github.com/Rocky5502",
    "70815297",
    "Rocky 文浩",
)

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".tex",
    ".sty",
    ".bib",
    ".cff",
}

ANONYMOUS_README = """# Anonymous review artifact — The Imperfective Uncertainty in Large Language Models

This package contains the source code, frozen experiment configuration, analysis
scripts, tests, and third-party dataset provenance metadata for anonymous review.

It intentionally excludes Git history, author identity, API credentials, downloaded
benchmark bytes, raw provider outputs, processed empirical results, and local evidence
snapshots. The ImperfectiveNLI benchmark must be fetched through the included provenance-
checking downloader before local execution; its bytes are not redistributed here.

No synthetic fixture output in this package is scientific evidence. Numerical manuscript
claims must come only from audited live experiment artifacts produced by the frozen run.

The official venue anonymity/artifact policy should be checked before uploading this ZIP.
"""


def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in FORBIDDEN_PARTS for part in rel.parts):
        return False
    if path.name in FORBIDDEN_FILENAMES:
        return False
    if path.is_dir():
        return False
    return True


def collect_files() -> list[Path]:
    files: list[Path] = []
    for name in TOP_LEVEL_FILES:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(f"required artifact input missing: {name}")
        files.append(path)

    for dirname in INCLUDE_DIRS:
        base = ROOT / dirname
        if not base.is_dir():
            raise FileNotFoundError(f"required artifact directory missing: {dirname}")
        files.extend(path for path in base.rglob("*") if should_include(path))

    for name in DATA_FILES:
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(f"required data-provenance file missing: {name}")
        files.append(path)

    unique = sorted(set(files), key=lambda p: p.relative_to(ROOT).as_posix())
    return unique


def scan_identity(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name != "LICENSE":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            problems.append(f"non-UTF8 text candidate: {path.relative_to(ROOT)}")
            continue
        for token in IDENTITY_TOKENS:
            if token.lower() in text.lower():
                problems.append(
                    f"identity token {token!r} found in {path.relative_to(ROOT).as_posix()}"
                )
    return problems


def write_deterministic(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arcname)
    # Stable ZIP metadata; avoids leaking local filesystem timestamps/user metadata.
    info.date_time = (2026, 9, 3, 0, 0, 0)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, data)


def build_zip(files: list[Path], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w") as zf:
        write_deterministic(zf, "README.md", ANONYMOUS_README.encode("utf-8"))
        for path in files:
            arcname = path.relative_to(ROOT).as_posix()
            write_deterministic(zf, arcname, path.read_bytes())


def audit_zip(out: Path) -> None:
    with zipfile.ZipFile(out, "r") as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise RuntimeError("anonymous artifact contains duplicate ZIP paths")
        for name in names:
            parts = Path(name).parts
            if any(part in FORBIDDEN_PARTS for part in parts):
                raise RuntimeError(f"forbidden path escaped into ZIP: {name}")
            if Path(name).name in FORBIDDEN_FILENAMES and name != "README.md":
                raise RuntimeError(f"forbidden filename escaped into ZIP: {name}")
            if name.endswith("imperfectiveNLI.json"):
                raise RuntimeError("downloaded third-party benchmark bytes must not be packaged")

        for name in names:
            suffix = Path(name).suffix.lower()
            if suffix not in TEXT_SUFFIXES and Path(name).name not in {"LICENSE", "README.md"}:
                continue
            try:
                text = zf.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            for token in IDENTITY_TOKENS:
                if token.lower() in text.lower():
                    raise RuntimeError(f"identity token {token!r} found inside ZIP file {name}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/local/ULLM_anonymous_review_artifact.zip"),
    )
    p.add_argument(
        "--check-only",
        action="store_true",
        help="scan the selected source set without creating a ZIP",
    )
    args = p.parse_args()

    files = collect_files()
    problems = scan_identity(files)
    if problems:
        print("Anonymous artifact identity scan FAIL", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        raise SystemExit(1)

    if args.check_only:
        print(f"Anonymous artifact source scan PASS ({len(files)} files; no ZIP written)")
        return

    build_zip(files, args.out)
    audit_zip(args.out)
    print(f"Anonymous artifact PASS: {args.out} ({len(files) + 1} files including README)")


if __name__ == "__main__":
    main()
