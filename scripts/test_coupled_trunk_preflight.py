"""Regression checks for numerical coupling: no new anatomical candidate is created."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'anatomy_fit'))
import coupled_trunk_preflight as pre

ANAT = HERE.parent / 'ORIGINAL_V1_WORK/anatomy'
C004 = ANAT / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json'
P003 = ANAT / 'audit/proposals/p003_spine_disc_repartition_rejected/proposal_record.json'


def fixture():
    bones = {}
    for i, bone in enumerate(pre.SPINE):
        z = 1.0 + 0.04 * i
        bones[bone] = {'head_m': [0, 0, z], 'tail_m': [0, 0, z + 0.03]}
    for i in range(1, 13):
        z = pre._rib_level(bones, i)
        for side in ('left', 'right'):
            x = 0.08 if side == 'left' else -0.08
            bones[f'rib_{i:02d}_{side}'] = {
                'head_m': [x, 0.1, z], 'tail_m': [x, -0.1, z - 0.02]}
    bones['sacrum'] = {'head_m': [0, 0, 0.96], 'tail_m': [0, 0, 0.92]}
    bones['sternum'] = {'head_m': [0, -0.08, 1.7], 'tail_m': [0, -0.08, 1.55]}
    for side in ('left', 'right'):
        x = 0.06 if side == 'left' else -0.06
        bones[f'clavicle_{side}'] = {
            'head_m': [x, -0.08, 1.75], 'tail_m': [x * 2, -0.08, 1.75]}
    return {'schema_version': 1, 'bones': bones}


def shifted(base, *, include_ribs=True, include_sternum=True, shift=0.025):
    other = copy.deepcopy(base)
    targets = set(pre.SPINE)
    if include_ribs:
        targets.update(pre.RIBS)
    if include_sternum:
        targets.add('sternum')
    for bid in targets:
        for end in ('head_m', 'tail_m'):
            other['bones'][bid][end][2] -= shift
    return other


class SyntheticCoupling(unittest.TestCase):
    def test_coupled_translation_is_coherent_but_never_anatomically_approved(self):
        base = fixture()
        before = json.dumps(base, sort_keys=True)
        candidate = shifted(base)
        r = pre.examine(base, candidate)
        self.assertEqual(r['status'], 'NO_MECHANICAL_BLOCKER_ANATOMY_UNVERIFIED')
        self.assertEqual(r['blockers'], [])
        self.assertFalse(r['safe_for_canonical_promotion'])
        self.assertTrue(r['shoulder_anchor_follow_up_required'])
        self.assertEqual(json.dumps(base, sort_keys=True), before)

    def test_spine_only_translation_rejects_ribs_and_sternum(self):
        r = pre.examine(fixture(), shifted(fixture(), include_ribs=False, include_sternum=False))
        self.assertIn('RIB_ARTICULAR_LEVEL_Z_REGRESSION', r['blockers'])
        self.assertIn('RIBS_NOT_COUPLED_TO_THORAX', r['blockers'])
        self.assertIn('STERNUM_NOT_COUPLED_TO_THORAX', r['blockers'])

    def test_moving_ribs_but_not_sternum_rejected(self):
        r = pre.examine(fixture(), shifted(fixture(), include_ribs=True, include_sternum=False))
        self.assertIn('STERNUM_NOT_COUPLED_TO_THORAX', r['blockers'])
        self.assertNotIn('RIBS_NOT_COUPLED_TO_THORAX', r['blockers'])

    def test_disc_overlap_regression_rejected(self):
        a = fixture()
        b = copy.deepcopy(a)
        b['bones']['l4']['head_m'] = copy.deepcopy(b['bones']['l5']['tail_m'])
        r = pre.examine(a, b)
        self.assertIn('INTERVERTEBRAL_DISC_CLEARANCE_INSUFFICIENT', r['blockers'])

    def test_oversized_disc_rejected(self):
        a = fixture()
        b = shifted(a)
        b['bones']['l4']['head_m'][2] += 0.024
        r = pre.examine(a, b)
        self.assertIn('INTERVERTEBRAL_DISC_CLEARANCE_OVERSIZE', r['blockers'])

    def test_unmodified_baseline_is_not_considered_a_rebuild(self):
        a = fixture()
        r = pre.examine(a, a)
        self.assertIn('NO_SPINE_RECONSTRUCTION', r['blockers'])
        self.assertFalse(r['safe_for_canonical_promotion'])

    def test_missing_rib_fails_closed(self):
        a = fixture()
        b = copy.deepcopy(a)
        del b['bones']['rib_12_left']
        with self.assertRaisesRegex(ValueError, 'exactly the same bone inventory'):
            pre.examine(a, b)

    def test_non_finite_bone_rejected(self):
        a = fixture()
        b = copy.deepcopy(a)
        b['bones']['t3']['tail_m'][0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'non-finite'):
            pre.examine(a, b)

    def test_rib_mapping_levels_1_2_9_10_12(self):
        b = fixture()['bones']
        for i in (1, 2, 9, 10, 12):
            left = b[f'rib_{i:02d}_left']['head_m'][2]
            right = b[f'rib_{i:02d}_right']['head_m'][2]
            self.assertAlmostEqual(left, pre._rib_level(b, i))
            self.assertAlmostEqual(right, pre._rib_level(b, i))

    def test_rebuild_input_dicts_not_modified(self):
        a = fixture()
        b = shifted(a)
        prior = json.dumps([a, b], sort_keys=True)
        pre.examine(a, b)
        self.assertEqual(json.dumps([a, b], sort_keys=True), prior)


class RealProposals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(C004.read_text())
        cls.rejected = json.loads(P003.read_text())

    def test_c004_is_unchanged_and_not_rebuilt(self):
        result = pre.examine(self.baseline, self.baseline)
        self.assertIn('NO_SPINE_RECONSTRUCTION', result['blockers'])
        self.assertIn('INTERVERTEBRAL_DISC_CLEARANCE_INSUFFICIENT', result['blockers'])

    def test_rejected_p003_still_fails_its_rib_level_gate(self):
        result = pre.examine(self.baseline, self.rejected)
        self.assertIn('RIB_ARTICULAR_LEVEL_Z_REGRESSION', result['blockers'])
        self.assertIn('RIBS_NOT_COUPLED_TO_THORAX', result['blockers'])
        self.assertEqual(result['status'], 'REJECTED_MECHANICAL_PREFLIGHT')
        self.assertGreater(result['rib_level_proposal_max_offset_mm'], 30)
        self.assertLess(result['rib_level_reference_max_offset_mm'], 10)

    def test_c004_and_p003_have_same_bone_ids(self):
        self.assertEqual(set(self.baseline['bones']), set(self.rejected['bones']))
        self.assertGreaterEqual(len(self.baseline['bones']), 206)


if __name__ == '__main__':
    unittest.main()
