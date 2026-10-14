# ORIGINAL_v1 review candidate R2 = R1 + S1 overhead-shoulder relax keys (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.** R2 replaces R1 as the single
consolidated review candidate. R1 stays in place unchanged as its parent; nothing in a003, the canonical bones or the
V-series assets changed.

## Why

R1's W3A helper removed the a003 axillary tear at full press, but it left about 230 more faces stretched beyond ×2 at 160°.
These are upper-arm-dominant skin with partial helper weight, i.e. the gradient between the half-rotation helper and the
full-rotation arm.

A helper parameter sweep on C5 (coupled 160°, collapse / stretch > 2 / pairs / volume %) shows the stretch is structural:

| Variant | 160° | 145° |
|---|---|---|
| no helper (a003 weights) | 42 / 400 / 444 / −5.02 | 48 / 428 / 176 / −4.0 |
| R1 (transfer 0.6, fraction 0.5) | 4 / 634 / 110 / −2.01 | 2 / 624 / 58 / −1.05 |
| transfer 0.4 / 0.8 / 1.0 | 12 / 522 / 174 / −3.29 · 12 / 750 / 108 / −0.87 · 4 / 796 / 46 / +0.05 | |
| fraction 0.4 / 0.6 / 0.7 | 10 / 634 / 134 · 4 / 600 / 112 · 10 / 548 / 162 | |
| smoothing 0 / 8; edge taper 8 | 6 / 616 / 116 · 4 / 632 / 122 · 16 / 528 / 234 | |

Every variant only trades stretch against collapse, collisions or volume. So the next step was a pose-space corrective that
adds no joints.

## S1 method (`scripts/build_original_shoulder_relax_corrective_blender.py`)

Keys `HGPT_S1_SHOULDER_<s>_<ht>` are solved at coupled 120°, 145° and 160°, with the R1 drives on. For each side:

1. **Region:** the W3A helper zone. Everything else is fixed.
2. **Pull-only tangential spring relaxation**, 150 iterations:
   - only edges longer than at rest are shortened back to rest length;
   - moves are projected onto the posed tangent plane, so skin slides rather than inflates.
3. **Rest-space mapping:** a damped inverse of the blended skinning matrix (λ 0.05, cap 30 mm), then 20 Laplacian passes
   with zero outside the zone.
4. **Volume:** a tapered rest-normal offset gives each key zero volume change at its pose.
5. **Collision/fold guard:** every 5° from 95° to 160° with the interpolated key values, any vertex in a new intersecting or
   collapsed face (+ 2 rings) has its delta halved, repeated until a full pass is clean. Volume is then restored and the
   guard re-run.

**Driving:** keys follow the measured humerothoracic elevation, through hats starting at 90°
(`original_v1_review_candidate_drives.py drive_s1`). Below 90° R2 is identical to R1.

**Rejected on the way (kept out of R2):**

| Variant | Result at 160° | Why rejected |
|---|---|---|
| Two-way springs | pairs 110 → 494 | skin slid ~50 mm into the axilla |
| 10–30 iterations | pairs up to 482 | — |
| Pull-only without a guard | pairs 0–10 → 12–44 at 110–140° | new collisions mid-range |
| Unsmoothed keys | — | faceted, lumpy rear-shoulder skin (renders) |
| Guard only at the key poses | pairs +8 at 140° | interpolated poses not checked |
| Single-pass guard | +2 collapsed at 130° | later edits touched keys active at 130° |

**Bug fixed before committing:** the volume offset was applied to both sides' zones in each side's key, so raising one arm
would have inflated the other shoulder. The native test `test_s1_deltas_are_bounded_and_symmetric` caught it. The keys now
touch only their own side.

## Results

**Coupled 0–160° sweep, R1 → R2** (`r2_s1_build.json`):

| HT | Collapse | Stretch > 2 | Pairs | Volume % |
|---|---|---|---|---|
| 100 | 0 → 0 | 438 → 408 | 0 → 0 | 2.79 → 2.75 |
| 120 | 4 → 4 | 572 → 478 | 0 → 0 | 1.12 → 1.12 |
| 130 | 0 → 0 | 594 → 506 | 4 → 4 | 0.21 → 0.21 |
| 140 | 2 → 2 | 618 → 518 | 10 → 10 | −0.66 → −0.66 |
| 150 | 4 → 4 | 636 → 532 | 98 → 92 | −1.41 → −1.41 |
| 160 | 4 → 2 | 634 → 542 | 110 → 106 | −2.01 → −2.01 |

- No angle gets worse in collapse, collisions or volume.
- Stretch falls by 30–104 faces between 100° and 160°.
- **Still above a003's 400 at 160°:** S1 recovers about 40 % of the stretch that W3A added. It does not remove all of it.

**All 13 benchmarks** (`r2_validation.json`):
- 12 benchmarks are identical to R1.
- **Shoulder press:** stretch 634 → 542, pairs 110 → 106, collapse 4 → 4, volume unchanged.

**Visual** (`closeups/`, 145° and 160° front, rear and side):
- Comparable to R1.
- The pinch at the posterior arm–back junction is a little softer.
- No new artefacts at full-resolution zoom.
- **Still present:** the armpit bulge and the posterior axillary web.

## Evidence

- **Close-ups:** `closeups/`, R1 vs R2.
- **Sequences:** `sequences/shoulder_press_sequence.jpg` and `.gif` (a003 vs R2).
- **Other 12 benchmarks:** use R1's sequences in `../claude_review_r1_20261014/sequences/`. The validation shows them numerically identical.
- **Full-body and other close-ups:** R1's sets apply; S1 is inactive at rest and below 90° elevation.

## Tests

`scripts/blender_tests/test_original_review_candidate_r2.py`, 6 native tests (CI workflow `original-review-candidate-r1.yml`):
- **Identity:** the SHAs.
- **Contents:** R2 equals R1 plus exactly six S1 keys; still 67 joints with the same weights.
- **Deltas:** bounded, on their own side and bilaterally symmetric.
- **Sweep:** no worse than R1 at any angle and less stretched.
- **Live check:** the 160° row is reproduced from the saved file.
- **Benchmarks:** unchanged except the press, which improves.

## Shipping would need (owner + Lane G, PR #26)

Everything R1 needs (69 joints with the helper drive, K1 morphs, the C3 foot decision), plus the S1 driven morphs (six keys
on the humerothoracic elevation).
