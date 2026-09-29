"""Audit the ORIGINAL v1 O2 authoring provenance boundary in Blender."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from original_v1_authoring_boundary import inspect_boundary

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "original_v1_authoring_boundary_audit.json"

args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
require_guarded = "--require-guarded" in args
blockers = inspect_boundary(require_guarded=require_guarded)
result = {
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "pass": not blockers,
    "require_guarded": require_guarded,
    "blocker_count": len(blockers),
    "blockers": blockers,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
sys.exit(0 if result["pass"] else 1)
