#!/usr/bin/env python3
"""Verify an evidence-backed experimental continuation decision without mutating shared state.

This closes the gap between an axilla post-validation disposition and a future
ORIGINAL_V1_PRODUCTION_CONTROL.json continuation_decisions entry. It never edits
production control, accepts anatomy, promotes a baseline, enters Phase 4 or approves
production.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, digest, ensure_finite
from original_v1_candidate_closure import candidate_entry
from original_v1_review_package import build_package
from verify_original_v1_production_promotion import safe_path

KIND = "EXPERIMENTAL_CONTINUATION_DECISION"
DECISION = "retain_experimental"
ALLOWED_DISPOSITIONS = {
    "READY_FOR_VISUAL_DISPOSITION_PHASE4_STILL_BLOCKED",
    "READY_FOR_VISUAL_DISPOSITION_AND_PHASE4_AFTER_LINEAGE",
}


def ref_file(root: Path, reference: dict, label: str) -> Path:
    if not isinstance(reference, dict) or not reference.get("path") or not re.fullmatch(r"[0-9a-f]{64}", str(reference.get("sha256", ""))):
        raise ValueError(label + " path/SHA-256 reference required")
    path = safe_path(root, reference["path"])
    if not path.is_file() or digest(path) != reference["sha256"]:
        raise ValueError(label + " hash/path differs")
    return path


def review_manifest_refs(review: dict) -> set[tuple[str, str]]:
    refs=set()
    for row in review.get("review_sets", []) if isinstance(review, dict) else []:
        manifest=row.get("manifest") if isinstance(row, dict) else None
        if isinstance(manifest, dict) and manifest.get("path") and manifest.get("sha256"):
            refs.add((manifest["path"], manifest["sha256"]))
    return refs


def validate_decision(root: Path, packet: dict, row: dict, parent: dict, disposition: dict, review: dict) -> list[str]:
    issues=[]
    try:
        ensure_finite(packet)
    except ValueError as exc:
        issues.append(str(exc))
    revision=packet.get("candidate_revision")
    parent_revision=packet.get("parent_revision")
    if packet.get("schema_version") != 1 or packet.get("kind") != KIND or packet.get("decision") != DECISION:
        issues.append("continuation decision identity/schema differs")
    if packet.get("production_approved") is not False or packet.get("baseline_promotion") is not False or packet.get("phase4_authorized") is not False:
        issues.append("continuation decision cannot claim production, baseline promotion or Phase 4 authorization")
    if not re.fullmatch(r"r\d+", str(revision or "")) or not re.fullmatch(r"r\d+", str(parent_revision or "")):
        issues.append("numbered candidate/parent revisions required")
    if revision == parent_revision:
        issues.append("candidate and parent must differ")
    if packet.get("candidate_sha256") != row.get("sha256"):
        issues.append("continuation candidate SHA differs from ledger")
    if packet.get("parent_candidate_sha256") != parent.get("sha256"):
        issues.append("continuation parent SHA differs from ledger")
    if row.get("parent_sha256") != parent.get("sha256"):
        issues.append("candidate direct-parent SHA differs from selected parent")
    if packet.get("classification") != row.get("classification"):
        issues.append("candidate classification differs from ledger")
    reason=packet.get("reason")
    if not isinstance(reason, str) or len(reason.strip()) < 20:
        issues.append("specific evidence-backed continuation reason required")
    if packet.get("visual_disposition") != "retained_after_real_render_review":
        issues.append("explicit retained-after-real-render-review disposition required")
    if not re.fullmatch(r"[0-9a-f]{40}", str(packet.get("source_git_commit", ""))):
        issues.append("exact source Git commit required")
    try:
        stamp=datetime.fromisoformat(str(packet.get("evidence_timestamp", "")).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("timezone")
    except (ValueError, TypeError):
        issues.append("timezone-aware evidence timestamp required")

    if disposition.get("kind") != "AXILLA_POST_VALIDATION_DISPOSITION":
        issues.append("axilla post-validation disposition kind differs")
    if disposition.get("candidate_revision") != revision or disposition.get("candidate_sha256") != row.get("sha256"):
        issues.append("disposition candidate identity differs")
    if disposition.get("direct_parent") != parent_revision:
        issues.append("disposition parent revision differs")
    if disposition.get("status") not in ALLOWED_DISPOSITIONS:
        issues.append("disposition is not ready for visual continuation decision")
    if disposition.get("development_failure_count") != 0:
        issues.append("development failures remain")
    if disposition.get("direct_parent_regression_count") != 0:
        issues.append("strict direct-parent regressions remain")
    if disposition.get("local_face_status") != "LOCAL_FACE_NUMERIC_CLEAR":
        issues.append("declared local-face audit is not clear")
    if disposition.get("evidence_closure_status") != "EVIDENCE_CLOSED":
        issues.append("candidate evidence closure is incomplete")
    if disposition.get("review_package_status") != "REVIEW_PACKAGE_READY":
        issues.append("real review package is not ready")
    if disposition.get("production_approved") is not False or disposition.get("visual_acceptance_inferred") is not False:
        issues.append("disposition must not claim production or inferred visual acceptance")

    if review.get("status") != "REVIEW_PACKAGE_READY" or review.get("candidate_sha256") != row.get("sha256"):
        issues.append("current review package is not ready/bound to candidate")
    visual_ref=packet.get("visual_review_manifest")
    try:
        visual_path=ref_file(root, visual_ref, "visual review manifest")
        actual=(visual_path.relative_to(root.resolve()).as_posix(), visual_ref["sha256"])
        if actual not in review_manifest_refs(review):
            issues.append("visual review manifest is not in the candidate's verified review package")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append(str(exc))

    comparisons=disposition.get("comparisons")
    if not isinstance(comparisons, dict) or len(comparisons) < 2:
        issues.append("disposition comparison evidence incomplete")
    else:
        for name, evidence in comparisons.items():
            try:
                ref_file(root, evidence, "comparison " + str(name))
            except (OSError, ValueError, KeyError, TypeError) as exc:
                issues.append(str(exc))
    try:
        ref_file(root, disposition.get("face_audit"), "axilla face audit")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append(str(exc))
    return list(dict.fromkeys(issues))


def make_template(row: dict, parent: dict, disposition_ref: dict, review: dict, source_commit: str) -> dict:
    manifests=[x.get("manifest") for x in review.get("review_sets", []) if isinstance(x, dict) and isinstance(x.get("manifest"), dict)]
    return {
        "schema_version": 1,
        "kind": KIND,
        "decision": DECISION,
        "candidate_revision": row.get("revision"),
        "candidate_sha256": row.get("sha256"),
        "parent_revision": parent.get("revision"),
        "parent_candidate_sha256": parent.get("sha256"),
        "classification": row.get("classification"),
        "disposition": disposition_ref,
        "visual_review_manifest": manifests[0] if manifests else None,
        "visual_disposition": None,
        "reason": None,
        "source_git_commit": source_commit,
        "evidence_timestamp": None,
        "baseline_promotion": False,
        "phase4_authorized": False,
        "production_approved": False,
        "note": "INCOMPLETE template. Fill visual_disposition only after inspecting the real review renders; verification is read-only.",
    }


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("decision", type=Path, nargs="?")
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--revision")
    ap.add_argument("--parent")
    ap.add_argument("--disposition", type=Path)
    ap.add_argument("--json-out", type=Path, required=True)
    args=ap.parse_args()
    try:
        if args.json_out.exists():
            raise ValueError("continuation-decision output collision")
        source_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
        if args.template:
            if args.decision is not None or not args.revision or not args.parent or args.disposition is None:
                raise ValueError("template mode requires --revision, --parent and --disposition only")
            row,_=candidate_entry(ROOT,args.revision)
            parent,_=candidate_entry(ROOT,args.parent)
            disposition_path=args.disposition.resolve()
            if not disposition_path.is_relative_to(ROOT.resolve()) or not disposition_path.is_file():
                raise ValueError("disposition must be a repository-local file")
            disposition=json.loads(disposition_path.read_text(encoding="utf-8-sig"))
            ensure_finite(disposition)
            if disposition.get("candidate_sha256") != row.get("sha256") or disposition.get("direct_parent") != args.parent:
                raise ValueError("disposition does not match requested candidate/parent")
            review=build_package(ROOT,args.revision)
            result=make_template(
                row,parent,
                {"path":disposition_path.relative_to(ROOT.resolve()).as_posix(),"sha256":digest(disposition_path)},
                review,source_commit,
            )
            args.json_out.parent.mkdir(parents=True,exist_ok=True)
            args.json_out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
            print("INCOMPLETE CONTINUATION DECISION TEMPLATE — inspect real renders before filling")
            return 0

        if args.decision is None:
            raise ValueError("decision packet required unless --template")
        decision_path=args.decision.resolve()
        if not decision_path.is_relative_to(ROOT.resolve()) or not decision_path.is_file():
            raise ValueError("decision packet must remain inside repository")
        packet=json.loads(decision_path.read_text(encoding="utf-8-sig"))
        ensure_finite(packet)
        revision=packet.get("candidate_revision")
        parent_revision=packet.get("parent_revision")
        row,_=candidate_entry(ROOT,revision)
        parent,_=candidate_entry(ROOT,parent_revision)
        disposition_path=ref_file(ROOT,packet.get("disposition"),"post-validation disposition")
        disposition=json.loads(disposition_path.read_text(encoding="utf-8-sig"))
        ensure_finite(disposition)
        review=build_package(ROOT,revision)
        issues=validate_decision(ROOT,packet,row,parent,disposition,review)
        comparisons=disposition.get("comparisons",{}) if isinstance(disposition,dict) else {}
        fragment=None
        if not issues:
            fragment={
                "candidate_sha256":row["sha256"],
                "chosen_parent":parent_revision,
                "classification":row.get("classification"),
                "reason":packet["reason"],
                "comparison_evidence":[comparisons[k] for k in sorted(comparisons)],
            }
        result={
            "schema_version":1,
            "kind":"EXPERIMENTAL_CONTINUATION_DECISION_RECEIPT",
            "contract_status":"REFUSED" if issues else "CONTINUATION_DECISION_VERIFIED",
            "candidate_revision":revision,
            "candidate_sha256":row.get("sha256") if isinstance(row,dict) else None,
            "parent_revision":parent_revision,
            "issues":issues,
            "production_control_fragment":fragment,
            "decision_packet":{"path":decision_path.relative_to(ROOT.resolve()).as_posix(),"sha256":digest(decision_path)},
            "production_approved":False,
            "baseline_promotion":False,
            "phase4_authorized":False,
            "note":"Read-only verification. Copying the fragment into production control remains a separate explicit repository edit.",
        }
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,indent=2))
        return 1 if issues else 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError,subprocess.SubprocessError) as exc:
        print("STOP — "+str(exc))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
