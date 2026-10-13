import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "anatomy_fit"))

import build_whole_skeleton_validation_matrix as a1


class WholeSkeletonValidationMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = a1.build()

    def test_committed_matrix_is_current(self):
        self.assertEqual(json.loads(a1.OUT.read_text()), self.m)

    def test_every_bone_maps_to_exactly_one_region(self):
        self.assertEqual(self.m["bones_not_mapped_to_a_region"], [])
        self.assertEqual(sum(r["containment"]["bones"] for r in self.m["regions"].values()), 206)

    def test_readiness_is_copied_never_upgraded(self):
        src = json.loads(a1.READINESS.read_text())["regions"]
        self.assertEqual({k: v["readiness"] for k, v in src.items()},
                         {k: v["readiness"] for k, v in self.m["regions"].items()})
        self.assertFalse(self.m["approved"])

    def test_containment_join_matches_audit(self):
        out = sorted(b for r in self.m["regions"].values() for b in r["containment"]["outside_skin"])
        self.assertEqual(len(out), self.m["containment_summary"]["bones_outside_skin"])


if __name__ == "__main__":
    unittest.main()
