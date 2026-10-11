# Actual Blender201source intensity tiles — candidate only

Courtesy of the U.S. National Library of Medicine.

Existing persisted201source mask reused; no new acquisition/calibration/threshold
tuning or named-bone seed. Actual nativeBlender5.2.1LTS, factory-startup,2threads,
build/save/reopen/render34.877s. Private scene contains21bounded unfiltered source
slabs1700..1709 through1900..1900, full512x512XY, <=10sources/tile. Each slab
stays below unchanged4000000source-sample/150000occupied-voxel helper budgets.
No production code or geometry promotion; other agents' work preserved.

Ruling: reuse existing bounded helper without increasing its geometry cap;
represent the finite201mask as21separate source-aligned diagnostic slabs.
Cost/limitation: **artificial closing faces exist at every slab boundary**.
These are diagnostic tiles, not complete bone surfaces or topology validation.
Do not weld, smooth, erase components or call a tile a bone; that would need
separate evidence and verified algorithms.

## Exact native verification and observation

- All320936selected intensity voxels retained across21tiles; no filtering/rank
  selection or anatomical names. Original201mask/report/header report pins checked.
- Every tile's sourceSrange, unchanged sourceXY and exposed six-neighbour face
  count checked before mesh construction. Coordinates retain scannerRASmm and
  explicit **unverified outer-edge pixel-origin assumption**. Unit display0.001m/mm.
- SavedBlend reopened:all21meshes,575126vertices/591852quads checked exactly
  against source-derived arrays; maximum vertexfloat difference0mm. No armatures.
  Closed anatomical, registration, pixel-centre, complete-coverage, naming and
  canonical gates checked; no source skeleton modification.
- One native768x768oblique preview actually viewed: broad bilateral curved
  shell-like intensity patterns and central complex, lower rounded/circular
  profiles and scattered separate fragments. This is qualitative pelvic-looking
  candidate evidence only. No independent named-bone/landmark acceptance, manifold
  assurance, complete endpoints or patient-to-HGPT registration follows from it.
- The fixedHU>=500threshold can miss low-density/cancellous structures and retain
  non-bone high intensities. Stair-step/porous profiles and slab caps stay visible;
  no claim that a pretty overall shape proves anatomical fidelity.

Readiness0READY/9PARTIAL/3BLOCKED; pelvic landmarks0/7; no canonical promotion.
201first reviews, raw calibration and mask comparisons already completed, not
repeated. Full regression remains non-green; targeted native checks do not cure it.

## Private files — do not upload medical/mesh bytes

Directory:
`C:/Users/Mark/Documents/Codex/hgpt-private-female-ct-candidate-1700-1900-20261011/full-intensity-native-tiles/`

`private_201_intensity_tiles.blend` SHA256:
`d970935549acc32162118cccc4d1913a56b45f66fb8e4b6412914aa951582fbc`.

`native_201_intensity_tiles.png` SHA256:
`32e154c888b210763e0a02e4e509d2e41bdcca3c134e78dd5ab7587475b39a85`.

`safe_native_tiles_report.json` records everytile range/count/endcut contact,
all verified counts and immutable source-mask pins; all bytes remain private.
Report SHA256: `77aeb5dfbb0b535d6aaefa5d1a1d29ce2f3560febb4b88bbbd608de2cac7db15`.
Private orchestration:
`C:/Users/Mark/Documents/Codex/hgpt-private-hip-plate-678c8c03/female_full_native_tiles.py`.
Generator refuses existing output directory. Reopen verified scene, do not regenerate.

## Claude/next task

Claude laptop can open this privateBlend, inspect the source-aligned intensity
tiles alongside the201source timeline, and record source-specific uncertainty.
Do not assign accepted bone labels or modify canonical skeleton geometry.

Next: inspect remaining master-plan regional evidence gaps before new source
work; source-specific full-resolution candidate contours/landmark prerequisites
are permissible, but qualified independent anatomical/landmark approval remains
separate. Never interpret intensity-component rank, slab closure or visual shape
as anatomy verification. Do not repeat completed201mask/native build.

Latest verified masterd57383014b226f5d8f7ee4e2d67296d90244eb92 all3CIchecks
PASS, run38100815073. Battery20% observed; no power/sleep settings changed.
