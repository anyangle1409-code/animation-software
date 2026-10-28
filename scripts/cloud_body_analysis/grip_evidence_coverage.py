#!/usr/bin/env python3
"""Read-only grip trial coverage and solver-guard audit from pinned evidence."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile


sys.path.insert(0, str(Path(__file__).resolve().parent))
from localize_failures import Evidence, SOURCES  # noqa: E402


STATUS = "READ_ONLY_GRIP_COVERAGE_AND_GUARD_AUDIT_NOT_ACCEPTANCE"
PAIR_GUARD_MAX = 5
SHORT_CIRCUIT = "NOT_RUN: pair guard short-circuits"
PINNED_MEMBER_SHA256 = {
    "W8": {"diagnosis.json":
           "b1afed85ffbf247604f2fd2afce6a9e8a0b3fe0d69ab93f943e8d49d36ec5923"},
    "V14": {"diagnosis.json":
            "2f49c51a780acf3834e35ef9e9a122515d16c8bed3e069a71282cd6983dd9321"},
    "R120": {"diagnosis.json":
             "399cca503451fea4f84812e97675bdcc8c57c26aaa9c2a9c6c18b0ad2fb68e5e"},
}


def verify_member_hashes(model, reader, expected=None):
    expected = PINNED_MEMBER_SHA256.get(model) if expected is None else expected
    if not isinstance(expected, dict) or not expected:
        raise ValueError(f"{model}: pinned member hashes unavailable")
    verified = {}
    for name, wanted in expected.items():
        try:
            raw = reader(name)
        except (KeyError, FileNotFoundError) as error:
            raise ValueError(f"{model}: missing pinned {name} member") from error
        if hashlib.sha256(raw).hexdigest() != wanted:
            raise ValueError(f"{model}: {name} member hash mismatch")
        verified[name] = raw
    return verified


def _finite_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def analyze_trials(model, trials):
    if not isinstance(trials, list) or not trials:
        raise ValueError(f"{model}: nonempty grip trial list required")
    suffix_counts = Counter()
    measured = []
    short_circuited = 0
    for index, row in enumerate(trials):
        if not isinstance(row, dict):
            raise ValueError(f"{model}: trial {index} must be an object")
        suffix = row.get("runtime_suffix")
        if suffix not in ("l", "r"):
            raise ValueError(f"{model}: trial {index} invalid runtime suffix")
        euler = row.get("thumb_01_euler_rad")
        if (not isinstance(euler, list) or len(euler) != 3
                or not all(_finite_number(value) for value in euler)):
            raise ValueError(f"{model}: trial {index} invalid thumb Euler")
        pairs = row.get("pairs")
        if not isinstance(pairs, int) or isinstance(pairs, bool) or pairs < 0:
            raise ValueError(f"{model}: trial {index} invalid pairs count")
        collapse = row.get("hand_collapse")
        if pairs > PAIR_GUARD_MAX:
            if collapse != SHORT_CIRCUIT:
                raise ValueError(f"{model}: trial {index} missing pair-guard short-circuit")
            short_circuited += 1
        else:
            if (not isinstance(collapse, int) or isinstance(collapse, bool)
                    or collapse < 0):
                raise ValueError(f"{model}: trial {index} invalid collapse count")
            measured.append({
                "trial_index": index,
                "authored_runtime_suffix_NOT_anatomical_side": suffix,
                "thumb_01_euler_rad": [float(value) for value in euler],
                "self_intersecting_pairs": pairs,
                "hand_collapse_count": collapse,
            })
        suffix_counts[suffix] += 1

    counts = {suffix: suffix_counts.get(suffix, 0) for suffix in ("l", "r")}
    missing = [suffix for suffix, count in counts.items() if count == 0]
    return {
        "status": STATUS,
        "model": model,
        "trial_count": len(trials),
        "authored_runtime_suffix_counts": counts,
        "missing_authored_runtime_suffixes": missing,
        "bilateral_trial_coverage": not missing,
        "anatomical_side_verified": False,
        "project_solver_pair_guard_max": PAIR_GUARD_MAX,
        "pair_guard_is_anatomical_threshold": False,
        "trials_reaching_collapse_measurement": len(measured),
        "trials_short_circuited_by_pair_guard": short_circuited,
        "observed_collapse_counts": [row["hand_collapse_count"] for row in measured],
        "pair_guard_trials": measured,
        "collapse_acceptance_threshold_defined": False,
        "contact_validation_performed": False,
        "grip_acceptance": False,
    }


def validate_diagnosis(model, source_sha256, diagnosis):
    if (not isinstance(diagnosis, dict)
            or diagnosis.get("model") != model
            or diagnosis.get("source_sha256") != source_sha256
            or diagnosis.get("source_and_copy_unchanged") is not True
            or diagnosis.get("anatomical_approval") != "NOT_GRANTED"
            or diagnosis.get("approved") is not False):
        raise ValueError(f"{model}: invalid source, preservation or approval metadata")
    grip = diagnosis.get("paths", {}).get("grip")
    if not isinstance(grip, dict):
        raise ValueError(f"{model}: grip path evidence missing")
    exception = grip.get("exception")
    if (grip.get("grip_exception_expected") is not True
            or not isinstance(exception, str)
            or "no thumb placement within the pair limit" not in exception):
        raise ValueError(f"{model}: expected failed grip solver evidence required")
    result = analyze_trials(model, grip.get("grip_trials"))
    result.update({
        "source_sha256": source_sha256,
        "source_unchanged": True,
        "solver_failed_without_placement": True,
        "last_rejected_trial_is_accepted_grip": False,
    })
    return result


def load_model(model, path):
    evidence = Evidence(model, path)
    try:
        raw = verify_member_hashes(model, evidence.read)["diagnosis.json"]
        return validate_diagnosis(model, SOURCES[model][0], json.loads(raw))
    finally:
        evidence.close()


def markdown(report):
    lines = [
        "# Grip evidence coverage and solver-guard audit — read-only",
        "",
        "**No accepted grip, anatomical side, hand-contact validation or collapse "
        "acceptance threshold.**",
        "",
        "The five-pair value is the pinned project's solver guard only. It is not a "
        "population ROM value, anatomical threshold or passing-grip criterion.",
    ]
    for model, result in report["models"].items():
        counts = result["authored_runtime_suffix_counts"]
        missing = ", ".join(result["missing_authored_runtime_suffixes"]) or "none"
        lines += [
            "", f"## {model}", "",
            f"- Trials: {result['trial_count']} (`l`: {counts['l']}, `r`: {counts['r']}); "
            f"missing authored runtime suffixes: {missing}.",
            f"- Pair guard reached collapse measurement: "
            f"{result['trials_reaching_collapse_measurement']}; short-circuited: "
            f"{result['trials_short_circuited_by_pair_guard']}.",
            f"- Observed collapse counts after the pair guard: "
            f"{result['observed_collapse_counts']}.",
            "- Solver result: failed to find a thumb placement within the pair limit; "
            "the last rendered state is rejected, not accepted.",
        ]
        if result["pair_guard_trials"]:
            lines += ["", "| Trial | Authored suffix | Thumb Euler rad | Pairs | Collapse count |",
                      "|---:|---|---|---:|---:|"]
            for row in result["pair_guard_trials"]:
                euler = ", ".join(f"{value:.9f}" for value in row["thumb_01_euler_rad"])
                lines.append(
                    f"| {row['trial_index']} | `{row['authored_runtime_suffix_NOT_anatomical_side']}` "
                    f"| {euler} | {row['self_intersecting_pairs']} | "
                    f"{row['hand_collapse_count']} |")
    lines += [
        "", "These counts document finite solver coverage and guard behavior only. They do "
        "not establish anatomical laterality, digit contact, grasp stability, pressure, "
        "load transfer, object fit, safe technique or a reusable accepted grip.", "",
    ]
    return "\n".join(lines)


def _aliases(first, second):
    first = Path(first)
    second = Path(second)
    if first.resolve(strict=False) == second.resolve(strict=False):
        return True
    try:
        return first.exists() and second.exists() and os.path.samefile(first, second)
    except OSError:
        return False


def write_outputs(report, out, evidence_paths):
    out = Path(out)
    json_path = out / "grip_evidence_coverage.json"
    markdown_path = out / "grip_evidence_coverage.md"
    outputs = (json_path, markdown_path)
    if _aliases(*outputs):
        raise ValueError("outputs must be outside and distinct from evidence")
    out_resolved = out.resolve(strict=False)
    for evidence_path in map(Path, evidence_paths):
        evidence_resolved = evidence_path.resolve(strict=False)
        if evidence_path.is_dir() and (
                out_resolved == evidence_resolved
                or out_resolved.is_relative_to(evidence_resolved)):
            raise ValueError("outputs must be outside and distinct from evidence")
        if any(_aliases(output, evidence_path) for output in outputs):
            raise ValueError("outputs must be outside and distinct from evidence")
        if evidence_path.is_dir():
            members = (member for member in evidence_path.rglob("*")
                       if member.is_file())
            if any(_aliases(output, member)
                   for member in members for output in outputs):
                raise ValueError("outputs must be outside and distinct from evidence")
    out.mkdir(parents=True, exist_ok=True)
    for path, content in (
            (json_path, json.dumps(report, indent=2) + "\n"),
            (markdown_path, markdown(report))):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=out,
                    prefix=f".{path.name}.", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    for model in SOURCES:
        parser.add_argument("--" + model.lower(), type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    selected = {model: getattr(args, model.lower()) for model in SOURCES}
    models = {model: load_model(model, path) for model, path in selected.items()}
    report = {
        "status": STATUS,
        "source_run": 39937882229,
        "models": models,
        "bilateral_coverage_complete": all(
            result["bilateral_trial_coverage"] for result in models.values()),
        "anatomical_approval": "NOT_GRANTED",
        "grip_acceptance": False,
        "contact_validation": "NOT_RUN",
        "collapse_acceptance_threshold": "NOT_DEFINED",
    }
    write_outputs(report, args.out, selected.values())


if __name__ == "__main__":
    main()
