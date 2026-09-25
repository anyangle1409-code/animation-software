"""Generate Phase C dumbbell grip seed candidates with the existing skinned solver.

This is a coarse seed generator, not an acceptance tool.

It fetches the latest source into a disposable worktree, reads the current
homeGymPTMale handle-centre baseline, then runs the existing
review-assets/harnesses/gripsolver.test.mts close-until-contact solver on the
accepted hand GLB at requested absolute Y corrections (millimetres relative to
the embedded handle centre).

Default coarse historical sweep: 0, -3, -6, -9, -12 mm.
Those values bracket the project's existing 0/-6/-9/-12 mm evidence; they are
not acceptance targets.

For every centre:
- solve left curl at the requested centre;
- convert solved exercise-closure angles into closure=1 SolvedGrip maxima;
- verify the same solved shape on the mirrored right hand;
- write a standalone candidate JSON suitable for EVALUATE_PHASE_C_GRIP.bat.

No source row is changed or promoted.
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
WORKTREE = REPO.parent / f"{REPO.name}-phase-c-seed-solve"
DEFAULT_Y_MM = [0.0, -3.0, -6.0, -9.0, -12.0]
FINGERS = ("index", "middle", "ring", "pinky")

def run(cmd, cwd, env=None, check=False, log=None):
    print("+", " ".join(str(x) for x in cmd), flush=True)
    p = subprocess.run(
        [str(x) for x in cmd],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    sys.stdout.write(p.stdout)
    if log:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text(p.stdout, encoding="utf-8")
    if check and p.returncode:
        raise subprocess.CalledProcessError(p.returncode, cmd)
    return p

def git(*args, check=False):
    return run(["git", *args], REPO, check=check)

def resolve_source():
    fetched = git("fetch", "origin", SOURCE_BRANCH)
    if fetched.returncode == 0:
        ref = "FETCH_HEAD"
    else:
        remote = f"origin/{SOURCE_BRANCH}"
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", remote],
            cwd=REPO,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ref = remote if probe.returncode == 0 else SOURCE_BRANCH
    sha = subprocess.check_output(["git", "rev-parse", ref], cwd=REPO, text=True).strip()
    message = subprocess.check_output(
        ["git", "show", "-s", "--format=%s", sha], cwd=REPO, text=True
    ).strip()
    return ref, sha, message, fetched.returncode

def remove_worktree():
    if WORKTREE.exists():
        git("worktree", "remove", "--force", str(WORKTREE))
        if WORKTREE.exists():
            shutil.rmtree(WORKTREE, ignore_errors=True)

def link_dependencies():
    target = WORKTREE / "node_modules"
    source = REPO / "node_modules"
    if target.exists():
        return "existing"
    if source.is_dir():
        try:
            if os.name == "nt":
                p = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(target), str(source)],
                    cwd=WORKTREE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                if p.returncode == 0:
                    return "junction-to-primary-node_modules"
            else:
                target.symlink_to(source, target_is_directory=True)
                return "symlink-to-primary-node_modules"
        except OSError:
            pass
    p = run(["npm", "ci"], WORKTREE)
    if p.returncode:
        raise SystemExit("npm ci failed in Phase C seed worktree")
    return "npm-ci"

def vitest_cmd():
    local = WORKTREE / "node_modules" / ".bin" / ("vitest.cmd" if os.name == "nt" else "vitest")
    return [str(local), "run"] if local.is_file() else ["npx", "--no-install", "vitest", "run"]

def current_handle_centre():
    text = (WORKTREE / "src" / "character" / "solvedGrip.ts").read_text(encoding="utf-8")
    block = re.search(
        r"homeGymPTMale\s*:\s*\{.*?dumbbell\s*:\s*\{.*?"
        r"handleCentre\s*:\s*\{\s*x\s*:\s*([-+0-9.eE]+)\s*,\s*"
        r"y\s*:\s*([-+0-9.eE]+)\s*,\s*z\s*:\s*([-+0-9.eE]+)\s*\}",
        text,
        re.S,
    )
    if not block:
        raise SystemExit("Could not read current homeGymPTMale dumbbell handleCentre.")
    return {"x": float(block.group(1)), "y": float(block.group(2)), "z": float(block.group(3))}

def parse_measurement(text):
    owners = {}
    for line in text.splitlines():
        m = re.match(
            r"\s*(index|middle|ring|pinky)\s+MCP/PIP/DIP.*near\s+([-0-9.]+)\s+mm\s+inside\s+(\d+)",
            line,
        )
        if m:
            owners[m.group(1)] = {"near_mm": float(m.group(2)), "inside": int(m.group(3))}
            continue
        m = re.match(r"\s*thumb\s+.*near\s+([-0-9.]+)\s+mm\s+inside\s+(\d+)", line)
        if m:
            owners["thumb"] = {"near_mm": float(m.group(1)), "inside": int(m.group(2))}
            continue
        m = re.match(r"\s*palm\s+near\s+([-0-9.]+)\s+mm\s+inside\s+(\d+)", line)
        if m:
            owners["palm"] = {"near_mm": float(m.group(1)), "inside": int(m.group(2))}
    wrap = None
    m = re.search(r"\bWRAP\s+([0-9.]+)deg", text)
    if m:
        wrap = float(m.group(1))
    return {"owners": owners, "wrap_deg": wrap}

def safe_seed_id(y_mm):
    sign = "P" if y_mm >= 0 else "M"
    value = abs(y_mm)
    text = f"{value:.1f}".replace(".", "p")
    return f"homeGymPTMaleV15SeedY{sign}{text}"

def solve_one(runner, glb, out, baseline, y_mm):
    desired = {"x": baseline["x"], "y": y_mm / 1000.0, "z": baseline["z"]}
    delta_mm = [
        (desired["x"] - baseline["x"]) * 1000.0,
        (desired["y"] - baseline["y"]) * 1000.0,
        (desired["z"] - baseline["z"]) * 1000.0,
    ]
    label = ("y_" + f"{y_mm:+.1f}").replace("+", "p").replace("-", "m").replace(".", "_")
    dump = out / f"{label}_solve.json"

    env = os.environ.copy()
    env["GLB"] = str(glb)
    env["OFFSET"] = json.dumps(delta_mm)
    env["EXERCISE"] = "curl"
    env["TIME"] = "2"
    env["SIDE"] = "l"
    env["DUMP"] = str(dump)
    solved = run(
        runner + ["review-assets/harnesses/gripsolver.test.mts"],
        WORKTREE,
        env=env,
        log=out / f"{label}_solve_left.log",
    )
    if solved.returncode or not dump.is_file():
        return {
            "desired_y_mm": y_mm,
            "desired_handleCentre": desired,
            "delta_from_current_mm": delta_mm,
            "solve_returncode": solved.returncode,
            "error": "left solve failed or produced no dump",
        }

    raw = json.loads(dump.read_text(encoding="utf-8"))
    closure = float(raw["closure"])
    if closure <= 0:
        raise RuntimeError("Grip solver returned a non-positive closure.")

    maxima = {
        finger: [float(v) / closure for v in raw["digits"][finger]]
        for finger in FINGERS
    }
    maxima["thumb"] = [float(v) / closure for v in raw["thumbAngles"]]
    opposition = float(raw["opposition"]) / closure

    verify = out / f"{label}_verify.json"
    verify.write_text(
        json.dumps(
            {
                "digits": raw["digits"],
                "thumbAngles": raw["thumbAngles"],
                "opposition": raw["opposition"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    env_r = os.environ.copy()
    env_r["GLB"] = str(glb)
    env_r["OFFSET"] = json.dumps(delta_mm)
    env_r["EXERCISE"] = "curl"
    env_r["TIME"] = "2"
    env_r["SIDE"] = "r"
    env_r["VERIFY"] = str(verify)
    mirrored = run(
        runner + ["review-assets/harnesses/gripsolver.test.mts"],
        WORKTREE,
        env=env_r,
        log=out / f"{label}_verify_right.log",
    )

    left_measure = parse_measurement(solved.stdout)
    right_measure = parse_measurement(mirrored.stdout)
    candidate = {
        "schema_version": 1,
        "solution_id": safe_seed_id(y_mm),
        "grip": "dumbbell",
        "radius": 0.015,
        "thumbOppositionX": opposition,
        "handleCentre": desired,
        "digits": maxima,
        "seed_evidence": {
            "source": "review-assets/harnesses/gripsolver.test.mts",
            "solve_exercise": raw.get("exercise"),
            "solve_side": raw.get("side"),
            "solve_closure": closure,
            "absolute_handle_centre_y_mm": y_mm,
            "delta_from_current_shipped_centre_mm": delta_mm,
        },
    }
    candidate_path = out / f"{label}_candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")

    owners = ("index", "middle", "ring", "pinky", "thumb")
    left_clean = all(left_measure["owners"].get(o, {}).get("inside", 0) == 0 for o in owners)
    right_clean = all(right_measure["owners"].get(o, {}).get("inside", 0) == 0 for o in owners)
    wraps = [x for x in (left_measure.get("wrap_deg"), right_measure.get("wrap_deg")) if x is not None]
    return {
        "desired_y_mm": y_mm,
        "desired_handleCentre": desired,
        "delta_from_current_mm": delta_mm,
        "solve_returncode": solved.returncode,
        "mirror_verify_returncode": mirrored.returncode,
        "left": left_measure,
        "right": right_measure,
        "left_digit_thumb_clean": left_clean,
        "right_digit_thumb_clean": right_clean,
        "min_wrap_deg": min(wraps) if wraps else None,
        "candidate_json": str(candidate_path),
        "solution_id": candidate["solution_id"],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", type=Path, required=True)
    ap.add_argument("--centre-y-mm", type=float, nargs="*", default=DEFAULT_Y_MM)
    ap.add_argument("--label", default="v15")
    ap.add_argument("--keep-worktree", action="store_true")
    args = ap.parse_args()

    character = args.character.resolve()
    if not character.is_file():
        raise SystemExit(f"Missing accepted hand GLB: {character}")
    if not args.centre_y_mm:
        raise SystemExit("At least one --centre-y-mm value is required.")

    out = ROOT / "reports" / f"phase_c_grip_seeds_{args.label}"
    out.mkdir(parents=True, exist_ok=True)

    ref, sha, message, fetch_code = resolve_source()
    remove_worktree()
    git("worktree", "add", "--detach", str(WORKTREE), sha, check=True)

    report = {
        "accepted_hand_glb": str(character),
        "source_branch": SOURCE_BRANCH,
        "source_head": sha,
        "source_commit_message": message,
        "fetch_returncode": fetch_code,
        "dependency_mode": None,
        "current_shipped_handleCentre": None,
        "requested_absolute_y_mm": args.centre_y_mm,
        "seeds": [],
        "diagnostic_order": [],
        "promotion": "none",
        "note": (
            "Seed generation only. Run EVALUATE_PHASE_C_GRIP.bat on shortlisted "
            "candidate JSON files and complete visual review before acceptance."
        ),
    }

    try:
        report["dependency_mode"] = link_dependencies()
        runner = vitest_cmd()
        baseline = current_handle_centre()
        report["current_shipped_handleCentre"] = baseline

        seeds = [
            solve_one(runner, character, out, baseline, y_mm)
            for y_mm in args.centre_y_mm
        ]
        report["seeds"] = seeds

        sortable = [s for s in seeds if "error" not in s]
        sortable.sort(
            key=lambda s: (
                not s.get("left_digit_thumb_clean", False),
                not s.get("right_digit_thumb_clean", False),
                -(s.get("min_wrap_deg") or -1e9),
            )
        )
        report["diagnostic_order"] = [
            {
                "solution_id": s.get("solution_id"),
                "desired_y_mm": s.get("desired_y_mm"),
                "left_clean": s.get("left_digit_thumb_clean"),
                "right_clean": s.get("right_digit_thumb_clean"),
                "min_wrap_deg": s.get("min_wrap_deg"),
                "candidate_json": s.get("candidate_json"),
            }
            for s in sortable
        ]
    finally:
        (out / "phase_c_grip_seed_report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        if not args.keep_worktree:
            remove_worktree()

if __name__ == "__main__":
    main()
