#!/usr/bin/env python3
"""Physical slice-to-region index and additional-range plan, from the pinned manifest only.

No image content is used.  Every region_status is UNVERIFIED.  Candidate gap-filling file ids
use the local hypothesis S = 1392 - index, which holds for the six pinned frames and MUST be
confirmed against each header (scripts/anatomy_fit/ct_pelvis_window_geometry.py validate/place)
before use.  --check regenerates and compares with the committed files.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ct_pelvis_window_geometry as geo  # noqa: E402

OFFSET = 1392            # hypothesis: scanner S (mm) = 1392 - file index, verified only for the 6 pins
CONTEXT_IDS = (1701, 1650, 1602)   # sparse context frames named in the PR #15 scout; S hypothesis only


def hypothesis_s(i):
    return float(OFFSET - i)


def build(manifest):
    pins = manifest["by_id"]
    for sid in geo.ALL_IDS:       # the hypothesis must reproduce every pin or the plan is void
        if abs(hypothesis_s(sid) - pins[sid]["scanner_S_mm"]) > 1e-9:
            raise ValueError("S = 1392 - index hypothesis does not reproduce the pins")
    gap = geo.window_gap_mm(manifest)
    bridge_ids = list(range(1758, 1795, 3))
    bridge_s = [hypothesis_s(i) for i in bridge_ids]
    return {
        "schema_version": 1,
        "kind": "PELVIC_CT_SLICE_TO_REGION_INDEX_AND_RANGE_PLAN",
        "region_status_for_all_rows": "UNVERIFIED",
        "image_review_performed": False,
        "canonical_promotion_allowed": False,
        "pinned_frames": geo.slice_index_rows(manifest),
        "windows": [
            {"window": "A", "source_ids": list(geo.TRIPLETS[0]), "scanner_S_extent_mm": [-364.5, -355.5],
             "physical_thickness_mm": 9.0},
            {"window": "B", "source_ids": list(geo.TRIPLETS[1]), "scanner_S_extent_mm": [-412.5, -403.5],
             "physical_thickness_mm": 9.0},
        ],
        "uncovered_gap_between_windows_mm": gap,
        "what_the_windows_can_support": (
            "Each window is 9 mm of axial section. Only in-plane observations at a single level are possible "
            "(for example an equatorial cross-section circle, if a reviewer finds one). Surfaces, sphere centres "
            "in S, endplate orientation and any length along S cannot be obtained, and nothing here is a 3D pelvis."),
        "region_assignment": "NONE: no image has been reviewed; no frame is assigned to an anatomical region",
        "additional_ranges_needed": {
            "S_equals_1392_minus_index_hypothesis": "verified only on the six pins; confirm on each new header before use",
            "tier_A_bridge_windows": {
                "purpose": "close the 39 mm gap so a reviewer can follow structures between windows A and B",
                "candidate_ids": bridge_ids, "hypothesised_S_mm": bridge_s, "frame_count": len(bridge_ids),
            },
            "tier_B_context_review": {
                "purpose": "find iliac crest, L4/L5 and sacral levels so contiguous runs can be sized from real levels",
                "candidate_ids": list(CONTEXT_IDS),
                "hypothesised_S_mm": [hypothesis_s(i) for i in CONTEXT_IDS],
                "note": "sparse context frames only; hypothesis-level coordinates until headers are checked",
            },
            "tier_C_contiguous_runs": {
                "rule": "after a reviewer names iliac-crest-top S and ischial-tuberosity/pubic-bottom S, size the run with "
                        "required_contiguous_range(levels, margin_mm=6) in ct_pelvis_window_geometry.py",
                "indicative_frame_counts_3mm": {
                    "whole_pelvis_surface_iliac_crest_to_ischium": "about 90-110 (pelvic height + ischium; sized from real levels)",
                    "each_acetabulum_and_head": "18-20 per side (about 53 mm)",
                    "S1_to_sacral_apex": "about 35-40",
                    "pubic_symphysis": "10-14",
                },
                "caveat": "indicative only; the exact ranges depend on levels a reviewer identifies",
            },
            "tier_D_caudal_extension": "extend toward the 1948 (S = -556 mm) fiducial named by the PR #15 scout, only after "
                                       "its header is checked",
        },
        "hard_constraints": [
            "raw PNG and header bytes stay private and untracked",
            "scanner RAS is not the Home Gym PT world frame",
            "source skeleton governs geometry",
        ],
    }


def render_md(d):
    L = ["# Physical slice-to-region index (pinned frames) and additional ranges needed", "",
         "All region statuses are **UNVERIFIED**; no image was reviewed in the cloud session.", "",
         "| Win | File | Scanner S (mm) | Slab S range (mm) | Pixel (mm) | Thick (mm) | PNG SHA-256 | Header SHA-256 | Region |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in d["pinned_frames"]:
        L.append(f"| {r['window']} | {r['png_filename']} | {r['scanner_S_mm']:g} | "
                 f"{r['slab_S_range_mm'][0]:g} to {r['slab_S_range_mm'][1]:g} | {r['pixel_spacing_mm']} | "
                 f"{r['slice_thickness_mm']:g} | `{r['png_sha256']}` | `{r['header_sha256']}` | {r['region_status']} |")
    L += ["", f"Uncovered gap between windows: **{d['uncovered_gap_between_windows_mm']:g} mm**.", "",
          d["what_the_windows_can_support"], "", "## Additional ranges needed", ""]
    a = d["additional_ranges_needed"]
    A, B = a["tier_A_bridge_windows"], a["tier_B_context_review"]
    L += [f"- Tier A bridge: {A['frame_count']} frames, candidate ids {A['candidate_ids'][0]}..{A['candidate_ids'][-1]} "
          f"(step 3), hypothesised S {A['hypothesised_S_mm'][0]:g}..{A['hypothesised_S_mm'][-1]:g} mm. {A['purpose']}.",
          f"- Tier B context: ids {', '.join(map(str, B['candidate_ids']))}, hypothesised S "
          f"{', '.join(f'{s:g}' for s in B['hypothesised_S_mm'])} mm. {B['purpose']}.",
          f"- Tier C runs: {a['tier_C_contiguous_runs']['rule']}. Indicative 3 mm frame counts: "
          + "; ".join(f"{k.replace('_', ' ')} {v}" for k, v in a["tier_C_contiguous_runs"]["indicative_frame_counts_3mm"].items()) + ".",
          f"- Tier D: {a['tier_D_caudal_extension']}.", "",
          "The id-to-S mapping S = 1392 - index is a hypothesis proven only for the six pinned frames; "
          "check each header before use."]
    return "\n".join(L)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--out-md", type=Path, required=True)
    p.add_argument("--check", action="store_true")
    a = p.parse_args(argv)
    d = build(geo.load_pinned_manifest(a.manifest))
    js, md = json.dumps(d, indent=2, sort_keys=True) + "\n", render_md(d) + "\n"
    if a.check:
        bad = [str(f) for f, t in ((a.out_json, js), (a.out_md, md)) if not f.exists() or f.read_text() != t]
        for f in bad:
            print(f"DRIFT: {f}", file=sys.stderr)
        return 1 if bad else 0
    for f, t in ((a.out_json, js), (a.out_md, md)):
        with open(f, "x", encoding="utf-8") as h:
            h.write(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
