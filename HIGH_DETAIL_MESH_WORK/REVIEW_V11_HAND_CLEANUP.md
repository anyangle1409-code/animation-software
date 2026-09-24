# V11 hand cleanup — review candidate, not accepted

V11 is the V11 cleanup that `V11_HAND_CLEANUP_PLAN.md` asked for, built from the V10 checkpoint. It was built in a cloud session (Claude) with Blender **5.2.1 LTS**, the same version as the laptop, running headless through the `bpy` module. Nothing was modelled by hand. Every step is in `scripts/build_v11_hand_cleanup_blender.py`, and `scripts/run_v11_pipeline.sh` rebuilds and re-validates the whole thing.

V8 remains the accepted geometry baseline. V9 and V10 are preserved and nothing in them was overwritten. There is no grip refit and no rig, exercise, equipment or production change. **Stop for visual review before Phase C.**

## Review images

- `renders_v11_hand_cleanup/V11_V10_OPEN_HAND_COMPARISON.jpg`: open palm, back, thumb-index web.
- `renders_v11_hand_cleanup/V11_V10_CLOSED_FIST_COMPARISON.jpg`: fist palm, back, side, with no equipment.
- `renders_v11_hand_cleanup/V11_V10_EXERCISE_HAND_COMPARISON.jpg`: curl grip, push-up contact, pull-up grip.
- `renders_v11_hand_cleanup/V11_V10_GLB_NORMALS_BIND_COMPARISON.jpg`: see "Reading the boards" below.

The first three boards are made by the V10 renderer and board script, unchanged, from identical poses and cameras. The baseline row is V10.

## What the V10 audit found

The plan's four defects were measured in the V8, V10 and V11 GLBs and Blends before any change was made (`scripts/audit_hand_seams.py`, `reports/hand_seam_audit.json`). Two of them are not shape problems, so no sculpt field can fix them.

1. **The hand is not one welded sheet, and V10 opened its seams.** V8's hand and wrist are built from skin patches. Their edges meet other patches' edges, or lie on other patches' faces, without being welded. In V8, 826 of the 862 hand boundary vertices sit within 1.5 mm of another face. The "stepped wrist" band and the pale outline across the palm are these seams. V10's subdivision and sculpt moved one side of many of them, so on the left hand 127 boundary vertices sit 0.5–1.5 mm off, and 32 more sit 1.5–4 mm off. The **dark thumb-index web seam** and the wrist-crease slit are two of those cracks. They are also why V9's smoothing passes "introduced dark seams" and "wrist slits": smoothing moves each side of an unwelded seam separately.
2. **The fingertips are open.** The index, middle, ring and pinky tips end in small holes, up to 3.6 mm across, in both V8 and V10.
3. **The ring banding and crumpling are V10's own sculpt.** V10 put joint pads, shaft narrowing and a 5.5 mm tip push on top of a subdivided surface. Folded edges (faces meeting at more than 100°) on the left hand went from 10 in V8 to 104 in V10.
4. **V10's thenar and web volume fields push along vertex normals.** Those normals differ on the two sides of an unwelded seam, so the push lifts the thenar patch's edge into an overhang. That is the dark wedge at the web in V10's views.

## What V11 does

In `scripts/build_v11_hand_cleanup_blender.py`:

1. Takes off V10's posed skin-interpolation correction, and restores it at the end. It is a fixed per-vertex bind offset, so it survives the reshaping.
2. Returns the hand to V8's accepted shape on V10's denser topology:
   - original vertices go back to their V8 positions;
   - added vertices go back to their interpolated V8 rest positions.

   None of V10's sculpt fields are re-applied.
3. Caps the eight fingertip holes. The caps use the existing tip vertices, so no vertex is added, and each corner copies its UVs from the surrounding surface.
4. Smooths the whole hand without shrinking it (Taubin), with a longer pass on the fingers.
   - The 682 protected push-up contact vertices never move.
   - Smoothing eases in over the three rings of vertices around each protected one, so none of them is left standing proud.
   - V10's mask faded to nothing near the push-up floor. That kept the palm side of the fingers from ever being smoothed, so V11 does not use it.
5. Relaxes the remaining folded faces locally.
6. Closes every seam: each boundary vertex that may move is laid onto the partner edge or face it belongs against, then re-mirrored left/right.
7. Gives each closed seam vertex the skin weights of the surface point it lies on (27 vertices), so the seam stays closed when the hand moves.

Vertices are moved, never merged. Every original V8 vertex keeps its ID, which the packer depends on. No vertex is added.

In `scripts/pack_v11_hand_glb.py` (V10's packer plus two changes):

- vertices that share a position in the hand region share one normal (675 vertices), so each closed seam shades as one surface;
- the 17 original seam vertices re-weighted in step 7 carry their new weights into the GLB.

Every other original vertex keeps V8's weights.

## Measured (left hand; `reports/hand_seam_audit.json`)

| | V8 | V10 | V11 |
|---|---:|---:|---:|
| Seam vertices closed (< 0.05 mm, bind pose) | 319 | 227 | **549** |
| Seam cracks 0.05–1.5 mm (bind pose) | 94 | 331 | **0** |
| Seam gaps 1.5–4 mm (bind pose) | 8 | 32 | **1** |
| Fingertip hole edges | 32 | 41 | **0** |
| Folded edges (> 100°) | 10 | 104 | **4** |
| Posed open hand, seam cracks 0.5–4 mm | — | 139 | **5** |

The few remaining gaps larger than 4 mm are the same in V8. They are seams where fixed vertices meet, such as forearm to wrist, and the rules keep those vertices still.

## Validation

All of these run against runtime `614033b` and frozen `hgpt_canonical_v3`, as V10's did:

- **Quick structural check: PASS.** No degenerate triangles, no edge shared by more than two faces, protected GLB fields unchanged. There are 46,675 vertices and 89,861 triangles, the same vertices as V10 plus 66 cap triangles.
- **Strict push-up floor guard: PASS.** All 682 protected vertices are unchanged in position, joints and weights, with a maximum shift of 0.0 mm (`reports/hand_floor_guard_…v11_hand_cleanup.json`).
- **Five focused guards: PASS** (`reports/v11_hand_cleanup_rig63_guards.log`): sagittal profile, bare/dressed equivalence, grip metric, dumbbell overlap, and renderer/solver/exporter grip agreement.
- **Seven exercises, 26 frames each, against V8: PASS** (`reports/exercise_validation_v11_hand_cleanup.json`).
  - Bone and equipment matrices match exactly, the push-up hand-floor height is identical, and there are no technique violations or unreachable targets. Loops close.
  - The largest original-hand vertex difference from V8 is **3.638 mm**, against V10's 5.674 mm. That is inside the default 4 mm envelope; V10 needed a 10 mm one.
- Build guarantees, asserted inside the build:
  - protected vertices moved 0.0 mm;
  - vertices outside the hand moved 0.0 mm;
  - every V8 vertex ID is preserved.
- The curl skin matrices the correction uses are byte-identical to V10's.

## Reading the boards

The V10 renderer rebuilds normals from positions, one patch at a time, so it draws every unwelded seam as a pale line. That is why the wrist band rectangles and the palm outline still show in both rows, although V11's seams are closed and share normals in the GLB. `V11_V10_GLB_NORMALS_BIND_COMPARISON.jpg` shades each GLB with its own normals, as the app does, and shows the difference. In that board the inside of the mesh shows through V10's wrist band, knuckle cracks and wrist-crease slit (magenta). In V11 none of them show.

## Decisions for the reviewer

- **The palm keeps V8's volume, not V10's.** V10's thenar, web and palm fields caused the web wedge. With `PALM_FIELDS=1` the build restores them, and the wedge with them. Adding that volume back without the wedge needs the fields applied along one shared normal per seam. That is a follow-up if the palm reads flat.
- **The fingers are V8's shape, smoothed, not V10's joint sculpt.** The ring banding is gone. The finger shape is the accepted V8 one with its facets softened.
- **Around the protected contact vertices,** the palm side of the fingers keeps a little of V8's faceting, because those vertices may not move. Relaxing them needs a replacement floor-contact proof, which the plan requires before they change.

## Not done

- No grip refit.
- No rig, weight-paint, exercise, equipment or production change. The only weight changes are the 27 seam vertices in step 7.

Runtime `614033b` is the pinned validation source. The source branches have since moved on (14 exercises at `87b881d`). See `NEXT_ACTION.md`.
