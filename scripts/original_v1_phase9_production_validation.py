#!/usr/bin/env python3
"""Build/verify the candidate-bound ORIGINAL-v1 Phase 9 production-validation receipt.

This closes evidence identity only. It never marks Phase 9 complete and never approves
production. The three production_target evaluator groups are recomputed from the exact
merged pose report; dressed range/contact/export/body-clothing evidence must all bind
the same candidate and locked rev2c rig.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

from original_v1_production_control import ROOT, digest, ensure_finite
from original_v1_locked_rig import load_locked_rig
from evaluate_original_v1_deformation_report import make_summary
from audit_original_v1_candidate_glbs import audit_candidate_set
import original_v1_export_evidence as export_evidence

ACCEPTANCE = "ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json"
EVALUATOR = "scripts/evaluate_original_v1_deformation_report.py"
HELPER = "scripts/original_v1_phase9_production_validation.py"
GROUPS = ("core_five", "extended", "shoulder_rhythm_diagnostics")


def local(root: Path, path: Path | str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    p = p.resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError("evidence path must remain inside repository")
    return p


def load_json(root: Path, path: Path | str, label: str) -> tuple[Path, dict | list]:
    p = local(root, path)
    if not p.is_file():
        raise ValueError(label + " missing")
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    ensure_finite(data)
    return p, data


def ref(root: Path, path: Path) -> dict:
    return {"path": path.resolve().relative_to(root.resolve()).as_posix(), "sha256": digest(path)}


def ref_path(root: Path, value: dict, label: str) -> Path:
    if not isinstance(value, dict) or not value.get("path") or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("sha256", ""))):
        raise ValueError(label + " path/SHA-256 required")
    p = local(root, value["path"])
    if not p.is_file() or digest(p) != value["sha256"]:
        raise ValueError(label + " bytes differ")
    return p


def expected_lock(root: Path) -> dict:
    rig = load_locked_rig(root)
    return {
        "revision": rig["revision"],
        "rig_structure_sha256": rig["rig_structure_sha256"],
        "bone_count": rig["bone_count"],
        "deform_bone_count": rig["deform_bone_count"],
        "lock": rig["lock"],
        "payload": rig["payload"],
    }


def lock_matches(value: dict, expected: dict) -> bool:
    return isinstance(value, dict) and all(value.get(k) == v for k, v in expected.items())


def summary_for_group(root: Path, merged: list, group: str) -> dict:
    spec = json.loads((root / ACCEPTANCE).read_text(encoding="utf-8"))
    return make_summary(merged, merged, spec, "production_target", group)


def final_identity_from_raw_and_export(root: Path, raw_pair: dict, export_receipt: dict) -> dict:
    snapshots = {}
    for item in raw_pair.get("source_evidence", []):
        try:
            p = ref_path(root, item, "raw snapshot")
            if p.suffix.lower() != ".json":
                continue
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            scope = data.get("snapshot_scope")
            if scope in ("body", "garment") and data.get("candidate_sha256") == raw_pair.get("candidate_sha256"):
                if scope in snapshots:
                    raise ValueError("duplicate " + scope + " raw snapshot")
                snapshots[scope] = item
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    if set(snapshots) != {"body", "garment"}:
        raise ValueError("raw pair does not expose exact body and garment snapshot receipts")

    exports = {}
    for item in export_receipt.get("source_evidence", []):
        p = ref_path(root, item, "export evidence")
        name = p.name.upper()
        if name.endswith("_BARE.GLB"):
            exports["bare_glb"] = item
        elif name.endswith("_DRESSED.GLB"):
            exports["dressed_glb"] = item
    if set(exports) != {"bare_glb", "dressed_glb"}:
        raise ValueError("verified export receipt does not expose exact bare/dressed GLB hashes")
    return {
        "body_snapshot": snapshots["body"],
        "garment_snapshot": snapshots["garment"],
        **exports,
    }


def _load_ref_json(root: Path, receipt: dict, key: str) -> tuple[Path, dict | list]:
    p = ref_path(root, receipt.get(key), key)
    data = json.loads(p.read_text(encoding="utf-8-sig"))
    ensure_finite(data)
    return p, data


def verify_receipt(root: Path, receipt: dict, expected_candidate_sha: str | None = None) -> list[str]:
    issues = []
    try:
        ensure_finite(receipt)
        candidate = receipt.get("candidate_sha256")
        if (receipt.get("schema_version") != 1 or receipt.get("phase") != 9 or
            receipt.get("phase_complete") is not False or receipt.get("production_approved") is not False):
            issues.append("Phase 9 receipt identity/schema differs")
        if not re.fullmatch(r"[0-9a-f]{64}", str(candidate or "")):
            issues.append("Phase 9 candidate SHA invalid")
        if expected_candidate_sha is not None and candidate != expected_candidate_sha:
            issues.append("Phase 9 receipt candidate differs from expected candidate")
        if not re.fullmatch(r"[0-9a-f]{40}", str(receipt.get("source_git_commit", ""))):
            issues.append("Phase 9 source Git commit missing/invalid")

        manifest_path, manifest = _load_ref_json(root, receipt, "full_evidence_manifest")
        merged_path, merged = _load_ref_json(root, receipt, "merged_pose_report")
        if not isinstance(manifest, dict) or not isinstance(merged, list):
            raise ValueError("full deformation evidence shape differs")
        if manifest.get("candidate_sha256") != candidate:
            issues.append("full evidence candidate differs")
        if manifest.get("merged_pose_report_sha256") != digest(merged_path):
            issues.append("full evidence merged-pose hash differs")
        if receipt.get("candidate_revision") != manifest.get("candidate_revision"):
            issues.append("Phase 9 revision differs from full evidence")

        prod = receipt.get("production_evaluations")
        if not isinstance(prod, dict) or set(prod) != set(GROUPS):
            issues.append("exact three production_target group evaluations required")
        else:
            for group in GROUPS:
                try:
                    p = ref_path(root, prod[group], group + " production evaluation")
                    actual = json.loads(p.read_text(encoding="utf-8-sig"))
                    expected = summary_for_group(root, merged, group)
                    if actual != expected:
                        issues.append(group + ": production evaluation differs from recomputation")
                    if actual.get("status") != "PASS" or actual.get("failure_count") != 0:
                        issues.append(group + ": production_target is not zero-failure PASS")
                except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                    issues.append(group + ": " + str(exc))

        lock = expected_lock(root)
        raw_path, raw = _load_ref_json(root, receipt, "raw_pair")
        static_path, static = _load_ref_json(root, receipt, "static_dressed")
        range_path, range_data = _load_ref_json(root, receipt, "range_evidence")
        _bridge_path, bridge = _load_ref_json(root, receipt, "contact_bridge")
        _equiv_path, equiv = _load_ref_json(root, receipt, "bare_dressed_equivalence")
        export_path, export_receipt = _load_ref_json(root, receipt, "export_evidence")

        for label, data in (("raw pair", raw), ("static dressed", static), ("range", range_data), ("equivalence", equiv), ("export", export_receipt)):
            if not isinstance(data, dict) or data.get("candidate_sha256") != candidate:
                issues.append(label + " candidate differs")

        for label, data in (("raw pair", raw), ("static dressed", static), ("range", range_data)):
            if not lock_matches(data.get("locked_rig"), lock):
                issues.append(label + " locked rev2c identity differs")
        if isinstance(equiv, dict):
            erig = equiv.get("locked_rig")
            if not isinstance(erig, dict) or any(erig.get(k) != v for k, v in lock.items()):
                issues.append("equivalence locked rev2c identity differs")

        if isinstance(static, dict) and receipt.get("raw_pair") not in static.get("source_evidence", []):
            issues.append("static dressed evidence is not bound to exact raw pair")
        if isinstance(range_data, dict) and receipt.get("static_dressed") not in range_data.get("source_evidence", []):
            issues.append("range evidence is not bound to exact static dressed parent")

        classification = range_data.get("classification", {}) if isinstance(range_data, dict) else {}
        if (classification.get("classification_complete") is not True or
            classification.get("unclassified_findings") != 0 or
            classification.get("unexplained_defects") != 0):
            issues.append("continuous range contact classification remains unresolved/defective")

        if not isinstance(bridge, dict) or bridge.get("source_bridge_status") != "VERIFIED_CURRENT_MODEL_BRANCH_SOURCE" or bridge.get("runtime_executed") is not False:
            issues.append("contact source bridge identity/status differs")
        elif set((bridge.get("scenarios") or {}).keys()) != {"push_up", "dumbbell_bicep_curl", "pull_up"}:
            issues.append("contact source bridge scenario coverage differs")

        if not isinstance(equiv, dict) or equiv.get("equivalence_status") != "IDENTICAL_UNDER_GARMENT_PRESENCE" or equiv.get("blockers") not in ([], None):
            issues.append("bare/dressed underlying-body equivalence is not clear")

        if not isinstance(export_receipt, dict) or export_receipt.get("status") != "EXPORT_IDENTITY_VERIFIED" or export_receipt.get("production_approved") is not False:
            issues.append("candidate export identity is not verified")
        else:
            manifests = []
            for item in export_receipt.get("source_evidence", []):
                try:
                    p = ref_path(root, item, "export source evidence")
                    if p.name == "CANDIDATE_GLB_EXPORT.json":
                        manifests.append(p)
                except (OSError, ValueError, KeyError, TypeError):
                    pass
            if len(manifests) != 1:
                issues.append("exact candidate export manifest receipt required")
            else:
                try:
                    reverified = export_evidence.verify(root, manifests[0])
                    structural = audit_candidate_set(manifests[0], root / export_evidence.RIG_PAYLOAD)
                    if reverified.get("candidate_sha256") != candidate or structural.get("pass") is not True:
                        issues.append("candidate export re-verification/structural audit failed")
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    issues.append("candidate export re-verification failed: " + str(exc))

        try:
            identity = final_identity_from_raw_and_export(root, raw, export_receipt)
            if receipt.get("final_body_clothing_hashes") != identity:
                issues.append("final body/clothing/export hash inventory differs")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            issues.append("final body/clothing identity invalid: " + str(exc))

        # Ensure the receipt itself binds current verifier/evaluator/spec bytes.
        expected_tools = {
            "verifier": ref(root, root / HELPER),
            "production_evaluator": ref(root, root / EVALUATOR),
            "acceptance_spec": ref(root, root / ACCEPTANCE),
        }
        for key, value in expected_tools.items():
            if receipt.get(key) != value:
                issues.append(key + " identity differs")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        issues.append(str(exc))
    return list(dict.fromkeys(issues))


def build(args) -> tuple[dict, int]:
    root = ROOT
    manifest_path, manifest = load_json(root, args.full_evidence_manifest, "full evidence manifest")
    merged_path, merged = load_json(root, args.merged_pose_report, "merged pose report")
    if not isinstance(manifest, dict) or not isinstance(merged, list):
        raise ValueError("full evidence inputs have unexpected shape")
    candidate = manifest.get("candidate_sha256")
    revision = manifest.get("candidate_revision")
    if not re.fullmatch(r"r\d+", str(revision or "")) or not re.fullmatch(r"[0-9a-f]{64}", str(candidate or "")):
        raise ValueError("full evidence candidate identity invalid")
    if manifest.get("merged_pose_report_sha256") != digest(merged_path):
        raise ValueError("merged report does not match full evidence manifest")

    out = local(root, args.out_dir)
    if out.exists():
        raise ValueError("Phase 9 output directory already exists; preserve evidence")
    out.mkdir(parents=True)

    prod_refs = {}
    for group in GROUPS:
        summary = summary_for_group(root, merged, group)
        path = out / ("production_target_" + group + ".json")
        path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        prod_refs[group] = ref(root, path)

    inputs = {}
    for key, path in (
        ("raw_pair", args.raw_pair),
        ("static_dressed", args.static_dressed),
        ("range_evidence", args.range_evidence),
        ("contact_bridge", args.contact_bridge),
        ("bare_dressed_equivalence", args.bare_dressed_equivalence),
        ("export_evidence", args.export_evidence),
    ):
        p, _ = load_json(root, path, key)
        inputs[key] = ref(root, p)

    raw = json.loads(ref_path(root, inputs["raw_pair"], "raw pair").read_text(encoding="utf-8-sig"))
    export_receipt = json.loads(ref_path(root, inputs["export_evidence"], "export evidence").read_text(encoding="utf-8-sig"))

    receipt = {
        "schema_version": 1,
        "phase": 9,
        "contract_status": "PHASE9_VALIDATION_VERIFIED",
        "phase_complete": False,
        "production_approved": False,
        "candidate_revision": revision,
        "candidate_sha256": candidate,
        "full_evidence_manifest": ref(root, manifest_path),
        "merged_pose_report": ref(root, merged_path),
        "production_evaluations": prod_refs,
        **inputs,
        "final_body_clothing_hashes": final_identity_from_raw_and_export(root, raw, export_receipt),
        "verifier": ref(root, root / HELPER),
        "production_evaluator": ref(root, root / EVALUATOR),
        "acceptance_spec": ref(root, root / ACCEPTANCE),
        "source_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "issues": [],
        "note": "Evidence-contract closure only. Does not complete Phase 9, prove runtime biomechanics, or approve production.",
    }
    issues = verify_receipt(root, receipt, candidate)
    if issues:
        receipt["contract_status"] = "PHASE9_VALIDATION_BLOCKED"
        receipt["issues"] = issues
    path = out / "PHASE9_VALIDATION_RECEIPT.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt, 0 if not issues else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--full-evidence-manifest", type=Path, required=True)
    ap.add_argument("--merged-pose-report", type=Path, required=True)
    ap.add_argument("--raw-pair", type=Path, required=True)
    ap.add_argument("--static-dressed", type=Path, required=True)
    ap.add_argument("--range-evidence", type=Path, required=True)
    ap.add_argument("--contact-bridge", type=Path, required=True)
    ap.add_argument("--bare-dressed-equivalence", type=Path, required=True)
    ap.add_argument("--export-evidence", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--verify-receipt", type=Path)
    args = ap.parse_args()
    try:
        if args.verify_receipt:
            _, data = load_json(ROOT, args.verify_receipt, "Phase 9 receipt")
            issues = verify_receipt(ROOT, data)
            print(json.dumps({"contract_status": "REFUSED" if issues else "PHASE9_VALIDATION_VERIFIED", "issues": issues, "production_approved": False}, indent=2))
            return 1 if issues else 0
        receipt, code = build(args)
        print(json.dumps({"contract_status": receipt["contract_status"], "candidate_revision": receipt["candidate_revision"], "issues": receipt["issues"], "production_approved": False}, indent=2))
        return code
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print("STOP — " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
