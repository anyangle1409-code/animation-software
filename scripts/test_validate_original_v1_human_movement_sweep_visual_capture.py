"""Tests for hashed candidate-bound human sweep visual capture manifests."""
import hashlib,importlib.util,json,tempfile
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_visual_capture.py")
S=importlib.util.spec_from_file_location("vis",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class SweepVisualCaptureTests(unittest.TestCase):
    def fixture(self,root,sweep="trunk_flexion"):
        plan=mod.read(mod.PLAN)["sweeps"][sweep]; csha="a"*64; samples=[]
        for label in plan["samples"]:
            views=[]
            for camera in plan["cameras"]:
                p=root/f"{label}_{camera}.png"; p.write_bytes(f"{label}|{camera}".encode())
                views.append({"camera_id":camera,"path":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                  "capture":{"candidate_sha256":csha,"sweep_id":sweep,"sample_label":label,"camera_id":camera,
                             "runner_script_sha256":"b"*64,"camera_matrix_world":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],
                             "resolution":[900,900,100]}})
            samples.append({"label":label,"views":views})
        return {"schema_version":1,"status":"HUMAN_MOVEMENT_SWEEP_VISUAL_CAPTURE","production_approved":False,
                "candidate_revision":"r96","candidate_sha256":csha,"sweep_id":sweep,"raw_sweep_report_path":"raw.json",
                "samples":samples,"engineering_review":"PASS","owner_review":"PENDING"}

    def test_complete_hashed_capture_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); out=mod.validate(self.fixture(root),root,True); self.assertEqual(out["engineering_review"],"PASS")

    def test_missing_camera_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root); d["samples"][0]["views"].pop()
            with self.assertRaisesRegex(ValueError,"camera coverage"): mod.validate(d,root,True)

    def test_changed_image_bytes_fail_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root); first=d["samples"][0]["views"][0]
            (root/first["path"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"SHA mismatch"): mod.validate(d,root,True)

    def test_capture_candidate_identity_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); d=self.fixture(root); d["samples"][0]["views"][0]["capture"]["candidate_sha256"]="c"*64
            with self.assertRaisesRegex(ValueError,"candidate identity mismatch"): mod.validate(d,root,True)

if __name__=="__main__": unittest.main()
