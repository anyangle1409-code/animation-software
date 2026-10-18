# R50 outline-preserving feasibility investigation — blocked, not accepted

The owner rejected R49 on 18 October and asked to continue. R47's actual overall
outline remains the target; its surface was never approved. This investigation
changes the search direction within the same previously approved skin region.
It does not authorize broader anatomy edits, save a Blender model, or start CI.

## What was measured

R49 moved at most 4.190928 mm in material coordinates, versus R47's 44.766335 mm.
It started from safe R41 and retained only steps that stayed safe, leaving a
36.754354 mm outline mismatch after its timeout. A 200-iteration least-squares
projection of R47 into the existing smooth field left 3.121720 mm outline error
and exceeded the 45 mm material cap. That projection did not converge; it is
not a proof that the field or authorized region cannot represent the target.

R50 instead seeds the exact unsafe R47 displacement, holds its actual rear and
three-quarter silhouettes, and reduces combined surface-repair residuals.
The final nonlinear safety function and its limits are structurally identical
to R49. Internal unsafe search states are permitted solely as experiments;
they are not accepted models or surface-safe checkpoints. All outline and
material bounds remain hard in the proposal and exact trial-retention checks.
The fitter samples the same 5 mm height stations as the original outline test
and uses a stricter 0.95 mm internal guard; the original test still requires 1 mm.

The old maximum-residual proposal lets nearly singular folded-face constraints
dominate. A new combined-slack LP passed a regression test that first failed
against that old proposal. Keeping only current constraints, rather than
accumulating predictive cuts, retained two search steps in 132 seconds:

| Measurement | R47 seed | Retained R50 trial | Required |
|---|---:|---:|---:|
| Error from approved R47 outline | 0 mm | 0.907752 mm | <= 1 mm |
| Reversed faces at marked pose | 17 | 14 | 0 |
| Back-motion excess | 3.556961 mm | 3.226985 mm | <= 0.5 mm |
| Posterior-crease excess | 179.212928 degrees | 177.658803 degrees | <= 2 degrees |
| Combined diagnostic repair score | 44142.578099 | 35483.282323 | Not an acceptance test |

The diagnostic score fell 19.616652%. It is an optimization objective, not a
percentage of anatomical correctness or proof of repair. Compared with safer
R49, this trial regresses surface orientation and motion, because it starts
from R47's unsafe approved-outline state. It must not replace R41 or R49.

## Failures and limits

- The initial outline-first minimax probe retained one small step, then a
  subsequent solve was killed with exit 137. Two large probes had overlapped;
  avoid that memory contention. Its first retained step slightly worsened the
  motion residual despite lowering the aggregate score.
- The combined objective with predictive memory timed out on its second LP
  after constraints grew from 46364 to 83173.
- Rebuilding current constraints avoided that growth, but the third LP still
  reached its 90-second limit with 49211 rows and 6606 active controls. The
  three-step preflight did not complete.
- Dual simplex on that same third-state problem, with the same 1.125 mm trust
  bound, also reached its 45-second limit. An earlier setup was interrupted
  before a result because its trust bound differed; that log remains retained.
- The unchanged marked-normal, motion and posterior-crease tests fail. The
  original 1 mm outline test and all four R47 scope/cap/anchor/distal-arm tests
  pass on the retained trial. The final-safety AST test and two new LP tests pass.
- No full 83-pose Blender/native BVH check, 13 benchmarks, native identity
  measurement, historical rendered contour/front tests, new images or video
  were run. No full workflow was launched. No Blender model was saved.

No existing test, target, acceptance limit, skeleton, weights, Basis, topology,
HGPT_SHOULDER key, V-series asset, lockout, anchor or protected distal arm was
edited. This commit adds investigation code and separately named evidence only.
No private reference image or trace is included.

## Evidence and reproducibility

Evidence: `ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r50_feasibility_20261018/`.
Its JSON records hashes, failures, full two-step history and unchanged test exits.
`retained_UNSAFE_search_delta.npz` is an unsafe displacement checkpoint, not a
saved Blender model. Experiment scripts and all failed logs are preserved there.
The root R50 solver/LP files are draft investigation code, not a finished build.

Inputs are the hash-verified R49 artifact from run 39166154369 and R47 artifact
from run 39153244090. The R49 archive SHA256 is
`f16479c0417bc3ca695ad0bbdd52e9dd83cae2b6c3b5495f2a78e3c4b31766a3`.
Source, seed, contact-report and retained-state hashes are in the record.
Authoring runtime: Python 3.12, NumPy 2.3.5, SciPy 1.17.0,
OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1. These are existing authoring tools;
no new app/runtime dependency or model asset was introduced.

## Next bounded investigation

Capture the complete third-step LP, including row scales, labels and trust, so
performance changes can be compared on byte-identical input. Investigate row
equilibration or a bounded working-set proposal without changing the mathematical
objective or any final test. Continue checking all 83 responses in the exact
trial merit and final gate, even if a proposal uses fewer active linear rows.
Do not treat a solver timeout or feasible-but-unverified proposal as optimal.

Before another long native run, require a completed short preflight, retained
outline error <= 0.95 mm, useful measured surface progress, and preserved scope.
Final model acceptance still requires every unchanged native, motion, crease,
benchmark, outline and protection check plus owner visual review. Any broader
anatomical scope or topology change requires owner approval.
