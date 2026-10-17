# R43: whole-motion back fitting

Owner authorized continuing after discussion of R42's failed moving back. Keep
the approved junction relation and newer arm/elbow; show native before/after
motion. R41 is the immutable model baseline; R42 is a rejected frozen study.

Diagnosis: S7 uses piecewise-linear elevation hats. R42's authored body changes
vary sharply between controls and fade to zero at156. The largest per-vertex
back-frame second difference exceeds R41 by10.194447mm. R42 also has six area
failures and four new contact records. Its soft objective traded these violations
against other energy terms; increasing iterations did not ensure feasibility.

New RED test: every sampled posterior body point's frame second difference must
stay within0.5mm of R41, over the full41-frame press. R42 fails by10.194447mm.
This is a motion diagnostic, not proof of anatomical realism; owner video review
is still required. All original shape, front, area, contact and preservation tests
remain unchanged. The R42 approved-junction profile envelope also remains.

Implementation: sequential linearized feasibility constraints on area,
orientation, measured native contact separation, exact front smoothness, the
marked junction profile,45mm material bound, and back-motion acceleration. Replace
R42's broad per-key contour-component locks with direct marked-pose silhouette
constraints, freeing surrounding back material to move smoothly. This changes an
optimizer construction, not an acceptance test. Frozen arms/elbows, control166, front anchors, non-S7 coordinates, Basis, bones, weights, topology,
HGPT_SHOULDER and V-assets stay exact. No private photo is stored.

1. Repair against all83 responses with sparse linearized constraints and small
   material steps; inspect every violated gate and keep failed checkpoints.
2. Validate actual Blender5.2.1 geometry and contacts before any model save.
3. Build a separately named R43 only if feasible, run original guards, unchanged
   tests and all13 benchmarks. Preserve failures and never overwrite a model.
4. Deliver R42/R43 and R41/R43 matching-angle back/three-quarter comparisons and
   a complete press video, with an honest report of regressions.


Whole-motion refinement: the initial strict repair using the seven original
linear hats stalled with motion violations. Densifying a smooth body curve while
still freezing body110/156 also failed to clear that limit. Both were stopped
before any model save; checkpoints remain diagnostic, not accepted candidates.
R43 now adds S7 samples at96..166 degrees and fits a clamped cubic body increment
across95/110/120/130/136/145/156/166. Original R41 arm deformation is reproduced
algebraically at every angle by linearly interpolating its original S7 baseline
into the added samples. The original drive code is unchanged.

Body-side110/156 increments are now editable, within45mm, to avoid forcing the
new fullness to appear and disappear over the shorter110..156 interval. Arms
and elbows at those controls remain exact, and166 remains entirely frozen so
top-of-press geometry is preserved. This is an intentional R43 body-motion scope
change; R42's endpoint-freeze tests remain unchanged for R42. The new whole-motion
0.5mm test and all older general profile/front/area/contact/identity tests remain.
The added S7 keys do not alter non-S7 keys or the canonical bone transforms.

Additional RED diagnostic: posterior adjacent-face crease angles must not exceed
R41 by more than2 degrees over both complete41-frame paths. R42 failed by
109.0886 degrees. This test is new; no older threshold was altered.

The minimum-step quadratic subproblem is solved through a bounded dual solve;
its residual is logged. Approximate subproblem solutions are only proposals:
exact nonlinear area, front, posterior crease, motion, contact separation and
material-bound checks still decide every accepted fitting step. A subproblem's
convergence is never reported as candidate acceptance. Normal-vector cone cuts
constrain the actual adjacent-normal difference, allowing existing folds to
unfold instead of freezing the original normal difference.
