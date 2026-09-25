from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import remote_state_sync  # noqa: E402


class RemoteStateSyncTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> tuple[Path, Path]:
        repo = root / "repo"
        work = repo / "HIGH_DETAIL_MESH_WORK"
        reports = work / "reports"
        checkpoints = work / "checkpoints" / "v15_manual"
        reports.mkdir(parents=True)
        checkpoints.mkdir(parents=True)
        (work / "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f.blend").write_bytes(b"blend")
        (checkpoints / "checkpoint_003.blend").write_bytes(b"blend")
        state = {
            "updated_utc": "2026-09-25T21:46:11+00:00",
            "route": "GPT_WORK",
            "v15f": {
                "version": "v15f_deep_hand_rebuild",
                "blend": r"C:\\Users\\PrivateName\\repo\\HIGH_DETAIL_MESH_WORK\\candidate.blend",
                "gates": {
                    "ring_L_proof": {"current": True, "pass": True, "path": r"C:\\secret\\proof.json"},
                    "ring_L_visual": {
                        "current": True,
                        "pass": False,
                        "decision": "FAIL",
                        "notes": "Visible proof still fails.",
                        "path": r"C:\\secret\\visual.json",
                    },
                },
                "next_action": "Repair ring_L only, then rerun AUDIT_V15F_RING_PROOF.bat",
                "reason": "The visual proof is marked FAIL.",
            },
            "budget": {"private_usage": "must-not-publish", "account_id": "acct_123"},
            "repository": {"branch": "work/test", "head": "abc123", "dirty": True},
            "next_file": r"C:\\Users\\PrivateName\\next.md",
        }
        (reports / "project_controller_state.json").write_text(json.dumps(state), encoding="utf-8")
        (reports / "project_controller.lock").write_text(json.dumps({"pid": 999999}), encoding="utf-8")
        (reports / "v15f_safe_runner_state.json").write_text(
            json.dumps({"state": "waiting", "last_action": state["v15f"]["next_action"]}), encoding="utf-8"
        )
        (reports / "v15f_ring_l_proof_gate.json").write_text("{}", encoding="utf-8")
        return repo, work

    def test_snapshot_is_sanitized_and_contains_required_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, work = self.make_fixture(Path(tmp))
            snapshot = remote_state_sync.collect_snapshot(repo, work, process_checker=lambda _pid: False)
            rendered = "\n".join(remote_state_sync.render_snapshot_files(snapshot, "2026-09-25T22:00:00Z").values())
            self.assertIn("controller state: stopped", rendered)
            self.assertIn("safe-runner state: waiting", rendered)
            self.assertIn("ring_L proof: PASS", rendered)
            self.assertIn("ring_L visual: FAIL", rendered)
            self.assertIn("Repair ring_L only", rendered)
            self.assertNotIn("C:\\\\Users", rendered)
            self.assertNotIn("PrivateName", rendered)
            self.assertNotIn("must-not-publish", rendered)
            self.assertNotIn("acct_123", rendered)

    def test_unchanged_snapshot_does_not_rewrite_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, work = self.make_fixture(Path(tmp))
            first = remote_state_sync.generate_snapshot(repo, work, process_checker=lambda _pid: False)
            status = work / "REMOTE_STATUS.md"
            before = status.read_bytes()
            second = remote_state_sync.generate_snapshot(repo, work, process_checker=lambda _pid: False)
            self.assertTrue(first)
            self.assertFalse(second)
            self.assertEqual(before, status.read_bytes())

    def test_meaningful_change_updates_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, work = self.make_fixture(Path(tmp))
            remote_state_sync.generate_snapshot(repo, work, process_checker=lambda _pid: False)
            state_path = work / "reports" / "project_controller_state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["v15f"]["next_action"] = "Run AUDIT_V15F_RING_PROOF.bat"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            self.assertTrue(remote_state_sync.generate_snapshot(repo, work, process_checker=lambda _pid: False))
            self.assertIn("Run AUDIT_V15F_RING_PROOF.bat", (work / "REMOTE_STATUS.md").read_text(encoding="utf-8"))

    def test_automatic_push_failure_is_nonfatal_and_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, work = self.make_fixture(Path(tmp))
            result = remote_state_sync.handle_push_result(
                subprocess.CompletedProcess(["git", "push"], 1, "", "network unavailable"),
                automatic=True,
                reports=work / "reports",
            )
            self.assertEqual(0, result)
            self.assertIn("network unavailable", (work / "reports" / "project_state_sync.log").read_text(encoding="utf-8"))

    def test_sanitizer_removes_windows_and_unc_paths_with_spaces(self):
        text = remote_state_sync.sanitise_text(
            r"Open C:\Users\Jane Doe\private\asset.blend or \\server\private share\audit.json, "
            r"C:/Users/Jane Doe/private/other.blend, and /home/jane/private/audit.json, then retry"
        )
        self.assertNotIn("Jane Doe", text)
        self.assertNotIn("server", text)
        self.assertNotIn("private share", text)
        self.assertNotIn("/home/jane", text)
        self.assertNotIn("C:/Users", text)
        self.assertIn("[local file]", text)

    def test_stale_visual_verdict_is_not_reported_as_pass(self):
        numeric, visual = remote_state_sync.gate_lines({
            "gates": {
                "ring_L_visual": {
                    "exists": True,
                    "current": False,
                    "pass": None,
                    "decision": "PASS",
                    "notes": "Old verdict",
                }
            }
        })
        self.assertEqual("none", numeric)
        self.assertEqual("ring_L visual: STALE", visual)

    def test_project_head_ignores_snapshot_only_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            implementation = repo / "implementation.txt"
            implementation.write_text("implementation", encoding="utf-8")
            subprocess.run(["git", "add", "implementation.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "implementation"], cwd=repo, check=True)
            expected = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, text=True, stdout=subprocess.PIPE
            ).stdout.strip()
            status = repo / "HIGH_DETAIL_MESH_WORK" / "REMOTE_STATUS.md"
            status.parent.mkdir()
            for index in range(25):
                status.write_text(f"status {index}", encoding="utf-8")
                subprocess.run(["git", "add", str(status.relative_to(repo))], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-q", "-m", "chore: publish sanitized project state"], cwd=repo, check=True
                )
            self.assertEqual(expected, remote_state_sync.project_head(repo))

    def test_matching_state_repairs_edited_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, work = self.make_fixture(Path(tmp))
            remote_state_sync.generate_snapshot(repo, work, process_checker=lambda _pid: False)
            status = work / "REMOTE_STATUS.md"
            status.write_text("PRIVATE TAMPER", encoding="utf-8")
            self.assertTrue(remote_state_sync.generate_snapshot(repo, work, process_checker=lambda _pid: False))
            self.assertNotIn("PRIVATE TAMPER", status.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
