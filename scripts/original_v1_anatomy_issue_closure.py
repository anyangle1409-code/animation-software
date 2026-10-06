#!/usr/bin/env python3
"""Verify structured closure evidence for ORIGINAL-v1 whole-body anatomy issues.

The ordinary issue ledger proves that closure files exist. This verifier proves
that Critical/High Fixed/Accepted rows are backed by candidate-bound numerical,
production-path visual, human-reference and whole-body regression evidence.

It never mutates the ledger and never grants production approval.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from original_v1_production_control import digest
from original_v1_whole_body_issues import validate_ledger

CLOSURE_STATUS = "ANATOMY_ISSUE_CLOSURE_EVIDENCE"
CLOSED_STATES = ("Fixed", "Accepted")
BLOCKING_SEVERITIES = ("Critical", "High")


def _safe_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("evidence path missing")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("evidence path missing/outside repository: " + relative)
    return path


def _verify_refs(root: Path, refs: object, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(refs, list) or not refs:
        return [label + " evidence refs missing"]
    for index, ref in enumerate(refs):
        prefix = f"{label}[{index}]"
        if not isinstance(ref, dict):
            errors.append(prefix + ": ref must be an object")
            continue
        relative = ref.get("path")
        sha = ref.get("sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", str(sha or "")):
            errors.append(prefix + ": SHA-256 invalid")
            continue
        try:
            path = _safe_file(root, relative)
            if digest(path) != sha:
                errors.append(prefix + ": hash differs")
        except (OSError, ValueError) as exc:
            errors.append(prefix + ": " + str(exc))
        if ref.get("passed") is not True:
            errors.append(prefix + ": passed=true required")
    return errors


def verify_receipt(
    root: Path,
    issue: dict[str, Any],
    receipt: dict[str, Any],
    human_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    issue_id = str(issue.get("id") or "unknown")
    candidate = issue.get("candidate") or {}
    if receipt.get("schema_version") != 1 or receipt.get("status") != CLOSURE_STATUS:
        errors.append(issue_id + ": closure receipt schema/status invalid")
    if receipt.get("production_approved") is not False:
        errors.append(issue_id + ": closure receipt must not claim production approval")
    if receipt.get("issue_id") != issue_id:
        errors.append(issue_id + ": closure receipt issue identity differs")
    if receipt.get("candidate_revision") != candidate.get("revision"):
        errors.append(issue_id + ": closure receipt candidate revision differs")
    if receipt.get("candidate_sha256") != candidate.get("sha256"):
        errors.append(issue_id + ": closure receipt candidate SHA differs")
    if not re.fullmatch(r"[0-9a-f]{40}", str(receipt.get("source_git_commit") or "")):
        errors.append(issue_id + ": closure receipt source Git commit invalid")

    for key in (
        "production_path_rendered",
        "visual_pass",
        "numerical_pass",
        "whole_body_regression_pass",
        "real_human_reference_checked",
    ):
        if receipt.get(key) is not True:
            errors.append(issue_id + ": " + key + " must be true")

    decision = receipt.get("closure_decision")
    if decision not in CLOSED_STATES or decision != issue.get("state"):
        errors.append(issue_id + ": closure decision must match ledger state")

    errors += [issue_id + ": " + x for x in _verify_refs(root, receipt.get("visual_evidence"), "visual")]
    errors += [issue_id + ": " + x for x in _verify_refs(root, receipt.get("numerical_evidence"), "numerical")]
    errors += [issue_id + ": " + x for x in _verify_refs(root, receipt.get("regression_evidence"), "regression")]

    verified_human = {
        row.get("id") for row in human_manifest.get("entries", [])
        if isinstance(row, dict) and row.get("review_status") == "verified"
    }
    human_ids = receipt.get("human_evidence_ids")
    if not isinstance(human_ids, list) or not human_ids:
        errors.append(issue_id + ": closure human evidence ids missing")
    else:
        for evidence_id in human_ids:
            if evidence_id not in verified_human:
                errors.append(issue_id + ": unknown/unverified human evidence " + str(evidence_id))
        declared = set(issue.get("human_evidence_ids") or [])
        if declared and not (declared & set(human_ids)):
            errors.append(issue_id + ": closure evidence does not overlap issue human-evidence basis")

    note = receipt.get("review_note")
    if not isinstance(note, str) or not note.strip():
        errors.append(issue_id + ": closure review note required")
    return list(dict.fromkeys(errors))


def verify_closed_issues(
    root: Path,
    ledger: dict[str, Any],
    human_manifest: dict[str, Any],
) -> list[str]:
    """Require one valid structured receipt for every closed Critical/High issue."""
    errors: list[str] = []
    ledger_errors = validate_ledger(ledger, root)
    if ledger_errors:
        return ["issue ledger invalid: " + x for x in ledger_errors]

    for issue in ledger.get("issues", []):
        if issue.get("severity") not in BLOCKING_SEVERITIES or issue.get("state") not in CLOSED_STATES:
            continue
        issue_id = issue["id"]
        candidates = []
        for relative in issue.get("closure_evidence", []):
            try:
                path = _safe_file(root, relative)
                if path.suffix.lower() != ".json":
                    continue
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                if isinstance(data, dict) and data.get("status") == CLOSURE_STATUS and data.get("issue_id") == issue_id:
                    candidates.append((path, data))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
        if len(candidates) != 1:
            errors.append(issue_id + ": exactly one structured anatomy closure receipt required")
            continue
        _, receipt = candidates[0]
        errors += verify_receipt(root, issue, receipt, human_manifest)
    return list(dict.fromkeys(errors))
