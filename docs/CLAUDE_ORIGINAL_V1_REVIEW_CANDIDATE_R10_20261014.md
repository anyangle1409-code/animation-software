# ORIGINAL_v1 review candidate R10: full-range press and shoulder/armpit corrections (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

**Owner, after comparing the press with a four-stage reference photo series** (start / mid / near top / lockout): "Yes, start with A then do B".

## A: finishing the movement

This is a runtime change, in `scripts/original_v1_press_extension.py`.

**What was wrong:** Work's coupled shoulder profile and the humeral axial hypothesis stop at 160°, so the press ended with the
arms in a wide V and the shoulders never rose.

**The change:** a review-only hook in the R4+ shoulder drive (`original_v1_shoulder_r4._S["extend"]`).
- **Beyond 160°:** it extends the girdle coupling, linearly, in the same directions. Over 160 → 180° that adds clavicle
  elevation +3°, retraction +4°, posterior rotation +6°, scapular upward rotation +8° and posterior tilt +6°. This is a
  project-authored extrapolation of the Ludewig 2009 directions.
- **Lockout shrug:** the full press path adds an active 12° clavicle elevation over the last 40 % of the lift.

**Full press path:** elevation 85 → 172°, elbow 100 → 0°.
- **Result at lockout:** the arm is 8° from vertical (the 160° path left it at 20°), and the AC joint rises 31 mm.
- **Unchanged below 160°:** poses up to 160° are bit-identical with the hook on or off. Work's profile file is unchanged.

**Test:** `test_original_press_extension.py`.

## B: corrective shapes (R10 = R9 + 8 keys)

The keys are `HGPT_S4_SCULPT_<s>_{85,110,145,172}`, from `scripts/build_original_sculpt_corrective_blender.py` with scale 2.0.
They are solved on the full-press poses with all drives on, and each one combines:
- **Deltoid cap:** pushed outward (a contracted deltoid; the photo shows a full, round cap at every stage);
- **Armpit vault:** pulled inward (the hollow between the pectoral and latissimus folds);
- **Upper trapezius:** pushed outward at lockout;
- **Unfolding:** of the lockout armpit crease.

**How they are made and applied:**
- the posed offsets are mapped to rest through the blended LBS matrices and capped at 40 mm;
- a count-based, mirror-symmetric guard runs along the press path;
- the keys are driven on elevation from 60°, and the last key holds above 172°.

Weights, bones and the basis mesh are unchanged.

**Press path, R9 (with A) → R10** (collapse / stretch > 2× / pairs; `r10_build.json`):

| t (HT) | R9 + A | R10 |
|---|---|---|
| 0.75 (158°) | 6 / 142 / 0 | 2 / 124 / 0 |
| 0.85 (167°) | 6 / 158 / 31 | 0 / 144 / 1 |
| 0.9 (170°) | 8 / 168 / 71 | 0 / 154 / 1 |
| 1.0 (172°, lockout) | 4 / 182 / 95 | 0 / 158 / 17 |

**Benchmarks** (`r10_validation.json`):
- **Press (the 160° benchmark path):** 4 / 124 / 0 → 2 / 108 / 0.
- **The other 12:** identical to R9.

**Recorded cost:** more volume loss at the top (−1.05 → −1.77 % at lockout). The armpit hollow pulls skin in.

## Variants measured and rejected

| Variant | Result |
|---|---|
| Sculpt scale 1.0 | barely visible |
| Sculpt scale 3.0, wider regions | tears / jagged edges at the back of the shoulder near the top |
| Back-of-shoulder skin taken off the cap helper (aimed at the side-view lump behind the armpit) | the lump stays, and a dark gash appears beneath it |

## Against the reference photo

The comparison sheet is kept outside the repo because it contains the owner's photo.

| Stage | Matches | Still differs |
|---|---|---|
| Lockout range | arms near vertical; the shoulders rise | — |
| Deltoid | rounder than R9 at start and mid | far less full than the photo |
| Armpit (near top, lockout) | some hollow; the crease is unfolded (pairs 95 → 17) | no deep hollow; vertical crease lines remain; the lockout silhouette beside the neck is lumpy |
| Side view | — | a rounded mass behind the armpit (partly real lat/teres) |

**Why:** the remaining gap is shape detail that procedural bumps cannot produce. It needs authored (sculpted) target shapes,
denser armpit topology, or muscle/skin simulation.

## Evidence

- `press/shoulder_press_r9_vs_r10.gif`;
- `press/shoulder_press_r10.gif`;
- renderer: `scripts/render_press_animation_blender.py --full [--poses ht:elbow:shrug,...]`.

## Tests

`scripts/blender_tests/test_original_review_candidate_r10.py`, 6 native tests:
- **Identity.**
- **Contents:** R10 = R9 + the 8 keys.
- **Deltas:** bounded and mirror-symmetric.
- **Press path:** pairs and collapse never above R9; at most 20 pairs from 160° up, against up to 95; lockout stretch lower; the volume cost is asserted.
- **Live drive:** the lockout row reproduces exactly.
- **Benchmarks vs R9.**

R1–R9 and the press-extension tests pass.
