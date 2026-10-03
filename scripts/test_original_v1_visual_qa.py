"""Deterministic ORIGINAL-v1 visual QA detector fixtures."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import original_v1_visual_qa as q


def write_p2(path: Path, rows: list[str]) -> None:
    h = len(rows)
    w = len(rows[0])
    values = []
    for row in rows:
        if len(row) != w:
            raise ValueError("ragged fixture")
        values.extend("255" if ch == "#" else "0" for ch in row)
    path.write_text(f"P2\n{w} {h}\n255\n" + " ".join(values) + "\n", encoding="ascii")


def write_reference_inventory(root: Path, reference_path: Path, manifest: dict, *, owner_review="accepted") -> None:
    source=manifest["source_image"]
    masks={row["role"]:row["sha256"] for row in manifest["masks"]}
    inventory={
        "schema_version":1,
        "mode":"explicit_versioned_references_only",
        "status":"ACTIVE_REFERENCES",
        "production_approved":False,
        "phase_complete":False,
        "references":[{
            "id":"ref-v1",
            "owner_review":owner_review,
            "capture_manifest":{"path":reference_path.relative_to(root).as_posix(),"sha256":q.digest(reference_path)},
            "candidate_sha256":manifest["candidate_sha256"],
            "asset_sha256":manifest["asset_sha256"],
            "runtime_commit":manifest["target_runtime_commit"],
            "source_image_sha256":source["sha256"],
            "mask_sha256":masks,
        }],
    }
    (root/q.REFERENCE_INVENTORY).write_text(json.dumps(inventory),encoding="utf-8")


class VisualQaTests(unittest.TestCase):
    def contract(self):
        return json.loads((q.ROOT / q.CONTRACT).read_text(encoding="utf-8"))

    def fixture(self, root: Path, name: str, rows: list[str], *, capture_key="same", view="front", edge=False):
        source = root / f"{name}.png"
        source.write_bytes(("fixture-" + name).encode())
        mask = root / f"{name}_subject.pgm"
        write_p2(mask, rows)
        manifest = {
            "schema_version": 1,
            "status": "CAPTURE_EVIDENCE",
            "phase_complete": False,
            "production_approved": False,
            "candidate_sha256": "a" * 64,
            "asset_sha256": "b" * 64,
            "target_runtime_commit": "c" * 40,
            "source_image": {
                "path": source.name,
                "sha256": q.digest(source),
                "width": len(rows[0]),
                "height": len(rows),
            },
            "capture": {
                "capture_key": capture_key,
                "view_id": view,
                "pose_or_exercise": "neutral",
                "frame_or_time": 0,
                "renderer": "fixture",
                "colour_management": "fixture",
                "crop": "fixed",
                "dressed": False,
            },
            "masks": [{
                "role": "subject",
                "path": mask.name,
                "sha256": q.digest(mask),
                "expected_visible": True,
                "allow_edge_touch": edge,
                "symmetry_axis_x": (len(rows[0]) - 1) / 2,
            }],
        }
        man = root / f"{name}.json"
        man.write_text(json.dumps(manifest), encoding="utf-8")
        return man

    def test_crop_detector_flags_edge_touch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            man = self.fixture(root, "crop", ["#....","##...",".....",".....","....."])
            report = q.analyse(root, man, self.contract())
            self.assertEqual(report["mask_results"][0]["crop_visibility_status"], "FAIL_CROPPED")
            self.assertEqual(report["summary"]["crop_visibility_failures"], 1)

    def test_empty_expected_region_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            man = self.fixture(root, "empty", ["....."] * 5)
            report = q.analyse(root, man, self.contract())
            self.assertEqual(report["mask_results"][0]["crop_visibility_status"], "FAIL_MISSING_VISIBLE_REGION")

    def test_connected_components_and_symmetry_are_measured(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            man = self.fixture(root, "shape", [
                ".....",
                ".#.#.",
                ".###.",
                "..#..",
                ".....",
            ])
            report = q.analyse(root, man, self.contract())
            metrics = report["mask_results"][0]["metrics"]
            self.assertEqual(metrics["component_count"], 1)
            self.assertAlmostEqual(metrics["symmetry"]["mirrored_xor_ratio"], 0.0)
            self.assertFalse(report["summary"]["owner_anatomy_acceptance_inferred"])

    def test_asymmetry_is_measured_not_promoted_to_fail_or_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            man = self.fixture(root, "asym", [
                ".....",
                ".##..",
                ".###.",
                "..#..",
                ".....",
            ])
            report = q.analyse(root, man, self.contract())
            symmetry = report["mask_results"][0]["metrics"]["symmetry"]
            self.assertGreater(symmetry["mirrored_xor_ratio"], 0)
            self.assertEqual(report["mask_results"][0]["crop_visibility_status"], "PASS")

    def test_matched_reference_reports_iou_and_xor(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ref = self.fixture(root, "ref", [
                ".....",
                ".###.",
                ".###.",
                ".....",
                ".....",
            ])
            cur = self.fixture(root, "cur", [
                ".....",
                "..##.",
                "..##.",
                ".....",
                ".....",
            ])
            report = q.analyse(root, cur, self.contract(), ref)
            self.assertEqual(report["comparison"]["status"], "MEASURED")
            row = report["comparison"]["per_role"][0]["metrics"]
            self.assertLess(row["iou"], 1.0)
            self.assertGreater(row["xor_ratio"], 0.0)

    def test_capture_mismatch_is_separate_from_regression(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ref = self.fixture(root, "ref", [".....",".###.",".###.",".....","....."], capture_key="A")
            cur = self.fixture(root, "cur", [".....",".###.",".###.",".....","....."], capture_key="B")
            report = q.analyse(root, cur, self.contract(), ref)
            self.assertEqual(report["comparison"]["status"], "CAPTURE_MISMATCH")
            self.assertIn("capture_key", report["comparison"]["mismatched_fields"])
            self.assertEqual(report["comparison"]["per_role"], [])

    def test_reference_inventory_accepts_exact_owner_accepted_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            ref=self.fixture(root,"accepted",[".....",".###.",".###.",".....","....."])
            manifest=json.loads(ref.read_text())
            write_reference_inventory(root,ref,manifest)
            row=q.verify_reference_inventory(root,ref,manifest)
            self.assertEqual(row["id"],"ref-v1")

    def test_reference_inventory_rejects_unlisted_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            ref=self.fixture(root,"unlisted",[".....",".###.",".###.",".....","....."])
            (root/q.REFERENCE_INVENTORY).write_text(json.dumps({
                "schema_version":1,"mode":"explicit_versioned_references_only",
                "production_approved":False,"phase_complete":False,"references":[]
            }),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"not uniquely pinned"):
                q.verify_reference_inventory(root,ref,json.loads(ref.read_text()))

    def test_reference_inventory_rejects_pending_owner_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            ref=self.fixture(root,"pending",[".....",".###.",".###.",".....","....."])
            manifest=json.loads(ref.read_text())
            write_reference_inventory(root,ref,manifest,owner_review="pending")
            with self.assertRaisesRegex(ValueError,"not owner-accepted"):
                q.verify_reference_inventory(root,ref,manifest)

    def test_invalid_capture_asset_sha_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            man=self.fixture(root,"badsha",[".....",".###.",".###.",".....","....."])
            data=json.loads(man.read_text());data["asset_sha256"]="short";man.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"asset SHA-256 invalid"):
                q.analyse(root,man,self.contract())

    def test_mask_hash_drift_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            man = self.fixture(root, "drift", [".....",".###.",".###.",".....","....."])
            data = json.loads(man.read_text())
            (root / data["masks"][0]["path"]).write_text("P2\n1 1\n255\n0\n", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "mask bytes differ"):
                q.analyse(root, man, self.contract())

    def test_source_hash_drift_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            man = self.fixture(root, "source", [".....",".###.",".###.",".....","....."])
            data = json.loads(man.read_text())
            (root / data["source_image"]["path"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "source image bytes differ"):
                q.analyse(root, man, self.contract())

    def test_approval_claim_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            man = self.fixture(root, "approval", [".....",".###.",".###.",".....","....."])
            data = json.loads(man.read_text())
            data["production_approved"] = True
            man.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "approval"):
                q.analyse(root, man, self.contract())


if __name__ == "__main__":
    unittest.main()
