# Work continuation: independent pelvic CT evidence

Date: 2026-10-09

## Controlling state

- Repository: `anyangle1409-code/animation-software`
- Development branch: `codex/pelvic-ct-identification-segmentation-20261009`
- Draft PR branch: `codex/independent-pelvis-stl-intake-20261009`
- Evidence baseline before full-series work: `e606c05c` (after `191b9734`); always fetch the current branch head before continuing.
- Source skeleton remains the geometry authority.
- Downloaded source images, scanner headers, anatomical cross-sections, and Blender review files remain outside Git.
- Candidate evidence must remain separate from canonical assets. No canonical promotion is authorized without independent evidence.

## What is now verified

1. Seventy-two NLM Visible Human CT images and scanner headers were downloaded privately. They form two internally uniform 3 mm acquisition groups with a 2 mm slab overlap at the boundary; they must not be flattened into a single uniform stack. The original six pinned anchors match the larger bundle exactly.
2. A real Blender 5.2.1 review scene loaded all six source-bound slices without packing them or changing the source skeleton.
3. The sparse upper and lower windows do not cover the complete pelvis. The lower window supports only a tentative sacrum-region observation.
4. The deterministic workflow records three source-pinned observations, a 27-voxel connectivity probe, zero defensible landmarks, zero canonical promotions, and all unmet gates.
5. Empty landmark packets are now valid so the workflow preserves absence instead of pressuring a reviewer to invent a landmark.
6. Ten source-bound candidate observations now cover representative iliac, sacral, acetabular, femoral-head, and pubic-region planes while retaining every unmet independent-review and promotion gate.
7. The anatomical review suite has 13 tests, candidate segmentation has 14, scanner geometry and calibration parsing has 20, raw-to-PNG calibration has 6, and the complete-series, multi-group bundle, and Blender occupancy gates have 19. The full pull-request intake command set contains 362 tests.
8. Blender 5.2.1 privately revalidated all 72 source image/header pairs and produced a two-group, coarse 8-by-8-pixel stored-scalar occupancy scene. Its 13,273 blocks expose useful volume and boundary evidence, but also 8 components in the superior group and 3 in the inferior group. No automatic component filtering was applied. The committed summary is deliberately labelled as not segmentation; source images and Blender outputs remain private and untracked.
9. Every one of the 72 source scanner headers explicitly reports a `-1024` addend from stored pixel value to Hounsfield annotation value. All 18,874,368 PNG samples were then compared with the official decompressed GE files: every sample was identical in file order, with zero differences. The separate calibration packet verifies `HU = PNG_stored_value - 1024`; the existing stored threshold 1200 corresponds to 176 HU. The historical Blender report retains its original limited claim. Calibration alone does not validate that threshold as bone segmentation.

## Required next sequence

### 1. Establish a contiguous source volume

Acquire a lawful, source-verifiable CT series that covers the complete bony pelvis. Record a manifest before analysis with exact source URLs or identifiers, byte hashes, slice ordering, pixel spacing, slice thickness, orientation, and scanner-coordinate positions. Keep source bytes private and out of Git.

Stop if continuity, orientation, scale, provenance, or de-identification cannot be verified.

### 2. Verify source anatomy before segmentation

Use source-linked review observations to identify the ilia, sacrum, acetabula, pubic rami, ischia, and proximal femora. Require citations, reviewer identity, source-slice identity, and uncertainty. Same-donor cross-modality images may help interpretation but do not count as independent population evidence.

### 3. Produce candidate-only 3D segmentation

Build reproducible candidate masks and surfaces from the verified contiguous volume. Validate coverage, connectivity, laterality, surface closure, voxel-to-scanner transforms, and source bounds. Preserve the unmodified source skeleton and do not replace canonical mesh geometry.

The current Blender occupancy scene does not satisfy this step. Source-value calibration is now verified. Before generating an anatomical surface, justify the bone selection method, review component identities, and add fail-closed tests for source bounds and group-boundary preservation. Component size alone must not determine anatomical identity.

### 4. Validate landmarks honestly

Record only landmarks that the available images and segmentation defend. Empty landmark output is acceptable. Any landmark must retain exact source support, reviewer identity, uncertainty, coordinate frame, and an independent second review before it can influence registration.

### 5. Use Blender only as a review stage

Blender work is appropriate once a source-bound candidate surface exists: import it into an isolated review collection, preserve scale and transforms, overlay it against the immutable source skeleton, render diagnostic views, and export reproducible evidence. Do not rig, deform, retopologize into the canonical body, or promote a mesh merely because it looks plausible.

### 6. Keep promotion gates closed

Canonical promotion remains prohibited until there is complete source coverage, independently verified bone surfaces and landmarks, a validated patient-scanner-to-HGPT transform, and genuinely independent evidence beyond the same Visible Human donor. Tests and CI must fail closed on missing evidence.

## Immediate implementation task for Work

Extend the existing manifest and review tooling for a complete contiguous pelvic CT series using synthetic fixtures first. Add failing tests for discontinuities, duplicated or reversed slices, mixed geometry, missing hashes, frame ambiguity, partial coverage, and attempts to claim canonical status. Only after those tests pass should Work privately acquire and inspect real source bytes. Commit and push each evidence-safe checkpoint; never commit the medical image bytes or a Blender file containing them.

## Handoff validation

Before continuing, fetch all live branch heads and compare them with this checkpoint. Preserve and reconcile any newer Claude, Work, or Codex commits rather than overwriting or force-pushing them. At every handoff report the exact pushed head, tests run, CI state, private artifacts retained outside Git, and the next unmet evidence gate.

## Superseding checkpoint — 2026-10-10 boundary extension

Do not repeat the completed 72-slice acquisition/calibration or 135-image sweeps. A private ten-frame boundary extension gives 82 rows in two scanner-header-defined groups (43 + 39) with their 2 mm slab overlap intact, covering S=-324..-565 mm. For the ten additions, source `.Z`, decompressed GE payload, PNG and scanner-header hashes are pinned; 2,621,440 samples compare exactly, and every added header declares the same -1024 HU addend. Combined with the unchanged 72-slice calibration packet, all 21,495,808 samples across 82 images support `HU = PNG_stored_value - 1024`. Raw medical bytes remain private. This does not validate anatomical identity or a bone threshold.

The targeted series-manifest suite passes 20/20. It now binds each added raw digest and decompressed digest to the exact pinned PNG and header, verifies zero differences, and combines the sample totals with the frozen base packet. A broad indiscriminate scripts discovery is noisy and failed unrelated frozen-evidence CRLF and missing-fixture tests (1,215 run; 27 failures, 382 errors); use named CT/source suites and the dedicated GitHub workflow instead. For calibration commit `e96356664b74eb2fb0737a412788890e159c0304`, PR #15's CT-review/test, mesh-intake, and trunk-source CI runs `38079214169`, `38079214075`, and `38079214068` all passed.

Blender 5.2.1 LTS also produced a private 10-frame contact sheet using 8-bit p1–p99.8 stored-value display derivatives. Each PNG/header was verified against the bundle before loading; images remain external/unpacked. The sheet has arbitrary display-grid placement, zero landmarks, no anatomical labels, no segmentation, no skeleton overlay, and no Home Gym PT transform. Headless Eevee crashed inside Intel `igc64.dll`; the successful render used the Workbench engine. Private report, render and `.blend` are in `work/private-nlm-ct-20261009/blender-boundary-extension-review-retry1-20261010/`; render SHA-256 `3ba32011810311c4accbcf4715f78255eb5f0f144ed6dc0b99c1fb379117bec3`, Blend SHA-256 `134070c82752fbaa1091a268201e9e89ad6e1977afcb5b24681197352e7c4a7a`.

Next: have an independent reviewer navigate from the contact sheet to the original full-resolution private PNG and scanner header for any candidate observation, recording exact source/pixel coordinates, uncertainty, and independent citation. Keep laterality unresolved without a source cue. Then decide whether to build candidate-only segmentation and its coverage/topology tests. Do not repeat completed source acquisition or calibration, and do not promote anatomy, landmarks, source-to-skeleton transform, or canonical geometry from this display diagnostic.
