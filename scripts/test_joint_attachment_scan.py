"""Joint attachment (closure) invariant over the committed isolated runs: reproduction, shared vs candidate-specific
results, and the pinned midfoot column-split defect (not fixed; coupling magnitudes unsourced)."""
import hashlib, json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import joint_attachment_scan as m  # noqa: E402

O = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/joint_attachment_scan'
RUNS = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs'
SCANS = {'a003_isolated_014': ('ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json', RUNS / 'isolated_bone_only_014/isolated_samples.json'),
         'c003_isolated_001': ('ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json',
                               RUNS / 'isolated_bone_only_c003_shoulder_thorax_001/isolated_samples.json')}
CENTRE_TYPES = ('ball_socket', 'hinge', 'pivot')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Attachment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.S = {k: json.loads((O / f'{k}.json').read_text()) for k in SCANS}

    def test_reproduces(self):
        for k, (rec, smp) in SCANS.items():
            r = m.scan(json.loads((ROOT / rec).read_text()), json.loads(smp.read_text()), self.S[k]['stride'])
            self.assertEqual(json.loads(json.dumps(r['opened'])), self.S[k]['opened'], k)
            self.assertEqual(self.S[k]['articulations_checked'], 368)

    def test_centre_type_joints_stay_within_2mm(self):
        for k, s in self.S.items():
            ct = {j: v['max_opening_mm'] for j, v in s['opened'].items() if any(t in v['type'] for t in CENTRE_TYPES) and 'translation' not in v['type']}   # TMJ glides by design
            self.assertEqual(set(ct), {f'{j}_{x}' for j in ('talocalcaneonavicular', 'proximal_radioulnar', 'talocrural') for x in ('left', 'right')}, k)
            self.assertLess(max(ct.values()), 2.0)

    def test_midfoot_column_split_pinned_shared(self):
        for k, s in self.S.items():
            for side in ('left', 'right'):
                for j in ('tmt_4', 'intermetatarsal_3_4', 'intertarsal_lateral_cuneiform_cuboid'):
                    v = s['opened'][f'{j}_{side}']
                    self.assertGreater(v['max_opening_mm'], 30, (k, j)); self.assertEqual(v['worst_test'], f'subtalar_inversion_eversion_{side}')
        rec = json.loads((ROOT / SCANS['a003_isolated_014'][0]).read_text())['bones']
        self.assertEqual(rec['metatarsal_4_left']['parent'], 'cuboid_left'); self.assertEqual(rec['metatarsal_3_left']['parent'], 'lateral_cuneiform_left')
        self.assertEqual(rec['navicular_left']['parent'], 'talus_left'); self.assertEqual(rec['calcaneus_left']['parent'], 'talus_left')

    def test_only_scapulothoracic_differs_between_a003_and_c003(self):
        a, c = self.S['a003_isolated_014']['opened'], self.S['c003_isolated_001']['opened']
        self.assertEqual(set(a), set(c))
        diff = {k for k in a if abs(a[k]['max_opening_mm'] - c[k]['max_opening_mm']) > 0.01}
        self.assertEqual(diff, {'scapulothoracic_left', 'scapulothoracic_right'})

    def test_clip_manifest(self):
        man = json.loads((O / 'clips/manifest.json').read_text())
        for rel, h in man['files_sha256'].items():
            self.assertEqual(sha(ROOT / rel), h, rel)


if __name__ == '__main__':
    unittest.main()
