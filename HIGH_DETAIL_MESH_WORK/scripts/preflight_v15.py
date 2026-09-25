"""Fail-fast V15 workspace preflight before Blender modelling starts.

Checks only prerequisites/invariants. It does not modify candidate assets.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORT = ROOT / "reports" / "v15_preflight.json"
EXPECTED_BRANCH = "work/v15-deep-hand-rebuild-prep-20260925"
FORBIDDEN_BRANCH = "chatgpt/absolute-retarget-imports"

def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git(*args):
    try:
        return subprocess.check_output(
            ["git", *args], cwd=REPO, text=True, stderr=subprocess.STDOUT
        ).strip()
    except subprocess.CalledProcessError as exc:
        return f"ERROR: {exc.output.strip()}"
    except Exception as exc:
        return f"ERROR: {exc}"

def find_blender():
    explicit = os.environ.get("BLENDER_EXE")
    if explicit and Path(explicit).is_file():
        return str(Path(explicit))
    found = shutil.which("blender")
    if found:
        return found
    if os.name == "nt":
        import glob
        hits = sorted(
            glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),
            reverse=True,
        )
        if hits:
            return hits[0]
    return None

def syntax_check(path: Path):
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        return None
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"

def main():
    failures = []
    warnings = []
    details = {}

    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    details["git_branch"] = branch
    details["git_head"] = head

    if branch == FORBIDDEN_BRANCH:
        failures.append("Refusing V15 mesh work on live source branch chatgpt/absolute-retarget-imports.")
    elif branch != EXPECTED_BRANCH:
        warnings.append(
            f"Expected preparation branch {EXPECTED_BRANCH}, current branch is {branch}. "
            "Continue only if this is an intentional descendant/candidate branch."
        )

    status = git("status", "--porcelain")
    details["working_tree_dirty"] = bool(status and not status.startswith("ERROR:"))
    if details["working_tree_dirty"]:
        warnings.append("Working tree has local/untracked changes; preserve them before destructive Git operations.")

    manifest_path = ROOT / "CANDIDATE_BASELINE_MANIFEST.json"
    if not manifest_path.is_file():
        failures.append("Missing CANDIDATE_BASELINE_MANIFEST.json")
        manifest = {}
    else:
        manifest = json.loads(manifest_path.read_text())

    required = [
        ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend",
        ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb",
        ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend",
        ROOT / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.glb",
        ROOT / "reports" / "hand_contact_guard_v5.json",
        ROOT / "renders_v14e_finger_body_trial" / "V14E_V13E_OPEN_HAND_COMPARISON.jpg",
        ROOT / "renders_v14e_finger_body_trial" / "V14E_V13E_CLOSED_FIST_COMPARISON.jpg",
        ROOT / "renders_v14e_finger_body_trial" / "V14E_V13E_EXERCISE_HAND_COMPARISON.jpg",
        ROOT / "scripts" / "pack_v11_hand_glb.py",
        ROOT / "scripts" / "run_candidate_gates.py",
        ROOT / "scripts" / "render_candidate_review.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    details["missing_required_files"] = missing
    if missing:
        failures.append("Missing required V15 baseline/tool files: " + ", ".join(missing))

    hash_checks = {}
    hash_specs = []
    try:
        v8 = manifest["geometry_baseline"]
        v13 = manifest["hand_fingertip_review_candidate"]
        hash_specs = [
            (ROOT / v8["dressed_glb"], v8["sha256"]["dressed_glb"]),
            (ROOT / v8["blend"], v8["sha256"]["blend"]),
            (ROOT / v13["dressed_glb"], v13["sha256"]["dressed_glb"]),
            (ROOT / v13["blend"], v13["sha256"]["blend"]),
        ]
    except Exception as exc:
        failures.append(f"Manifest does not contain expected V8/V13e hash entries: {exc}")

    for path, expected in hash_specs:
        if not path.is_file():
            continue
        actual = sha256(path)
        ok = actual.lower() == expected.lower()
        hash_checks[path.name] = {"expected": expected, "actual": actual, "match": ok}
        if not ok:
            failures.append(f"Baseline hash mismatch: {path.name}")
    details["baseline_hashes"] = hash_checks

    contact_path = ROOT / "reports" / "hand_contact_guard_v5.json"
    if contact_path.is_file():
        try:
            contact = json.loads(contact_path.read_text())
            count = len(contact["original_vertex_ids"])
            details["protected_contact_ids"] = count
            if count != 682:
                failures.append(f"Expected 682 protected hand-contact IDs, found {count}.")
        except Exception as exc:
            failures.append(f"Could not read hand_contact_guard_v5.json: {exc}")

    # Compile every Python helper in the mesh workspace, not only the V15
    # scripts. Later-phase tools are already prepared on this branch and a
    # syntax error there should be caught before precious Work/Blender usage.
    scripts = sorted((ROOT / "scripts").glob("*.py"))
    syntax = {}
    for path in scripts:
        if not path.is_file():
            continue
        error = syntax_check(path)
        syntax[path.name] = "PASS" if error is None else error
        if error:
            failures.append(f"Python syntax failure in {path.name}: {error}")
    details["python_syntax"] = syntax

    modules = {}
    for name in ("numpy", "PIL"):
        try:
            __import__(name)
            modules[name] = "available"
        except Exception as exc:
            modules[name] = f"missing: {exc}"
            failures.append(f"Required Python module unavailable: {name}")
    details["python_modules"] = modules

    blender = find_blender()
    details["blender_executable"] = blender
    if not blender:
        failures.append("Blender executable not found. Set BLENDER_EXE or add Blender to PATH.")
    else:
        try:
            proc = subprocess.run(
                [blender, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=20,
            )
            details["blender_version"] = proc.stdout.splitlines()[0] if proc.stdout else ""
            if proc.returncode:
                failures.append(f"Blender --version returned {proc.returncode}.")
        except Exception as exc:
            failures.append(f"Could not execute Blender: {exc}")

    tools = {
        "git": shutil.which("git"),
        "npm": shutil.which("npm"),
        "node": shutil.which("node"),
    }
    details["command_tools"] = tools
    for name, value in tools.items():
        if not value:
            failures.append(f"Required command unavailable: {name}")

    details["node_modules_present"] = (REPO / "node_modules").is_dir()
    if not details["node_modules_present"]:
        warnings.append(
            "Primary repo node_modules is absent. Latest-source validation may run npm ci in its disposable worktree."
        )

    report = {
        "pass": not failures,
        "failures": failures,
        "warnings": warnings,
        "details": details,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
