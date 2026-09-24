# V12c hand palm review — candidate only

V8 remains the accepted body and knee geometry baseline. V11 remains an intact hand cleanup checkpoint. V12c is a separate hand candidate derived from the V11 Blender file; it is **not visually accepted and not promoted to production**. No grip refit was done.

The V11 palm was still flat in the open-hand and fist views. V12c adds modest interior thenar, hypothenar, palm-arch and wrist volume without moving the V11 patch boundaries. It keeps V11 topology, fingertip caps, UVs, weights, materials, the 63-bone hierarchy, runtime/retarget source, equipment, contacts and exercise mechanics. A four-to-eight-ring falloff holds each open seam edge and the protected floor vertices fixed. The edit is symmetric. Blender build maximum displacement from V11 was 1.767 mm; all 682 protected push-up contact vertices, seam-boundary vertices and non-hand vertices moved 0 mm.

Two earlier local shape trials showed why the smaller field was selected: the first raised folded hand edges over 100° from V11's 4 to 26; a narrower pass left 6. V12c tapers the field at the palmar-side boundary and restores the count to 4. Those trials are not review candidates.

## Measured checks

- GLB: 46,675 body vertices, 89,861 triangles, zero degenerate triangles and zero edges with more than two faces. New-vertex skin weight loss is zero. GLB nodes, skins, animations and materials match V8; the rig and equipment source are unchanged.
- Strict push-up guard: all 682 protected original vertices keep their position and skin rows exactly; both hand floor heights match the V8 baseline.
- Frozen runtime `614033b`: five focused guards pass. Seven exercises sampled at 26 frames each pass, with zero bone/equipment matrix difference, no technique violations, reachable clips and closed loops. Maximum hand difference from V8 is 3.638 mm; V11-to-V12c is 1.496 mm.
- Hand seam audit: V12c and V11 have the same bind and posed open-hand seam bands. Bind: 549 left-hand boundary vertices within 0.05 mm of another surface, zero in the 0.05–1.5 mm bands, one at 1.5–4 mm, four at 4–12 mm and five over 12 mm. These larger openings are inherited. No fingertip hole edges. Four folded edges over 100°, the same as V11.
- Dressed and bare variants preserve posed-body equivalence. No production asset or `bundled.ts` edit.

## Matched visual review

In `renders_v12c_palm_volume/`, V11 is the top row and V12c the bottom row, with matched pose, camera and lighting:

- `V12C_V11_OPEN_HAND_COMPARISON.jpg` — palm, back and thumb-index web.
- `V12C_V11_CLOSED_FIST_COMPARISON.jpg` — palm, back and side.
- `V12C_V11_EXERCISE_HAND_COMPARISON.jpg` — curl grip, push-up contact and pull-up grip.

The improvement is restrained. The thenar/palm reads slightly fuller, especially in the fist and side views, without reopening the web seam. Finger-pad facets near the protected floor vertices and the broad inherited hand silhouette are still visible. This is a review candidate, not a declaration that hand anatomy is finished.

**Next:** review the boards. Keep V8, V10, V11 and V12c separate. Do not start grip refit until hand anatomy is visually accepted. If the palm change is too subtle, a future candidate needs targeted topology or a new contact-preserving proof; increasing this displacement field reopened folds.
