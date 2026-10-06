"""Fail-closed tests for real-human deformation evidence and movement coverage."""
import copy
import json
from pathlib import Path
import unittest

import validate_original_v1_human_evidence as evidence

ROOT = Path(__file__).resolve().parents[1]


class HumanEvidenceTests(unittest.TestCase):
    def valid_entry(self):
        return {
            "id": "HE-TEST-001",
            "region": "shoulder_axilla",
            "movement_primitive": "shoulder_flexion",
            "source_type": "supplementary_video",
            "source": {
                "url": "https://example.org/study",
                "citation": "Test study",
                "license_use_note": "Development reference only; do not redistribute media."
            },
            "movement_phase": "raising_rest_to_maximum",
            "view": ["front", "three_quarter"],
            "diversity": {"subject_count": 12, "notes": "Mixed-sex healthy-adult cohort."},
            "observable_landmarks": ["anterior axillary fold", "acromion"],
            "permissible_conclusions": ["surface_contour", "movement_timing"],
            "uncertainty": "Clothing and sensor straps partly obscure the skin surface.",
            "development_only": True,
            "review_status": "verified"
        }

    def valid_manifest(self):
        entries=[]
        for index, primitive in enumerate(evidence.REQUIRED_VISUAL_PRIMITIVES, 1):
            row=self.valid_entry(); row["id"]=f"HE-TEST-{index:03d}"; row["movement_primitive"]=primitive
            entries.append(row)
        return {"schema_version":1,"asset":"HomeGymPT_Male_ORIGINAL_v1","entries":entries}

    def coverage_fixture(self):
        manifest=self.valid_manifest()
        envelope={"schema_version":1,"character_target":"HomeGymPT_Male_ORIGINAL_v1",
                  "required_categories":[{"id":"vertical_push"},{"id":"hand_grip"}]}
        coverage={
            "schema_version":1,
            "asset":"HomeGymPT_Male_ORIGINAL_v1",
            "production_approved":False,
            "categories":[
                {"id":"vertical_push","evidence_ids":["HE-TEST-001"],"status":"COVERED_WITH_LIMITATIONS","notes":"Fixture coverage."},
                {"id":"hand_grip","evidence_ids":["HE-TEST-002"],"status":"COVERED_WITH_LIMITATIONS","notes":"Fixture coverage."},
            ],
        }
        return manifest,envelope,coverage

    def test_live_manifest_is_valid(self):
        manifest=json.loads((ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence.validate_manifest(manifest), [])

    def test_live_movement_envelope_is_fully_covered(self):
        manifest=json.loads((ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
        envelope=json.loads((ROOT/"ORIGINAL_V1_MOVEMENT_ENVELOPE.json").read_text(encoding="utf-8"))
        coverage=json.loads((ROOT/"ORIGINAL_V1_HUMAN_EVIDENCE_COVERAGE.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence.validate_coverage(coverage,manifest,envelope), [])

    def test_missing_url_or_capture_id_is_rejected(self):
        manifest=self.valid_manifest(); manifest["entries"][0]["source"].pop("url")
        self.assertIn("source requires URL or capture_id", "\n".join(evidence.validate_manifest(manifest)))

    def test_missing_license_use_note_is_rejected(self):
        manifest=self.valid_manifest(); manifest["entries"][0]["source"].pop("license_use_note")
        self.assertIn("license_use_note", "\n".join(evidence.validate_manifest(manifest)))

    def test_missing_movement_phase_is_rejected(self):
        manifest=self.valid_manifest(); manifest["entries"][0]["movement_phase"]=""
        self.assertIn("movement_phase", "\n".join(evidence.validate_manifest(manifest)))

    def test_empty_diversity_notes_are_rejected(self):
        manifest=self.valid_manifest(); manifest["entries"][0]["diversity"]["notes"]=""
        self.assertIn("diversity.notes", "\n".join(evidence.validate_manifest(manifest)))

    def test_invalid_subject_count_is_rejected(self):
        manifest=self.valid_manifest(); manifest["entries"][0]["diversity"]["subject_count"]=0
        self.assertIn("subject_count", "\n".join(evidence.validate_manifest(manifest)))

    def test_unsupported_conclusion_is_rejected(self):
        manifest=self.valid_manifest(); manifest["entries"][0]["permissible_conclusions"]=["invent_missing_muscle"]
        self.assertIn("unsupported permissible conclusion", "\n".join(evidence.validate_manifest(manifest)))

    def test_movement_primitive_without_visual_source_is_rejected(self):
        manifest=self.valid_manifest()
        for row in manifest["entries"]:
            if row["movement_primitive"]=="shoulder_axial_rotation": row["source_type"]="primary_study"
        self.assertIn("no visual source for required movement primitive shoulder_axial_rotation",
                      "\n".join(evidence.validate_manifest(manifest)))

    def test_duplicate_ids_and_non_development_use_are_rejected(self):
        manifest=self.valid_manifest(); manifest["entries"][1]["id"]=manifest["entries"][0]["id"]
        manifest["entries"][0]["development_only"]=False
        errors="\n".join(evidence.validate_manifest(manifest))
        self.assertIn("duplicate evidence id", errors)
        self.assertIn("development_only must be true", errors)

    def test_coverage_rejects_missing_movement_category(self):
        manifest,envelope,coverage=self.coverage_fixture()
        coverage["categories"].pop()
        errors=evidence.validate_coverage(coverage,manifest,envelope)
        self.assertTrue(any("movement categories without evidence coverage" in x for x in errors))

    def test_coverage_rejects_unknown_or_unverified_evidence(self):
        manifest,envelope,coverage=self.coverage_fixture()
        coverage["categories"][0]["evidence_ids"]=["HE-NOT-REAL"]
        manifest["entries"][1]["review_status"]="needs_review"
        errors="\n".join(evidence.validate_coverage(coverage,manifest,envelope))
        self.assertIn("unknown evidence id HE-NOT-REAL",errors)
        self.assertIn("evidence not verified HE-TEST-002",errors)

    def test_coverage_rejects_duplicate_or_extra_category(self):
        manifest,envelope,coverage=self.coverage_fixture()
        coverage["categories"].append(copy.deepcopy(coverage["categories"][0]))
        coverage["categories"].append({
            "id":"not_in_envelope","evidence_ids":["HE-TEST-003"],
            "status":"COVERED","notes":"Fixture extra."
        })
        errors="\n".join(evidence.validate_coverage(coverage,manifest,envelope))
        self.assertIn("duplicate coverage category",errors)
        self.assertIn("category is not in movement envelope",errors)

    def test_coverage_never_claims_production_approval(self):
        manifest,envelope,coverage=self.coverage_fixture()
        coverage["production_approved"]=True
        self.assertIn("coverage must not claim production approval",
                      evidence.validate_coverage(coverage,manifest,envelope))


if __name__ == "__main__":
    unittest.main()
