import json
import math
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FRAME = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_s1_pelvic_frame_p1.json"


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(dot(a, a))


def cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


class CanonicalS1PelvicFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = json.loads(FRAME.read_text())

    def test_pi_identity(self):
        s = self.f["source_family"]
        self.assertAlmostEqual(
            s["pelvic_tilt_deg"]["mean"] + s["sacral_slope_deg"]["mean"],
            s["pelvic_incidence_deg"]["mean"],
            places=9,
        )

    def test_pelvic_thickness_and_tilt_geometry(self):
        h = self.f["retained_hip_axis"]["HA_midpoint_m"]
        s1 = self.f["derived_S1_superior_endplate"]["centre_m"]
        v = [(b - a) * 1000.0 for a, b in zip(h, s1)]
        self.assertAlmostEqual(norm(v), 107.0, places=6)
        self.assertGreater(v[1], 0.0)  # posterior
        self.assertGreater(v[2], 0.0)  # superior
        angle = math.degrees(math.atan2(v[1], v[2]))
        self.assertAlmostEqual(angle, 9.2, places=6)

    def test_s1_axes_are_orthonormal_and_right_handed(self):
        axes = self.f["derived_S1_superior_endplate"]["local_axes_world"]
        x = axes["X_left"]
        y = axes["Y_anterior_to_posterior_along_endplate"]
        z = axes["Z_superior_endplate_normal"]
        for a in (x, y, z):
            self.assertAlmostEqual(norm(a), 1.0, places=9)
        self.assertAlmostEqual(dot(x, y), 0.0, places=9)
        self.assertAlmostEqual(dot(x, z), 0.0, places=9)
        self.assertAlmostEqual(dot(y, z), 0.0, places=9)
        xyz = cross(x, y)
        for actual, expected in zip(xyz, z):
            self.assertAlmostEqual(actual, expected, places=9)

    def test_sacral_slope_from_plane_tangent(self):
        y = self.f["derived_S1_superior_endplate"]["local_axes_world"][
            "Y_anterior_to_posterior_along_endplate"
        ]
        # In the sagittal plane, elevation of the endplate tangent from
        # horizontal is atan2(superior component, posterior component).
        angle = math.degrees(math.atan2(y[2], y[1]))
        self.assertAlmostEqual(angle, 40.9, places=6)

    def test_frame_remains_provisional(self):
        self.assertIn("PROVISIONALLY", self.f["status"])
        self.assertTrue(any(
            "does not alter retained HJC or production geometry" in check
            for check in self.f["hard_checks"]
        ))


if __name__ == "__main__":
    unittest.main()
