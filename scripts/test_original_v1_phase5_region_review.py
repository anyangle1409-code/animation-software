"""Phase 5 regional capture plan matches anatomy execution coverage."""
import unittest
import original_v1_phase5_region_review as r

class Phase5RegionReviewTests(unittest.TestCase):
    def test_capture_plan_matches_every_region_required_view(self):
        plan=r.load_capture_plan(r.ROOT)
        self.assertEqual(set(plan["regions"]),{"5A","5B","5C","5D","5E","5F","5G"})
        self.assertTrue(all(plan["regions"][k]["captures"] for k in plan["regions"]))

    def test_capture_ids_are_unique_per_region(self):
        plan=r.load_capture_plan(r.ROOT)
        for region,row in plan["regions"].items():
            ids=[x["id"] for x in row["captures"]]
            self.assertEqual(len(ids),len(set(ids)),region)

    def test_exact_capture_metadata_contract(self):
        plan=r.load_capture_plan(r.ROOT)
        row=next(x for x in plan["regions"]["5D"]["captures"] if x["id"]=="palm_right")
        meta=r.expected_capture_metadata(plan,"5D",row)
        self.assertEqual(meta["camera"],row["camera"])
        self.assertEqual(meta["renderer"],"BLENDER_WORKBENCH")
        self.assertEqual(meta["resolution"],[900,900,100])
        self.assertFalse(meta["dressed"])
        self.assertFalse(meta["whole_body"])

    def test_high_detail_views_missing_from_generic_board_are_explicit(self):
        plan=r.load_capture_plan(r.ROOT)
        self.assertIn("wrist_close",{x["id"] for x in plan["regions"]["5C"]["captures"]})
        hands={x["id"] for x in plan["regions"]["5D"]["captures"]}
        self.assertTrue({"palm_left","palm_right","dorsal_left","dorsal_right"}.issubset(hands))
        self.assertIn("neutral_sole",{x["id"] for x in plan["regions"]["5F"]["captures"]})

if __name__=="__main__":
    unittest.main()
