import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = ROOT / "ORIGINAL_V1_WORK/anatomy/rib_demographic_model_holcombe2017_v1.json"
MODULE = ROOT / "scripts/anatomy_fit/rib_demographic_model.py"


def load_module():
    spec = importlib.util.spec_from_file_location("rib_demographic_model", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RibDemographicModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads(MODEL.read_text())
        cls.mod = load_module()

    def test_all_12_levels_and_all_9_parameters_are_present(self):
        self.assertEqual(set(self.m["levels"]), {str(i) for i in range(1, 13)})
        expected = {"Sx", "Xpk", "Ypk", "phi_pia", "Bp", "Bd", "alpha_PH", "alpha_LS", "alpha_BH"}
        self.assertEqual(set(self.m["scales"]), expected)
        for rib in self.m["levels"].values():
            self.assertEqual(set(rib["coefficients_raw"]), expected)

    def test_scale_interpretation_matches_published_rib6_examples(self):
        # Table A2: rib-6 Sx H coefficient is 562 with E-1 scaling,
        # i.e. 56.2 mm per metre = 0.562 mm per cm.
        raw = self.m["levels"]["6"]["coefficients_raw"]["Sx"]
        scale = self.m["scales"]["Sx"]
        self.assertAlmostEqual(raw[3] * scale[3] / 100.0, 0.562, places=9)
        # Female coding is 1; -102 with E-1 gives -10.2 mm vs matched male.
        self.assertAlmostEqual(raw[2] * scale[2], -10.2, places=9)

    def test_evaluator_uses_source_coding_and_is_linear(self):
        kwargs = dict(age_years=50, height_m=1.82, weight_kg=80)
        male = self.mod.predict_parameter(self.m, 6, "Sx", sex=0, **kwargs)
        female = self.mod.predict_parameter(self.m, 6, "Sx", sex=1, **kwargs)
        self.assertAlmostEqual(female - male, -10.2, places=9)
        taller = self.mod.predict_parameter(self.m, 6, "Sx", sex=0, age_years=50, height_m=1.83, weight_kg=80)
        self.assertAlmostEqual(taller - male, 0.562, places=9)

    def test_reference_demographic_is_intentionally_not_frozen(self):
        policy = self.m["HGPT_policy"]
        self.assertEqual(policy["known_sex"], 0)
        self.assertAlmostEqual(policy["known_height_m"], 1.8200002908706665)
        self.assertEqual(policy["unresolved_inputs"], ["age_years", "weight_kg"])
        self.assertIn("NOT_YET_FROZEN", self.m["status"])

    def test_nonfinite_predictors_and_malformed_coefficients_fail_closed(self):
        import copy
        for field in ('age_years', 'height_m', 'weight_kg'):
            for value in (float('nan'), float('inf'), -float('inf')):
                kwargs=dict(age_years=40, sex=0, height_m=1.82, weight_kg=80)
                kwargs[field]=value
                with self.assertRaises(ValueError):
                    self.mod.predict_rib(self.m, 6, **kwargs)
        for replacement in ([1, 2], [0, 0, float('nan'), 0, 0]):
            bad=copy.deepcopy(self.m)
            bad['levels']['6']['coefficients_raw']['Sx']=replacement
            with self.assertRaises(ValueError):
                self.mod.predict_rib(bad, 6, age_years=40, sex=0, height_m=1.82, weight_kg=80)

    def test_invalid_inputs_fail(self):
        with self.assertRaises(ValueError):
            self.mod.predict_rib(self.m, 0, age_years=40, sex=0, height_m=1.82, weight_kg=80)
        with self.assertRaises(ValueError):
            self.mod.predict_rib(self.m, 6, age_years=17, sex=0, height_m=1.82, weight_kg=80)
        with self.assertRaises(ValueError):
            self.mod.predict_rib(self.m, 6, age_years=40, sex=2, height_m=1.82, weight_kg=80)


if __name__ == "__main__":
    unittest.main()
