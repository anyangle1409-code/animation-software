"""List V15 attempts and optionally start the next unused version."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PATTERN = re.compile(r"v15([a-z])_deep_hand_rebuild$", re.I)

def versions_present():
    found = set()
    for path in ROOT.glob("HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15*_deep_hand_rebuild*"):
        name = path.name
        prefix = "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_"
        if not name.startswith(prefix):
            continue
        stem = name[len(prefix):]
        for suffix in ("_BARE.glb", "_EXPORT.blend", ".blend", ".glb"):
            if stem.endswith(suffix):
                stem = stem[:-len(suffix)]
                break
        if PATTERN.fullmatch(stem):
            found.add(stem)
    for path in REPORTS.glob("v15*_deep_hand_rebuild_frozen_pipeline_status.json"):
        stem = path.name[:-len("_frozen_pipeline_status.json")]
        if PATTERN.fullmatch(stem):
            found.add(stem)
    return sorted(found)

def read_json(path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None

def status(version):
    blend = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend"
    glb = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb"
    bare = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}_BARE.glb"
    frozen = read_json(REPORTS / f"{version}_frozen_pipeline_status.json")
    visual = read_json(REPORTS / f"{version}_visual_change_metrics.json")
    integration = read_json(REPORTS / f"current_source_{version}" / "integration_report.json")
    return {
        "version": version,
        "blend": blend.is_file(),
        "dressed_glb": glb.is_file(),
        "bare_glb": bare.is_file(),
        "frozen_pass": bool(frozen and frozen.get("pass")),
        "clears_rejected_v14e_change": (
            visual.get("clearly_exceeds_rejected_v14e_change")
            if visual else None
        ),
        "latest_source_no_regression": (
            integration.get("integration_no_regression")
            if integration else None
        ),
        "latest_source_head": integration.get("source_head") if integration else None,
        "report": str(ROOT / f"V15_POST_EDIT_REPORT_{version}.md")
            if (ROOT / f"V15_POST_EDIT_REPORT_{version}.md").is_file() else None,
    }

def next_version():
    used = set(versions_present())
    for code in range(ord("a"), ord("z") + 1):
        version = f"v15{chr(code)}_deep_hand_rebuild"
        if version not in used:
            return version
    raise SystemExit("No unused V15 letter remains from a-z.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--next", action="store_true", help="Start the next unused V15 attempt")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = [status(v) for v in versions_present()]
    if args.json:
        print(json.dumps({"attempts": rows, "next": next_version()}, indent=2))
    else:
        print("V15 attempts:")
        if not rows:
            print("  none")
        for row in rows:
            print(
                f"  {row['version']}: "
                f"blend={'Y' if row['blend'] else 'N'} "
                f"glb={'Y' if row['dressed_glb'] else 'N'} "
                f"frozen={row['frozen_pass']} "
                f"visual>{'V14e' if row['clears_rejected_v14e_change'] else 'not-yet/NO'} "
                f"latest={row['latest_source_no_regression']}"
            )
        print("Next unused:", next_version())

    if args.next:
        version = next_version()
        print("Starting fresh candidate from V13e:", version)
        subprocess.run([
            sys.executable, ROOT / "scripts" / "start_v15_hand.py",
            "--version", version,
        ], cwd=ROOT, check=True)

if __name__ == "__main__":
    main()
