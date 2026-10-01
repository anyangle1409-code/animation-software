"""Review package indexes only verified existing real review artifacts."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

import original_v1_review_package as p


class ReviewPackageTests(unittest.TestCase):
    def fixture(self,root):
        sha="a"*64
        ledger={"candidates":[{"revision":"r30","sha256":sha,"classification":"EXPERIMENTAL",
                              "state":"experimental","owner_review":"pending"}]}
        (root/p.CAND).mkdir(parents=True)
        (root/"ORIGINAL_V1_CANDIDATE_LEDGER.json").write_text(json.dumps(ledger))
        return sha

    def test_no_capture_is_explicit_not_error(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root)
            data=p.build_package(root,"r30")
            self.assertEqual(data["status"],"NO_REVIEW_CAPTURE_YET")
            self.assertEqual(data["image_count"],0)

    def test_verified_review_is_indexed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);sha=self.fixture(root)
            folder=root/p.CAND/"review/milestone_r30";folder.mkdir(parents=True)
            image=folder/"real.png";image.write_bytes(b"real fixture render")
            man={"candidate_revision":"r30","candidate_sha256":sha,"owner_review":"pending","blocking":False,
                 "files":[{"output":image.relative_to(root).as_posix(),"sha256":p.digest(image),
                           "pose":"neutral","view":"front","capture":{"protocol":"fixture"}}]}
            (folder/"visual_review_manifest.json").write_text(json.dumps(man))
            data=p.build_package(root,"r30")
            self.assertEqual(data["status"],"REVIEW_PACKAGE_READY")
            self.assertEqual(data["image_count"],1)
            self.assertFalse(data["production_approved"])

    def test_tampered_review_image_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);sha=self.fixture(root)
            folder=root/p.CAND/"review/visual_r30";folder.mkdir(parents=True)
            image=folder/"real.png";image.write_bytes(b"changed")
            man={"candidate_revision":"r30","candidate_sha256":sha,"owner_review":"pending","blocking":False,
                 "files":[{"output":image.relative_to(root).as_posix(),"sha256":"b"*64,"capture":{}}]}
            (folder/"visual_review_manifest.json").write_text(json.dumps(man))
            with self.assertRaisesRegex(ValueError,"hash/path"):p.build_package(root,"r30")


if __name__=="__main__":
    unittest.main()
