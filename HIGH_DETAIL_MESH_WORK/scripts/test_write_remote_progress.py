"""Focused behavioural test for the unattended progress heartbeat writer."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("write_remote_progress.py")
spec = importlib.util.spec_from_file_location("heartbeat", SCRIPT)
heartbeat = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(heartbeat)

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder)
    (root / "reports").mkdir()
    heartbeat.ROOT = root
    heartbeat.REPO = root
    heartbeat.OUT = root / "REMOTE_PROGRESS.md"
    base = [
        "write_remote_progress.py",
        "--status", "ACTIVE",
        "--task-start", "2026-09-27T10:00:00Z",
        "--operation-start", "2026-09-27T10:01:00Z",
        "--phase", "diagnosis",
        "--digit", "ring_L",
        "--attempt", "strategy 1",
        "--operation", "same long operation",
        "--completed", "preflight",
        "--checkpoint", "checkpoint_004.blend",
        "--numeric", "PASS",
        "--visual", "FAIL",
        "--last-successful-gate", "ring_L numeric PASS",
        "--blocker", "anchor buffer",
        "--report", "report.json",
        "--blender-state", "idle",
        "--next", "continue diagnosis",
        "--battery", "80",
        "--work-remaining", "50%",
    ]
    sys.argv = base
    assert heartbeat.main() == 0
    sys.argv = base
    assert heartbeat.main() == 0
    text = heartbeat.OUT.read_text(encoding="utf-8")
    assert "- Blender state: idle" in text
    assert "- last successful gate: ring_L numeric PASS" in text
    assert "- current unresolved blocker: anchor buffer" in text
    assert "- progress_counter: 2" in text
    assert "- possible_stall: true" in text
    assert "- current operation elapsed time:" in text

print("HEARTBEAT_TEST_PASS")
