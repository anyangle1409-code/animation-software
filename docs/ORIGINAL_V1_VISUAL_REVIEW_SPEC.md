# ORIGINAL v1 standard visual review protocol

REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Only actual candidate renders may
appear in review folders. Missing views stay explicitly missing. No AI images,
legacy model renders, old GLBs relabelled as a new revision, or fake previews.

## Capture identity

Every capture set records exact candidate Blend SHA, render-script SHA, pose
script identity, report SHA, Blender version, camera transform/orthographic scale,
resolution, lighting/shading and dressed state. A PNG hash alone proves image
identity, not candidate identity. Legacy renders lacking a source manifest may
be inspected as historical evidence but cannot become a new verified snapshot.

Keep front along the existing front camera direction; side follows the existing
side direction. Rear and 3/4 rear must be added by a versioned capture-only script
when those actual views are produced. Never modify exercise poses to get a
better picture. Use a pinned camera/scale/crop per pose and region for comparisons;
the existing auto-fit whole-body camera is informational if bounds change.

## Required milestone coverage

| Set | Required actual views |
|---|---|
| Neutral | front, rear, side, 3/4 front, 3/4 rear |
| Anatomy close-ups | head/neck, shoulder, chest/torso, back, elbow, palm, dorsal hand, thumb, hip, knee, foot |
| Exercise/deformation | curl/curl_peak, curl_handle, press_bottom, press_top, pullup_hang, pullup_top, squat_bottom, lunge, pushup_bottom, row |

For each anatomy close-up capture two useful angles, including loaded/bent views
for articulation regions. For a Phase 3 local trial the existing compact 17-view
set is sufficient for the repair snapshot; it is NOT full milestone coverage.
Missing rear/head/foot views must be produced on the laptop before claiming the
complete milestone board. Mark every board with revision, SHA prefix, view/pose,
EXPERIMENTAL and owner_review pending.

## Outputs and comparison boards

1. Run the existing full evidence runner; capture manifests are now emitted with
   each render group. `collect_original_v1_review_images.py <revision>` verifies
   the candidate/source/image hashes and copies the existing compact views.
2. Save under `ORIGINAL_V1_WORK/candidates/review/visual_<revision>/`, with
   `visual_review_manifest.json` recording owner_review pending and non-blocking.
3. For previous-versus-new boards run:
   `python scripts/build_original_v1_comparison_boards.py <previous> <new>`.
   Output `review/comparison_<previous>_<new>/`. The SVGs embed only the actual
   PNGs and labels. The manifest flags whether capture settings exactly match;
   mismatched framing must never be presented as a quantitative comparison.
4. Commit/push images and manifests where practical, regenerate daily status and
   ledger, then continue read-only diagnostics or the next safe local experiment.
   Commit binaries only under the existing candidate/review policy, never release.
5. Owner feedback records the exact SHA and accepted/rejected regions. A pending
   review does not authorize destructive subjective choices or final promotion.

## Phone inspection

Show compact front/3/4 plus the current repair close-up, and matched old/new pairs.
Keep readable labels and report metrics beside imagery, rather than a blended
quality score. Each candidate retains its own folder; never overwrite rejected
or superseded review evidence. No screenshots currently exist in the committed
r29 evidence, so cloud preparation cannot truthfully show a current render.

## Numeric source lineage from r30 onward

Publish the full merger's evidence receipt plus all six original group report and
render-source JSON pairs. The cloud checker verifies candidate/manifest/script
identities, source hashes and identical overlapping metrics before selecting a
future candidate. This numeric lineage check is separate from the local PNG-byte
verification and owner visual review. Full-resolution images can remain local;
publish the verified compact review set. Git attributes protect evidence byte hashes
from automatic newline conversion. Never rewrite historical evidence or invent
source manifests for earlier renders.

## Prepared full milestone capture runner

```bat
RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat r29
```

This opt-in review task does not replace the next deformation experiment. Use it
for a meaningful checkpoint when laptop time/power allows. It checks live branch
HEAD, clean working tree, frozen inputs, candidate bytes, Blender availability,
process conflicts, free disk and fresh output paths. Power/process information may
be unknown. It never saves the Blend or reruns an optimiser.

`ORIGINAL_V1_VISUAL_BOARD_PLAN.json` defines 57 actual bare-body images: five
neutral views, two angles for each of 11 anatomical regions, and three views for
each of ten exercise poses. Whole-body cameras use fixed centres/scales and fail
if evaluated body vertices would be clipped. Close-ups follow owned rig landmarks;
palm/dorsal directions come from the existing posed-hand normal. All existing
stress pose definitions and metric calculations are preserved. No model editing
or Phase 5 execution occurs. The ordinary repair render mode remains unchanged.

Capture folder: `repair_checks/milestone_<revision>/`. Published folder:
`review/milestone_<revision>/`. A phone-friendly README shows neutral views and
exercise 3/4 views, with links to the other images. The publisher verifies all PNG
hashes, candidate/plan identity, exact 57-view coverage and complete numeric pose
evidence before copying files. It marks owner_review pending and NON-BLOCKING.
Commit the published folder plus the raw capture `render_source_manifest.json`
and `pose_test_report.json`; full-resolution source PNGs may remain local because
the published copy is verified against its original source manifest.

For a completed capture whose publication was interrupted, preserve the source
folder and run `python scripts/original_v1_milestone_review.py <revision>` without
--capture. Existing published folders are never overwritten. Incomplete capture
folders remain diagnostic evidence; do not silently resume with mixed script bytes.

Compare two actual published milestone sets:
`python scripts/build_original_v1_comparison_boards.py <previous> <new> --milestone`.
Boards retain labels/SHA prefixes and flag different camera/capture settings.
Rebuild daily status; validated published snapshots become pending review links.
Continue safe diagnostics or local work while owner review is pending.

Cloud validation covers plan membership, source/hash/publication safety and Python
syntax. Actual Blender execution, anatomical camera usefulness, occlusion and image
quality remain unvalidated until the first laptop run. The utility refuses clipped
whole-body views; it cannot infer subjective anatomy quality from camera metadata.
