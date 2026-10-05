"""Tests for critical ORIGINAL-v1 operator runner-link audit."""
import importlib.util,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_operator_runner_links.py")
S=importlib.util.spec_from_file_location("operator_links",P)
mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class OperatorRunnerLinkTests(unittest.TestCase):
    def test_live_operator_links_resolve(self):
        out=mod.validate(mod.ROOT)
        self.assertEqual(out["status"],"PASS")
        self.assertEqual(out["critical_operator_files"],len(mod.CRITICAL))

    def test_missing_nested_runner_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"scripts").mkdir()
            old=mod.CRITICAL; mod.CRITICAL=["RUN_TEST.bat"]
            try:
                (root/"RUN_TEST.bat").write_text("call RUN_MISSING.bat\n",encoding="utf-8")
                with self.assertRaisesRegex(ValueError,"operator link targets missing"):
                    mod.validate(root)
            finally:
                mod.CRITICAL=old

    def test_missing_python_script_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"scripts").mkdir()
            old=mod.CRITICAL; mod.CRITICAL=["RUN_TEST.bat"]
            try:
                (root/"RUN_TEST.bat").write_text("python scripts\\missing.py\n",encoding="utf-8")
                with self.assertRaisesRegex(ValueError,"operator link targets missing"):
                    mod.validate(root)
            finally:
                mod.CRITICAL=old

if __name__=="__main__": unittest.main()
