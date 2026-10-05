"""Fail-closed tests for real-human deformation evidence."""
import copy
import json
from pathlib import Path
import tempfile
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
            row=self.valid_entry(); row['id']=f'HE-TEST-{index:03d}'; row['movement_primitive']=primitive
            entries.append(row)
        return {"schema_version":1,"asset":"HomeGymPT_Male_ORIGINAL_v1","entries":entries}

    def test_live_manifest_is_valid(self):
        manifest=json.loads((ROOT/'ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence.validate_manifest(manifest), [])

    def test_missing_url_or_capture_id_is_rejected(self):
        manifest=self.valid_manifest(); manifest['entries'][0]['source'].pop('url')
        self.assertIn('source requires URL or capture_id', '\n'.join(evidence.validate_manifest(manifest)))

    def test_missing_license_use_note_is_rejected(self):
        manifest=self.valid_manifest(); manifest['entries'][0]['source'].pop('license_use_note')
        self.assertIn('license_use_note', '\n'.join(evidence.validate_manifest(manifest)))

    def test_missing_movement_phase_is_rejected(self):
        manifest=self.valid_manifest(); manifest['entries'][0]['movement_phase']=''
        self.assertIn('movement_phase', '\n'.join(evidence.validate_manifest(manifest)))

    def test_empty_diversity_notes_are_rejected(self):
        manifest=self.valid_manifest(); manifest['entries'][0]['diversity']['notes']=''
        self.assertIn('diversity.notes', '\n'.join(evidence.validate_manifest(manifest)))

    def test_unsupported_conclusion_is_rejected(self):
        manifest=self.valid_manifest(); manifest['entries'][0]['permissible_conclusions']=['invent_missing_muscle']
        self.assertIn('unsupported permissible conclusion', '\n'.join(evidence.validate_manifest(manifest)))

    def test_extended_joint_kinematics_conclusion_is_allowed(self):
        manifest=self.valid_manifest(); manifest['entries'][0]['permissible_conclusions']=['joint_kinematics','interjoint_coordination']
        self.assertNotIn('unsupported permissible conclusion', '\n'.join(evidence.validate_manifest(manifest)))

    def test_movement_primitive_without_visual_source_is_rejected(self):
        manifest=self.valid_manifest()
        for row in manifest['entries']:
            if row['movement_primitive']=='shoulder_axial_rotation': row['source_type']='primary_study'
        self.assertIn('no visual source for required movement primitive shoulder_axial_rotation',
                      '\n'.join(evidence.validate_manifest(manifest)))

    def test_duplicate_ids_and_non_development_use_are_rejected(self):
        manifest=self.valid_manifest(); manifest['entries'][1]['id']=manifest['entries'][0]['id']
        manifest['entries'][0]['development_only']=False
        errors='\n'.join(evidence.validate_manifest(manifest))
        self.assertIn('duplicate evidence id', errors)
        self.assertIn('development_only must be true', errors)


if __name__ == '__main__':
    unittest.main()
