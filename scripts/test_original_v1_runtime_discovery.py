"""Runtime discovery stays read-only, source-bound and fail-closed."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import original_v1_runtime_discovery as d


class RuntimeDiscoveryTests(unittest.TestCase):
    def contract(self):
        return json.loads((d.ROOT / d.CONTRACT).read_text(encoding="utf-8"))

    def runtime_fixture(self, root: Path, contract: dict):
        spec = json.loads((d.ROOT / d.CONTACT_SPEC).read_text(encoding="utf-8"))
        for rel in spec["sources"]:
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(d.ROOT / rel, dst)
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs/CURRENT_HANDOFF.md").write_text(
            "# Current handoff\nLatest fully verified implementation checkpoint:\n"
            "`27ac3697d47bbcf32c9e94e674707f8e4b1eb5c3`\n"
            "the accepted v3 humanoid remains the live canonicalSkeleton\n",
            encoding="utf-8",
        )
        model_rig=d.model_rig_state(d.ROOT)
        (root / "CANONICAL_V4_RUNTIME_CONTRACT.json").write_text(
            json.dumps({
                "mode":"v4_active",
                "rig_identity":model_rig["identity"],
                "rig_revision":model_rig["revision"],
                "rig_structure_sha256":model_rig["rig_structure_sha256"],
                "bone_count":model_rig["bone_count"],
            }) + "\n", encoding="utf-8"
        )
        skeleton = root / "src/rig/skeleton.ts"
        skeleton.parent.mkdir(parents=True, exist_ok=True)
        skeleton.write_text(
            "import { HGPT_CANONICAL_V4_ORIGINAL_BONES } from './canonicalV4Original';\n"
            "class Skeleton { constructor(definitions: BoneDefinition[] = HGPT_CANONICAL_V4_ORIGINAL_BONES) {} }\n"
            "export const canonicalSkeleton = new Skeleton();\n",
            encoding="utf-8",
        )

    def test_prepared_snapshot_discovers_semantics_but_stays_blocked(self):
        contract = self.contract()
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp)
            self.runtime_fixture(runtime, contract)
            report = d.build_discovery(
                d.ROOT, runtime, contract, check_git=False, check_remote=False
            )
        self.assertTrue(report["contact_semantics"]["verified"])
        self.assertTrue(report["runtime_rig"]["v4_default_confirmed"])
        self.assertTrue(report["runtime_rig"]["rev2c_identity_confirmed"])
        self.assertEqual(report["model_rig"]["bone_count"],67)
        self.assertFalse(report["runtime_execution_permitted"])
        self.assertFalse(report["integration_ready"])
        self.assertIn("standalone verification", report["blockers"][0])

    def test_v4_active_without_rev2c_identity_stays_blocked(self):
        contract=self.contract()
        with tempfile.TemporaryDirectory() as temp:
            runtime=Path(temp)
            self.runtime_fixture(runtime,contract)
            (runtime/"CANONICAL_V4_RUNTIME_CONTRACT.json").write_text(json.dumps({"mode":"v4_active"})+"\n",encoding="utf-8")
            report=d.build_discovery(d.ROOT,runtime,contract,check_git=False,check_remote=False)
        self.assertFalse(report["runtime_rig"]["rev2c_identity_confirmed"])
        self.assertTrue(any("exact locked rev2c rig identity" in x for x in report["blockers"]))

    def test_v4_contract_source_mismatch_refused(self):
        contract = self.contract()
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp)
            self.runtime_fixture(runtime, contract)
            (runtime / "src/rig/skeleton.ts").write_text(
                "export const canonicalSkeleton = new Skeleton();\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "v4_active"):
                d.runtime_rig_state(runtime)

    def test_contact_semantic_drift_refused(self):
        contract = self.contract()
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp)
            self.runtime_fixture(runtime, contract)
            path = runtime / "src/equipment/attach.ts"
            body = path.read_text(encoding="utf-8")
            body = body.replace("attachment.mode === 'hand'", "attachment.mode === 'changed'", 1)
            path.write_text(body, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hand attachment resolver"):
                d.build_discovery(
                    d.ROOT, runtime, contract, check_git=False, check_remote=False
                )

    def test_new_runtime_head_has_unknown_ci(self):
        state = d.known_ci_snapshot(self.contract(), "f" * 40)
        self.assertFalse(state["head_matches_snapshot"])
        self.assertFalse(state["known_green"])
        self.assertEqual(state["status"], "UNKNOWN_FOR_NEW_HEAD")

    def test_source_byte_comparison_reports_divergence(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            left, right = Path(a), Path(b)
            (left / "x").write_text("one", encoding="utf-8")
            (right / "x").write_text("two", encoding="utf-8")
            row = d.compare_source_bytes(left, right, ["x"])[0]
            self.assertFalse(row["byte_identical"])
            self.assertNotEqual(row["model_sha256"], row["runtime_sha256"])

    def test_contract_cannot_claim_approval(self):
        contract = self.contract()
        contract["production_approved"] = True
        with tempfile.TemporaryDirectory() as temp:
            runtime = Path(temp)
            self.runtime_fixture(runtime, contract)
            with self.assertRaisesRegex(ValueError, "approval"):
                d.build_discovery(
                    d.ROOT, runtime, contract, check_git=False, check_remote=False
                )


if __name__ == "__main__":
    unittest.main()
