import contextlib, io, json, shutil, sys, tempfile, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
import ct_pelvis_slice_index as si  # noqa: E402
import ct_pelvis_window_geometry as g  # noqa: E402

AUDIT = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/claude_pelvis_ct_review_20261009"
PINNED = AUDIT / "pinned_six_frames_from_pr15_4680b49.json"
MAN = g.load_pinned_manifest(PINNED)


class SliceIndex(unittest.TestCase):
    def test_hypothesis_reproduces_pins_and_gap(self):
        d = si.build(MAN)
        self.assertEqual(d["uncovered_gap_between_windows_mm"], 39.0)
        self.assertEqual({r["region_status"] for r in d["pinned_frames"]}, {"UNVERIFIED"})
        self.assertEqual(len(d["pinned_frames"]), 6)

    def test_bridge_ids_fill_gap_exactly(self):
        a = si.build(MAN)["additional_ranges_needed"]["tier_A_bridge_windows"]
        self.assertEqual(a["frame_count"], 13)
        self.assertEqual(a["hypothesised_S_mm"][0], -366.0)
        self.assertEqual(a["hypothesised_S_mm"][-1], -402.0)
        self.assertTrue(all(y - x == -3 for x, y in zip(a["hypothesised_S_mm"], a["hypothesised_S_mm"][1:])))

    def test_broken_hypothesis_is_rejected(self):
        bad = {"by_id": {k: dict(v) for k, v in MAN["by_id"].items()}}
        bad["by_id"][1749]["scanner_S_mm"] = -358
        with self.assertRaises(ValueError):
            si.build(bad)

    def test_no_claim_of_review_and_committed_files_match(self):
        d = si.build(MAN)
        self.assertIs(d["image_review_performed"], False)
        self.assertIs(d["canonical_promotion_allowed"], False)
        self.assertEqual(si.main(["--manifest", str(PINNED), "--check",
                                  "--out-json", str(AUDIT / "physical_slice_to_region_index.json"),
                                  "--out-md", str(AUDIT / "physical_slice_to_region_index.md")]), 0)

    def test_create_only(self):
        t = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, t, True)
        args = ["--manifest", str(PINNED), "--out-json", str(t / "a.json"), "--out-md", str(t / "a.md")]
        self.assertEqual(si.main(args), 0)
        with self.assertRaises(FileExistsError):
            si.main(args)


if __name__ == "__main__":
    unittest.main()
