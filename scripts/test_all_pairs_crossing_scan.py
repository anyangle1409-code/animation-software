"""All-pairs unconnected bone-axis crossing scan: committed results pinned (shared by a003 and c003) and detection proven by
mutation (static contact, dynamic crossing)."""
import copy, json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import all_pairs_crossing_scan as m  # noqa: E402

O = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/all_pairs_crossing_scan'
RUNS = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs'
REC = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json').read_text())
S = json.loads((RUNS / 'isolated_bone_only_014/isolated_samples.json').read_text())


class Committed(unittest.TestCase):
    def test_shared_results(self):
        for name in ('a003_isolated_014', 'c003_isolated_001'):
            d = json.loads((O / f'{name}.json').read_text())
            self.assertEqual(d['eligible_pairs'], 20747)
            self.assertEqual(d['dynamic_tests'], ['hip_abduction_adduction_left', 'hip_abduction_adduction_right'])
            self.assertEqual({tuple(x['bones']) for x in d['dynamic_new_crossings']}, {('tibia_left', 'tibia_right')})
            st = d['static_unconnected_axis_contacts']
            self.assertEqual([x['bones'] for x in st], [['mandible', 'vomer']])
            self.assertEqual(st[0]['classification'], 'REPRESENTATION_ARTEFACT')


class Mutations(unittest.TestCase):
    def test_static_contact_detected(self):
        rec = copy.deepcopy(REC)
        rec['bones']['digit3_distal_phalanx_left']['tail_m'] = list(REC['bones']['femur_left']['head_m'])   # unconnected, now touching
        r = m.scan(rec, {})
        self.assertIn(['digit3_distal_phalanx_left', 'femur_left'], [x['bones'] for x in r['static_unconnected_axis_contacts']])

    def test_dynamic_crossing_detected(self):
        fr = copy.deepcopy(S['knee_flexion_extension_left'])
        dx = REC['bones']['tibia_right']['head_m'][0] - REC['bones']['tibia_left']['head_m'][0]
        for f in fr[30:40]:
            M = f['moving_deltas']['tibia_left']
            f['moving_deltas']['tibia_left'] = [[1, 0, 0, dx], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        r = m.scan(REC, {'knee_flexion_extension_left': fr}, stride=1)
        self.assertIn(['tibia_left', 'tibia_right'], [x['bones'] for x in r['dynamic_new_crossings']])


if __name__ == '__main__':
    unittest.main()
