# Pelvic CT Identification, Segmentation, and Landmark Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible, source-pinned workflow that accepts independent pelvic CT review evidence, constructs explicitly noncanonical candidate 3D mask summaries, and validates candidate bony landmarks without changing the Home Gym PT skeleton.

**Architecture:** Extend the existing NLM source-integrity and scanner-RAS utilities with three focused standard-library modules. An evidence validator binds human anatomical claims to exact source hashes; a segmentation validator turns sparse per-slice masks into bounded scanner-space candidate volumes only when slice geometry is contiguous; a landmark validator checks observations against those masks and emits pixel-cell/slice-slab uncertainty. Every output remains noncanonical and records unmet evidence gates.

**Tech Stack:** Python 3 standard library, `unittest`, JSON manifests, GitHub Actions.

**Spec:** `docs/NLM_ORIGINAL_CT_PELVIC_REGION_SCOUT_20261009.md` and `docs/CLAUDE_BLENDER_PELVIS_CT_LAPTOP_HANDOFF_20261009.md`

## Global Constraints

- The source skeleton always governs geometry; do not alter c004 or promote c005.
- Raw CT pixels, original headers, identifying fields, and packed CT Blender files must not be committed or redistributed.
- Every CT frame must match an independently pinned PNG SHA-256, header SHA-256, scanner position, pixel spacing, and slice thickness before it can support a claim.
- Stored PNG scalar values are not accepted as Hounsfield units and no intensity threshold is accepted as bone segmentation.
- Mixed scan groups, gaps, duplicate frames, non-axial geometry, and guessed filename-to-Z mappings fail closed.
- The donor is not a canonical 182 cm male and cannot set population anatomy targets.
- Pixel placement retains the existing unverified outer-FOV-corner assumption and full pixel-cell plus slice-slab uncertainty.
- No output may set `canonical_promotion_allowed` true or map scanner RAS into Home Gym PT world coordinates.
- No third-party runtime dependencies.

## Review Focus

- A review packet with correct frame numbers but altered SHA values must be rejected before its anatomical labels are read.
- Masks spanning the 42 mm gap between the two pinned triplets must be rejected rather than interpolated into one volume.
- Overlapping, duplicated, reversed, or out-of-bounds sparse mask runs must fail closed without allocating a full unbounded volume.
- A landmark outside its declared structure mask or on an unreviewed slice must remain `UNVERIFIED`.
- Conflicting reviewers or absent independent citations must not become accepted anatomy, even when the numerical point lies inside a mask.

---

### Task 1: Source-bound anatomical review packets

**Files:**
- Create: `scripts/anatomy_fit/nlm_ct_anatomical_review.py`
- Create: `scripts/test_nlm_ct_anatomical_review.py`

**Interfaces:**
- Consumes: pinned manifest schema `PINNED_NLM_SIX_ADJACENT_ORIGINAL_CT_FRAMES` and exact source records from `nlm_contiguous_pelvis_ct_windows.py`.
- Produces: `validate_review_packet(packet: dict, pinned_manifest: dict) -> dict` and `load_json_object(path: Path) -> dict`.

- [ ] **Step 1: Write failing tests for a minimal valid candidate review packet**

  Add `test_valid_packet_binds_candidate_label_to_exact_source_bytes`, asserting exact source/frame/hash retention, `anatomical_status == "CANDIDATE"`, `source_skeleton_governs_geometry is True`, and `canonical_promotion_allowed is False`. Add mutation tests for altered PNG/header SHA, unknown frame, duplicate observation ID, malformed row/column, empty citation URL, unsupported label, reviewer conflict, and any input promotion flag.

- [ ] **Step 2: Run the review tests and verify RED**

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_ct_anatomical_review.py' -v`

  Expected: import failure because `nlm_ct_anatomical_review` does not exist.

- [ ] **Step 3: Implement strict packet validation**

  Implement a closed vocabulary for candidate osseous regions (`iliac_blade`, `sacrum`, `acetabulum_left`, `acetabulum_right`, `femoral_head_left`, `femoral_head_right`, `pubic_region`, `other`, `unverified`) and require unique observation IDs, exact pinned hashes, integer pixel indices, reviewer identity, confidence in `[0, 1]`, and at least one independent HTTPS anatomical citation. Treat labels as candidate evidence only and return unmet gates explicitly.

- [ ] **Step 4: Run the review tests and full existing CT suite**

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_ct_anatomical_review.py' -v`

  Expected: all review tests pass.

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_*ct*.py' -v`

  Expected: all existing and new CT tests pass.

- [ ] **Step 5: Commit**

  Commit: `Add source-bound NLM CT anatomical review packets`

### Task 2: Candidate 3D sparse-mask volume validation

**Files:**
- Create: `scripts/anatomy_fit/nlm_ct_candidate_segmentation.py`
- Create: `scripts/test_nlm_ct_candidate_segmentation.py`

**Interfaces:**
- Consumes: validated review result from Task 1; sparse mask rows shaped as `[row, first_col, last_col]`; scanner records for exactly one contiguous physical slice group.
- Produces: `validate_candidate_segmentation(packet: dict, review_result: dict, scanner_by_source: dict) -> dict`, including validated runs, component counts, voxel/sample bounds, coverage gaps, and nonpromotion gates.

- [ ] **Step 1: Write failing tests for bounded sparse masks and one contiguous triplet**

  Add tests proving deterministic voxel count, 6-neighbour connected-component count, scanner-space bounds derived from `place_pixel`, and mandatory `coverage_complete is False`, `bone_surface_segmentation_verified is False`, and `canonical_promotion_allowed is False` for the current three-slice inputs. Add rejection tests for a 1749-to-1797 cross-gap volume, non-3 mm steps, mixed spacing, duplicate/reversed/overlapping runs, excessive run count, missing review observation, out-of-grid masks, and intensity-derived/HU claims.

- [ ] **Step 2: Run the segmentation tests and verify RED**

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_ct_candidate_segmentation.py' -v`

  Expected: import failure because `nlm_ct_candidate_segmentation` does not exist.

- [ ] **Step 3: Implement bounded mask validation and summary geometry**

  Validate runs without allocating arbitrary full volumes; cap slices, runs, and expanded voxels. Require exact 512x512 grids, one physical scanner group, strictly contiguous 3 mm centres, and source-reviewed structure labels. Expand only within the bounded cap to compute 6-neighbour components and cell-centre bounds using `nlm_ct_pixel_ras_envelope.place_pixel`. Do not derive masks from stored intensities and do not emit a canonical mesh.

- [ ] **Step 4: Run segmentation tests and the full CT suite**

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_ct_candidate_segmentation.py' -v`

  Expected: all segmentation tests pass.

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_*ct*.py' -v`

  Expected: all CT tests pass.

- [ ] **Step 5: Commit**

  Commit: `Add bounded candidate CT mask-volume validation`

### Task 3: Candidate bony landmark validation

**Files:**
- Create: `scripts/anatomy_fit/nlm_ct_landmark_validation.py`
- Create: `scripts/test_nlm_ct_landmark_validation.py`

**Interfaces:**
- Consumes: validated Task 1 observations, validated Task 2 mask summary, and per-slice safe scanner geometry.
- Produces: `validate_landmarks(packet: dict, review_result: dict, segmentation_result: dict, scanner_by_source: dict) -> dict`.

- [ ] **Step 1: Write failing tests for mask-supported landmarks and uncertainty**

  Add tests for ASIS, pubic-region, S1/endplate, acetabular, and femoral-head candidate semantics. Assert that a mask-supported point retains its exact pixel-cell corners, ±1.5 mm slab, source hashes, citations, reviewer IDs, and `validation_status == "CANDIDATE_SOURCE_OBSERVATION"`; because the pixel-centre convention and scanner-to-HGPT transform are unverified, it must never be `VERIFIED`. Add failures for wrong side/structure, absent mask voxel, unreviewed source slice, conflicting reviewer labels, missing citation, claimed submillimetre accuracy, and any Home Gym PT world coordinate.

- [ ] **Step 2: Run landmark tests and verify RED**

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_ct_landmark_validation.py' -v`

  Expected: import failure because `nlm_ct_landmark_validation` does not exist.

- [ ] **Step 3: Implement landmark validation**

  Match each landmark to one reviewed structure and one included segmentation voxel, call `place_pixel` for its physical envelope, retain all uncertainty flags, and report unmet independent-evidence gates. Reject exact-point, submillimetre, canonical, or world-frame claims.

- [ ] **Step 4: Run landmark tests and full CT suite**

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_ct_landmark_validation.py' -v`

  Expected: all landmark tests pass.

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_*ct*.py' -v`

  Expected: all CT tests pass.

- [ ] **Step 5: Commit**

  Commit: `Add noncanonical CT landmark validation gates`

### Task 4: End-to-end CLI, documentation, and CI

**Files:**
- Create: `scripts/anatomy_fit/nlm_ct_pelvis_workflow.py`
- Create: `scripts/test_nlm_ct_pelvis_workflow.py`
- Create: `docs/NLM_PELVIC_CT_IDENTIFICATION_SEGMENTATION_WORKFLOW_20261009.md`
- Modify: `.github/workflows/independent-pelvis-stl-intake.yml`

**Interfaces:**
- Consumes: Task 1 review packet, Task 2 mask packet, Task 3 landmark packet, pinned source manifest, and privacy-safe scanner geometry JSON.
- Produces: `run_workflow(inputs: dict) -> dict` plus a CLI that reads private local inputs, prints or exclusive-creates a noncanonical JSON report, and never copies source pixels.

- [ ] **Step 1: Write failing end-to-end and CLI tests**

  Add a synthetic happy-path test that executes all three stages and asserts `status == "CANDIDATE_EVIDENCE_ONLY"`, stage-specific evidence, explicit missing full-volume coverage, zero canonical promotions, and no raw pixel/header fields. Add tests for exclusive-create output, private path omission, stage failure propagation, malformed JSON, and refusal when a caller requests canonical output.

- [ ] **Step 2: Run workflow tests and verify RED**

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_ct_pelvis_workflow.py' -v`

  Expected: import failure because `nlm_ct_pelvis_workflow` does not exist.

- [ ] **Step 3: Implement the orchestrator and CLI**

  Compose the three validators without weakening their contracts. Keep inputs local, output only hashes/safe geometry/evidence statuses, and use exclusive-create mode for saved reports.

- [ ] **Step 4: Document the workflow and its evidence boundary**

  Document private input schemas, synthetic examples, exact commands, Blender handoff integration, the need for additional contiguous source ranges, and the rule that Claude/Codex agreement is evidence review rather than canonical approval.

- [ ] **Step 5: Add offline CI coverage while retaining live pin verification**

  Add all four new test files and implementation paths to the workflow trigger. Run the four new suites in `review-intake`; leave existing live NLM source jobs intact and ensure they still verify the six pinned source/header hashes.

- [ ] **Step 6: Run focused and inherited verification**

  Run: `python3 -m unittest discover -s scripts -p 'test_nlm_*ct*.py' -v`

  Expected: all CT workflow and inherited CT tests pass.

  Run the complete existing `review-intake` command list from `.github/workflows/independent-pelvis-stl-intake.yml`.

  Expected: all focused pelvis/trunk tests pass with no warnings or network requirement.

- [ ] **Step 7: Commit**

  Commit: `Wire candidate pelvic CT workflow into CI`
