"""Tests for authoritative human movement sweep camera plan."""
import copy,importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_camera_plan.py")
S=importlib.util.spec_from_file_location("cams",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)
class SweepCameraPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=mod.read(mod.CAM); cls.p=mod.read(mod.PLAN)
    def test_live_camera_plan_covers_all_required_views(self):
        out=mod.validate(self.c,self.p); self.assertEqual(out["cameras"],36)
    def test_missing_camera_fails(self):
        bad=copy.deepcopy(self.c); bad["cameras"].pop(next(iter(bad["cameras"])))
        with self.assertRaisesRegex(ValueError,"camera coverage differs"): mod.validate(bad,self.p)
    def test_non_bare_renderer_fails(self):
        bad=copy.deepcopy(self.c); bad["renderer"]["bare_body"]=False
        with self.assertRaisesRegex(ValueError,"renderer contract differs"): mod.validate(bad,self.p)
if __name__=="__main__": unittest.main()
