# Reference body match — candidate review

Front-reference fit of the production body against the supplied muscular male
photograph, per `docs/REFERENCE_BODY_MATCH_HANDOFF.md`. **Nothing is promoted.**
Built on `HomeGymPT_Male_BASELINE_v7.glb` (`54222af3…b16c4`), which is unchanged,
as are v6, v6 dressed and proven v5.

| File | SHA-256 |
|---|---|
| `HomeGymPT_Male_REFMATCH_CANDIDATE.glb` | `19f350ad610536c9ebdc76aacba1f8ab22bbf8de3a6e691d327ae99463c52f4c` |
| `HomeGymPT_Male_REFMATCH_CANDIDATE_SHORTS.glb` | `309e751d421a88adc4464c36a20597173694516c442c9af6cfdf19b626a8e7ff` |

3127 of 10839 vertices moved, worst displacement 30.6 mm. `JOINTS_0`,
`WEIGHTS_0`, `TEXCOORD_0`, `COLOR_0` and the 19304 triangles are bit-identical
to v7; the node graph is identical and the inverse bind matrices differ by
exactly 0. Only `POSITION` and `NORMAL` changed. Worst left/right difference
across 4181 mirrored vertex pairs is 0.322 mm, which is the source mesh's own
asymmetry rather than anything the masks introduced — they are mirrored by
construction.

## How both figures were measured

The photograph is segmented per row against that row's own background, sampled
at the plate margins, because the plate carries a vignette and a floor shadow
that a flat threshold swallows. Every run in a row is kept rather than the
longest: below the shorts there are two legs, and beside the torso two arms with
daylight between them and the ribs, and those gaps are the measurement.

The model is then rasterised through **the same** run extraction. Its silhouette
is produced by a CPU poser and an orthographic projection rather than a camera,
so there is no perspective to calibrate away and no render variance. Both
figures span the same sole-to-crown rows and are registered on the pelvis
midline — never on a width, since widths are what is being compared.

Two things had to be got right before any of this was trustworthy:

- **Weight normalisation.** 2912 vertices carry more than four influences, so
  `WEIGHTS_0` alone does not sum to 1. three.js reads only the first set and
  calls `normalizeSkinWeights()`; matching that is what makes these numbers
  agree with the viewport. Skinning without it put vertices 678 mm out.
- **The bind pose is a wide A-pose** — upper arm 44.4° from vertical, forearm
  57.5°. A horizontal band across an A-posed arm measures its length, not its
  width, and reported the arm as *growing* toward the wrist. The arms are posed
  down before anything is measured.

### The pose is fitted, not assumed

Stance moves a silhouette outline exactly the way thickness does. Arm hang and
leg abduction are therefore fitted first, by minimising disagreement with the
reference: **arms 10° from vertical, legs 2° adducted**. Before this, the legs
showed a strong red/blue split in the overlay that looked like a shape error and
was entirely stance; afterwards, leg widths agree to within 0.1–0.8% of height
and the difference disappears.

## The dominant mismatch is skeletal, and was not sculpted away

v7's shoulders are 3.45% of body height narrower than the reference's. A
silhouette-driven optimiser closes most of that by adding 30 mm of deltoid mass.
That is wrong, and the measurement that shows why is the outer radius of the arm
from **each figure's own humerus axis**, recovered by fitting a line through the
centres of the arm runs where the arm is clear of the torso:

| height | reference radius | v7 radius | Δ |
|---|---|---|---|
| 70% | 3.36 | 3.40 | +0.03 |
| 68% | 3.05 | 3.56 | +0.51 |
| 66% | 2.67 | 3.58 | +0.91 |
| 64% | 2.80 | 3.40 | +0.60 |
| 62% | 2.99 | 2.85 | −0.15 |
| 60% | 2.90 | 2.58 | −0.32 |

**v7's arm is already the thicker of the two.** The span gap is where the arm
attaches: the reference's humerus axis sits 10.64% of body height from the
midline, v7's at 8.23% — 2.41% per side, 4.8% of height across. That is the
clavicle and the shoulder joint, which this task may not move. Matching the
reference's shoulder width with geometry would need roughly 48 mm of radial mass
per deltoid on a body whose deltoid is already larger than the reference's.

Constraining the deltoid term to what the radii support costs almost nothing:
the unconstrained fit scored 13.75% disagreement, the constrained one 13.74%.
The inflation was buying a number, not a shape.

**This is the one finding that would change the character materially, and it
needs a decision that is out of this task's scope:** a wider clavicle and
shoulder joint in the rig. Everything downstream of it — retargeting, the
exercise definitions, the accepted curl motion, the grip — depends on the
skeleton, so it is not a body-shape edit.

## What was changed

Region by region, each term set from a measurement rather than from the score.

| Region | Term | Why |
|---|---|---|
| Deltoid / upper arm | −5 mm radial | radii above: v7 is 0.5–0.9% of height too thick at 64–68% |
| Forearm | +7 mm radial | v7 is 0.3–0.8% too thin at 56–60% |
| Thigh | −5 mm radial | landmark table: +0.58% too wide |
| Calf | −6 mm radial | landmark table: +0.79% too wide |
| Shoulder yoke | 26 mm drop | v7's shoulder top sits 2.4% of height above the reference's |
| Hip | −5.5% lateral | v7 trunk is ~1% of height too wide from 48% to 56% |
| Waist | −8% lateral | v7's narrowest point is 4.4% of height too high |
| Lower ribcage / lat | +18% lateral | v7 holds 16.8% at the 68% band where the reference reaches 19.4% — a column, not a V |

Limb terms displace radially about the bone axis, which thickens a limb without
lengthening it or moving a joint. Girdle terms are lateral scales inside a
smooth vertical window, gated on skin weight.

Three things that gating got wrong first, all found by the numbers disagreeing
with what the term should have done:

- The hip scale was gated on height alone. In an A-pose the hands hang at hip
  height, so it squeezed the arms inward and turned a 16 mm edit into a 67 mm
  one. It is gated on pelvis and thigh weight now.
- The trunk terms were gated on the spine chain alone, leaving roughly two
  thirds of each vertex's weight outside the mask, so they ran at a third of
  their nominal gain. They match the pectoral bones too now. `DEF-shoulder` is
  deliberately still excluded — widening there would fake shoulder span.
- The lat term's effect could not be read off the silhouette at all once it grew
  enough for the trunk to touch the arms: two runs merge and the reading jumps
  from 16.89% to 29.62%. It is verified against the mesh with arm vertices
  excluded.

The yoke drop saturates. 35 mm moves the shoulder top by 0.7% of height and the
score stops improving at 45 mm, because the residual sits right beside the neck
where a large drop would carve a hollow into the trapezius. 26 mm takes most of
the available benefit; the rest is left rather than trading a metric for a
scooped trap.

## Result

Silhouette disagreement with the reference, over 12–86% of height (the head,
hands and feet are excluded: hair, finger spread and stance are not body shape):

**v7 17.10% → candidate 15.86%.** Bands differing by more than 1.5% of height:
**29 of 49 → 23 of 49.**

| Landmark | reference | v7 | candidate | v7 Δ | candidate Δ |
|---|---|---|---|---|---|
| head width | 10.35 | 9.92 | 9.92 | −0.43 | −0.43 |
| neck width | 7.26 | 7.26 | 7.26 | 0.00 | 0.00 |
| shoulder width | 29.69 | 26.24 | 25.74 | −3.45 | −3.95 |
| hip width | 21.50 | 23.51 | 23.01 | +2.01 | +1.51 |
| narrowest waist | 15.82 | 16.03 | 15.38 | +0.22 | −0.43 |
| thigh | 11.21 | 11.79 | 11.57 | +0.58 | +0.36 |
| knee | 5.75 | 6.04 | 5.82 | +0.29 | +0.07 |
| calf | 7.26 | 8.05 | 7.76 | +0.79 | +0.50 |

Percentages of sole-to-crown height. The shoulder figure gets *worse* by design:
thinning the over-thick upper arm to match the reference's radius narrows the
span that the attachment position already made too narrow. Closing it the other
way is the skeletal change above.

Trunk width down the body, which is where the V-taper lives:

| height | 50% | 52% | 56% | 58% | 64% | 66% | 68% |
|---|---|---|---|---|---|---|---|
| reference | 20.63 | 19.84 | 17.61 | 16.61 | 15.96 | 17.25 | 19.41 |
| v7 | 21.64 | 20.63 | 18.55 | 17.33 | 16.92 | 16.20 | 16.78 |
| candidate | 20.70 | 19.48 | 17.47 | 16.46 | 16.41 | 16.29 | 19.61 |

**Shoulder slope**, the handoff's primary criterion, measured from the top edge
of the silhouette between the head's widest point and the deltoid tip:
reference 50.7°, v7 57.0° (+6.2°), candidate 56.8° (+6.1°). The 2° target is not
met and cannot be met by geometry: the angle is steeper because the run is
shorter, and the run is the shoulder width.

### Largest remaining front-silhouette mismatches

1. **Shoulder and upper-arm span, 70–80% of height, 2–4% of height.** Skeletal,
   above.
2. **Hand height, 42–46% of height, up to 15%.** The reference's hands hang
   lower. Arm length is bone length.
3. **Neck/trapezius, 82–84%, +2.2% and +5.0%.** The residual yoke, deliberately
   left rather than hollowed.
4. **Feet, 2–8%.** Stance width and the photograph's floor shadow, not shape.

## Rig integrity

`05_candidate_skeleton_overlay.png` draws the proven joint centres on the
candidate: shoulder joints inside the deltoid mass, elbow centres at the visible
elbows, wrists at the wrists, hip centres inside the pelvis/thigh transition,
knees and ankles on their joints. Nothing was moved to chase the image. The
same image shows the reference silhouette behind, where the shoulder markers sit
visibly inboard of the reference's deltoid outline.

## Validation

Whole-body edge strain through the real-character diagnostic, worst value per
exercise, v7 → candidate:

| Exercise | P95 | P99 | max | over 3× |
|---|---|---|---|---|
| Bodyweight squat | 1.2410 → 1.2377 | 1.6216 → 1.6251 | 3.063 → 3.087 | 4 → 4 |
| Dumbbell curl | 1.2197 → 1.2105 | 1.4891 → 1.4855 | 2.247 → 2.223 | 0 → 0 |
| Shoulder press | 1.2369 → 1.2393 | 1.6954 → 1.6777 | 3.235 → 3.254 | 10 → 10 |
| Push-up | 1.2391 → 1.2364 | 1.6572 → 1.6626 | 2.458 → 2.477 | 0 → 0 |
| Pull-up | 1.3254 → 1.3271 | 1.9065 → 1.9305 | 4.283 → 4.286 | 146 → 126 |

P95 within 0.009, P99 within 0.024, maximum stretch within 0.025, and the only
change in the over-3× counts is a pull-up improvement. No threshold was altered.

Inspected at curl bottom, mid and peak; deepest squat; press bottom and
overhead; push-up top and bottom; pull-up bottom and top, against v7 on the same
frames and cameras. No pinching, crease, shoulder collapse, self-intersection,
weight-transition defect, asymmetry or equipment-contact change.

Typecheck clean, `vite build` clean, suite 292 passed / 1 skipped / 1 failed —
the pre-existing `strainReview` 5-second timeout, which reproduces with no
changes and is environmental. Two further files (`neck`, `shoulder`) time out
the same way when a Playwright render is running concurrently and pass when it
is not; that is machine load, not a regression.

## Shorts

The approved F3 garment is carried onto the candidate verbatim — the builder
does not reproduce F3 bit for bit, so it is transplanted, as it was for v7. The
body only moved inward under the garment, and the closest body-to-garment
approach improves from **0.67 mm to 1.97 mm**. No intersection, no distortion.

## What genuinely needs side or rear reference views

The supplied image is a front view and was used for widths, vertical
proportions, front silhouette and mass distribution only. Front-invisible depth
is left at v7 apart from the smooth transitions the lateral terms imply. These
cannot be judged from it and were not invented:

- chest depth and the sternum-to-spine dimension;
- scapular shape, mid-trapezius and the rhomboid region;
- glute projection and depth;
- lumbar curve and the small of the back;
- calf depth as opposed to width;
- the profile of the deltoid from the side.

The rear renders in `shots/` show the lat flare the front fit implies, which is
the one place a rear reference would most change the result.
