# NLM pelvic CT candidate-evidence workflow

Date: 2026-10-09

This workflow records source-bound anatomical observations, bounded sparse-mask
volumes, and mask-supported candidate landmarks for the six pinned NLM normalCT
frames. It does **not** replace or reshape the source skeleton. Every result is
`CANDIDATE_EVIDENCE_ONLY`; canonical promotion remains prohibited.

## Evidence boundary

The pinned source manifest proves the identity of six original PNG files and
their paired scanner headers. It does not prove the anatomical level, CT HU
calibration, a complete pelvic volume, a bone surface, the pixel-centre
convention, or a scanner-to-Home-Gym-PT transform. The two reviewed windows are
only three 3 mm slices each, separated by 39 mm of unreviewed anatomy.

Claude/Codex agreement can review evidence and expose disagreements. It is not
independent anatomical evidence and cannot approve canonical geometry. A
qualified independent reviewer, fuller contiguous source coverage, and
validated coordinate transforms remain required.

## Private inputs

Keep the workflow bundle, original PNG files, scanner headers, windowed display
copies, and Blender files outside the repository. The JSON bundle contains:

- `pinned_manifest`: the committed six-frame pin manifest;
- `review_packet`: reviewer identity, an independent HTTPS citation, and
  observations tied to exact source IDs and PNG/header hashes;
- `segmentation_packet`: one manually authored sparse mask on exactly one
  contiguous triplet, with rows shaped as `[row, first_col, last_col]`;
- `landmark_packet`: candidate semantic, side, source pixel, review observation,
  and reviewer identity;
- `scanner_by_source`: privacy-filtered 512×512 plane geometry only;
- `canonical_output_requested`: always `false`.

Minimal sparse-mask slice example:

```json
{
  "source_id": 1749,
  "review_observation_id": "obs-1749-left-ilium",
  "runs": [[220, 100, 114], [221, 98, 116]]
}
```

Masks must come from manual review. Intensity-derived or claimed-HU masks are
refused. Inputs claiming complete coverage, a verified bone surface, exact or
submillimetre landmarks, Home Gym PT world coordinates, or canonical output are
also refused.

## Run locally

```text
python scripts/anatomy_fit/nlm_ct_pelvis_workflow.py --input D:\private\pelvis_ct\workflow.json
python scripts/anatomy_fit/nlm_ct_pelvis_workflow.py --input D:\private\pelvis_ct\workflow.json --out D:\private\pelvis_ct\candidate_report.json
```

Saved reports use exclusive-create mode and never overwrite an existing file.
They contain hashes, privacy-safe scanner geometry summaries, candidate labels,
uncertainty envelopes, citations, and unmet gates—never source pixels, raw
headers, or private paths.

Run the offline regression suite with:

```text
python -m unittest discover -s scripts -p "test_nlm_*ct*.py" -v
```

## Complete-series manifest gate

Before loading a larger private series into the anatomical review or Blender
stages, validate its privacy-safe manifest with:

```text
python scripts/anatomy_fit/pelvic_ct_series_manifest.py D:\private\pelvis_ct\series_manifest.json --out D:\private\pelvis_ct\series_geometry_report.json
```

The manifest gate requires exact image/header hashes, stable source IDs,
explicit scanner RAS coordinates, superior-to-inferior ordering, physically
continuous spacing, consistent grid/spacing/thickness/normal geometry, and a
declared scanner-space range. It rejects duplicates, gaps, reversals, mixed
geometry, ambiguous frames, incomplete declared ranges, exported patient
identifiers, committed source bytes, anatomical self-claims, and canonical
claims. A successful result proves source-series continuity only; it does not
prove that the series covers the complete bony pelvis.

## Blender review handoff

Use `ct_pelvis_window_geometry.py` to verify private source bytes and create
windowed display copies, then `ct_pelvis_review_scene_blender.py` to assemble the
review scene. Blender is a viewing and annotation surface only. Transfer a
reviewed pixel into this workflow by recording its exact source ID, source
hashes, row/column, candidate label, citation, and reviewer ID. The fixed
scanner-RAS-to-display rotation is not a Home Gym PT world transform.

The sparse three-slice mask summary may be visualised in Blender, but it is not
a watertight mesh or a verified bone surface. Do not export it as canonical
geometry.

## What is still needed

Acquire additional, independently verified contiguous original CT ranges for
the complete structure under review. Bilateral femoral-head centres,
acetabula, ASIS points, pubic region, and the S1 superior endplate generally
cannot all be established from the current two short windows. After coverage,
the project still needs independent landmark review, surface validation, and a
validated scanner-to-project registration before any separate canonical-change
proposal can be considered.
