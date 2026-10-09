"""Bone-by-bone audit, defect register and diagnostic proposal P001: committed results pinned and the detectors/builders
proven by mutation. Nothing here is acceptance."""
import copy, json, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import bone_by_bone_audit as bba  # noqa: E402
import build_proposal_p001_metacarpals as p001  # noqa: E402

A = ROOT / 'ORIGINAL_V1_WORK/anatomy'
R = A / 'audit/claude_independent_review_20261009'
C4 = json.loads((A / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json').read_text())
P1 = json.loads((A / 'audit/proposals/p001_metacarpal_m2_m4/proposal_record.json').read_text())


class BoneAudit(unittest.TestCase):
    def test_committed(self):
        d = json.loads((R / 'bone_by_bone_audit_v1.json').read_text())
        for lab in ('a003', 'c004'):
            B = d['records'][lab]['bones']
            self.assertEqual(len(B), 206)
            self.assertNotIn('UNCLASSIFIED', {v['representation'] for v in B.values()})
            self.assertTrue(all(v.get('mirror_max_mm', 0) < 0.5 for v in B.values()))
        self.assertTrue(d['records']['a003']['bones']['clavicle_left']['corridor']['outside_observed_range'])
        self.assertFalse(d['records']['c004']['bones']['clavicle_left']['corridor']['outside_observed_range'])

    def test_detached_bone_detected(self):
        rec = copy.deepcopy(C4)
        for e in ('head_m', 'tail_m'):
            rec['bones']['radius_left'][e] = (np.asarray(rec['bones']['radius_left'][e]) + [0, 0, -0.02]).tolist()
        rows = bba.audit(rec, bba.corridors())
        self.assertGreater(rows['radius_left']['joint_to_own_stick_mm'], 19)
        self.assertGreater(rows['radius_left']['mirror_max_mm'], 19)

    def test_corridor_z(self):
        rows = bba.audit(C4, bba.corridors())
        self.assertAlmostEqual(rows['metacarpal_3_left']['corridor']['z'], -2.5, delta=0.02)


class Register(unittest.TestCase):
    def test_entries(self):
        d = json.loads((R / 'skeleton_defect_register_v1.json').read_text())
        classes = {'GEOMETRY_DEFECT', 'JOINT_COORDINATE_DEFECT', 'STRUCTURAL_INVARIANT_FAIL', 'MOVEMENT_TEST_DESIGN', 'MOVEMENT_MODEL_GAP',
                   'REPRESENTATION_LIMIT', 'EVIDENCE_GAP', 'NOT_A_DEFECT'}
        status = {'CORRECTED_IN_CANDIDATE', 'DIAGNOSTIC_PROPOSAL', 'OPEN', 'BLOCKED', 'NONE'}
        E = {e['id']: e for e in d['entries']}
        self.assertTrue(all(e['cls'] in classes and e['status'] in status and e['evidence'] for e in E.values()))
        self.assertNotIn('ACCEPTED', json.dumps(d))
        self.assertEqual(E['U5']['cls'], 'STRUCTURAL_INVARIANT_FAIL')
        self.assertEqual(E['H7']['measured'], {'c003_radiocarpal_opening_mm': 16.687, 'c004_radiocarpal_opening_mm': 0.0})
        self.assertAlmostEqual(E['H3']['measured']['trapezium_tail_to_MC1_base_mm'], 10.61, places=2)
        self.assertEqual(E['L5']['measured']['calcaneocuboid_to_cuboid_mm'], 33.5)


class P001(unittest.TestCase):
    def test_builder_reproduces(self):
        out, table = p001.build()
        self.assertEqual(json.loads(json.dumps(out, default=float)), P1)
        self.assertEqual(len(table), 6)

    def test_only_intended_change(self):
        moved = {f'metacarpal_{d}_{s}' for d in (2, 3, 4) for s in ('left', 'right')} | \
                {f'digit{d}_{p}_phalanx_{s}' for d in (2, 3, 4) for p in ('proximal', 'middle', 'distal') for s in ('left', 'right')}
        for n, b in C4['bones'].items():
            if n not in moved:
                self.assertEqual(b, P1['bones'][n], n)
        for d in (2, 3, 4):
            mc0, mc1 = C4['bones'][f'metacarpal_{d}_left'], P1['bones'][f'metacarpal_{d}_left']
            self.assertEqual(mc0['head_m'], mc1['head_m'])                                    # CMC end fixed
            L = np.linalg.norm(np.subtract(mc1['tail_m'], mc1['head_m'])) * 1000
            self.assertAlmostEqual(L, p001.TARGET_MM[d], places=6)
            u0 = np.subtract(mc0['tail_m'], mc0['head_m']); u1 = np.subtract(mc1['tail_m'], mc1['head_m'])
            self.assertAlmostEqual(float(u0 @ u1 / np.linalg.norm(u0) / np.linalg.norm(u1)), 1.0, places=12)   # same axis
            # seam preserved exactly as in c004 (whose float32-stored seam is ~6e-8 m); within the float32 storage bound 1e-6 m
            seam1 = np.subtract(P1['bones'][f'digit{d}_proximal_phalanx_left']['head_m'], mc1['tail_m'])
            seam0 = np.subtract(C4['bones'][f'digit{d}_proximal_phalanx_left']['head_m'], mc0['tail_m'])
            np.testing.assert_allclose(seam1, seam0, rtol=0, atol=1e-12); self.assertLess(np.abs(seam1).max(), 1e-6)
        for k, m in C4['joint_markers'].items():
            if not any(k.startswith(f'digit{d}_') for d in (2, 3, 4)):
                self.assertEqual(m, P1['joint_markers'][k], k)
        self.assertEqual(P1['candidate']['status'], 'DIAGNOSTIC_PROPOSAL_NOT_A_CANDIDATE_NOT_CANONICAL')
        self.assertFalse(P1['candidate']['freeze_ready'])


if __name__ == '__main__':
    unittest.main()
