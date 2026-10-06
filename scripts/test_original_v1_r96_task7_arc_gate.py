import copy
import unittest

from original_v1_r96_task7_arc_gate import compare_arcs, validate_arc

TOL = {
    "volume_deviation_from_1_rise": 0.005,
    "edge_ratio_p99_rise": 0.05,
    "region_min_ratio_drop": 0.02,
    "region_max_ratio_rise": 0.1,
}


def record():
    rows = []
    for i, fraction in enumerate((0.0, 0.5, 1.0)):
        rows.append(
            {
                "fraction": fraction,
                "elevation_l_deg": 10 + 70 * fraction,
                "elevation_r_deg": 10 + 70 * fraction,
                "scapula_rot_l_deg": 5 + 20 * fraction,
                "scapula_rot_r_deg": 5 + 20 * fraction,
                "torso_drift_max_m": 0.02 + 0.04 * fraction,
                "torso_drift_n_over_5cm": i,
                "torso_drift_n_over_10cm": 0,
                "torso_edge_max": 1.2 + 0.4 * fraction,
                "torso_edge_min": 0.9 - 0.1 * fraction,
                "shoulder_edge_max": 1.3 + 0.3 * fraction,
                "shoulder_edge_min": 0.85 - 0.05 * fraction,
                "edge_p99": 1.2 + 0.2 * fraction,
                "volume_ratio": 1.0 - 0.01 * fraction,
            }
        )
    return {
        "schema_version": 1,
        "source_candidate_sha256": "a" * 64,
        "poses": {
            "press_top": copy.deepcopy(rows),
            "press_top_rhythm": copy.deepcopy(rows),
            "pullup_hang": copy.deepcopy(rows),
            "pullup_hang_rhythm": copy.deepcopy(rows),
        },
    }


class Task7ArcGateTests(unittest.TestCase):
    def test_equal_arc_passes(self):
        base = record()
        cand = copy.deepcopy(base)
        cand["source_candidate_sha256"] = "b" * 64
        result = compare_arcs(base, cand, TOL)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["regression_count"], 0)

    def test_existing_region_max_tolerance_blocks_regression(self):
        base = record()
        cand = copy.deepcopy(base)
        cand["source_candidate_sha256"] = "b" * 64
        cand["poses"]["press_top"][1]["torso_edge_max"] += 0.11
        result = compare_arcs(base, cand, TOL)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any(x["metric"] == "torso_edge_max" for x in result["regressions"]))

    def test_existing_region_min_tolerance_blocks_regression(self):
        base = record()
        cand = copy.deepcopy(base)
        cand["source_candidate_sha256"] = "b" * 64
        cand["poses"]["pullup_hang"][2]["shoulder_edge_min"] -= 0.021
        result = compare_arcs(base, cand, TOL)
        self.assertTrue(any(x["metric"] == "shoulder_edge_min" for x in result["regressions"]))

    def test_mismatched_sampling_blocks(self):
        base = record()
        cand = copy.deepcopy(base)
        cand["source_candidate_sha256"] = "b" * 64
        cand["poses"]["press_top"].pop()
        result = compare_arcs(base, cand, TOL)
        self.assertIn("arc_sample_count_mismatch:press_top", result["issues"])

    def test_drift_is_measured_without_inventing_a_new_threshold(self):
        base = record()
        cand = copy.deepcopy(base)
        cand["source_candidate_sha256"] = "b" * 64
        cand["poses"]["press_top"][2]["torso_drift_max_m"] += 0.5
        result = compare_arcs(base, cand, TOL)
        self.assertEqual(result["status"], "PASS")
        row = next(x for x in result["measurements"] if x["pose"] == "press_top")
        self.assertGreater(row["torso_drift_max_rise_m"], 0.49)

    def test_arc_requires_zero_to_one_ordered_fractions(self):
        broken = record()
        broken["poses"]["press_top"][1]["fraction"] = 0.0
        self.assertIn(
            "arc_fractions_not_strictly_increasing:press_top",
            validate_arc(broken),
        )


if __name__ == "__main__":
    unittest.main()
