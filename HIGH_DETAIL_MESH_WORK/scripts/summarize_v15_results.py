"""Build one concise post-edit report for a versioned V15 candidate."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "v15a_deep_hand_rebuild"
REPORTS = ROOT / "reports"

def read(path):
    return json.loads(path.read_text()) if path.is_file() else None

def label_for(version: str) -> str:
    m = re.match(r"v(\d+)([a-z]?)", version, re.I)
    if not m:
        return version.upper()
    return f"V{m.group(1)}{m.group(2)}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=DEFAULT_VERSION)
    args = ap.parse_args()
    version = args.version
    label = label_for(version)

    audit = read(REPORTS / f"audit_{version}_blender.json")
    v14_audit = read(REPORTS / "audit_v14e_finger_body_trial_blender.json")
    pack = read(REPORTS / f"build_{version}_glb.json")
    floor = read(REPORTS / f"hand_floor_guard_HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.json")
    integration = read(REPORTS / f"current_source_{version}" / "integration_report.json")
    visual = read(REPORTS / f"{version}_visual_change_metrics.json")
    pipeline = read(REPORTS / f"{version}_frozen_pipeline_status.json")
    seams = read(REPORTS / "hand_seam_audit.json")
    checkpoint = read(REPORTS / f"checkpoint_{version}.json")

    board_prefix = f"{label.upper()}_V13E"
    boards = [
        ROOT / f"renders_{version}" / f"{board_prefix}_OPEN_HAND_COMPARISON.jpg",
        ROOT / f"renders_{version}" / f"{board_prefix}_CLOSED_FIST_COMPARISON.jpg",
        ROOT / f"renders_{version}" / f"{board_prefix}_EXERCISE_HAND_COMPARISON.jpg",
    ]

    technical = {
        "blender_invariants": bool(audit and audit.get("pass")),
        "protected_floor_guard": bool(floor and floor.get("protected_floor_guard_unchanged")),
        "frozen_614033b_pipeline": bool(pipeline and pipeline.get("pass")),
        "latest_source_no_regression": bool(integration and integration.get("integration_no_regression")),
        "matched_boards_present": all(x.is_file() for x in boards),
    }

    seam_note = "not available"
    if seams and "v13e_fingertip_retopology" in seams and version in seams:
        b = seams["v13e_fingertip_retopology"]
        c = seams[version]
        seam_note = (
            f"V13e -> {label}: fingertip hole edges {b.get('fingertip_hole_edges')} -> "
            f"{c.get('fingertip_hole_edges')}; folds >100deg "
            f"{b.get('folds_over_100deg')} -> {c.get('folds_over_100deg')}."
        )

    blocked = [k for k, v in technical.items() if not v]
    if blocked:
        state = "BLOCKED"
    elif visual and not visual.get("clearly_exceeds_rejected_v14e_change", visual.get("change_signal_present", False)):
        state = "TECHNICALLY CLEAN, BUT VISUAL CHANGE DOES NOT CLEAR REJECTED V14e"
    else:
        state = "TECHNICALLY CLEAN — VISUAL ANATOMY REVIEW STILL REQUIRED"

    lines = [
        f"# {label} post-edit summary",
        "",
        f"**Candidate:** {version}",
        f"**State:** {state}",
        "",
        "## Automated gates",
    ]
    for key, value in technical.items():
        lines.append(f"- {'PASS' if value else 'FAIL/MISSING'} — {key.replace('_',' ')}")

    lines += [
        "",
        "## Geometry/export",
        f"- Blender invariant audit: {audit.get('candidate') if audit else 'missing'}",
        f"- Dressed GLB: {pack.get('candidate') if pack else 'missing'}",
        f"- Body vertices: {pack.get('body_vertices') if pack else '—'}",
        f"- Body triangles: {pack.get('body_triangles') if pack else '—'}",
        f"- New GLTF vertices: {pack.get('new_gltf_vertices') if pack else '—'}",
        f"- New-vertex max lost weight: {pack.get('new_vertex_max_lost_weight') if pack else '—'}",
        "",
        "## Hand topology",
        f"- {seam_note}",
        "",
        "## Visual-change calibration",
        f"- Clears rejected V14e change magnitude: {visual.get('clearly_exceeds_rejected_v14e_change') if visual else 'missing'}",
        f"- {label} median changed subject: {visual.get('v15_summary', {}).get('primary_changed_subject_median_pct') if visual else '—'}%",
        f"- Rejected V14e median changed subject: {visual.get('v14e_rejected_summary', {}).get('primary_changed_subject_median_pct') if visual else '—'}%",
        f"- {label} max silhouette XOR: {visual.get('v15_summary', {}).get('primary_silhouette_xor_max_pct') if visual else '—'}%",
        f"- Rejected V14e max silhouette XOR: {visual.get('v14e_rejected_summary', {}).get('primary_silhouette_xor_max_pct') if visual else '—'}%",
        "- This calibration does not approve anatomy. Inspect the three matched V13e/candidate boards.",
        "",
        "## Current-source integration",
        f"- Source HEAD tested: {integration.get('source_head') if integration else 'missing'}",
        f"- New failing gate files vs V13e: {integration.get('new_failing_gate_files_vs_v13e') if integration else '—'}",
        f"- Gate files with increased failures: {integration.get('gate_files_with_increased_failed_test_count') if integration else '—'}",
        f"- Body/equipment measurement coverage unchanged: {integration.get('measurement_coverage_unchanged') if integration else '—'}",
        f"- V13e/candidate body measurements unchanged within 0.05 mm: {integration.get('body_measurements_unchanged_within_0_05mm') if integration else '—'}",
        "",
        "## Decision rule",
        "- Do not refit grips unless the matched boards show a clear anatomical improvement over V13e.",
        "- Do not promote automatically.",
        "- If blocked, follow V15_FAILURE_RECOVERY.md from the first failed stage.",
    ]

    if checkpoint:
        lines += [
            "",
            "## Artifact hashes",
            f"- Dressed: {checkpoint['artifacts']['dressed_glb']['sha256']}",
            f"- Bare: {checkpoint['artifacts']['bare_glb']['sha256']}",
            f"- Blend: {checkpoint['artifacts']['blend']['sha256']}",
        ]

    out = ROOT / f"V15_POST_EDIT_REPORT_{version}.md"
    out.write_text("\n".join(lines) + "\n")
    if version == DEFAULT_VERSION:
        (ROOT / "V15_POST_EDIT_REPORT.md").write_text(out.read_text())
    print(out.read_text())

if __name__ == "__main__":
    main()
