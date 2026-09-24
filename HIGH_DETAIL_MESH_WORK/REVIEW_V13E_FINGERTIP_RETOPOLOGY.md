# V13e fingertip retopology — candidate review

V8 remains the accepted body/knee geometry baseline. V12c is preserved as the prior hand review candidate. V13e starts from its Blender mesh and adds 1,646 vertices/3,292 triangles only in the distal index, middle, ring and little fingers, with a small rounded cap and taper. It is **not visually accepted or promoted to production**. No grip refit was done.

The first distal sculpt was almost invisible because the source finger surface ends 9–20 mm before the frozen bone tails. The final build locates each finger's actual surface end before placing local loops. Two intermediate topology/sculpt trials created extra sharp folds and were discarded. V13e relaxes those two distal regions without moving any protected original floor-contact vertex or unwelded seam boundary. Maximum Blender displacement from V12c is 1.379 mm. The thumb, palm, wrist, non-hand body, UVs, skin influences, rig, animation, equipment and exercises are unchanged.

## Validation

- Dressed GLB: 48,321 body vertices, 93,153 triangles, no degenerate triangles or edges with more than two faces. Added-vertex skin-weight loss is zero. Nodes, skins, animations and materials match the V8 source GLB.
- All 682 protected original push-up contacts retain exactly the same positions and skin rows. The posed hand floor matches V8 and V12c.
- Frozen runtime `614033b`: five focused guards pass. Seven exercises sampled at 26 frames each pass, with zero bone/equipment matrix difference, no technique violations, reachable clips and closed loops. V12c-to-V13e maximum hand difference is 1.196 mm.
- Bind and posed open-hand seam bands match V12c; there are no fingertip hole edges. Four hand edges exceed 100° fold, the same as V12c.
- Bare/dressed posed equivalence passes. Nothing in production, `bundled.ts`, the canonical hierarchy, retargeting, exercise mechanics, grip logic or equipment locks changed.

## Visual assessment

Matched V12c (top) and V13e (bottom) boards in `renders_v13e_fingertip_retopology/`:

- `V13E_V12C_OPEN_HAND_COMPARISON.jpg` — palm, back, thumb-index web.
- `V13E_V12C_CLOSED_FIST_COMPARISON.jpg` — palm, back, side.
- `V13E_V12C_EXERCISE_HAND_COMPARISON.jpg` — curl grip, push-up contact, pull-up grip.

The distal contours are slightly rounder, most visible at the open fingertips. The broader inherited finger-body facets and angular transitions near protected floor vertices remain visible. This checkpoint establishes local tip topology that can support a deeper finger-body anatomy pass, but it does **not** establish that hand geometry is finished. Review before deciding whether to retain this candidate as the next source. Do not start grip refitting until the hand anatomy is visually accepted.
