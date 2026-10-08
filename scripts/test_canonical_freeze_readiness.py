import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANAT = ROOT / "ORIGINAL_V1_WORK/anatomy"

SOURCES = ANAT / "canonical_proportion_sources_v1.json"
CORRIDORS = ANAT / "canonical_target_corridors_v1.json"
READINESS = ANAT / "canonical_freeze_readiness_v1.json"
FOOT = ANAT / "canonical_foot_proportion_audit_v1.json"
SPEC = ANAT / "canonical_skeleton_rebuild_spec_v1.json"


class CanonicalFreezeReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = json.loads(SOURCES.read_text())
        cls.corridors = json.loads(CORRIDORS.read_text())
        cls.readiness = json.loads(READINESS.read_text())
        cls.foot = json.loads(FOOT.read_text())
        cls.spec = json.loads(SPEC.read_text())

    def test_all_corridor_source_ids_are_registered(self):
        known = {s["id"] for s in self.sources["sources"]}
        refs = []

        def walk(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if k == "source" and isinstance(v, str):
                        refs.append(v)
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)

        walk(self.corridors)
        missing = sorted(set(refs) - known)
        self.assertEqual(missing, [])

    def test_numeric_bands_are_ordered(self):
        bad = []

        def walk(x, path=""):
            if isinstance(x, dict):
                if "band_1sd" in x and isinstance(x["band_1sd"], list):
                    b = x["band_1sd"]
                    if len(b) != 2 or not b[0] < b[1]:
                        bad.append(path)
                    if "mean" in x and not (b[0] <= x["mean"] <= b[1]):
                        bad.append(path + ".mean")
                for k, v in x.items():
                    walk(v, f"{path}.{k}" if path else k)
            elif isinstance(x, list):
                for i, v in enumerate(x):
                    walk(v, f"{path}[{i}]")

        walk(self.corridors)
        self.assertEqual(bad, [])

    def test_readiness_counts_match_regions(self):
        vals = [r["readiness"] for r in self.readiness["regions"].values()]
        counts = {k: vals.count(k) for k in ("READY", "PARTIAL", "BLOCKED")}
        self.assertEqual(counts, self.readiness["region_counts"])
        self.assertGreater(counts["BLOCKED"], 0)
        self.assertEqual(self.readiness["overall_status"], "NOT_READY_FOR_NEW_CANONICAL_BLENDER_REVISION")

    def test_foot_correction_prevents_patill_only_shrink(self):
        self.assertEqual(
            self.foot["status"],
            "SURFACE_FOOT_LENGTH_DEFECT_CONFIRMED_INTERNAL_BONE_DISTRIBUTION_UNRESOLVED",
        )
        self.assertIn("stature_aware_crosscheck", self.foot)
        self.assertGreater(
            self.foot["stature_aware_crosscheck"]["Portugal_2009_M2_max_predicted_at_stature_mm"],
            80.0,
        )
        self.assertTrue(any("Do not implement" in x for x in self.foot["next_steps"]))

    def test_rebuild_spec_is_not_mislabelled_final(self):
        self.assertEqual(self.spec["status"], "IMPLEMENTATION_SPEC_NOT_A_FINAL_SKELETON")
        self.assertNotEqual(self.spec["regions"]["forefoot_toes"]["status"], "RED_RETARGET")
        self.assertIn("Conflicting population or measurement-definition evidence must reopen a target rather than be averaged silently.", self.spec["global_rules"])


if __name__ == "__main__":
    unittest.main()
