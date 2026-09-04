#!/usr/bin/env python3
"""Fail fast on likely credentials or machine-local paths in tracked source files.

This is a lightweight release safeguard, not a replacement for GitHub secret scanning or
provider-side key rotation. It intentionally scans only Git-tracked files so ignored raw
results, downloaded data, virtual environments, and local evidence are outside the public
artifact boundary.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT_BYTES = 2_000_000

TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".cff",
    ".sh", ".ps1", ".ini", ".cfg", ".svg",
}

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OpenAI-style secret", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("Bearer credential", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}", re.I)),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Windows user profile path", re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\s]+", re.I)),
    ("project-local Windows path", re.compile(r"[A-Za-z]:\\\\IASEAI[^\s\"']*", re.I)),
)

SAFE_PLACEHOLDER_VALUES = {"replace_me", "example", "changeme", "your_key_here", ""}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    )
    return [ROOT / p.decode("utf-8") for p in result.stdout.split(b"\0") if p]


def scan_text(path: Path, text: str) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    problems: list[str] = []

    if rel == ".env":
        problems.append("tracked .env file")

    for name, pattern in PATTERNS:
        if pattern.search(text):
            problems.append(name)

    for match in re.finditer(r"(?im)^\s*(?:ZZZ_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY)\s*=\s*([^#\r\n]*)", text):
        value = match.group(1).strip().strip('"\'')
        if value.lower() not in SAFE_PLACEHOLDER_VALUES:
            problems.append("non-placeholder API-key assignment")

    return sorted(set(problems))


def main() -> None:
    findings: list[tuple[str, str]] = []
    for path in tracked_files():
        if not path.is_file() or path.stat().st_size > MAX_TEXT_BYTES:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {
            "README.md", "LICENSE", ".env.example", ".gitignore"
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for finding in scan_text(path, text):
            findings.append((path.relative_to(ROOT).as_posix(), finding))

    if findings:
        print("SECURITY SCAN FAIL")
        for rel, finding in findings:
            print(f"  - {rel}: {finding}")
        raise SystemExit(1)

    print("SECURITY SCAN PASS: no likely tracked credentials or machine-local paths found")


if __name__ == "__main__":
    main()
