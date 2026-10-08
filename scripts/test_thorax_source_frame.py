"""Analytic and rigid-transform fixtures for source-coordinate mapping.

The fixtures are mathematical, not selected anatomical landmarks.
"""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

PATH = Path(__file__).resolve().parent / 'anatomy_fit/thorax_source_frame.py'


class ThoraxFrame(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PATH.exists(), 'source-to-world thorax mapping is not implemented')
        spec = importlib.util.spec_from_file_location('thorax', PATH)
        self.m = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.m)
        self.points = {'IJ': [0, -0.1, 1.5], 'C7': [0, 0.1, 1.5],
                       'PX': [0, -0.1, 1.2], 'T8': [0, 0.1, 1.2]}

    def test_aligned_hgpt_basis_and_signed_coordinate_mapping(self):
        origin, R = self.m.thorax_frame(self.points)
        np.testing.assert_allclose(origin, [0, -0.1, 1.5])
        np.testing.assert_allclose(R, [[0, 0, -1], [-1, 0, 0], [0, 1, 0]])
        # Source X anterior, Y superior, Z anatomical right: all in metres.
        np.testing.assert_allclose(self.m.map_source_point(origin, R, [0.02, -0.03, 0.04]),
                                   [-0.04, -0.12, 1.47])

    def test_tilt_translation_and_scale_covariance(self):
        Q = np.array([[1, 0, 0], [0, 0.8, -0.6], [0, 0.6, 0.8]])
        shift = np.array([0.1, 0.2, -0.3])
        origin, R = self.m.thorax_frame(self.points)
        p = np.array([0.02, -0.03, 0.04])
        for scale in (0.001, 1, 1000):
            pts = {k: scale * (Q @ np.array(v) + shift) for k, v in self.points.items()}
            o, F = self.m.thorax_frame(pts)
            np.testing.assert_allclose(F, Q @ R, atol=1e-12)
            np.testing.assert_allclose(self.m.map_source_point(o, F, scale*p),
                                       scale*(Q @ (origin + R@p) + shift), atol=1e-12)

    def test_non_aligned_model_frame_transfers_under_rigid_motion(self):
        # Coordinates from the original Seth archive, not HGPT target anatomy.
        model = {'IJ': [0., 0., 0.], 'C7': [-.0899063, .0327569, 0.],
                 'PX': [.0697635, -.164311, 0.], 'T8': [-.111155, -.154433, 0.]}
        point = np.array([.006325, .00693, .025465])
        Q = np.array([[0., 0., -1.], [-1., 0., 0.], [0., 1., 0.]])
        shift = np.array([.1, -.2, 1.3])
        target = {k: Q @ np.array(v) + shift for k, v in model.items()}
        mapped = self.m.map_between_thorax_frames(model, target, point)
        np.testing.assert_allclose(mapped, Q @ point + shift, atol=1e-12)
        # Direct use of model XYZ as ISB coordinates must not silently pass.
        origin, frame = self.m.thorax_frame(target)
        naive = self.m.map_source_point(origin, frame, point)
        self.assertGreater(np.linalg.norm(naive - mapped), .001)
        self.assertAlmostEqual(np.linalg.norm(mapped - shift), np.linalg.norm(point))

    def test_frame_transfer_uses_source_origin_and_rejects_bad_inputs(self):
        source = {k: np.array(v) + [1., 2., 3.] for k, v in self.points.items()}
        point = np.array([1.02, 1.87, 4.47])
        mapped = self.m.map_between_thorax_frames(source, self.points, point)
        np.testing.assert_allclose(mapped, [.02, -.13, 1.47], atol=1e-12)
        with self.assertRaises(ValueError):
            self.m.map_between_thorax_frames(source, self.points, [0., float('nan'), 0.])
        with self.assertRaises(ValueError):
            self.m.map_between_thorax_frames(dict(source, C7=source['IJ']), self.points, point)

    def test_invalid_landmarks_and_degenerate_planes_reject(self):
        for v in (None, [0, 1], [0, True, 1], [0, float('nan'), 1]):
            with self.subTest(value=v):
                pts = dict(self.points, IJ=v)
                with self.assertRaises(ValueError): self.m.thorax_frame(pts)
        for changed in ({'C7': self.points['IJ']},
                        {'PX': self.points['IJ'], 'T8': self.points['C7']},
                        {'C7': [0, -0.1, 1.6], 'T8': [0, -0.1, 1.3]}):
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError): self.m.thorax_frame(dict(self.points, **changed))
        pts = dict(self.points); del pts['T8']
        with self.assertRaises(ValueError): self.m.thorax_frame(pts)

    def test_improper_or_nonfinite_mapping_frames_reject(self):
        for R in (np.diag([-1, 1, 1]), np.diag([2, 1, 1]), np.zeros((3, 3)),
                  [[True, 0, 0], [0, 1, 0], [0, 0, 1]], np.full((3, 3), np.inf)):
            with self.subTest(frame=R):
                with self.assertRaises(ValueError): self.m.map_source_point([0, 0, 0], R, [0, 0, 0])


if __name__ == '__main__': unittest.main()
