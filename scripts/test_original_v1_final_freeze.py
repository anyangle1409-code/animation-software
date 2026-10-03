"""Phase 12 final freeze must bind every prerequisite and never self-approve."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_original_v1_final_freeze as f
import verify_original_v1_phase_exit as phase_exit
import verify_original_v1_production_promotion as promotion


class FinalFreezeTests(unittest.TestCase):
    def ref(self, root: Path, path: Path) -> dict:
        return {"path": path.relative_to(root).as_posix(), "sha256": f.digest(path)}

    def write(self, root: Path, name: str, data: dict) -> tuple[Path, dict]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path, self.ref(root, path)

    def fixture(self, root: Path):
        sha = "a" * 64
        runtime = "b" * 40
        model_commit = "c" * 40
        source_commit = "d" * 40

        assets = []
        for role in ("bare", "dressed"):
            path = root / f"{role}.glb"
            path.write_bytes((role + " fixture").encode())
            assets.append({
                "role": role,
                "path": path.name,
                "sha256": f.digest(path),
                "candidate_sha256": sha,
            })

        raw = root / "raw.txt"
        raw.write_text("synthetic unit-test evidence only", encoding="utf-8")
        raw_ref = self.ref(root, raw)

        gate_refs = {}
        for gate, checks in promotion.REQUIRED_GATES.items():
            report = {
                "gate_id": gate,
                "candidate_sha256": sha,
                "status": "PASS",
                "checks": [
                    {"id": check, "passed": True, "evidence": [raw_ref]}
                    for check in checks
                ],
                "command": "fixture command",
                "source_git_commit": source_commit,
                "evidence_timestamp": "2026-10-01T13:00:00+01:00",
                "source_evidence": [raw_ref],
                "assets": copy.deepcopy(assets),
            }
            if gate in ("runtime_animation", "standalone_release"):
                report["target_runtime_commit"] = runtime
            _path, gate_refs[gate] = self.write(root, f"gates/{gate}.json", report)

        owner = {
            "decision": "OWNER ACCEPTED",
            "actor": "owner",
            "candidate_sha256": sha,
            "decision_source": "synthetic unit-test owner decision",
            "evidence_timestamp": "2026-10-01T13:00:00+01:00",
            "assets": copy.deepcopy(assets),
        }
        _owner_path, owner_ref = self.write(root, "owner_acceptance.json", owner)

        promo = {
            "schema_version": 1,
            "status": "FINAL",
            "production_approved": False,
            "candidate_sha256": sha,
            "target_runtime_commit": runtime,
            "assets": copy.deepcopy(assets),
            "gates": gate_refs,
            "owner_acceptance": owner_ref,
        }
        promo_path, promo_ref = self.write(root, "promotion_packet.json", promo)

        receipt = {
            "schema_version": 1,
            "eligibility": "ALL_REQUIRED_GATES_SATISFIED",
            "production_approved": False,
            "issues": [],
            "promotion_packet": promo_ref,
            "candidate_sha256": sha,
            "target_runtime_commit": runtime,
        }
        receipt_path, receipt_ref = self.write(root, "promotion_receipt.json", receipt)

        # Synthetic but contract-real Phase 4->5 lineage used by the final-freeze verifier.
        # This keeps the unit test aligned with the production Phase 5 ordered receipt rule.
        phase5_plan_path, phase5_plan_ref = self.write(
            root, "ORIGINAL_V1_PHASE5_ANATOMY_EXECUTION_PLAN.json",
            {"schema_version": 1, "fixture": "final-freeze ordered anatomy chain"},
        )
        (root / "ORIGINAL_V1_PRODUCTION_CONTROL.json").write_text(json.dumps({
            "phase_completion_records": {"4": {"candidate_sha256": sha}}
        }), encoding="utf-8")
        phase5_receipts = {}
        previous_region_receipt_ref = None
        for check_id, region in phase_exit.PHASE5_REGION_CHECKS:
            region_report = {
                "schema_version": 1,
                "phase": 5,
                "region": region,
                "status": "REGION_EVIDENCE_COMPLETE",
                "phase_complete": False,
                "production_approved": False,
                "candidate_sha256": sha,
                "parent_candidate_sha256": sha,
                "development_freeze_candidate_sha256": sha,
                "active_epoch_baseline_revision": "P3B1",
                "active_epoch_baseline_candidate_sha256": "9" * 64,
                "previous_region_receipt": copy.deepcopy(previous_region_receipt_ref),
            }
            region_report_path, region_report_ref = self.write(
                root, f"phase5/{region}_report.json", region_report
            )
            receipt = {
                "schema_version": 1,
                "phase": 5,
                "region": region,
                "contract_status": "REGION_EVIDENCE_VERIFIED",
                "phase_complete": False,
                "production_approved": False,
                "issues": [],
                "candidate_sha256": sha,
                "region_report": region_report_ref,
                "plan": phase5_plan_ref,
                "source_git_commit": source_commit,
            }
            region_receipt_path, region_receipt_ref = self.write(
                root, f"phase5/{region}_receipt.json", receipt
            )
            phase5_receipts[check_id] = region_receipt_ref
            previous_region_receipt_ref = region_receipt_ref

        phase_refs = {}
        for phase in f.PHASES:
            report = {
                "schema_version": 1,
                "phase": int(phase),
                "candidate_sha256": sha,
                "status": "PASS",
                "production_approved": False,
                "source_git_commit": model_commit if phase == "9" else source_commit,
                "evidence_timestamp": "2026-10-01T13:00:00+01:00",
                "command": "fixture phase command",
                "owner_review": "accepted" if phase == "11" else "pending",
                "blocking": False,
                "checks": [
                    {
                        "id": check,
                        "passed": True,
                        "evidence": [phase5_receipts[check]]
                            if phase == "5" and check in phase5_receipts
                            else [raw_ref],
                    }
                    for check in phase_exit.REQUIRED_CHECKS[phase]
                ],
            }
            if phase in ("10", "11"):
                report["target_runtime_commit"] = runtime
            _path, phase_refs[phase] = self.write(root, f"phases/phase_{phase}.json", report)

        authorization = {
            "decision": "OWNER AUTHORISED PRODUCTION FREEZE",
            "actor": "owner",
            "candidate_sha256": sha,
            "target_runtime_commit": runtime,
            "production_approved": False,
            "decision_source": "synthetic unit-test freeze authorization",
            "evidence_timestamp": "2026-10-01T13:05:00+01:00",
            "assets": copy.deepcopy(assets),
            "promotion_packet": promo_ref,
            "promotion_receipt": receipt_ref,
        }
        _auth_path, auth_ref = self.write(root, "freeze_authorization.json", authorization)

        packet = {
            "schema_version": 1,
            "status": "FINAL_FREEZE_PACKET",
            "production_approved": False,
            "candidate_sha256": sha,
            "model_source_commit": model_commit,
            "target_runtime_commit": runtime,
            "assets": copy.deepcopy(assets),
            "promotion_packet": promo_ref,
            "promotion_receipt": receipt_ref,
            "phase_exit_reports": phase_refs,
            "freeze_authorization": auth_ref,
        }
        state = {
            "last_known_candidate_sha256": sha,
            "candidate_state": "accepted",
            "development_failure_count": 0,
            "unresolved_regressions": [],
            "incomplete_candidates": [],
            "phases": {str(n): {"state": "complete"} for n in range(13)},
            "latest_evidence": [{"path": "fixture_merged_pose_report.json"}],
        }
        return packet, state

    def verify(self, root, packet, state):
        with patch.object(f, "build", return_value=(state, None)), patch.object(
            f, "evaluate", return_value={"failure_count": 0}
        ):
            return f.verify_final_freeze(root, packet)

    def test_valid_fixture_satisfies_contract_without_approving(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet, state = self.fixture(root)
            self.assertEqual(self.verify(root, packet, state), [])
            self.assertFalse(packet["production_approved"])

    def test_promotion_receipt_must_bind_exact_packet(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet, state = self.fixture(root)
            receipt_path = root / packet["promotion_receipt"]["path"]
            receipt = json.loads(receipt_path.read_text())
            receipt["promotion_packet"]["sha256"] = "e" * 64
            receipt_path.write_text(json.dumps(receipt))
            packet["promotion_receipt"]["sha256"] = f.digest(receipt_path)
            issues = self.verify(root, packet, state)
            self.assertTrue(any("exact promotion packet" in x for x in issues))

    def test_phase_10_runtime_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet, state = self.fixture(root)
            ref = packet["phase_exit_reports"]["10"]
            path = root / ref["path"]
            report = json.loads(path.read_text())
            report["target_runtime_commit"] = "e" * 40
            path.write_text(json.dumps(report))
            ref["sha256"] = f.digest(path)
            issues = self.verify(root, packet, state)
            self.assertTrue(any("Phase 10" in x and "runtime" in x for x in issues))

    def test_phase_9_model_commit_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet, state = self.fixture(root)
            packet["model_source_commit"] = "e" * 40
            issues = self.verify(root, packet, state)
            self.assertTrue(any("Phase 9" in x and "model source commit" in x for x in issues))

    def test_pending_freeze_authorization_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet, state = self.fixture(root)
            ref = packet["freeze_authorization"]
            path = root / ref["path"]
            auth = json.loads(path.read_text())
            auth["decision"] = "pending"
            path.write_text(json.dumps(auth))
            ref["sha256"] = f.digest(path)
            issues = self.verify(root, packet, state)
            self.assertTrue(any("OWNER AUTHORISED PRODUCTION FREEZE" in x for x in issues))

    def test_asset_byte_change_invalidates_all_bindings(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet, state = self.fixture(root)
            (root / "bare.glb").write_bytes(b"changed")
            issues = self.verify(root, packet, state)
            self.assertTrue(any("assets" in x for x in issues))

    def test_current_phase_incomplete_refuses_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            packet, state = self.fixture(root)
            state["phases"]["11"]["state"] = "not_started"
            issues = self.verify(root, packet, state)
            self.assertIn("Phase 11 is incomplete", issues)

    def test_template_is_incomplete_and_pending(self):
        state = {
            "last_known_candidate_sha256": "a" * 64,
            "current_candidate": "r29",
            "candidate_state": "experimental",
            "development_failure_count": 7,
            "production_failure_count": 109,
            "phases": {"12": {"state": "not_started"}},
        }
        template = f.make_template(state)
        self.assertEqual(template["status"], "INCOMPLETE")
        self.assertFalse(template["production_approved"])
        self.assertEqual(template["freeze_authorization_template"]["decision"], "pending")
        self.assertEqual(set(template["phase_exit_reports"]), set(f.PHASES))


if __name__ == "__main__":
    unittest.main()
