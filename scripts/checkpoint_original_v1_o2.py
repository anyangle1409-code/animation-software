"""Record a passing ORIGINAL v1 O2 modelling checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "ORIGINAL_V1_WORK" / "HomeGymPT_Male_ORIGINAL_v1.blend"
CHECKPOINTS = ROOT / "ORIGINAL_V1_WORK" / "checkpoints"
LOG = ROOT / "ORIGINAL_V1_WORK" / "O2_AUTHORING_LOG.jsonl"
REPORTS = ROOT / "reports"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_report(name: str) -> dict:
    path = REPORTS / name
    if not path.exists():
        raise SystemExit(f"Missing audit report: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace"
        ).strip()
    except Exception:
        return "unknown"


parser = argparse.ArgumentParser()
parser.add_argument("--region", required=True)
parser.add_argument("--strict", action="store_true")
args = parser.parse_args()

if not BLEND.exists():
    raise SystemExit(f"Missing Blend: {BLEND}")

boundary = read_report("original_v1_authoring_boundary_audit.json")
rig = read_report("original_v4_blender_audit.json")
mesh = read_report("original_v1_o2_mesh_audit.json")

if not boundary.get("pass"):
    raise SystemExit("Authoring-boundary audit is not passing.")
if not boundary.get("require_guarded"):
    raise SystemExit("Authoring-boundary audit did not require the guarded launcher.")
if not rig.get("pass"):
    raise SystemExit("Canonical-v4 Blender audit is not passing.")
if args.strict and not mesh.get("pass"):
    raise SystemExit("Strict O2 mesh audit is not passing.")

slug = "".join(character if character.isalnum() else "_" for character in args.region.strip()).strip("_").lower()
if not slug:
    raise SystemExit("Region name is empty.")

timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
CHECKPOINTS.mkdir(parents=True, exist_ok=True)
destination = CHECKPOINTS / f"O2_{slug}_{timestamp}.blend"
shutil.copy2(BLEND, destination)

source_hash = sha256(BLEND)
checkpoint_hash = sha256(destination)
if source_hash != checkpoint_hash:
    raise SystemExit("Checkpoint hash differs from source Blend after copy.")

record = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "stage": "O2_neutral_anatomy",
    "region": args.region,
    "strict": args.strict,
    "branch": git_value("branch", "--show-current"),
    "head": git_value("rev-parse", "HEAD"),
    "blend_sha256": source_hash,
    "checkpoint": str(destination.relative_to(ROOT)).replace("\\", "/"),
    "checkpoint_sha256": checkpoint_hash,
    "authoring_boundary_pass": True,
    "v4_rig_pass": True,
    "mesh_numeric_pass": bool(mesh.get("pass")),
}
with LOG.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, sort_keys=True) + "\n")

print(json.dumps(record, indent=2))
