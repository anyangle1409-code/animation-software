"""Tests for generic Blender sweep runner static source contract."""
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_runner_source.py")
S=importlib.util.spec_from_file_location("runner_source",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class SweepRunnerSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=mod.RUNNER.read_text(encoding="utf-8")
        cls.spec=mod.read_json(mod.SPEC)

    def test_live_runner_source_contract(self):
        out=mod.validate_source(self.text,self.spec)
        self.assertEqual(out["sweeps"],11)

    def test_save_operation_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"forbidden save operation"):
            mod.validate_source(self.text+"\nbpy.ops.wm.save_as_mainfile(filepath='bad.blend')\n",self.spec)

    def test_missing_adapter_is_rejected(self):
        sid=next(iter(self.spec["sweeps"]))
        bad=self.text.replace(f'name=="{sid}"',f'name=="BROKEN_{sid}"')
        with self.assertRaisesRegex(ValueError,"missing sweep adapter"):
            mod.validate_source(bad,self.spec)

    def test_syntax_error_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"syntax invalid"):
            mod.validate_source(self.text+"\nif :\n",self.spec)

if __name__=="__main__": unittest.main()
