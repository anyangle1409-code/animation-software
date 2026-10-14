# ORIGINAL_v1 review candidate R7: top-of-shoulder fold keys (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**

**Owner instruction (14 Oct), on R6:** "Let's fix before continuing". Four issues were open:
1. the top-of-shoulder fold;
2. the lateral-back stretch band;
3. mid-range crushed faces;
4. blade lift-off.

R7 fixes the fold from 110° to 135° (part of issues 1 and 3). The 140–160° fold, the stretch band and the blade lift-off
remain open; each was measured, and the reasons are given below.

**Parent:** R6. R7 is R6 plus 10 shape keys, `HGPT_S2_FOLD_<s>_{125,130,135,140,145}`. Bones, weights, basis mesh and every
R6 key are unchanged. The 145 key is empty: it closes the hat, so the fold keys fade out by 145°.

**Drive:** `scripts/original_v1_review_candidate_drives.drive_s1` now drives two key families on humerothoracic elevation:
- `HGPT_S1_SHOULDER_` through `hgpt_s1_angles_<s>`;
- `HGPT_S2_FOLD_` through `hgpt_s2_angles_<s>`.

## Build

The builder is `scripts/build_original_shoulder_relax_corrective_blender.py`, run on R6 with:

`S1_PREFIX=HGPT_S2_FOLD_ S1_ZONE=fold S1_MODE=smooth S1_SRINGS=4 S1_ITERS=100 S1_KEYS=125,130,135,140,145 S1_ZEROKEYS=145 S1_GUARD=score S1_GRINGS=0`

- **Zone:** the vertices of the faces that overlap or are crushed at 130/145/160° (all drives on), plus 4 rings. 409 vertices per side.
- **Keys:**
  - each key is solved at its own pose by Laplacian smoothing of the posed zone;
  - it is mapped to rest space through the blended LBS matrices (damped);
  - it is capped at 30 mm, then volume-restored.
- **Guard ("score"):**
  - it checks every 5° from 95° to 160°;
  - a key is halved only around the measure that got worse, and only on the faces involved;
  - one crushed face counts as 10 overlapping pairs.
- **Why not the stricter guard:** under the strict "no new pair and no new crushed face" guard, the fold fix trades 62 pairs for 2 crushed faces. That guard reverted it entirely. The trade is recorded in the tests below.

**Variants measured and rejected:**

| Variant | Result |
|---|---|
| Keys at 120/145/160 | Strict guard reverts them; without the guard, 160° goes 216 → 286 pairs |
| One key at 130 (held on above it) | 336 pairs at 160° |
| Keys up to 160 every 5°, no guard | 150°: 136, 160°: 296 pairs |
| Count-only guard | Reverted |
| Taubin (non-shrinking) smoothing at 145–160 | 160°: 216 → 200–208, 130° unchanged; not worth it |
| Cap 50 mm | No change |

At 140–160° the arm skin passes 6–20 mm under the shoulder skin. Smoothing cannot separate layers that deep. Plain
smoothing also shrinks the zone, moving it up to 59 mm (about 270 deltas per key clip at the 30 mm cap).

## Results

**Coupled 0–160° sweep, R6 → R7** (collapse / stretch > 2× / pairs / volume %):

| HT | R6 | R7 |
|---|---|---|
| ≤ 100 | unchanged | unchanged (stretch 44 → 42 at 100) |
| 110 | 6 / 44 / 0 / −0.56 | **2** / 42 / 0 / −0.56 |
| 120 | 10 / 46 / 10 / −0.99 | 10 / 54 / **0** / −1.00 |
| 130 | 24 / 54 / 84 / −1.45 | 26 / 62 / **22** / −1.45 |
| 140 | 14 / 56 / 98 / −1.91 | 12 / 62 / 98 / −1.91 |
| 150 | 14 / 60 / 156 / −2.34 | unchanged |
| 160 | 26 / 60 / 216 / −2.73 | unchanged |

**Shoulder press, frame by frame** (collapse / stretch / pairs):

| t | R6 | R7 |
|---|---|---|
| 0.375 | 8 / 46 / 0 | 6 / 46 / 0 |
| 0.5 | 22 / 50 / 30 | **14 / 56 / 0** |
| 0.625 | 16 / 56 / 92 | 18 / 64 / 92 |
| 0.75–1.0 | unchanged | unchanged |

**All 13 benchmarks** (`r7_validation.json`): every worst frame is identical to R6, except the press stretch, 62 → 64. The press's
worst frame is the top of the lift, where the fold keys are off.

**Recorded costs:**
- **Crushed faces:** +2 at 130°.
- **Stretched faces:** up to +8 faces above 2× at 120–140°.
- **Press stretch:** 62 → 64 faces above 2×.

## What remains, and why

| Issue | Measured | Why it is not fixed in R7 | What would fix it |
|---|---|---|---|
| Top-of-shoulder fold at 140–160° | 98–216 pairs; arm skin 6–20 mm under the shoulder skin | Pose-space keys cannot unfold layers that deep (all variants above) | A structural fix: a top-of-shoulder helper joint that takes part of the elevation, or a corrective joint chain. R1–R3's W3A helper cut 160° pairs to 132 but brought back stretch (118) and mid-range pairs, so it needs to be restricted to the top-of-shoulder skin. Owner decision. |
| Lateral-back / axillary stretch band | 6–8 faces per side above 3× (max 6×) at 120–160°; front and back axillary folds | Faces weighted across spine_03, scapula and upper arm (each about 0.25–0.4) | Weight redistribution in the axilla, or an axillary helper; the axilla is also the skin that stretches most in reality |
| Blade inferior-angle lift-off | +47 mm off the thorax ellipsoid at 160° (+48 mm against the rib guides) | Skeleton-only: the inferior angle is 255 mm from the AC joint, and the scapula's skin weight is zero beyond 180 mm, so the lift moves no skin. Closing it needs 15° more posterior tilt (tilt penalty 0.1: lift 80 → 64 mm), which brings back the tilted blade the owner asked to remove. | Upstream: the blade and thorax guide shapes (frozen canonical) |

## Evidence

`fold/fold_{120,130,160}_r6_r7.jpg`: front, rear and side views of R6 and R7. Overlapping faces are red and crushed faces blue; most of the overlap sits inside the crease.
They are rendered by `scripts/render_shoulder_fold_compare_blender.py`.

## Tests

`scripts/blender_tests/test_original_review_candidate_r7.py`, 6 native tests (CI: `original-review-candidate-r1.yml`):
- **Identity.**
- **Contents:** R7 = R6 + the 10 fold keys only, and the closing key is empty.
- **Deltas:** bounded and mirror-symmetric.
- **Sweep:**
  - pairs are never higher than R6;
  - 120° reaches 0 pairs, 130° at most a third of R6's, and 110° has fewer crushed faces;
  - the costs above are asserted, and so is the unchanged 160° fold.
- **Live drive:** the fold keys are on at 130° and off at 160°, and the 160° row reproduces exactly.
- **Benchmarks:** identical to R6 except the press.
