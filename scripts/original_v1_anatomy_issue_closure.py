#!/usr/bin/env python3
"""Verify structured closure evidence for ORIGINAL-v1 Critical/High issues.

Two closure contracts exist:

* model_anatomy for visible/biomechanical model defects. It requires
  candidate-bound numerical, production-path visual, human-reference and
  whole-body regression evidence.
* process_control for validation/workflow failures such as WB-QA-*.
  It requires committed process evidence proving the fail-closed controls and
  regression tests, without pretending that a workflow defect needs a human
  anatomy render.

The verifier never mutates the ledger and never grants production approval.
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
CLOSURE_TYPES = ("model_anatomy", "process_control")


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


def _common_receipt_errors(issue: dict[str, Any], receipt: dict[str, Any]) -> list[str]:
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
    decision = receipt.get("closure_decision")
    if decision not in CLOSED_STATES or decision != issue.get("state"):
        errors.append(issue_id + ": closure decision must match ledger state")
    note = receipt.get("review_note")
    if not isinstance(note, str) or not note.strip():
        errors.append(issue_id + ": closure review note required")
    closure_type = receipt.get("closure_type")
    if closure_type not in CLOSURE_TYPES:
        errors.append(issue_id + ": closure_type invalid")
    if issue_id.startswith("WB-QA-") and closure_type != "process_control":
        errors.append(issue_id + ": WB-QA issue requires process_control closure")
    if not issue_id.startswith("WB-QA-") and closure_type != "model_anatomy":
        errors.append(issue_id + ": anatomy issue requires model_anatomy closure")
    return errors


def _verify_model_anatomy(
    root: Path,
    issue: dict[str, Any],
    receipt: dict[str, Any],
    human_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    issue_id = str(issue.get("id") or "unknown")
    for key in (
        "production_path_rendered",
        "visual_pass",
        "numerical_pass",
        "whole_body_regression_pass",
        "real_human_reference_checked",
    ):
        if receipt.get(key) is not True:
            errors.append(issue_id + ": " + key + " must be true")

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
    return errors


def _verify_process_control(
    root: Path,
    issue: dict[str, Any],
    receipt: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    issue_id = str(issue.get("id") or "unknown")
    for key in (
        "process_regression_tests_passed",
        "fail_closed_visual_blocking_verified",
        "historical_records_preserved",
        "production_approval_not_inferred",
    ):
        if receipt.get(key) is not True:
            errors.append(issue_id + ": " + key + " must be true")
    errors += [issue_id + ": " + x for x in _verify_refs(root, receipt.get("process_evidence"), "process")]
    command = receipt.get("test_command")
    if not isinstance(command, str) or not command.strip():
        errors.append(issue_id + ": test_command required")
    return errors


def verify_receipt(
    root: Path,
    issue: dict[str, Any],
    receipt: dict[str, Any],
    human_manifest: dict[str, Any],
) -> list[str]:
    errors = _common_receipt_errors(issue, receipt)
    if receipt.get("closure_type") == "model_anatomy":
        errors += _verify_model_anatomy(root, issue, receipt, human_manifest)
    elif receipt.get("closure_type") == "process_control":
        errors += _verify_process_control(root, issue, receipt)
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
            errors.append(issue_id + ": exactly one structured issue closure receipt required")
            continue
        _, receipt = candidates[0]
        errors += verify_receipt(root, issue, receipt, human_manifest)
    return list(dict.fromkeys(errors))
