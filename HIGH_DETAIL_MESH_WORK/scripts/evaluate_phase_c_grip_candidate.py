"""Evaluate a versioned Phase C dumbbell grip candidate without touching production.

The accepted hand GLB is never modified. A tagged copy selects a temporary
solution ID that is injected only into a detached latest-source worktree.

No promotion or merge occurs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SOURCE_BRANCH = "chatgpt/absolute-retarget-imports"
WORKTREE = REPO.parent / f"{REPO.name}-phase-c-grip-eval"

FOCUSED_TESTS = [
    "src/retargeting/mirroredHands.test.ts",
    "src/exercises/equipmentClearance.test.ts",
    "src/exercises/selfCollision.test.ts",
]

GRIP_CASES = [
    {"exercise": "curl", "time": 0.0, "side": "l"},
    {"exercise": "curl", "time": 2.0, "side": "l"},
    {"exercise": "curl", "time": 0.0, "side": "r"},
    {"exercise": "curl", "time": 2.0, "side": "r"},
    {"exercise": "press", "time": 0.0, "side": "l"},
    {"exercise": "press", "time": 2.0, "side": "l"},
    {"exercise": "press", "time": 0.0, "side": "r"},
    {"exercise": "press", "time": 2.0, "side": "r"},
]

FINGERS = ("index", "middle", "ring", "pinky", "thumb")
MAGIC = 0x46546C67
JSON_CHUNK = 0x4E4F534A

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
        raise SystemExit("npm ci failed in Phase C worktree")
    return "npm-ci"

def vitest_cmd():
    local = WORKTREE / "node_modules" / ".bin" / ("vitest.cmd" if os.name == "nt" else "vitest")
    return [str(local), "run"] if local.is_file() else ["npx", "--no-install", "vitest", "run"]

def test_counts(text):
    clean = re.sub(r"\x1b\[[0-9;]*m", "", text)
    lines = [line for line in clean.splitlines() if "Tests" in line]
    line = lines[-1] if lines else ""
    def value(label):
        m = re.search(r"(\d+)\s+" + label, line)
        return int(m.group(1)) if m else 0
    return {
        "failed": value("failed"),
        "passed": value("passed"),
        "skipped": value("skipped"),
        "line": line.strip(),
    }

def validate_candidate(candidate):
    failures = []
    if candidate.get("grip") != "dumbbell":
        failures.append("Only the dumbbell family is supported by this Phase C runner.")
    sid = candidate.get("solution_id")
    if not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z0-9_]+", sid):
        failures.append("solution_id must contain only letters, digits or underscore.")
    if not isinstance(candidate.get("radius"), (int, float)) or candidate["radius"] <= 0:
        failures.append("radius must be a positive number.")
    if not isinstance(candidate.get("thumbOppositionX"), (int, float)):
        failures.append("thumbOppositionX must be numeric.")
    centre = candidate.get("handleCentre")
    if not isinstance(centre, dict) or any(not isinstance(centre.get(k), (int, float)) for k in ("x", "y", "z")):
        failures.append("handleCentre must contain numeric x/y/z values.")
    digits = candidate.get("digits")
    if not isinstance(digits, dict):
        failures.append("digits must be an object.")
    else:
        for finger in FINGERS:
            row = digits.get(finger)
            if (
                not isinstance(row, list)
                or len(row) != 3
                or any(not isinstance(v, (int, float)) for v in row)
            ):
                failures.append(f"digits.{finger} must be three numbers.")
    if failures:
        raise SystemExit("Invalid candidate JSON:\n- " + "\n- ".join(failures))

def candidate_ts_block(candidate):
    sid = json.dumps(candidate["solution_id"])
    c = candidate["handleCentre"]
    d = candidate["digits"]
    rows = "\n".join(
        f"        {finger}: [{', '.join(str(float(x)) for x in d[finger])}],"
        for finger in FINGERS
    )
    return f"""  {sid}: {{
    dumbbell: {{
      radius: {float(candidate['radius'])},
      thumbOppositionX: {float(candidate['thumbOppositionX'])},
      handleCentre: {{ x: {float(c['x'])}, y: {float(c['y'])}, z: {float(c['z'])} }},
      digits: {{
{rows}
      }},
    }},
  }},
"""

def inject_candidate(candidate):
    path = WORKTREE / "src" / "character" / "solvedGrip.ts"
    text = path.read_text(encoding="utf-8")
    if candidate["solution_id"] in text:
        raise SystemExit(f"Candidate solution id already exists in latest source: {candidate['solution_id']}")
    m = re.search(
        r"const\s+SOLVED\s*:\s*Record<string,\s*Partial<Record<GripKind,\s*SolvedGrip>>>\s*=\s*\{",
        text,
    )
    if not m:
        raise SystemExit("Could not locate SOLVED table in src/character/solvedGrip.ts")
    text = text[:m.end()] + "\n" + candidate_ts_block(candidate) + text[m.end():]
    path.write_text(text, encoding="utf-8")

def read_glb(path):
    data = Path(path).read_bytes()
    if len(data) < 20:
        raise ValueError(f"Too short for GLB: {path}")
    magic, version, total = struct.unpack_from("<III", data, 0)
    if magic != MAGIC or version != 2 or total != len(data):
        raise ValueError(f"Invalid GLB header: {path}")
    chunks = []
    offset = 12
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        start = offset + 8
        chunks.append((kind, data[start:start + length]))
        offset = start + length
    return chunks

def tag_glb(source, target, solution_id):
    chunks = read_glb(source)
    new_chunks = []
    found_json = False
    for kind, payload in chunks:
        if kind != JSON_CHUNK:
            new_chunks.append((kind, payload))
            continue
        found_json = True
        doc = json.loads(payload.decode("utf-8").rstrip(" \t\r\n\0"))
        scenes = doc.get("scenes") or []
        scene_index = int(doc.get("scene", 0))
        if not scenes or not (0 <= scene_index < len(scenes)):
            raise RuntimeError("GLB has no active scene to carry gripSolutionId metadata.")
        scene = scenes[scene_index]
        extras = scene.setdefault("extras", {})
        home = extras.setdefault("homeGymPT", {})
        home["gripSolutionId"] = solution_id
        encoded = json.dumps(doc, separators=(",", ":")).encode("utf-8")
        encoded += b" " * ((-len(encoded)) % 4)
        new_chunks.append((kind, encoded))
    if not found_json:
        raise RuntimeError("GLB has no JSON chunk.")
    total = 12 + sum(8 + len(payload) for _, payload in new_chunks)
    out = bytearray(struct.pack("<III", MAGIC, 2, total))
    for kind, payload in new_chunks:
        out.extend(struct.pack("<II", len(payload), kind))
        out.extend(payload)
    Path(target).write_bytes(out)

def write_joint_limit_test(candidate):
    sid = json.dumps(candidate["solution_id"])
    path = WORKTREE / "src" / "character" / "__phase_c_candidate_limits.test.ts"
    content = f"""import {{ describe, expect, it }} from 'vitest';
import {{ canonicalSkeleton }} from '../rig/skeleton';
import {{ EXERCISES }} from '../exercises/library';
import {{ FINGERS }} from '../rig/boneNames';
import type {{ BoneName }} from '../rig/boneNames';
import {{ solvedGripFor }} from './solvedGrip';

describe('Phase C temporary grip candidate limits', () => {{
  it('stays inside every current dumbbell exercise closure', () => {{
    const solved = solvedGripFor({sid}, 'dumbbell');
    expect(solved).not.toBeNull();
    const exercises = EXERCISES.filter((exercise) => exercise.hands.grip === 'dumbbell');
    expect(exercises.length).toBeGreaterThan(0);
    for (const exercise of exercises) {{
      const closure = exercise.hands.closure;
      for (const finger of FINGERS) {{
        solved!.digits[finger].forEach((maximum, index) => {{
          const boneName = (finger + '_0' + (index + 1) + '_l') as BoneName;
          const bone = canonicalSkeleton.byName.get(boneName);
          expect(bone, exercise.id + ' ' + boneName).toBeDefined();
          const limit = bone!.definition.limits.z;
          const applied = maximum * closure;
          if (!limit) return;
          expect(applied, exercise.id + ' ' + boneName + ' z').toBeGreaterThanOrEqual(limit.min - 1e-9);
          expect(applied, exercise.id + ' ' + boneName + ' z').toBeLessThanOrEqual(limit.max + 1e-9);
        }});
      }}
      const thumbBase = canonicalSkeleton.byName.get('thumb_01_l')!;
      const opposition = solved!.thumbOppositionX * closure;
      expect(opposition, exercise.id + ' thumb opposition').toBeLessThanOrEqual(
        (thumbBase.definition.limits.x?.max ?? 0) + 1e-9,
      );
      expect(opposition, exercise.id + ' thumb opposition').toBeGreaterThanOrEqual(
        (thumbBase.definition.limits.x?.min ?? 0) - 1e-9,
      );
    }}
  }});
}});
"""
    path.write_text(content, encoding="utf-8")
    return path

def write_solution_selection_test(candidate):
    sid = json.dumps(candidate["solution_id"])
    path = WORKTREE / "src" / "character" / "__phase_c_solution_selection.test.ts"
    content = f"""import {{ readFileSync }} from 'node:fs';
import {{ describe, expect, it }} from 'vitest';
import {{ canonicalSkeleton }} from '../rig/skeleton';
import {{ retargetedCharacterSource }} from './retargetSource';

describe('Phase C temporary solution selection', () => {{
  it('loads the candidate grip solution id from tagged GLB scene metadata', async () => {{
    const asset = process.env.PHASE_C_TAGGED_GLB!;
    const bytes = readFileSync(asset);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const character = await retargetedCharacterSource({{
      id: 'phase-c-selection',
      label: 'Phase C selection',
      data,
    }}).build(canonicalSkeleton);
    expect(character.gripSolutionId).toBe({sid});
    character.dispose?.();
  }});
}});
"""
    path.write_text(content, encoding="utf-8")
    return path

def parse_grip_harness(text):
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

def run_grip_case(runner, glb, case, out, label):
    env = os.environ.copy()
    env["GLB"] = str(glb)
    env["SHIPPED"] = "1"
    env["EXERCISE"] = case["exercise"]
    env["TIME"] = str(case["time"])
    env["SIDE"] = case["side"]
    name = f"{label}_{case['exercise']}_t{case['time']}_{case['side']}".replace(".", "_")
    p = run(
        runner + ["review-assets/harnesses/gripsolver.test.mts"],
        WORKTREE,
        env=env,
        log=out / f"{name}.log",
    )
    return {
        "case": case,
        "returncode": p.returncode,
        "tests": test_counts(p.stdout),
        "measurement": parse_grip_harness(p.stdout),
    }

def summarize_cases(rows):
    finger_inside_max = {finger: 0 for finger in FINGERS}
    finger_near_min = {finger: None for finger in FINGERS}
    palm_near_min = None
    palm_inside_max = 0
    wraps = []
    for row in rows:
        measurement = row["measurement"]
        for finger in FINGERS:
            item = measurement["owners"].get(finger)
            if not item:
                continue
            finger_inside_max[finger] = max(finger_inside_max[finger], item["inside"])
            value = item["near_mm"]
            finger_near_min[finger] = (
                value if finger_near_min[finger] is None else min(finger_near_min[finger], value)
            )
        palm = measurement["owners"].get("palm")
        if palm:
            palm_inside_max = max(palm_inside_max, palm["inside"])
            palm_near_min = (
                palm["near_mm"] if palm_near_min is None else min(palm_near_min, palm["near_mm"])
            )
        if measurement.get("wrap_deg") is not None:
            wraps.append(measurement["wrap_deg"])
    return {
        "finger_inside_max": finger_inside_max,
        "finger_near_min_mm": finger_near_min,
        "palm_inside_max": palm_inside_max,
        "palm_near_min_mm": palm_near_min,
        "wrap_min_deg": min(wraps) if wraps else None,
        "wrap_max_deg": max(wraps) if wraps else None,
    }

def run_focused(runner, glb, out, label):
    env = os.environ.copy()
    env["REAL_CHARACTER_GLB"] = str(glb)
    results = {}
    for test in FOCUSED_TESTS:
        p = run(
            runner + [test],
            WORKTREE,
            env=env,
            log=out / f"{label}__{Path(test).stem}.log",
        )
        results[test] = {"returncode": p.returncode, "tests": test_counts(p.stdout)}
    return results

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--label", default="v15_grip_candidate")
    ap.add_argument("--skip-full-suite", action="store_true")
    ap.add_argument("--keep-worktree", action="store_true")
    args = ap.parse_args()

    character = args.character.resolve()
    candidate_path = args.candidate.resolve()
    if not character.is_file():
        raise SystemExit(f"Missing accepted hand GLB: {character}")
    if not candidate_path.is_file():
        raise SystemExit(f"Missing candidate JSON: {candidate_path}")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    validate_candidate(candidate)

    out = ROOT / "reports" / f"phase_c_grip_{args.label}"
    out.mkdir(parents=True, exist_ok=True)
    tagged = out / f"{character.stem}_{candidate['solution_id']}.glb"
    tag_glb(character, tagged, candidate["solution_id"])

    ref, sha, message, fetch_code = resolve_source()
    remove_worktree()
    git("worktree", "add", "--detach", str(WORKTREE), sha, check=True)

    report = {
        "label": args.label,
        "accepted_hand_glb": str(character),
        "candidate_json": str(candidate_path),
        "candidate_solution_id": candidate["solution_id"],
        "source_branch": SOURCE_BRANCH,
        "source_head": sha,
        "source_commit_message": message,
        "fetch_returncode": fetch_code,
        "dependency_mode": None,
        "source_suite": None,
        "typecheck": None,
        "joint_limits": None,
        "solution_selection": None,
        "baseline_grip_cases": [],
        "candidate_grip_cases": [],
        "baseline_grip_summary": None,
        "candidate_grip_summary": None,
        "focused_baseline": {},
        "focused_candidate": {},
        "new_failing_focused_tests": [],
        "focused_tests_with_increased_failures": [],
        "checks": {},
        "pass": False,
        "promotion": "none",
    }

    try:
        report["dependency_mode"] = link_dependencies()
        runner = vitest_cmd()
        inject_candidate(candidate)
        limit_test = write_joint_limit_test(candidate)
        selection_test = write_solution_selection_test(candidate)

        if not args.skip_full_suite:
            suite = run(["npm", "test"], WORKTREE, log=out / "full_source_suite.log")
            report["source_suite"] = {
                "returncode": suite.returncode,
                "tests": test_counts(suite.stdout),
            }

        typecheck = run(["npm", "run", "typecheck"], WORKTREE, log=out / "typecheck.log")
        report["typecheck"] = {"returncode": typecheck.returncode}

        selection_env = os.environ.copy()
        selection_env["PHASE_C_TAGGED_GLB"] = str(tagged)
        selection = run(
            runner + [str(selection_test.relative_to(WORKTREE))],
            WORKTREE,
            env=selection_env,
            log=out / "candidate_solution_selection.log",
        )
        report["solution_selection"] = {
            "returncode": selection.returncode,
            "tests": test_counts(selection.stdout),
        }

        limits = run(
            runner + [str(limit_test.relative_to(WORKTREE))],
            WORKTREE,
            log=out / "candidate_joint_limits.log",
        )
        report["joint_limits"] = {
            "returncode": limits.returncode,
            "tests": test_counts(limits.stdout),
        }

        baseline_rows = [
            run_grip_case(runner, character, case, out, "baseline")
            for case in GRIP_CASES
        ]
        candidate_rows = [
            run_grip_case(runner, tagged, case, out, "candidate")
            for case in GRIP_CASES
        ]
        report["baseline_grip_cases"] = baseline_rows
        report["candidate_grip_cases"] = candidate_rows
        report["baseline_grip_summary"] = summarize_cases(baseline_rows)
        report["candidate_grip_summary"] = summarize_cases(candidate_rows)

        baseline_focused = run_focused(runner, character, out, "baseline")
        candidate_focused = run_focused(runner, tagged, out, "candidate")
        report["focused_baseline"] = baseline_focused
        report["focused_candidate"] = candidate_focused

        new_failing = [
            test for test in FOCUSED_TESTS
            if baseline_focused[test]["returncode"] == 0
            and candidate_focused[test]["returncode"] != 0
        ]
        increased = [
            test for test in FOCUSED_TESTS
            if candidate_focused[test]["tests"]["failed"] > baseline_focused[test]["tests"]["failed"]
        ]
        report["new_failing_focused_tests"] = new_failing
        report["focused_tests_with_increased_failures"] = increased

        candidate_summary = report["candidate_grip_summary"]
        finger_clean = all(
            candidate_summary["finger_inside_max"].get(finger, 0) == 0
            for finger in FINGERS
        )
        wrap_ok = (
            candidate_summary["wrap_min_deg"] is not None
            and candidate_summary["wrap_min_deg"] >= 190
        )
        harness_clean = all(row["returncode"] == 0 for row in candidate_rows)
        source_suite_clean = (
            True if args.skip_full_suite
            else bool(report["source_suite"] and report["source_suite"]["returncode"] == 0)
        )
        checks = {
            "normal_source_suite_clean": source_suite_clean,
            "candidate_typecheck_clean": typecheck.returncode == 0,
            "candidate_solution_id_selected": selection.returncode == 0,
            "candidate_joint_limits_clean": limits.returncode == 0,
            "candidate_grip_harness_runs_clean": harness_clean,
            "no_digit_or_thumb_penetration_over_0_5mm": finger_clean,
            "skinned_wrap_at_least_190deg": wrap_ok,
            "no_new_focused_regression": not new_failing and not increased,
        }
        report["checks"] = checks
        report["pass"] = all(checks.values())
        report["notes"] = [
            "Palm penetration/contact is reported but is not treated as a failure because a loaded palm is intentional.",
            "The 190-degree wrap floor reuses the established grip diagnostic threshold; visual fist review remains required.",
            "The runner never replaces homeGymPTMale and never promotes the candidate solution.",
            "After a numeric pass, generate matched high-zoom grip boards before acceptance.",
        ]
    finally:
        (out / "phase_c_grip_evaluation.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
        if not args.keep_worktree:
            remove_worktree()

    if not report["pass"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
