# ORIGINAL v1 deterministic QA mask capture

Prepared tooling for model/Blender source captures. This does not substitute for
the exact Phase 10 runtime-frame masks required by final Phase 11 execution.

## Why this exists

The visual-QA detector consumes first-party PGM masks rather than deriving anatomy
from lighting/colour. This package creates those masks without Pillow/OpenCV,
external segmentation models or material-ID render tricks.

The implementation has two layers:

- `scripts/original_v1_mask_raster.py` — standard-Python z-buffer triangle
  rasterizer and PGM writer;
- `scripts/capture_original_v1_visual_qa_masks_blender.py` — read-only Blender
  adapter that projects the current evaluated scene through the active camera.

## Source-scene identity rule

The Blender scene must still be at the **same pose and camera state used for the
source PNG**.

The mask adapter checks source PNG dimensions against the current render dimensions
and records:

- candidate SHA;
- source PNG SHA/dimensions;
- camera transform/type/lens;
- render engine/dimensions;
- mask byte hashes;
- capture/rasterizer hashes;
- source git commit.

It never saves the Blend.

For posed captures, call the mask adapter immediately from the same Blender capture
session after the source image is written. Do not reopen an unrelated neutral scene
and bind its masks to a posed source image.

## Mask roles

The adapter always writes:

- `subject.pgm`
- `body.pgm`
- `hand_l.pgm`
- `hand_r.pgm`
- `foot_l.pgm`
- `foot_r.pgm`

For dressed capture it also writes:

- `garment.pgm`

When named mesh equipment objects are supplied it also writes:

- `equipment.pgm`

Zero-pixel roles are still written. That is deliberate: the downstream visibility
detector can flag an expected-visible hand/foot/equipment region instead of the
capture layer silently omitting it.

Hand/foot roles are derived from evaluated deform-group names. Body/garment and
equipment are separate depth-buffer labels. The closest projected evaluated
triangle controls visible-role pixels.

## First-party rasterizer

The standard-Python rasterizer:

- rasterizes triangle pixel centres;
- uses perspective reciprocal-depth interpolation;
- maintains a z-buffer;
- merges role labels at identical depth;
- writes binary 8-bit PGM without image libraries;
- refuses non-finite/behind-camera triangle inputs;
- refuses output overwrite.

CI fixture tests cover fill, occlusion, role merging, invalid depth and PGM output
collision.

## Known limit

Triangles crossing the camera near plane are omitted instead of geometrically
clipped. Normal project review cameras should keep the whole subject in front of
the near plane. This limit is explicit in every mask bundle and cannot be silently
relabelled as complete coverage if a review camera violates it.

## Phase 11 runtime boundary

These Blender masks are useful for:

- Phase 5 anatomy review captures;
- Phase 7 dressed review captures;
- Phase 8 presentation captures;
- model-side milestone regression checks.

They do **not** prove the actual runtime presentation.

For final Phase 11, the runtime capture provider must output the same PGM semantics
bound to:

- exact Phase 10 runtime commit;
- exact runtime frame/time;
- exact final asset SHA;
- exact source image/camera/view identity.

Only then should those masks be wrapped in the existing
`ORIGINAL_V1_VISUAL_QA_CAPTURE_TEMPLATE.json` contract and consumed by
`RUN_ORIGINAL_V1_VISUAL_QA.bat`.
