#!/usr/bin/env python3
"""Verify a local git-ignored ORIGINAL-v1 candidate against its committed manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path)
    ap.add_argument("manifest", type=Path)
    args = ap.parse_args()

    if not args.candidate.is_file():
        raise SystemExit("candidate not found: " + str(args.candidate))
    if not args.manifest.is_file():
        raise SystemExit("manifest not found: " + str(args.manifest))

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    expected_name = data.get("candidate")
    expected_sha = data.get("candidate_sha256")
    if not expected_name or not expected_sha:
        raise SystemExit("manifest is missing candidate/candidate_sha256")
    if args.candidate.name != expected_name:
        raise SystemExit("candidate filename mismatch: expected " + expected_name + ", found " + args.candidate.name)

    actual = sha256(args.candidate)
    if actual.lower() != str(expected_sha).lower():
        raise SystemExit(
            "candidate SHA-256 mismatch:\n  expected " + str(expected_sha) +
            "\n  actual   " + actual
        )

    print("LOCAL CANDIDATE VERIFIED", args.candidate.name, actual)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
