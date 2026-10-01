"""Contact source bridge stays source-bound and never implies runtime execution."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import original_v1_contact_source_bridge as b


class ContactSourceBridgeTests(unittest.TestCase):
    def spec(self):
        return json.loads((b.ROOT / b.SPEC).read_text(encoding="utf-8"))

    def test_current_repository_sources_verify(self):
        report = b.verify_bridge(b.ROOT, self.spec())
        self.assertEqual(report["status"], "EVIDENCE_ONLY")
        self.assertFalse(report["runtime_executed"])
        self.assertFalse(report["production_approved"])
        self.assertEqual(len(report["source_files"]), len(self.spec()["sources"]))
        self.assertTrue(all(len(x["sha256"]) == 64 for x in report["source_files"]))

    def test_bridge_cannot_claim_approval(self):
        spec = self.spec(); spec["production_approved"] = True
        with self.assertRaisesRegex(ValueError, "approval"):
            b.verify_bridge(b.ROOT, spec)

    def test_bridge_cannot_claim_phase_complete(self):
        spec = self.spec(); spec["phase_complete"] = True
        with self.assertRaisesRegex(ValueError, "approval"):
            b.verify_bridge(b.ROOT, spec)

    def test_duplicate_source_paths_refused(self):
        spec = self.spec(); spec["sources"].append(spec["sources"][0])
        with self.assertRaisesRegex(ValueError, "paths invalid"):
            b.verify_bridge(b.ROOT, spec)

    def test_missing_source_refused(self):
        spec = self.spec(); spec["sources"][0] = "src/exercises/definitions/does_not_exist.ts"
        with self.assertRaisesRegex(ValueError, "source missing"):
            b.verify_bridge(b.ROOT, spec)

    def test_push_endpoint_spec_drift_refused(self):
        spec = self.spec()
        spec["scenarios"]["push_up"]["root_endpoints"]["start"]["pitch_deg"] += 1
        with self.assertRaisesRegex(ValueError, "push top pitch differs"):
            b.verify_bridge(b.ROOT, spec)

    def test_pull_endpoint_spec_drift_refused(self):
        spec = self.spec()
        spec["scenarios"]["pull_up"]["root_endpoints"]["peak"]["y_m"] += 0.01
        with self.assertRaisesRegex(ValueError, "pull top y differs"):
            b.verify_bridge(b.ROOT, spec)

    def test_changed_hand_attachment_source_refused(self):
        spec = self.spec()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rel in spec["sources"]:
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(b.ROOT / rel, dst)
            path = root / "src/equipment/attach.ts"
            text = path.read_text(encoding="utf-8")
            text = text.replace("attachment.mode === 'hand'", "attachment.mode === 'changed'", 1)
            path.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hand attachment resolver"):
                b.verify_bridge(root, spec)


if __name__ == "__main__":
    unittest.main()
