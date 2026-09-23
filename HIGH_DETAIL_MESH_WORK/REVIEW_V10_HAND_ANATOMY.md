# V10 hand anatomy — visual review candidate, not accepted

V8 remains the accepted body and knee geometry source. V9 is preserved as a rejected experimental hand pass. V10 was built independently from the V8 Blend/GLB with local Blender topology and sculpt edits on the hands and wrists only. It is for visual review; do not promote it or start grip refitting until the user accepts the hand shape.

## Review images

- `renders_v10_hand_retopology/V10_V8_OPEN_HAND_COMPARISON.jpg` — open palm, back, thumb-index web
- `renders_v10_hand_retopology/V10_V8_CLOSED_FIST_COMPARISON.jpg` — fist palm, back, side, without equipment
- `renders_v10_hand_retopology/V10_V8_EXERCISE_HAND_COMPARISON.jpg` — curl, push-up, pull-up
- The same folder contains full-size matched V8/V10 PNGs for each view.

## Candidate work

- Blender subdivided 8,438 interior hand/wrist edges and 5,148 finger/web edges, adding 13,586 local vertices. Body topology is 46,675 GLB vertices and 89,795 triangles, up from V8's 33,089 and 62,961.
- Candidate-only finger pad/taper/cap, thumb/thenar, palm, hypothenar and wrist fields were applied, with mirrored left/right sculpt. Original V8 vertex IDs are retained as a GLB prefix.
- The GLB packer preserves the V8 rig, skins, nodes, animations, UV/material definitions and shorts. Added vertices carry up to 12 source-compatible bone influences with zero influence truncation. The editable Blend preserves the local topology and transferred UVs/weights.
- A posed-surface skin correction based on the pinned runtime's actual curl transforms prevents the new finger loops from producing bone-blend ridges. The correction changed added bind vertices by median 0.079 mm, maximum 1.361 mm. It did not move originals.
- All 682 protected original push-up floor vertices are unchanged. No non-hand original vertex moved.

## Validation

The quick GLB check passes with zero degenerate triangles and zero edges shared by more than two faces. Five focused guards and seven exercises over 26 frames each pass against runtime `614033b` and frozen `hgpt_canonical_v3`. Bone/equipment matrices match V8 exactly, push-up minimum hand-floor height is unchanged, and bare/dressed posed equivalence passes. The maximum original-hand posed difference is 5.667 mm. No grip refit or exercise/rig change was made.

## Visual caveats for the reviewer

V10 is a stronger topology edit than V9, but the finger ends and some joint bands still read faceted in close-up. The thumb-index web has a small dark seam in some angles, and the wrist transition remains visibly segmented. The push-up and curl contact shapes stay coherent, but anatomical acceptance needs the user's visual decision. If rejected, continue with a new candidate from V8 or this V10 checkpoint, keeping V8 accepted and V9/V10 preserved. Do not refit grip yet.

Assets: `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v10_hand_retopology.blend`, `.glb`, and `_BARE.glb`. Source and build scripts are under `scripts/`; validation reports are under `reports/`.
