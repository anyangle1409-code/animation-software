"""Collision-free ORIGINAL-v1 revision selection preserves partial local work."""
from pathlib import Path
import tempfile
import unittest

import select_original_v1_collision_free_revision as s


class RevisionSelectorTests(unittest.TestCase):
    def touch(self,root,rel):
        p=root/"ORIGINAL_V1_WORK"/"candidates"/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text("fixture",encoding="utf-8")

    def test_r55_only_selects_r56(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.touch(root,"HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r55.json")
            self.assertEqual(s.choose(root,"r55")["selected_revision"],"r56")

    def test_partial_r56_evidence_reserves_revision(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.touch(root,"repair_preparation/r56_axilla_pit_declared/mask.json")
            result=s.choose(root,"r55")
            self.assertEqual(result["highest_observed_revision"],"r56")
            self.assertEqual(result["selected_revision"],"r57")

    def test_highest_observed_revision_wins_over_after_floor(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.touch(root,"repair_checks/full_r61_evidence_manifest.json")
            self.assertEqual(s.choose(root,"r55")["selected_revision"],"r62")

    def test_unrelated_digits_do_not_reserve_revision(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.touch(root,"review/phase5_5A_camera56.json")
            self.assertEqual(s.choose(root,"r55")["selected_revision"],"r56")

    def test_invalid_after_revision_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"numbered revision"):
                s.choose(Path(td),"candidate55")


if __name__=="__main__":
    unittest.main()
