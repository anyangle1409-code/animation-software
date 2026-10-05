"""Tests for package-specific diagnostic selection."""
import importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("original_v1_workspace_requires_diagnostic.py")
S=importlib.util.spec_from_file_location("requires_diag",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class WorkspaceDiagnosticSelectionTests(unittest.TestCase):
    def test_shoulder_package_is_selected(self):
        selected=mod.selected_packages(packages="RP-PEC-AX-002")
        self.assertTrue(selected & mod.PROFILES["shoulder_layer"]["packages"])

    def test_trunk_package_is_not_shoulder_diagnostic_scope(self):
        selected=mod.selected_packages(packages="RP-TRUNK-008")
        self.assertFalse(selected & mod.PROFILES["shoulder_layer"]["packages"])

    def test_unknown_package_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"unknown repair packages"):
            mod.selected_packages(packages="RP-NOT-REAL-999")

    def test_workspace_package_selection_is_read(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"workspace_manifest.json").write_text(json.dumps({
              "status":"PRE_EDIT_REPAIR_WORKSPACE",
              "repair_package_ids":["RP-FOOT-014"]
            }),encoding="utf-8")
            self.assertEqual(mod.selected_packages(workspace=str(root)),{"RP-FOOT-014"})

    def test_exactly_one_source_is_required(self):
        with self.assertRaisesRegex(ValueError,"exactly one"):
            mod.selected_packages()
        with self.assertRaisesRegex(ValueError,"exactly one"):
            mod.selected_packages(workspace="x",packages="RP-TRUNK-008")

if __name__=="__main__": unittest.main()
