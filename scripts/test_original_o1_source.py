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


if __name__ == '__main__':
    unittest.main()
