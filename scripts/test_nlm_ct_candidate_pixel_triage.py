#!/usr/bin/env python3
"""Source provenance and anatomical rejection contract for original CT pixel triage."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
import nlm_ct_candidate_pixel_triage as triage

AUDIT = ROOT / "ORIGINAL_V1_WORK" / "anatomy" / "audit"
BUNDLE = AUDIT / "nlm_pelvic_ct_full_series_candidate_bundle_20261009.json"
CAL = AUDIT / "nlm_pelvic_ct_full_series_hu_calibration_20261009.json"
REVIEW = AUDIT / "nlm_pelvic_ct_full_series_candidate_review_20261009.json"


def files():
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in
                 (BUNDLE, CAL, REVIEW))


def geometry(s):
    return {
        "scanner_S_mm": s,
        "plane_TL_RAS_mm": [228, 291, s],
        "plane_TR_RAS_mm": [-232, 291, s],
        "plane_BR_RAS_mm": [-232, -169, s],
    }


def synthetic_loader(rows):
    def load(_path, source):
        pixels = [1024] * (512 * 512)
        for obs in rows:
            if obs["source_id"] == source["source_id"]:
                r, c = obs["pixel"]["row"], obs["pixel"]["column"]
                pixels[r * 512 + c] = 1500
                pixels[(r+1) * 512 + c] = 1330
        return geometry(source["scanner_centre_RAS_mm"][2]), pixels
    return load


class OriginalPelvicPixelTriage(unittest.TestCase):
    def test_all_observations_are_provenance_linked_but_unaccepted(self):
        manifest, calibration, review = files()
        obs = review["observations"]
        right = triage.triage(
            manifest, calibration, review, 1, "/tmp/original-ct",
            source_loader=synthetic_loader(obs))
        left = triage.triage(
            manifest, calibration, review, 2, "/tmp/original-ct",
            source_loader=synthetic_loader(obs))
        self.assertEqual([right["summary"]["observations"],
                          left["summary"]["observations"]], [5, 5])
        self.assertEqual([right["summary"]["source_slices_read_once"],
                          left["summary"]["source_slices_read_once"]], [3, 2])
        for result in (right, left):
            self.assertEqual(result["summary"]["centre_passes_by_HU"],
                             {"150": 5, "300": 5, "500": 0, "700": 0})
            self.assertFalse(result["anatomical_bone_geometry_or_surface_verified"])
            self.assertFalse(result["canonical_promotion_allowed"])
            self.assertEqual(result["required_pelvic_bony_landmarks_anatomically_accepted"], 0)
            self.assertEqual(result["summary"]["declared_side_disagreements"], [])
            for p in result["observations"]:
                self.assertEqual(p["point_HU_from_verified_addend"], 476)
                self.assertEqual(p["five_by_five_HU_range"], [0, 476])
                self.assertEqual(
                    [x["five_by_five_samples_passing"]
                     for x in p["five_by_five_neighbourhood_threshold_support"]],
                    [2, 2, 0, 0])
                self.assertFalse(p["source_pixel_confirms_anatomical_bone_identity"])
                self.assertFalse(p["suitable_seed_for_full_bone_surface_verified"])
                self.assertNotEqual(
                    p["scanner_RAS_mm_if_FOV_corners_are_outer_edges"],
                    p["scanner_RAS_mm_if_first_pixel_is_at_FOV_corner"])

    def test_low_hu_is_reported_not_silently_snapped_to_bone(self):
        manifest, cal, review = files()
        def load(_folder, row):
            return geometry(row["scanner_centre_RAS_mm"][2]), [1024] * (512 * 512)
        result = triage.triage(manifest, cal, review, 2, "/tmp/original-ct",
                               source_loader=load)
        self.assertEqual(result["summary"]["centre_passes_by_HU"]["150"], 0)
        self.assertEqual(len(result["summary"]["centre_fails_300_HU"]), 5)
        self.assertEqual(len(result["observations"]), 5)
        self.assertTrue(all(p["point_HU_from_verified_addend"] == 0
                            for p in result["observations"]))

    def test_laterality_mismatch_is_flagged_not_accepted(self):
        manifest, cal, review = files()
        obs = copy.deepcopy(review["observations"][0])
        pixels = [1024] * (512 * 512)
        pixels[obs["pixel"]["row"] * 512 + obs["pixel"]["column"]] = 1600
        point = triage.audit_pixel(obs, manifest["series"][0]["slices"][10],
                                   geometry(-372), pixels)
        self.assertTrue(point["source_R_sign_consistent_with_proposed_side"])
        obs["observation_id"] = obs["observation_id"].replace("-right-", "-left-")
        wrong = triage.audit_pixel(obs, manifest["series"][0]["slices"][10],
                                   geometry(-372), pixels)
        self.assertFalse(wrong["source_R_sign_consistent_with_proposed_side"])
        self.assertFalse(wrong["source_pixel_confirms_anatomical_bone_identity"])

    def test_wrong_original_image_hash_is_rejected_for_both_groups(self):
        manifest, cal, review = files()
        for field in ("source_png_sha256", "source_header_sha256"):
            altered = copy.deepcopy(review)
            altered["observations"][0][field] = "0"*64
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "pin"):
                triage.triage(manifest, cal, altered, 2, "/tmp/original-ct",
                              source_loader=synthetic_loader([]))
        altered = copy.deepcopy(review)
        altered["observations"][0]["scanner_S_mm"] += 1
        with self.assertRaisesRegex(ValueError, "pin"):
            triage.triage(manifest, cal, altered, 1, "/tmp/original-ct",
                          source_loader=synthetic_loader([]))

    def test_invalid_observations_cannot_become_landmarks(self):
        manifest, cal, review = files()
        cases = [
            ("duplicate", lambda r: r["observations"].append(
                copy.deepcopy(r["observations"][0])), "duplicate"),
            ("bad_source", lambda r: r["observations"][0].update(
                source_id="cvm999999f"), "missing"),
            ("bad_grid", lambda r: r["observations"][0]["pixel"].update(
                column=513), "outside"),
            ("nonint", lambda r: r["observations"][0]["pixel"].update(
                row=True), "outside"),
        ]
        for label, edit, failure in cases:
            packet = copy.deepcopy(review)
            edit(packet)
            with self.subTest(case=label), self.assertRaisesRegex(ValueError, failure):
                triage.triage(manifest, cal, packet, 1, "/tmp/original-ct",
                              source_loader=synthetic_loader(review["observations"]))
        with self.assertRaisesRegex(ValueError, "group"):
            triage.triage(manifest, cal, review, 3, "/tmp/original-ct")

    def test_nearest_dense_pixel_leads_are_deterministic_and_not_landmarks(self):
        pixels = [1024] * (512 * 512)
        pixels[203*512 + 204] = 1624   # 600 HU; five image pixels away
        pixels[196*512 + 197] = 1624   # 600 HU; also five away, selected by row tie
        pixels[200*512 + 201] = 1230   # 206 HU, nearest for threshold 150
        result = triage.nearby_dense_pixel_leads(
            geometry(-372), pixels, 200, 200, [.898438, .898438])
        self.assertEqual([v["minimum_HU"] for v in result], [150, 300, 500, 700])
        self.assertEqual(result[0]["nearest_intensity_only_not_anatomy"]["pixel"],
                         {"row": 200, "column": 201})
        self.assertEqual(result[1]["nearest_intensity_only_not_anatomy"]["pixel"],
                         {"row": 196, "column": 197})
        self.assertEqual(result[1]["nearest_intensity_only_not_anatomy"]["distance_pixels"], 5)
        self.assertFalse(result[1]["nearest_intensity_only_not_anatomy"][
            "anatomical_identity_or_seed_accepted"])
        self.assertIsNone(result[3]["nearest_intensity_only_not_anatomy"])

    def test_review_lead_never_escapes_bounds_and_rejects_invalid_geometry(self):
        pixels = [1024] * (512*512)
        pixels[0] = 1800
        v = triage.nearby_dense_pixel_leads(
            geometry(-372), pixels, 0, 0, [.898438, .898438])
        self.assertEqual(v[2]["nearest_intensity_only_not_anatomy"]["pixel"],
                         {"row": 0, "column": 0})
        for bad in ([-1, .8], [0, .8], [.9, True], [.8], [999, 1]):
            with self.subTest(spacing=bad), self.assertRaises(ValueError):
                triage.nearby_dense_pixel_leads(
                    geometry(-372), pixels, 0, 0, bad)
        with self.assertRaisesRegex(ValueError, "search"):
            triage.nearby_dense_pixel_leads(
                geometry(-372), pixels, 0, 0, [.9, .9], radius_pixels=33)

    def test_private_non_overwrite_and_pins_guard_extraction(self):
        bundle, calibration, review = files()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "candidate_pixel_review.json"
            args = SimpleNamespace(out=str(output),
                                   ct_dir=str(Path(tmp) / "source"),
                                   group=1, bundle=str(BUNDLE),
                                   calibration=str(CAL), review=str(REVIEW))
            # Runner supplies original images. This test substitutes only
            # deterministic synthetic image pixels, with real pinned metadata.
            with patch.object(triage, "_private_source_slice",
                              side_effect=synthetic_loader(review["observations"])):
                result = triage.run(args)
            self.assertTrue(output.is_file())
            self.assertEqual(result["summary"]["observations"], 5)
            self.assertFalse(result["canonical_promotion_allowed"])
            with self.assertRaisesRegex(ValueError, "overwrite"):
                triage.run(args)


if __name__ == "__main__":
    unittest.main()
