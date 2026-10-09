"""Regression checks for the read-only mesh-independent hand probe.

Runs in plain Python (NumPy only); it requires no Blender, body mesh, or
production geometry. It does not approve a candidate or create c005.
"""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))

import hand_input_source_rebuild_audit as prior  # noqa: E402
import mesh_independent_hand_probe as probe  # noqa: E402


def records():
    return {k: json.loads(path.read_text()) for k, path in prior.P.items()}


class MeshIndependentHandProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = probe.analyse()

    def test_reconstruction_is_diagnostic_only(self):
        r = self.report
        self.assertEqual(r['state'], 'DIAGNOSTIC_ONLY_NOT_CANONICAL_NO_C005')
        self.assertFalse(r['promotion_allowed'])
        self.assertFalse(r['mesh_geometry_used'])
        self.assertFalse(r['contain_applied'])
        self.assertTrue(r['skeleton_fit_build_used'])

    def test_exact_points_and_unresolved_fingertip_stations(self):
        r = self.report
        self.assertEqual(
            (r['points_checked'], r['exact_reconstruction_points'],
             r['inherited_pre_containment_tips']), (108, 98, 10))
        self.assertEqual(len(r['tip_offsets_mm']), 10)
        self.assertTrue(all(5.0 < x['difference_from_c004_mm'] < 10.0
                            for x in r['tip_offsets_mm']))
        self.assertEqual({p['side'] for p in r['tip_offsets_mm']},
                         {'left', 'right'})
        self.assertLess(r['maximum_source_offset_residual_mm'], 0.00001)
        for p in r['details']:
            if p['classification'] == 'UNIQUE_EXACT':
                self.assertLess(p['difference_from_c004_mm'], 0.00001)

    def test_both_gh_translations_are_recorded(self):
        self.assertAlmostEqual(self.report['gh_translation_mm']['left'],
                               38.432, places=2)
        self.assertAlmostEqual(self.report['gh_translation_mm']['right'],
                               38.432, places=2)

    def test_containment_is_never_invoked(self):
        real_rebuild = prior.rebuild
        seen = []
        def audit_rebuild(L, clearance):
            seen.append(clearance)
            self.assertIsNone(clearance)
            return real_rebuild(L, clearance)
        with patch.object(prior, 'rebuild', side_effect=audit_rebuild):
            probe.analyse()
        self.assertEqual(seen, [None])

    def test_records_are_unchanged(self):
        before = {k: hashlib.sha256(p.read_bytes()).hexdigest()
                  for k, p in prior.P.items()}
        probe.analyse()
        after = {k: hashlib.sha256(p.read_bytes()).hexdigest()
                 for k, p in prior.P.items()}
        self.assertEqual(before, after)

    def test_mutation_invalid_gh_translation_rejected(self):
        r = records()
        r['c004']['bones']['lunate_left']['head_m'][0] += 0.001
        with self.assertRaisesRegex(ValueError, 'not all a rigid GH'):
            probe.analyse(r)

    def test_mutation_stale_input_contract_rejected(self):
        r = records()
        r['c004']['skeleton_input']['sides']['left']['carpals']['lunate'][0][0] += 0.001
        with self.assertRaisesRegex(ValueError, 'not all stale'):
            probe.analyse(r)

    def test_report_output_is_create_only(self):
        script = ROOT / 'scripts/anatomy_fit/mesh_independent_hand_probe.py'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'result.json'
            first = subprocess.run([sys.executable, str(script), '--out', str(out)],
                                   check=False, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(out.read_text())['points_checked'], 108)
            old_bytes = out.read_bytes()
            second = subprocess.run([sys.executable, str(script), '--out', str(out)],
                                    check=False, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(old_bytes, out.read_bytes())


if __name__ == '__main__':
    unittest.main()
