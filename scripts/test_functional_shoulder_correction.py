import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "anatomy_fit"))

import functional_shoulder_correction as corr
from rib_spiral_reconstruction import distal_curve

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json"


def _rot(v, axis, deg):
    return corr.rotate_about(v, (0.0, 0.0, 0.0), axis, math.radians(deg))


class RibReferenceShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = corr.load_holcombe()

    def test_inplane_curve_hits_published_endpoints_and_peak_for_every_level(self):
        for level in range(1, 13):
            p = corr.rib_level_parameters(self.model, level)
            curve = corr.rib_inplane_curve(p)
            self.assertEqual(curve[0], (0.0, 0.0))
            self.assertAlmostEqual(curve[-1][0], 1.0, places=12)
            self.assertAlmostEqual(curve[-1][1], 0.0, places=12)
            ys = [y for _, y in curve]
            self.assertAlmostEqual(max(ys), p["Ypk"], places=9)
            self.assertTrue(all(math.isfinite(v) for pt in curve for v in pt))

    def test_distal_segment_is_the_exact_source_spiral(self):
        p = corr.rib_level_parameters(self.model, 7)
        curve = corr.rib_inplane_curve(p, distal_samples=33)
        expected = distal_curve(p["Xpk"], p["Ypk"], p["Bd"], samples=33)
        for got, want in zip(curve[-33:], expected):
            self.assertAlmostEqual(got[0], want[0], places=12)
            self.assertAlmostEqual(got[1], want[1], places=12)

    def test_proximal_start_follows_published_inner_angle(self):
        for level in range(1, 13):
            p = corr.rib_level_parameters(self.model, level)
            c = corr.rib_inplane_curve(p, proximal_samples=400)
            start = math.degrees(math.atan2(c[1][1], c[1][0]))
            self.assertLess(abs(start - p["phi_pia_deg"]), 3.0, level)

    def test_inplane_rejects_out_of_bound_parameters(self):
        p = corr.rib_level_parameters(self.model, 5)
        for bad in (dict(p, Xpk=0.9), dict(p, Ypk=0.01), dict(p, phi_pia_deg=10.0), dict(p, phi_pia_deg=181.0)):
            with self.assertRaises(ValueError):
                corr.rib_inplane_curve(bad)

    def test_3d_rib_keeps_frozen_endpoints_and_bulges_outward_in_plane(self):
        p = corr.rib_level_parameters(self.model, 6)
        head, tail = (0.022, 0.086, 1.431), (0.057, -0.110, 1.336)
        pts = corr.rib_points_reference(head, tail, "left", p)
        self.assertEqual(pts[0], head)
        self.assertEqual(pts[-1], tail)
        chord = math.dist(head, tail)
        ex = tuple((t - h) / chord for h, t in zip(head, tail))
        normal = corr._unit(corr._cross(ex, (1.0, 0.0, 0.0)))
        self.assertLess(max(abs(corr._dot(corr._sub(q, head), normal)) for q in pts), 1e-9)
        peak = max(pts, key=lambda q: q[0])
        self.assertGreater(peak[0], max(head[0], tail[0]) + 0.5 * p["Ypk"] * chord)
        mirrored = corr.rib_points_reference((-head[0], *head[1:]), (-tail[0], *tail[1:]), "right", p)
        for a, b in zip(pts, mirrored):
            self.assertAlmostEqual(a[0], -b[0], places=12)
            self.assertAlmostEqual(a[1], b[1], places=12)

    def test_3d_rib_rejects_wrong_side_and_collapse(self):
        p = corr.rib_level_parameters(self.model, 6)
        with self.assertRaises(ValueError):
            corr.rib_points_reference((0.02, 0.0, 1.0), (0.05, -0.1, 0.9), "right", p)
        with self.assertRaises(ValueError):
            corr.rib_points_reference((0.02, 0.0, 1.0), (0.02, 0.0, 1.0), "left", p)
        with self.assertRaises(ValueError):
            corr.rib_level_parameters(self.model, 13)


class ScapulaRigidPlacementTests(unittest.TestCase):
    def test_rigid_fit_preserves_every_distance_and_anchors_the_head(self):
        rec = json.loads(RECORD.read_text())
        L = [tuple(v / 1000 for v in p) for p in rec["candidate"]["scapula_landmarks_world_mm"]["left"]]
        rb = rec["bones"]["scapula_left"]
        th, tt = (0.176, 0.02, 1.47), (0.10, 0.11, 1.27)       # a longer (1.39x-like) target stick
        out = corr.fit_segment_rigid(L, rb["head_m"], rb["tail_m"], th, tt)
        for i in range(0, len(L), 3):
            for j in range(i + 1, len(L), 4):
                self.assertAlmostEqual(math.dist(L[i], L[j]), math.dist(out[i], out[j]), places=9)
        moved_head = corr.fit_segment_rigid([tuple(rb["head_m"])], rb["head_m"], rb["tail_m"], th, tt)[0]
        self.assertLess(math.dist(moved_head, th), 1e-12)

    def test_record_outline_matches_lee_182cm_predictions(self):
        rec = json.loads(RECORD.read_text())
        L = rec["candidate"]["scapula_landmarks_world_mm"]["left"]
        for name, ref in corr.lee_reference_distances().items():
            i, j = ref["pair_1based"]
            self.assertLess(abs(math.dist(L[i - 1], L[j - 1]) - ref["pred_mm"]), ref["resid_sd_mm"], name)

    def test_place_on_thorax_reaches_target_on_a_synthetic_wall(self):
        pts = [(0.10, 0.06, 1.40), (0.08, 0.07, 1.35), (0.07, 0.08, 1.30)]
        clearance = lambda q: q[1] - 0.05            # wall at y = 0.05, outward +Y
        yaw, tilt, rms, out = corr.place_on_thorax(pts, (0.18, 0.02, 1.45), clearance, [0, 1, 2], 0.012)
        self.assertLess(rms, 0.004)
        self.assertLessEqual(abs(yaw), 25)
        self.assertLessEqual(abs(tilt), 25)
        self.assertEqual(len(out), 3)

    def test_place_on_thorax_rejects_unsafe_inputs(self):
        with self.assertRaises(ValueError):
            corr.place_on_thorax([(0, 0, 0)], (0, 0, 0), lambda q: 0.0, [3], 0.01)
        with self.assertRaises(ValueError):
            corr.place_on_thorax([(0, 0, 0)], (0, 0, 0), lambda q: 0.0, [0], 0.2)


class HumeralAxialTests(unittest.TestCase):
    def test_profile_is_authored_bounded_and_monotone(self):
        values = [corr.humeral_external_rotation_deg(a) for a in range(0, 161, 10)]
        self.assertEqual(values[0], 0.0)
        self.assertAlmostEqual(values[-1], corr.HUMERAL_AXIAL_TOP_DEG)
        self.assertTrue(all(b >= a for a, b in zip(values, values[1:])))
        for bad in (True, -1, 161, math.nan, "90"):
            with self.assertRaises(ValueError):
                corr.humeral_external_rotation_deg(bad)

    def test_external_rotation_sign_moves_anterior_probe_laterally(self):
        down = (0.0, 0.0, -1.0)
        for side, lateral in (("right", -1.0), ("left", 1.0)):
            probe = _rot((0.0, -1.0, 0.0), down, corr.external_rotation_sign(side) * 30.0)
            self.assertGreater(probe[0] * lateral, 0.4, side)

    def test_axial_angle_tracks_rotation_about_the_shaft_and_mirrors(self):
        shaft = corr._unit((0.3, -0.2, -0.9))
        elbow = corr._unit(corr._cross(shaft, (0.0, 1.0, 0.0)))
        a0 = corr.humeral_axial_angle_deg(shaft, elbow, 40.0, "left")
        a1 = corr.humeral_axial_angle_deg(shaft, _rot(elbow, shaft, 25.0), 40.0, "left")
        self.assertAlmostEqual(((a1 - a0 + 180) % 360) - 180, 25.0, places=9)
        hang = (0.0, 0.0, -1.0)
        left = corr.humeral_axial_angle_deg(hang, (1.0, 0.0, 0.0), 40.0, "left")
        right = corr.humeral_axial_angle_deg(hang, (1.0, 0.0, 0.0), 40.0, "right")
        self.assertAlmostEqual(left, -right, places=9)
        with self.assertRaises(ValueError):
            corr.humeral_axial_angle_deg(hang, (1.0, 0.0, 0.0), 40.0, "middle")


if __name__ == "__main__":
    unittest.main()
