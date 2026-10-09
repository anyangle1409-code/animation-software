"""Wrist/hand model source context: committed findings pinned (model is not a dimensional source; carpal topology holds
on model and a003), topology detector and the .vtp decoder proven by mutation/synthetic data. The live re-run needs the
external opensim-models clone and is skipped without it."""
import base64, copy, json, os, struct, sys, tempfile, unittest, zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import wrist_hand_model_context as w  # noqa: E402
import opensim_model_geometry as og  # noqa: E402

OUT = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/claude_independent_review_20261009/wrist_hand_model_context_v1.json'
REPO = Path(os.environ.get('OPENSIM_MODELS', '/home/user/opensim-org/opensim-models'))


class Committed(unittest.TestCase):
    def test_findings(self):
        d = json.loads(OUT.read_text())
        self.assertEqual(d['kind'], 'SOURCE_CONTEXT_NOT_A_TARGET')
        self.assertEqual(d['provenance']['commit'], 'd9b05d470b1a481c222372c85b75772faf8f7792')
        self.assertIn('Gonzalez', d['provenance']['credits'])
        s = d['scale']
        self.assertGreater(s['max'] - s['min'], 0.25)                       # not a constant scale
        self.assertGreater(s['model_over_ayd_mean'], 1.2)
        self.assertEqual(d['carpal_topology_all_hold'], {'model': True, 'a003_left': True, 'a003_right': True})
        self.assertEqual(d['decision']['coordinates_or_lengths_adopted'], 0)
        self.assertIn('REMAIN UNRESOLVED', d['decision']['fingertip_tails'])

    @unittest.skipUnless((REPO / 'Models/WristModel/wrist.osim').exists(), 'external opensim-models clone not present')
    def test_live_rerun_matches(self):
        d = json.loads(OUT.read_text())
        r = w.run(REPO)
        self.assertEqual(r['provenance']['model_sha256'], d['provenance']['model_sha256'])
        self.assertEqual(json.loads(json.dumps(r['lengths'])), d['lengths'])


class Topology(unittest.TestCase):
    def test_a003_holds_and_mutations_fail(self):
        fr = w.a003_frames()['left']
        self.assertTrue(all(x['holds'] for x in w.relations(fr)))
        bad = copy.deepcopy(fr); bad['pisiform'][2] = bad['triquetrum'][2] - 0.005            # pisiform dorsal
        self.assertIn('pisiform +palmar of triquetrum', [x['relation'] for x in w.relations(bad) if not x['holds']])
        bad = copy.deepcopy(fr); bad['lunate'], bad['triquetrum'] = bad['triquetrum'], bad['lunate']
        self.assertTrue(any(not x['holds'] for x in w.relations(bad)))


class Vtp(unittest.TestCase):
    def test_compressed_roundtrip(self):
        P = np.array([[0.1, 0.2, 0.3], [-1.5, 2.0, 7.25], [3, 4, 5]], dtype='<f4')
        raw = P.tobytes(); comp = zlib.compress(raw)
        header = struct.pack('<4I', 1, len(raw), len(raw), len(comp))
        text = base64.b64encode(header).decode() + base64.b64encode(comp).decode()
        xml = ('<?xml version="1.0"?><VTKFile type="PolyData" version="0.1" byte_order="LittleEndian" compressor="vtkZLibDataCompressor">'
               f'<PolyData><Piece NumberOfPoints="3"><Points><DataArray type="Float32" NumberOfComponents="3" format="binary">{text}</DataArray>'
               '</Points></Piece></PolyData></VTKFile>')
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'x.vtp'; p.write_text(xml)
            np.testing.assert_allclose(og.read_vtp(p), P.astype(float))

    def test_rotation_convention(self):
        R = og.xyz_body_fixed([0.0, 0.0, np.pi / 2])
        np.testing.assert_allclose(R @ [1, 0, 0], [0, 1, 0], atol=1e-12)


if __name__ == '__main__':
    unittest.main()
