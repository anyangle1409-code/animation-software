import unittest
import json
from pathlib import Path

from validate_original_o1_source import validate_o1_source


RECORD = {
    'asset_id': 'HomeGymPT_Male_ORIGINAL_v1',
    'source_branch': 'work/standalone-first-party-audit-20260927',
    'clean_room': True, 'starting_geometry': 'blank', 'legacy_geometry_imported': False,
    'blend_sha256': 'a' * 64,
    'scaffold': {
        'vertex_count': 3890, 'triangle_count': 7280, 'bone_count': 53,
        'third_party_geometry_imported': False, 'legacy_projection_used': False,
        'profile_commit': 'e6ef05b4312a1928cc6fbb71b92a94ceaff1cc62',
        'profile_blob_sha': 'ee56a49bfb2e32530520fd1811ed9427460256bd',
        'historical_mesh_algorithm_blob_sha': '0216035a6574a0b753f8716f49e603967923f68f',
        'historical_clean_rig_commit': '287f72c6a6ac9b1dcd771946ef548d77a40b8ea1',
        'historical_clean_rig_blob_sha': '5c0182ae6db57e8de99547aa96d80216105a36ba',
    },
}


class O1SourceTests(unittest.TestCase):
    def test_committed_o1_provenance_fields(self):
        record = json.loads((Path(__file__).resolve().parents[1] / 'ORIGINAL_V1_WORK/ORIGINAL_V1_PROVENANCE.json').read_text())
        self.assertEqual(validate_o1_source(record, record['blend_sha256']), [])

    def test_accepts_exact_pinned_source(self):
        self.assertEqual(validate_o1_source(RECORD, 'a' * 64), [])

    def test_rejects_changed_blend_despite_matching_object_counts(self):
        self.assertIn('blend hash mismatch', validate_o1_source(RECORD, 'b' * 64))

    def test_rejects_legacy_projection_flag(self):
        record = {**RECORD, 'scaffold': {**RECORD['scaffold'], 'legacy_projection_used': True}}
        self.assertIn('legacy projection', validate_o1_source(record, 'a' * 64))

    def test_rejects_drift_from_pinned_pre_makehuman_sources(self):
        mutations = (
            ('profile_commit', 'b' * 40, 'profile commit'),
            ('profile_blob_sha', 'c' * 40, 'profile blob'),
            ('historical_mesh_algorithm_blob_sha', 'd' * 40, 'mesh algorithm blob'),
            ('historical_clean_rig_commit', 'e' * 40, 'clean rig commit'),
            ('historical_clean_rig_blob_sha', 'f' * 40, 'clean rig blob'),
        )
        for key, value, message in mutations:
            with self.subTest(key=key):
                record = {**RECORD, 'scaffold': {**RECORD['scaffold'], key: value}}
                self.assertIn(message, validate_o1_source(record, 'a' * 64))


if __name__ == '__main__':
    unittest.main()
