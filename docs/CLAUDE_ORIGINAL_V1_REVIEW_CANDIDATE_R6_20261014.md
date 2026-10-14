# ORIGINAL_v1 review candidate R6 = R5 + stretch-zone relax keys (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production.**
- **Owner question:** "What about the shoulder press? The skin still looks stretched".
- **Lineage:** R6 replaces R5 as the single review candidate. R5 is unchanged.

## Where the stretch was

The stretch map at 160° (`stretch/stretch_map_a003_r5_r6.jpg`, faces coloured by area vs rest) shows R5's remaining stretch in:
- the **lateral back below the armpit** (latissimus area, `spine_03`-dominant: 254 of 538 faces over 1.5×, up to 6.8×);
- the inner upper arm.

**Why:** R4/R5 hand the scapula's influence on that skin to the static thorax, so it is pinned while the armpit rises 15–20 cm. In a real body the latissimus inserts on the humerus and the skin slides.

**Rejected alternative:** a wider scapula weight taper (10→24 or 12→30 cm). Volume improves, but faces over 2× rise (100 → 104–128).

## Fix: S1 relax keys on the measured stretch zone

`scripts/build_original_shoulder_relax_corrective_blender.py` with `S1_ZONE=stretch`, `S1_SRATIO=1.2`, `S1_SRINGS=20`, `S1_ITERS=1000`, `S1_KEYS=105,120,145,160`.

**Zone:** per side, the faces stretched more than 1.2× at 160° plus 20 rings (3,113 vertices).

**Method (as R2):**
- pull-only tangential relaxation (neighbouring skin slides in to share the stretch);
- damped rest-space mapping and smoothing;
- volume restored per key;
- collision/fold guard over 95–160°.

**Fixed while building:**
- **Symmetric guard:** the guard backed off one side only (odd counts in its log), leaving the left/right corrections up to 2.4 mm apart. It now also softens the mirror vertices; mirrored deltas agree to 0.003 mm.
- **105° key:** the first build lost 0.05 points more volume than R5 at 100–110°. With the 105° key, volume matches R5 within 0.03 points at every angle.

**Variants measured** (faces over 2× at 160°):

| Variant | Faces over 2× |
|---|---|
| 6 rings / 150 iterations | 78 |
| 12 / 600 | 64 |
| **20 / 1000 (selected)** | **60** |

## Results

**Coupled sweep, R5 → R6:**
- stretch is lower at every angle from 100° (e.g. 160°: 100 → 60; 140°: 88 → 56);
- collapse and pairs are never higher;
- volume is within 0.03 points.

**Stretch map at 160°:**

| Stretch | a003 | R5 | R6 |
|---|---|---|---|
| Faces over 1.5× | 938 | 538 | 244 |
| Faces over 2× | 400 | 100 | 60 |
| Faces over 3× | 66 | 32 | 16 |

**Benchmarks** (`r6_validation.json`):
- **Shoulder press** (collapse / stretch / pairs): R5 28 / 100 / 216 → R6 26 / 62 / 216.
- **Other 12 benchmarks:** identical to R5 (row 32 pairs).

**Remaining:**
- a narrow band of stretch on the lateral back (up to 6×; 16 faces over 3×);
- the press pairs (216, posterior-axillary curl);
- mid-range collapsed faces;
- the inferior-angle lift-off.

## Evidence

- `stretch/stretch_map_a003_r5_r6.jpg`: stretch heat map.
- `stretch/skin_160_a003_r5_r6.jpg`: plain skin.
- `sequences/shoulder_press*`: press sequence.

## Tests

`scripts/blender_tests/test_original_review_candidate_r6.py`, 6 native tests:
- **Identity.**
- **Contents:** R6 equals R5 plus exactly 8 S1 keys (same weights and bones).
- **Deltas:** bounded, on their own side, and mirror-symmetric to 0.5 mm.
- **Sweep:** no worse than R5 at any angle (collapse, pairs, volume ±0.05 points); less stretch at 160°.
- **Live check:** the 160° row is reproduced from the saved file.
- **Benchmarks:** unchanged except the press, which improves.
