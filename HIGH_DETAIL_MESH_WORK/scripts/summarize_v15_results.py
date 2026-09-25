"""Build one concise V15 post-edit report from generated validation artifacts."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v15a_deep_hand_rebuild"
REPORTS = ROOT / "reports"

def read(path):
    return json.loads(path.read_text()) if path.is_file() else None

audit = read(REPORTS / "audit_v15a_deep_hand_rebuild_blender.json")
pack = read(REPORTS / f"build_{VERSION}_glb.json")
floor = read(REPORTS / f"hand_floor_guard_HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.json")
if floor is None:
    # guard script names report from candidate stem
    floor = read(REPORTS / f"hand_floor_guard_HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{VERSION}.json")
integration = read(REPORTS / "current_source_v15" / "integration_report.json")
visual = read(REPORTS / f"{VERSION}_visual_change_metrics.json")
pipeline = read(REPORTS / f"{VERSION}_frozen_pipeline_status.json")
seams = read(REPORTS / "hand_seam_audit.json")
checkpoint = read(REPORTS / f"checkpoint_{VERSION}.json")

boards = [
    ROOT / f"renders_{VERSION}" / "V15A_V13E_OPEN_HAND_COMPARISON.jpg",
    ROOT / f"renders_{VERSION}" / "V15A_V13E_CLOSED_FIST_COMPARISON.jpg",
    ROOT / f"renders_{VERSION}" / "V15A_V13E_EXERCISE_HAND_COMPARISON.jpg",
]

technical = {
    "blender_invariants": bool(audit and audit.get("pass")),
    "protected_floor_guard": bool(floor and floor.get("protected_floor_guard_unchanged")),
    "frozen_614033b_pipeline": bool(pipeline and pipeline.get("pass")),
    "latest_source_no_regression": bool(integration and integration.get("integration_no_regression")),
    "matched_boards_present": all(x.is_file() for x in boards),
}

seam_note = "not available"
if seams and "v13e_fingertip_retopology" in seams and VERSION in seams:
    b = seams["v13e_fingertip_retopology"]
    c = seams[VERSION]
    seam_note = (
        f"V13e -> V15: fingertip hole edges {b.get('fingertip_hole_edges')} -> "
        f"{c.get('fingertip_hole_edges')}; folds >100deg "
        f"{b.get('folds_over_100deg')} -> {c.get('folds_over_100deg')}."
    )

blocked = [k for k, v in technical.items() if not v]
if blocked:
    state = "BLOCKED"
elif visual and not visual.get("change_signal_present", False):
    state = "TECHNICALLY CLEAN, BUT VISUAL CHANGE LOOKS MARGINAL"
else:
    state = "TECHNICALLY CLEAN — VISUAL ANATOMY REVIEW STILL REQUIRED"

lines = [
    "# V15a post-edit summary",
    "",
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
    "## Visual-change heuristic",
    f"- Change signal present: {visual.get('change_signal_present') if visual else 'missing'}",
    f"- Median changed subject pixels: {visual.get('primary_changed_subject_median_pct') if visual else '—'}%",
    f"- Max silhouette XOR: {visual.get('primary_silhouette_xor_max_pct') if visual else '—'}%",
    "- This heuristic does not approve anatomy. Inspect the three matched V13e/V15 boards.",
    "",
    "## Current-source integration",
    f"- Source HEAD tested: {integration.get('source_head') if integration else 'missing'}",
    f"- New failing gate files vs V13e: {integration.get('new_failing_gate_files_vs_v13e') if integration else '—'}",
    f"- V13e/V15 body measurements unchanged within 0.05 mm: {integration.get('body_measurements_unchanged_within_0_05mm') if integration else '—'}",
    "",
    "## Decision rule",
    "- Do not refit grips unless the matched boards show a clear anatomical improvement over V13e.",
    "- Do not promote automatically.",
]
if checkpoint:
    lines += [
        "",
        "## Artifact hashes",
        f"- Dressed: {checkpoint['artifacts']['dressed_glb']['sha256']}",
        f"- Bare: {checkpoint['artifacts']['bare_glb']['sha256']}",
        f"- Blend: {checkpoint['artifacts']['blend']['sha256']}",
    ]

out = ROOT / "V15_POST_EDIT_REPORT.md"
out.write_text("\n".join(lines) + "\n")
print(out.read_text())
