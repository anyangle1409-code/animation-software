"""Run the standard candidate-only validation gates with one command.

Run from HIGH_DETAIL_MESH_WORK:
    python scripts/run_candidate_gates.py --version v7_example

Expected files:
    HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_example.glb
    HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_example_BARE.glb

This runner does not install dependencies and does not edit production files.
It first runs the fast structural guard, then the focused runtime guards, then
the sampled five-exercise comparison. Logs are written under reports/.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
VALIDATION = ROOT / "validation"
REPAIR = VALIDATION / "scratchpad" / "repair"
HANDOFF = REPO / "HOME_GYM_PT_GPT_MESH_HANDOFF" / "harnesses"

GUARDS = [
    "sagittal.test.mts",
    "dressed_equivalence.test.mts",
    "gripmetric.test.mts",
    "overlap.test.mts",
    "gripagree.test.mts",
]

def run(cmd, cwd=None, env=None, log=None):
    print("+", " ".join(str(x) for x in cmd), flush=True)
    proc = subprocess.Popen(
        [str(x) for x in cmd],
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    chunks = []
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="")
        chunks.append(line)
    code = proc.wait()
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("".join(chunks))
    if code:
        raise SystemExit(code)

def ensure_harnesses():
    REPAIR.mkdir(parents=True, exist_ok=True)
    if not HANDOFF.is_dir():
        raise SystemExit(f"Missing harness source: {HANDOFF}")
    for name in GUARDS + ["vitest.config.mts"]:
        source = HANDOFF / name
        destination = REPAIR / name
        if not source.is_file():
            raise SystemExit(f"Missing harness: {source}")
        if not destination.exists():
            shutil.copyfile(source, destination)
    review = REPAIR / "review_v3.test.mts"
    if not review.is_file():
        raise SystemExit(f"Missing exercise review harness: {review}")

def vitest_command():
    local = VALIDATION / "node_modules" / ".bin" / ("vitest.cmd" if os.name == "nt" else "vitest")
    if local.is_file():
        return [str(local), "run"]
    pnpm = shutil.which("pnpm")
    if pnpm:
        return [pnpm, "exec", "vitest", "run"]
    npx = shutil.which("npx")
    if npx:
        return [npx, "--no-install", "vitest", "run"]
    raise SystemExit("Vitest is unavailable. Install the validation dependencies first.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="Candidate suffix, e.g. v7_knee_retopology")
    ap.add_argument("--skip-exercise", action="store_true")
    args = ap.parse_args()

    version = args.version
    dressed = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb"
    bare = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}_BARE.glb"
    if not dressed.is_file():
        raise SystemExit(f"Missing candidate: {dressed}")
    if not bare.is_file():
        raise SystemExit(f"Missing bare candidate: {bare}")

    run([
        sys.executable,
        str(ROOT / "scripts" / "candidate_quick_check.py"),
        str(dressed),
    ], cwd=ROOT)

    ensure_harnesses()
    config = REPAIR / "vitest.config.mts"
    runner = vitest_command()
    env = os.environ.copy()
    env.update({
        "GLB": str(dressed.resolve()),
        "ASSETS": str(dressed.resolve()),
        "DRESSED": str(dressed.resolve()),
        "BARE": str(bare.resolve()),
        "CANDIDATE_VERSION": version,
    })

    guard_files = [str((REPAIR / name).relative_to(VALIDATION)) for name in GUARDS]
    run(
        runner + ["--config", str(config.relative_to(VALIDATION)), *guard_files],
        cwd=VALIDATION,
        env=env,
        log=ROOT / "reports" / f"{version}_guards.log",
    )

    if not args.skip_exercise:
        review = str((REPAIR / "review_v3.test.mts").relative_to(VALIDATION))
        run(
            runner + ["--config", str(config.relative_to(VALIDATION)), review],
            cwd=VALIDATION,
            env=env,
            log=ROOT / "reports" / f"{version}_exercise.log",
        )

    print("\nCANDIDATE GATES PASS")
    print("version:", version)
    print("guards:", ROOT / "reports" / f"{version}_guards.log")
    if not args.skip_exercise:
        print("exercise:", ROOT / "reports" / f"{version}_exercise.log")

if __name__ == "__main__":
    main()
