"""Tests for static human sweep visual-renderer source contract."""
import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_visual_renderer_source.py")
S=importlib.util.spec_from_file_location("visual_source",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)
class SweepVisualRendererSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=mod.SCRIPT.read_text(encoding="utf-8"); cls.cam=mod.read(mod.CAM); cls.plan=mod.read(mod.PLAN)
    def test_live_source_contract(self):
        out=mod.validate_source(self.text,self.cam,self.plan); self.assertEqual(out["cameras"],36)
    def test_save_operation_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"save operation"):
            mod.validate_source(self.text+"\nbpy.ops.wm.save_as_mainfile(filepath='bad.blend')",self.cam,self.plan)
    def test_missing_capture_token_fails(self):
        bad=self.text.replace("camera_matrix_world","BROKEN_CAMERA_MATRIX")
        with self.assertRaisesRegex(ValueError,"contract token missing"): mod.validate_source(bad,self.cam,self.plan)
if __name__=="__main__": unittest.main()
