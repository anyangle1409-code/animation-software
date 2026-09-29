"""Deterministic gates for the project-authored ORIGINAL v1 O2 body generator."""
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import original_v1_o2_body as generator  # noqa: E402
from original_o2_mesh_checks import inspect_mesh  # noqa: E402


class OriginalV1O2BodyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = generator.build()
        V = cls.result["vertices"]
        cls.report = inspect_mesh([tuple(p) for p in V], [tuple(f) for f in cls.result["faces"]])

    def test_numeric_o2_mesh_gates(self):
        r = self.report
        self.assertAlmostEqual(r["height_m"], generator.TARGET_HEIGHT, delta=0.002)
        for key in ("unmatched_mirror_vertices", "boundary_edges", "nonmanifold_edges",
                    "inconsistent_winding_edges", "loose_vertices", "degenerate_faces", "duplicate_faces"):
            self.assertEqual(r[key], 0, key)

    def test_all_quads_and_grounded(self):
        self.assertTrue(all(len(f) == 4 for f in self.result["faces"]))
        self.assertAlmostEqual(float(self.result["vertices"][:, 2].min()), 0.0, places=9)

    def test_deterministic(self):
        again = generator.build()
        digest = lambda r: hashlib.sha256(r["vertices"].round(9).tobytes()).hexdigest()
        self.assertEqual(digest(self.result), digest(again))
        self.assertEqual(self.result["faces"], again["faces"])

    def test_reads_only_committed_rig_payload(self):
        payload = generator.RIG_PAYLOAD
        self.assertEqual(payload.name, "hgpt_canonical_v4_original.json")
        self.assertEqual(self.result["rig_payload_sha256"],
                         hashlib.sha256(payload.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
