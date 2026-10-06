"""Tests for the candidate-bound whole-body deformation audit gate."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

import original_v1_whole_body_audit_gate as gate


CATEGORIES = [
    "trunk_flexion","trunk_extension","trunk_rotation","lateral_flexion","anti_rotation",
    "hip_hinge","deep_squat","unilateral_lunge","ankle_calf","horizontal_push","vertical_push",
    "vertical_pull","shoulder_raise","elbow_flexion","elbow_extension","forearm_rotation",
    "wrist_floor_load","hand_grip","thumb_opposition",
]
TEMPORAL = [
    "start","outbound_intermediate","peak_or_bottom",
    "return_intermediate","end_or_loop_close","turnaround_neighbourhood",
]


class WholeBodyAuditGateTests(unittest.TestCase):
    def fixture(self, root: Path):
        visual = root / "visual.png"
        numeric = root / "numeric.json"
        reproduction = root / "repro.png"
        visual.write_text("visual")
        numeric.write_text("{}")
        reproduction.write_text("repro")
        ref_visual = {"path":"visual.png","sha256":gate.digest(visual),"passed":True}
        ref_numeric = {"path":"numeric.json","sha256":gate.digest(numeric),"passed":True}

        entries = []
        for index, category in enumerate(CATEGORIES, 1):
            entries.append({
                "id":f"HE-CAT-{index:03d}",
                "region":"fixture",
                "movement_primitive":category,
                "source_type":"primary_study",
                "source":{"url":"https://example.org/"+category,"citation":"Fixture citation","license_use_note":"Development-only fixture."},
                "movement_phase":"fixture_phase",
                "view":["fixture_view"],
                "diversity":{"subject_count":10,"notes":"Fixture cohort."},
                "observable_landmarks":["fixture_landmark"],
                "permissible_conclusions":["movement_timing"],
                "uncertainty":"Fixture uncertainty.",
                "development_only":True,
                "review_status":"verified",
            })
        # The manifest validator also requires real visual-source coverage for the
        # three shoulder primitives, independent of the 19 audit categories.
        for offset, primitive in enumerate(gate.validate_manifest.__globals__["REQUIRED_VISUAL_PRIMITIVES"], 100):
            entries.append({
                "id":f"HE-VIS-{offset:03d}",
                "region":"shoulder_fixture",
                "movement_primitive":primitive,
                "source_type":"supplementary_video",
                "source":{"url":"https://example.org/"+primitive,"citation":"Fixture visual","license_use_note":"Development-only fixture."},
                "movement_phase":"fixture_phase",
                "view":["fixture_view"],
                "diversity":{"subject_count":10,"notes":"Fixture cohort."},
                "observable_landmarks":["fixture_landmark"],
                "permissible_conclusions":["surface_contour"],
                "uncertainty":"Fixture uncertainty.",
                "development_only":True,
                "review_status":"verified",
            })
        manifest={"schema_version":1,"asset":"HomeGymPT_Male_ORIGINAL_v1","entries":entries}
        (root/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json").write_text(json.dumps(manifest))

        envelope={
            "schema_version":1,
            "character_target":"HomeGymPT_Male_ORIGINAL_v1",
            "required_categories":[{"id":category} for category in CATEGORIES],
        }
        coverage={
            "schema_version":1,
            "asset":"HomeGymPT_Male_ORIGINAL_v1",
            "production_approved":False,
            "categories":[
                {"id":category,"evidence_ids":[f"HE-CAT-{i:03d}"],"status":"COVERED_WITH_LIMITATIONS","notes":"Fixture coverage."}
                for i,category in enumerate(CATEGORIES,1)
            ],
        }

        zones=[]
        for i in range(1,17):
            zone_categories=CATEGORIES if i==1 else [CATEGORIES[(i-1)%len(CATEGORIES)]]
            zones.append({
                "id":f"WBZ-{i:02d}",
                "name":f"fixture_zone_{i}",
                "structures":["fixture_structure"],
                "movement_categories":zone_categories,
                "checks":["fixture_check"],
            })
        plan={
            "schema_version":1,
            "status":"PREPARED_WHOLE_BODY_DEFORMATION_AUDIT_PLAN",
            "asset":"HomeGymPT_Male_ORIGINAL_v1",
            "production_approved":False,
            "movement_categories_required":list(CATEGORIES),
            "transition_zones":zones,
            "temporal_sampling":{"required_classes":list(TEMPORAL)},
        }

        # A Medium issue proves the ledger schema without blocking the candidate.
        ledger={
            "schema_version":1,
            "asset":"HomeGymPT_Male_ORIGINAL_v1",
            "issues":[{
                "id":"WB-FIX-001",
                "region":"fixture",
                "severity":"Medium",
                "state":"Open",
                "candidate":{"revision":"r99","sha256":"a"*64},
                "reproduction":{"poses":["fixture"],"views":["fixture"],"description":"Fixture reproduction."},
                "evidence_paths":["repro.png"],
                "human_evidence_ids":["HE-CAT-001"],
                "evidence_gap":None,
                "defect":"Fixture defect.",
                "acceptance":"Fixture acceptance.",
                "closure_evidence":[],
            }],
        }

        zone_rows=[]
        for zone in zones:
            ids=[]
            for category in zone["movement_categories"]:
                index=CATEGORIES.index(category)+1
                ids.append(f"HE-CAT-{index:03d}")
            zone_rows.append({
                "id":zone["id"],
                "status":"PASS",
                "candidate_sha256":"a"*64,
                "temporal_classes":list(TEMPORAL),
                "visual_evidence":[copy.deepcopy(ref_visual)],
                "numerical_evidence":[copy.deepcopy(ref_numeric)],
                "human_evidence_ids":ids,
                "review_note":"Fixture zone explicitly reviewed.",
            })
        movement_rows=[]
        for i,category in enumerate(CATEGORIES,1):
            movement_rows.append({
                "id":category,
                "status":"PASS",
                "transition_zone_ids":["WBZ-01"],
                "human_evidence_ids":[f"HE-CAT-{i:03d}"],
                "review_note":"Fixture movement explicitly reviewed.",
            })
        record={
            "schema_version":1,
            "status":gate.STATUS,
            "production_approved":False,
            "candidate_revision":"r99",
            "candidate_sha256":"a"*64,
            "source_git_commit":"b"*40,
            "production_path_rendered":True,
            "whole_body_regression_pass":True,
            "transition_zones":zone_rows,
            "movement_categories":movement_rows,
        }
        return record,plan,envelope,manifest,coverage,ledger

    def verify(self, root, record, plan, envelope, manifest, coverage, ledger):
        return gate.verify_audit(
            root,record,plan,envelope,manifest,coverage,ledger,
            expected_revision="r99",expected_candidate_sha256="a"*64,
        )

    def test_complete_fixture_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            values=self.fixture(root)
            self.assertEqual(self.verify(root,*values),[])

    def test_open_critical_issue_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            record,plan,envelope,manifest,coverage,ledger=self.fixture(root)
            ledger["issues"][0]["severity"]="Critical"
            errors="\n".join(self.verify(root,record,plan,envelope,manifest,coverage,ledger))
            self.assertIn("Critical/High whole-body anatomy blockers remain",errors)

    def test_missing_temporal_class_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            record,plan,envelope,manifest,coverage,ledger=self.fixture(root)
            record["transition_zones"][0]["temporal_classes"].remove("turnaround_neighbourhood")
            errors="\n".join(self.verify(root,record,plan,envelope,manifest,coverage,ledger))
            self.assertIn("WBZ-01: temporal coverage incomplete",errors)

    def test_tampered_visual_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            record,plan,envelope,manifest,coverage,ledger=self.fixture(root)
            (root/"visual.png").write_text("tampered")
            errors="\n".join(self.verify(root,record,plan,envelope,manifest,coverage,ledger))
            self.assertIn("evidence hash differs",errors)

    def test_plan_cannot_shrink_to_skip_regions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            record,plan,envelope,manifest,coverage,ledger=self.fixture(root)
            plan["transition_zones"].pop()
            record["transition_zones"].pop()
            errors="\n".join(self.verify(root,record,plan,envelope,manifest,coverage,ledger))
            self.assertIn("WBZ-01..WBZ-16",errors)

    def test_movement_row_must_bind_declared_human_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            record,plan,envelope,manifest,coverage,ledger=self.fixture(root)
            record["movement_categories"][0]["human_evidence_ids"]=["HE-CAT-002"]
            errors="\n".join(self.verify(root,record,plan,envelope,manifest,coverage,ledger))
            self.assertIn("movement row does not bind declared evidence coverage",errors)


if __name__=="__main__":
    unittest.main()
