# Deterministic automated visual QA protocol

Stage 11 GPT preparation. This package prepares the first-party visual QA layer
without executing Phase 11, changing the model, changing the rig, editing poses,
activating assets or using any external vision model/reference image.

The current real Blender priority remains `RUN_ORIGINAL_V1_R30.bat`.

## Design boundary

Phase 11 uses two evidence layers:

1. the **actual source image** — immutable render/runtime evidence for human review;
2. a **derived binary mask** — machine-readable evidence bound to that exact image.

The source image remains the visual truth for owner review. The mask exists only
to make objective checks deterministic. Lighting, colour and material presentation
therefore cannot make a silhouette/crop detector silently pass.

Masks use portable grayscale PGM (`P5` or `P2`, 8-bit). Foreground is any
sample above zero. The parser in `scripts/original_v1_visual_qa.py` uses only the
Python standard library.

No third-party image package, external AI vision service, generated reference
image, stock character image or historical V-series render is required or allowed.

## Prepared first-party mask generation

For Blender/model-side source images, use the project-owned rasterization path in
`VISUAL_QA_MASK_CAPTURE_PROTOCOL.md`. It projects evaluated scene triangles through
the active camera and writes deterministic PGM masks with a z-buffer, without
Pillow/OpenCV/external segmentation or special material passes. It can produce
subject/body/garment/left-right hand/left-right foot/equipment masks and records
zero-pixel roles explicitly.

These Blender masks do not replace final runtime capture. Phase 11 runtime masks
must still bind the exact Phase 10 runtime commit, frame/time and final asset SHA.


## Capture manifest

`ORIGINAL_V1_VISUAL_QA_CAPTURE_TEMPLATE.json` is a template only. A real capture
must change `status` to `CAPTURE_EVIDENCE` and bind:

- exact candidate SHA-256;
- exact asset SHA-256;
- exact target runtime commit where applicable;
- immutable source image path/hash/dimensions;
- capture key, view, pose/exercise and exact frame/time;
- renderer/version;
- colour management;
- crop/framing;
- camera/scale/lighting;
- dressed state;
- every mask path/hash and its visibility/crop policy.

The mandatory `subject` mask represents the visible owned character silhouette.
Conditional masks may identify body, garment, hands, feet and equipment. A mask
provider that cannot supply one of those domains must omit it; the detector records
the unsupported domain as UNKNOWN elsewhere rather than fabricating evidence.

## Objective detectors

`scripts/original_v1_visual_qa.py` implements only checks with deterministic
meaning:

### Source integrity

Every source image and mask must exist and match its declared SHA-256. Mask
dimensions must equal declared source-image dimensions.

A hash mismatch is invalid evidence, not a visual regression.

### Crop and visibility

For each mask marked `expected_visible=true`:

- an empty mask is `FAIL_MISSING_VISIBLE_REGION`;
- if `allow_edge_touch=false`, any foreground pixel on the image edge is
  `FAIL_CROPPED`;
- close-ups may explicitly permit edge touch.

This lets future region-mask providers detect a lost hand, foot or equipment item
without converting subjective anatomy judgement into a numeric rule.

### Connected components

The tool records component count and largest-component ratio. This is a
measurement only. No production threshold is introduced at this preparation stage.

### Neutral horizontal symmetry

Where an actual neutral front/rear mask declares a symmetry axis, record:

- mirrored XOR ratio;
- left/right occupancy;
- side occupancy delta;
- silhouette centroid offset from the axis.

These are measurements, not automatic anatomy acceptance. Natural asymmetry,
camera alignment and deliberately asymmetric poses must not be collapsed into one
"quality score".

### Matched silhouette regression

A reference/current pair is quantitatively compared only when these fields match:

- source dimensions;
- capture key;
- view ID;
- pose/exercise;
- frame/time;
- renderer;
- colour management;
- crop;
- dressed state.

If any differs, the result is `CAPTURE_MISMATCH` and **no model-regression metric
is computed**.

Matched masks report:

- IoU;
- XOR ratio;
- occupancy delta;
- centroid shift in pixels;
- bounding-box edge deltas.

No universal pass threshold is created here. Future phase-specific tolerances must
be justified from actual owned captures and may not replace the R2 deformation
baseline or existing contact/deformation gates.

## What still requires other evidence

Visual-mask QA cannot establish:

- subjective anatomy quality;
- anatomy hidden by occlusion;
- real 3D physical contact;
- temporal smoothness from isolated still frames;
- material/presentation aesthetics.

Those remain UNKNOWN unless the corresponding Phase 9/10 numeric/runtime evidence
or owner review exists. A visual silhouette cannot override a failed 3D contact
measurement.

## Reference policy

References must be actual project-authored captures. Bind the reference manifest,
source image, mask, candidate/asset and runtime commit hashes.

A replacement reference is a **new versioned record**. Never overwrite an old
reference or silently move the baseline. A reference with owner review pending
remains experimental; it is not "accepted" merely because the detector can compare
against it.

Controlled synthetic/deliberately altered masks are allowed only under
`SYNTHETIC_TEST_FIXTURE_ONLY` for detector tests. They must never appear in
candidate review folders, reference inventories or production evidence.

## Coverage

`ORIGINAL_V1_VISUAL_QA_COVERAGE_PLAN.json` separates model visibility planning
from real-runtime evidence.

Model planning reuses the existing 57-view
`ORIGINAL_V1_VISUAL_BOARD_PLAN.json`:

- 5 neutral views;
- 2 views for each of 11 anatomy regions;
- 3 views for each of 10 stress/exercise poses.

That is useful for Blender camera/visibility QA only. It does not prove runtime
capture.

Future real-runtime QA covers the Phase 10 scenarios:

- dumbbell shoulder press;
- dumbbell bicep curl;
- pull-up;
- push-up;
- air squat;
- lunge;
- bent-over row.

For each, capture front/side/three-quarter evidence across real deterministic
runtime times representing start, outbound intermediate, peak/bottom, return
intermediate, end/loop close and turnaround neighbourhood. Exact numeric frame
times must come from the real Phase 10 runtime packet; Stage 11 does not invent
them.

## Command

After real capture manifests/masks exist:

```bat
RUN_ORIGINAL_V1_VISUAL_QA.bat <capture-manifest.json> [reference-manifest.json] [fresh-output.json]
```

The output remains `EVIDENCE_ONLY`, with
`owner_anatomy_acceptance_inferred=false`.

## Current execution boundary

Stage 11 is **PREPARED only**. There is currently no Phase 10-approved final asset
or exact green integration commit, so no real runtime visual QA execution is
claimed.

The prepared tools have standard-library fixture tests that deliberately exercise:

- edge cropping;
- missing visible regions;
- connected components;
- perfect and imperfect symmetry;
- matched silhouette changes;
- capture-setting mismatch;
- source-image hash drift;
- mask hash drift;
- false approval claims.

These fixtures prove detector behaviour only. They are not model evidence.

Phase 11 can exit only after real candidate/runtime source images and masks,
coverage/replay reports, detector limits and owner-facing overlays are bound to the
exact final candidate/runtime identities. Final anatomy acceptance remains an owner
decision, and Phase 12 alone controls production promotion.
