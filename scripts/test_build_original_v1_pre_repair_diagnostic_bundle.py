"""Tests for package-aware pre-repair diagnostic bundle builder."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest

P=Path(__file__).with_name("build_original_v1_pre_repair_diagnostic_bundle.py")
S=importlib.util.spec_from_file_location("pre_repair_bundle",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class PreRepairDiagnosticBundleTests(unittest.TestCase):
    def write(self,root,name,obj):
        p=root/name; p.write_text(json.dumps(obj),encoding="utf-8"); return p

    def fixture(self,root,packages):
        candidate=root/"candidate.blend"; candidate.write_bytes(b"candidate-fixture")
        sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
        selection=self.write(root,"selection.json",{
          "schema_version":1,"status":"PACKAGE_VALIDATION_SELECTION","production_approved":False,
          "repair_package_ids":packages,"validation_definition_complete":True,
          "uncovered_proof_movements":[],"proof_movement_families":["fixture_motion"],
          "pose_names":["neutral"],"sweep_only_movements_requiring_generic_runner":["fixture_motion"]
        })
        skin=self.write(root,"skin.json",{"candidate_sha256":sha,"armature_modifiers":[]})
        scope=self.write(root,"scope.json",{"candidate_sha256":sha,"status":"READ_ONLY_POSE_COUPLING_SCOPE","poses":{"neutral":{}}})
        plan=self.write(root,"plan.json",{"candidate_sha256":sha,"status":"POSE_CAPTURE_EVIDENCE_PLAN","poses":{"neutral":{}}})
        rev=self.write(root,"rev.json",{"candidate_sha256":sha,"overall_status":"CLEAN"})
        cont=self.write(root,"cont.json",{"candidate_sha256":sha})
        shoulder=self.write(root,"shoulder.json",{"candidate_sha256":sha})
        return candidate,selection,skin,scope,plan,rev,cont,shoulder

    def test_shoulder_package_requires_and_accepts_shoulder_diagnostic(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); args=self.fixture(root,["RP-PEC-AX-002"])
            out=mod.build(args[0],"x",["RP-PEC-AX-002"],args[1],args[2],args[3],args[4],args[5],args[6],args[7])
            self.assertTrue(out["package_specific_diagnostics"]["shoulder_layer_required"])
            self.assertIn("shoulder_layer_diagnostic",out["evidence_paths"])

    def test_shoulder_package_without_shoulder_diagnostic_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); args=self.fixture(root,["RP-PEC-AX-002"])
            with self.assertRaisesRegex(ValueError,"shoulder-layer diagnostic required"):
                mod.build(args[0],"x",["RP-PEC-AX-002"],args[1],args[2],args[3],args[4],args[5],args[6],None)

    def test_trunk_package_must_not_require_shoulder_diagnostic(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); args=self.fixture(root,["RP-TRUNK-008"])
            out=mod.build(args[0],"x",["RP-TRUNK-008"],args[1],args[2],args[3],args[4],args[5],args[6],None)
            self.assertFalse(out["package_specific_diagnostics"]["shoulder_layer_required"])
            self.assertEqual(out["summary"]["shoulder_layer_status"],"NOT_REQUIRED_FOR_SELECTED_PACKAGES")

    def test_wrong_candidate_sha_in_any_evidence_blocks_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); args=list(self.fixture(root,["RP-TRUNK-008"]))
            args[6].write_text(json.dumps({"candidate_sha256":"f"*64,"overall_status":"CLEAN"}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"candidate SHA mismatch"):
                mod.build(args[0],"x",["RP-TRUNK-008"],args[1],args[2],args[3],args[4],args[5],args[6],None)

    def test_selection_scope_mismatch_blocks_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); args=self.fixture(root,["RP-TRUNK-008"])
            with self.assertRaisesRegex(ValueError,"selection differs"):
                mod.build(args[0],"x",["RP-ARM-005"],args[1],args[2],args[3],args[4],args[5],args[6],None)

if __name__=="__main__": unittest.main()
