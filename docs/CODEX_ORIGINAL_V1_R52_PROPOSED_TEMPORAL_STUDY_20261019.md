# Proposed R52: motion throughout the press, owner decision pending

No R52 geometry, saved model, native render or workflow exists. This proposal
follows the owner's report of the body swelling halfway through the exercise.
R47's overall outline is approved; R47/R51 surfaces remain rejected. R41 is the
latest saved Blender model. No previous candidate or test is changed.

## Further measured evidence

The original motion mask contains1796 vertices. In R51,1237 exceed the unchanged
0.5mm extra-frame-acceleration guard. At the marked pose,152 motion-mask vertices
belong to currently active silhouette-support edges;136 of them fail motion.
The worst vertex21317 supports the current outline. This connects the motion
problem to the owner-reviewed boundary, not just an unrelated interior patch.
An active edge may change after editing; this count is not an impossibility proof.

An independent convex single-vertex minimax calculation checked motion at all39
second differences of the original41 press samples. It uses the original five
editable source controls, original affine transforms and fixed110/166 controls.
Primal/dual residuals and support-plane norm checks are retained. Control boxes
relax the original45mm norm cap, making their lower bounds conservative.

| Conditional preservation at vertex21317 | Numerically verified lower bound on motion excess |
|---|---:|
| Exact marked world point |0.958798mm|
| Marked XYZ each within1mm |0.907067mm|
| Marked X within1mm, Y/Z free |0.859867mm|

All exceed0.5mm. These are conditional statements about that individual point,
not the actual full-outline requirement. Vertices could slide along the contour
or trade which edge defines it. Do not infer that the approved outline is
globally impossible or loosen it based on these reduced problems.

## Rejected finer-control probe

The existing native installer already samples71 integer-degree skin states, but
their added corrections are tied to seven source vectors. A diagnostic allowed
those integer-degree increments to vary independently at vertex21317, keeping
95/110/166 zero and its marked world point fixed.

The first coordinate-box probes exceeded45mm vector norms (up to77.942286mm).
A150-iteration material-cone probe still retained51.906220/48.183215mm maxima;
both are rejected. A stricter inscribed material box guarantees45mm vector norms.
That last probe reached0.139341mm sampled motion excess, zero early outward
increment at sampled poses, exact marked-point preservation and45mm vector norm.
However, independent inspection of adjacent integer-degree controls reveals a
90mm material jump. It is an unusable oscillating trajectory that hides between
the41 samples. It is explicitly rejected, not a passing candidate or proof of
a repair. The original tests are unchanged; additional temporal coverage is needed.

A further probe fixed every integer-degree increment through110 to zero. Its
150-iteration run retained a0.615148mm LP lower bound/0.617726mm actual excess,
then failed its unchanged0.5mm assertion. It is rejected. This conservative
inscribed-box case does not prove infeasibility under the full norm ball.

## Concrete proposed change, before implementation

Develop R52 as a separately named, unsaved study that gives the skin corrections
more control between the seven authored poses. Jointly fit space and time;
preserve the approved actual R47 outline rather than freezing every vertex at
its R51 marked position. Make the existing motion limit mandatory and explicitly
check/regularize adjacent integer-degree states, so a sampled pass cannot hide
an oscillation. Use spatial coupling so independently moving points do not
create folds. Start with a short instrumented feasibility trial, not another
unchanged long R51 search.

Keep the frozen skeleton, Basis, weights, topology, all HGPT_SHOULDER/non-S7 keys,
anchors,110 and166 controls and newer elbow/distal-arm details unchanged.
Retain the exact approved anatomical material domain; a new temporal degree of
freedom does not authorize a new anatomical editing region. Define and verify
its per-angle preservation mask before fitting. A necessary change to any of
these protections requires a separate owner decision.

Retain the original1mm actual-outline guard,0.5mm motion guard,2degree crease
guard,45mm displacement caps, all original83 native surface/contact/affine
checks,13 benchmarks, marked-normal guard, scope/protection tests and all five
historical contour/front test groups. Add temporal-coverage/oscillation tests;
never replace or loosen the old tests. If a proposal improves motion but loses
the outline or worsens folds/intersections/stretch, retain and report the failure.

Produce actual R51/R52 same-angle rear/three-quarter comparisons and press video,
with R47 shown as the approved-outline reference. Do not substitute an affine
point trace or generated image for a native model render. No model save or
promotion unless all unchanged required gates pass; owner visual approval remains
separate. A full-body feasibility result and native media remain outstanding.

This changes the skin-authoring approach. The owner asked to be consulted before
large changes, so implementation of this proposed R52 study awaits confirmation.
No workflow is launched by this report. Existing completion watches remain disabled.

## Evidence and reproduction

Read-only scripts and reports are in `docs/midpress_motion_bounds_20261019/` and
the new `scripts/audit_original_review_*_20261019.py` files. Run each audit as:

```sh
python scripts/AUDIT_SCRIPT.py SOURCE.npz SOLUTION.npz OUTPUT.json
```

Inputs are the hash-verified original-v1-r51-review artifact from run39172099330,
artifact12153660809 (SHA256d148d451c17714c0407c0134080b53f992fe4e11c7541a6d9deea56747865742).
Use tmp/r51-response/source.npz and solved.npz. Runtime NumPy2.3.5/SciPy1.17.0.
No private reference image or trace enters the repository.
