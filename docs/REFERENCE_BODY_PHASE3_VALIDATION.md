# Phase 3 — full exercise/contact/deformation validation

Run once on the retained Stage 2 state, as the brief asks, rather than
repeatedly during tuning. Nothing promoted or merged.

## Every required pose

| pose | worst belly outside skin | nearest offender | technique / reachability |
|---|---|---|---|
| curl Bottom | 0.59 mm | deltoid_medial | clean |
| curl Mid | 0.59 mm | deltoid_medial | clean |
| curl Peak | 0.41 mm | deltoid_medial | clean |
| curl Return | 0.59 mm | deltoid_medial | clean |
| squat deepest | 5.71 mm | erector_mid | clean |
| press Bottom | 0.93 mm | erector_mid | clean |
| press Overhead | 0.93 mm | erector_mid | clean |
| push-up Top | 3.77 mm | pectoralis | clean |
| push-up Bottom | 0.68 mm | forearm_extensors | clean |
| pull-up Bottom | 0.68 mm | quadriceps | clean |
| pull-up Top | 5.03 mm | erector_mid | clean |

Allowance is 7 mm. Every pose is inside it, nothing is unreachable, and no
authored technique rule is violated in any of the five exercises. The 5.71 mm
at the deepest squat is the pre-existing erector figure and is unchanged by
Stage 2 — it reads identically with the widening disabled.

## What this pass does and does not measure

Measured here: containment across every belly at every required pose, and the
full technique and reachability report per exercise.

**Not** measured here, deliberately. An earlier version of this harness posed a
skinned rig and read edge lengths off `mesh.geometry`, and reported strain of
exactly 1.000 everywhere — three.js skins on the GPU, so that attribute never
moves. Rather than report a column that could only ever say "no deformation",
skin strain is left to the two tests that do the CPU skinning properly and both
pass in the suite:

- `src/body/shoulder.test.ts` — worst stretch 5.215 and tightest 0.1580 across
  the shoulder through every exercise, both **better** than leaving the Stage 2
  surface shift out (5.308 and 0.1324);
- `src/editor/strainReview.ts` — whole-repetition strain scan.

Equipment lock and contact likewise come from tests that already cover them:
`exercises.test.ts` holds every locked contact still for the whole repetition in
all five exercises, and renderer-versus-exporter grip agreement measures
0.0000 mm at every sampled time on both sides.

## Regions

The inspection list is covered by the measurements above plus the retained
Phase 1 and Stage 2 evidence: neck/traps/shoulders/armpits by the containment
survey and the shoulder strain test; elbows, forearms and wrists by the strain
scan and the Stage 1 forearm proportion; palms, fingers and thumbs by the locked
grip figures (fingers −0.46 / −0.36 / −0.22 / −0.11 mm with zero inside, thumb
+1.18 mm, palm −2.54 mm, wrap 252°); equipment lock as above; chest, waist,
hips, knees, calves and feet by the reference overlay, where every landmark
except the shoulders sits inside 0.8% of figure height and the shoulders are now
at −0.29%.

Contacts were re-derived from rules rather than preserved: the pull-up grip
sockets moved with the shoulder, the pull-up hang height was recomputed from arm
length and shoulder position, and the push-up width and body-line envelope were
re-derived. None of the previously accepted world-space positions were kept
merely because they had been accepted.

Curl remains closed: no Stage 2 regression was found in it, and its thigh
clearance improved to +4.68 / +4.79 mm.

**Phase 3 passes.** Continuing to Phase 4.
