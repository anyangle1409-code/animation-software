# R49 bounded-refinement surface repair study

Owner-approved target: R47's actual overall arm-to-body outline. R47's
surface was unsafe and no model was saved. R48 timed out before its first
accepted increment; its failure record and original artifact are retained.

## Diagnosis and change

R48's unregularized minimax solution introduced many unrelated movements.
Its predictive cone-refinement loop requested1251,4177 and4661 additional
cuts before ever checking a real step, then timed out after25minutes.

R49 restores the existing R46 minimum-L1 preference, limits predictive
refinement to two solves per accepted epoch, retains the latest learned
normal/motion cone directions between epochs, and immediately applies the
same exact nonlinear area/orientation/contact/front/crease/motion gates with
backtracking. A structural test verifies the nonlinear gate and numerical
safety-limit expressions are identical to R48. Every original source array,
target, editable material coordinate and posterior coverage mask is preserved.

This changes proposal computation only. No old test or acceptance threshold,
skeleton, Basis, weights, topology,166, anchor, protected distal arm,
HGPT_SHOULDER or non-S7 key changes. Source and dense45mm limits remain.

## Local preflight evidence (not native model acceptance)

- Unregularized single-proposal step: accepted in5.5seconds, but only a tiny
  movement. A three-step regularized-only trial closed the outline gap by
  0.5507mm and failed the new1mm short-preflight progress guard.
- Retained cone information plus two predictive rounds: three accepted steps
  in44.2seconds, closing the actual marked-outline gap by1.723454mm. The
  progress guard now passes. The remaining gap is39.311509mm at the fitter's
  sampled stations, so the owner's shape requirement is still unresolved.
- Unchanged back-motion test passes:0.452526mm excess (limit0.5).
- Unchanged posterior-crease test passes:1.872746degrees excess (limit2).
- Exact nonlinear gate/limit policy test passes; all-parent-array preservation
  test passes. The unchanged R47 distal/anchor/outside-scope and source/dense
  cap tests pass on this preliminary state. The complete original R47 test,
  including its movement assertion, still runs later on the native study.
- The final instrumented implementation repeated those exact delta arrays
  in45.6seconds and passed the five R49 preparation/policy/retention/progress
  checks plus all four unchanged R48 preparation/derivative checks.

The local benchmark uses NumPy2.3.5/SciPy1.17.0. R48 used NumPy1.26.4/
SciPy1.11.4 in CI. R49 pins its fitting/test environment to the locally tested
versions; Blender remains checksum-pinned5.2.1. These are authoring tools;
no runtime/app dependency or third-party asset is introduced.

A crossover-disabled LP probe was discarded because the solver returned an
unknown/nonoptimal status. It was not accepted based only on primal feasibility.
Its benchmark and unchanged-R48 problem capture are retained as diagnostics.

## Native execution and honest reporting

The local preflight used a120second bound. CI permits180seconds for runner
CPU variation; no model-test threshold changes. The workflow repeats it,
then runs its unchanged safety/protection tests and the new early-progress
test before the main fit. Main fitting is bounded to25minutes. Accepted
checkpoints and the latest linear problem are retained. Fit exit and chosen
checkpoint are recorded even if fitting fails. If the main fit cannot improve
on the verified preflight, that fact is reported explicitly.

All83 native responses,13 benchmarks, actual approved-outline1mm guard,
marked-normal test, old motion/crease and historical contour/front tests,
full R47 scope test and protected identities remain mandatory evidence.
The pipeline has no model-save step. Native R47/R49 images and a press video
compare matching rear/three-quarter cameras and angles. Partial fitting or
workflow success never counts as shape completion or owner visual approval.

Any further large anatomical scope change still requires the owner. Private
reference images and their traces stay outside the repository.
