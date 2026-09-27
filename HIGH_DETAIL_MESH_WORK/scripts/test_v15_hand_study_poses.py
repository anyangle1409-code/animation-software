import copy
import unittest

from v15_hand_study_poses import study_payload


class StudyPayloadTests(unittest.TestCase):
    def test_creates_no_equipment_review_without_mutating_source(self):
        source = {
            "exercise": "Dumbbell Bicep Curl",
            "label": "bottom",
            "time": 0,
            "meshes": [{"name": "body"}],
            "equipment": [{"name": "dumbbell"}],
        }
        original = copy.deepcopy(source)

        result = study_payload(source, "Closed Fist Review")

        self.assertEqual(result["exercise"], "Closed Fist Review")
        self.assertEqual(result["label"], "review")
        self.assertEqual(result["equipment"], [])
        self.assertEqual(result["meshes"], source["meshes"])
        self.assertEqual(source, original)


if __name__ == "__main__":
    unittest.main()
