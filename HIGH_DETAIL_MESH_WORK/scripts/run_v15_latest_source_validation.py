"""Disposable latest-source integration validation for V15.

This never merges the source branch into the mesh branch. It resolves/fetches
chatgpt/absolute-retarget-imports, creates a detached git worktree, runs the
source suite once, then runs every current REAL_CHARACTER_GLB-dependent gate
against production, V8, V13e and V15. Logs/reports are kept in
HIGH_DETAIL_MESH_WORK/reports/current_source_v15/.

The detached worktree is removed at the end unless --keep-worktree is passed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SOURCE_BRANCH = "chatgpt/absolute-retarget-imports"
WORKTREE = REPO.parent / f"{REPO.name}-v15-current-source-validation"
OUT = ROOT / "reports" / "current_source_v15"
VERSION = "v15a_deep_hand_rebuild"

FILES = [
    "src/exercises/equipmentClearance.test.ts",
    "src/exercises/selfCollision.test.ts",
    "src/exercises/families/lunge.test.ts",
    "src/exercises/families/rotation.test.ts",
    "src/exercises/families/trunkFlexion.test.ts",
    "src/retargeting/mirroredHands.test.ts",
    "src/retargeting/palmMapping.test.ts",
    "src/retargeting/realCharacterDiagnostic.test.ts",
    "src/retargeting/unmappedBones.test.ts",
]

def run(cmd, cwd, env=None, check=True, log=None):
    print("+", " ".join(str(x) for x in cmd), flush=True)
    p = subprocess.run(
        [str(x) for x in cmd],
        cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    sys.stdout.write(p.stdout)
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text(p.stdout, encoding="utf-8")
    if check and p.returncode:
        raise subprocess.CalledProcessError(p.returncode, cmd)
    return p

def git(*args, check=True):
    return run(["git", *args], REPO, check=check)

def resolve_source():
    # Fetch updates the remote ref only; no checkout/merge occurs in REPO.
    fetch = git("fetch", "origin", SOURCE_BRANCH, check=False)
    if fetch.returncode == 0:
        ref = "FETCH_HEAD"
    else:
        remote = f"origin/{SOURCE_BRANCH}"
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", remote],
            cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        ref = remote if probe.returncode == 0 else SOURCE_BRANCH
    sha = subprocess.check_output(["git", "rev-parse", ref], cwd=REPO, text=True).strip()
    return ref, sha, fetch.returncode

def remove_worktree():
    if WORKTREE.exists():
        git("worktree", "remove", "--force", str(WORKTREE), check=False)
        if WORKTREE.exists():
            shutil.rmtree(WORKTREE, ignore_errors=True)

def link_dependencies():
    source = REPO / "node_modules"
    target = WORKTREE / "node_modules"
    if target.exists():
        return "existing"
    if source.is_dir():
        try:
            if os.name == "nt":
                p = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(target), str(source)],
                    cwd=WORKTREE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True,
                )
                if p.returncode == 0:
                    return "junction-to-primary-node_modules"
            else:
                target.symlink_to(source, target_is_directory=True)
                return "symlink-to-primary-node_modules"
        except OSError:
            pass
    # Fallback: install only inside disposable worktree.
    run(["npm", "ci"], WORKTREE)
    return "npm-ci"

def vitest_cmd():
    local = WORKTREE / "node_modules" / ".bin" / ("vitest.cmd" if os.name == "nt" else "vitest")
    if local.is_file():
        return [str(local), "run"]
    return ["npx", "--no-install", "vitest", "run"]

def parse_measurements(text):
    arm = {}
    for m in re.finditer(r"^\s+([a-z_]+)\s+[LR]\s+closest\s+([-0-9.]+) mm", text, re.M):
        ex, value = m.group(1), float(m.group(2))
        arm[ex] = min(arm.get(ex, 1e9), value)
    equipment = {}
    for m in re.finditer(
        r"^\s+(PASS|FAIL)\s+([a-z_]+)\s+([a-z_]+)\s+(closest|deepest)\s+"
        r"([-0-9.]+) mm\s+inside (\d+)", text, re.M
    ):
        _, ex, item, kind, value, inside = m.groups()
        equipment[(ex, item, kind)] = (float(value), int(inside))
    return arm, equipment

def compare_measurements(a_text, b_text):
    a_arm, a_eq = parse_measurements(a_text)
    b_arm, b_eq = parse_measurements(b_text)
    arm_delta = {
        k: abs(a_arm[k] - b_arm[k])
        for k in sorted(set(a_arm) & set(b_arm))
    }
    eq_delta = {
        "|".join(k): abs(a_eq[k][0] - b_eq[k][0])
        for k in sorted(set(a_eq) & set(b_eq))
    }
    return {
        "arm_common": len(arm_delta),
        "arm_max_abs_delta_mm": max(arm_delta.values(), default=0.0),
        "arm_changed_over_0_05mm": {k:v for k,v in arm_delta.items() if v > 0.05},
        "equipment_common": len(eq_delta),
        "equipment_max_abs_delta_mm": max(eq_delta.values(), default=0.0),
        "equipment_changed_over_0_05mm": {k:v for k,v in eq_delta.items() if v > 0.05},
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-worktree", action="store_true")
    ap.add_argument("--skip-full-suite", action="store_true")
    args = ap.parse_args()

    assets = {
        "v8": ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb",
        "v13e": ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.glb",
        "v15": ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.glb",
    }
    missing = [str(p) for p in assets.values() if not p.is_file()]
    if missing:
        raise SystemExit("Missing comparison asset(s):\n- " + "\n- ".join(missing))

    OUT.mkdir(parents=True, exist_ok=True)
    ref, sha, fetch_code = resolve_source()
    remove_worktree()
    git("worktree", "add", "--detach", str(WORKTREE), sha)
    dependency_mode = None
    try:
        dependency_mode = link_dependencies()
        runner = vitest_cmd()

        suite = None
        if not args.skip_full_suite:
            suite_proc = run(
                ["npm", "test"],
                WORKTREE, check=False,
                log=OUT / "full_source_suite.log",
            )
            suite = {"returncode": suite_proc.returncode}
            if suite_proc.returncode != 0:
                raise SystemExit("Latest source full suite is not clean; see full_source_suite.log")

        production = WORKTREE / "review-assets" / "characters" / "HomeGymPT_Male_CORNER_FINAL_SHORTS.glb"
        runs = {"production": production, **assets}
        codes = {}
        texts = {}
        for name, glb in runs.items():
            env = os.environ.copy()
            env["REAL_CHARACTER_GLB"] = str(glb.resolve())
            proc = run(
                runner + FILES,
                WORKTREE, env=env, check=False,
                log=OUT / f"{name}.log",
            )
            codes[name] = proc.returncode
            texts[name] = proc.stdout

        # Reuse the current source's own table generator.
        table = run(
            [sys.executable, WORKTREE / "scripts" / "mesh-coordination-report.py",
             str(OUT), "production", "v8", "v13e", "v15"],
            WORKTREE, check=True,
            log=OUT / "coordination_tables.md",
        )

        delta = compare_measurements(texts["v13e"], texts["v15"])

        # Files that pass for V13e must not become failing for V15. Run each
        # current gate file independently to catch a new category regression.
        per_file = {}
        for path in FILES:
            results = {}
            for name in ("v13e", "v15"):
                env = os.environ.copy()
                env["REAL_CHARACTER_GLB"] = str(assets[name].resolve())
                proc = run(
                    runner + [path],
                    WORKTREE, env=env, check=False,
                    log=OUT / f"{name}__{Path(path).stem}.log",
                )
                results[name] = proc.returncode
            per_file[path] = results

        new_failing_files = [
            path for path, result in per_file.items()
            if result["v13e"] == 0 and result["v15"] != 0
        ]

        # A hand-only candidate should leave trunk/equipment measurements
        # effectively the same as V13e. 0.05 mm is report noise tolerance, not
        # a relaxation of any source test threshold.
        body_measurements_unchanged = (
            not delta["arm_changed_over_0_05mm"]
            and not delta["equipment_changed_over_0_05mm"]
        )
        passed = not new_failing_files and body_measurements_unchanged

        report = {
            "source_branch": SOURCE_BRANCH,
            "resolved_ref": ref,
            "source_head": sha,
            "fetch_returncode": fetch_code,
            "dependency_mode": dependency_mode,
            "full_suite": suite,
            "combined_gate_returncodes": codes,
            "per_file_returncodes": per_file,
            "new_failing_gate_files_vs_v13e": new_failing_files,
            "v13e_vs_v15_measurement_delta": delta,
            "body_measurements_unchanged_within_0_05mm": body_measurements_unchanged,
            "integration_no_regression": passed,
            "notes": [
                "V13e already has known source-gate failures from high-detail body shape; those are baseline context, not automatically V15 regressions.",
                "This runner does not merge the source branch and does not modify production assets.",
                "Inspect coordination_tables.md and v15.log before acceptance even when integration_no_regression is true.",
            ],
        }
        (OUT / "integration_report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        if not passed:
            raise SystemExit(1)
    finally:
        if not args.keep_worktree:
            remove_worktree()

if __name__ == "__main__":
    main()
