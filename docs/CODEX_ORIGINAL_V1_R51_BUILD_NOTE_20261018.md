# R51 bounded outline-preserving repair study

Owner target: R47's actual overall arm/body outline, with its rejected surface
repaired. R49 was rejected. R50's unsafe retained checkpoint held the outline
but stalled during its third LP. R41 remains the latest saved model baseline.

## Measured bottleneck and rejected probes

The captured third LP has 49211 rows, 7389 field columns, 6606 active controls,
12103715 coefficients, and a1.125mm trust box. Its input hashes and runtime
diagnostics are in docs/r51_preflight_evidence_20261018/. Reconstruct it from
the immutable R49 response and R50 retained checkpoint; no private image is input.

Exact box presolve replaces8537 always-violated soft hinges with their identical
linear cost and removes3158 always-zero soft hinges. It preserves all750 hard
rows and the full mathematical objective. Four tests, including30 seeded full
versus reduced LP comparisons, pass. The reduced37516-row optimal LP still timed
out. A solver trace confirmed slow interior-point convergence, not crossover.
An inspected intermediate HiGHS point was invalid and violated hard/control
bounds; it was rejected, never applied and never called an optimum.

Two prototype benchmark wrappers also timed out before optimization because
they repeatedly decompressed an NPZ metadata array. The harness was fixed to
cache it. These failures remain recorded and are not solver timing evidence.

## R51 change

A first-party bounded diagonal primal-dual calculation now proposes a search
direction for the same weighted-hinge objective. Exact hinge presolve remains.
Independent half-space/box projection and original-row reconstruction require
hard residual <=1e-6 and control bound residual <=1e-8. Approximate proposals are
explicitly marked NOT OPTIMAL. The captured stalled problem produced a verified
proposal in7.617 seconds with hard residual9.5027e-8 and no control-bound excess.
Its objective was8936.340164 versus11285.296348 at the starting point.

The actual fitter retains a trial only when it lowers the full joint-pose repair
merit, keeps both unchanged45mm source/dense material caps, and keeps the actual
R47 rear/three-quarter outline within0.95mm at all original5mm height stations.
The original outline test is unchanged at1mm. Internal unsafe trials are search
evidence, never accepted surfaces. The exact final nonlinear function and every
area/orientation/contact/front/posterior/motion limit match R50/R49, verified by
an AST test. All83 native checks and13 benchmarks still run afterwards.

No prior test or model acceptance threshold is edited. The R49 safe-seed
preflight policy is inapplicable to an explicitly unsafe R47-shape repair search:
R51 gates its short preflight on completed useful progress, outline and scope;
unchanged surface/motion tests still run and their failures remain retained.
The pipeline has no Blender model-save or promotion step, even if checks pass.

## Local preflight, not native acceptance

Three retained steps completed in53.9 seconds from R50's exact checkpoint.
The diagnostic repair merit fell31.425611%; this is an optimization score,
not a percentage of anatomical correctness. All six new test groups pass:
four exact-presolve tests, three bounded-proposal tests, final-policy test,
three retention tests, immutable-input test and three-step progress test.

| Unchanged measurement | R50 checkpoint | R51 local preflight | Guard |
|---|---:|---:|---:|
| Approved-outline error |0.907752mm|0.948416mm|<=1mm|
| Marked-pose reversed faces |14|9|0|
| Back-motion excess |3.226985mm|2.622249mm|<=0.5mm|
| Posterior-crease excess |177.658803degrees|176.805114degrees|<=2degrees|

The outline error got slightly worse but remains within its unchanged guard.
All four unchanged R47 scope/cap/anchor/distal-arm tests pass. Marked-normal,
motion and posterior-crease tests still fail. No local native BVH/contact report,
13-movement benchmark, new render/video or Blender model was produced.
The early preflight log inherited a stale backtracking reason from the old
nonprofile reporter; production now prints actual cap/merit/outline values.
This changes logging only; the retained geometry/condition is unchanged.

## Native execution and honest reporting

Workflow .github/workflows/original-review-r51.yml repeats the three-step trial
within180seconds and requires >=10% merit improvement, <=0.95mm outline error
and unchanged scope tests before a bounded15minute main search. It retains
timeout/failure exit codes and the latest search state, including preflight-only
fallback, explicitly as unverified. Authoring versions remain NumPy2.3.5,
SciPy1.17.0 and checksum-pinned Blender5.2.1. No app/runtime dependency is added.

Then run all83 native checks, all13 unchanged benchmarks, original motion and
posterior-crease tests, original R48 marked-normal and1mm actual-outline tests,
full R47 scope/protection tests and all five historical contour/front tests.
Every failure remains recorded. Render actual matched R47/R51 full-outline and
both shoulder close-ups plus comparison and R51 press videos. R50 had no native
media, so R47 is the real previous rendered comparison. Never substitute old media.

All output goes into a new immutable codex_review_r51_study_20261018 folder.
Frozen skeleton, Basis, weights, topology, HGPT_SHOULDER/non-S7 keys, lockout,
anchors and protected distal arm/elbow remain unchanged. No main merge or force
push. No private photo or trace enters the repository. Any broader anatomical
scope or topology change still requires owner approval.

Workflow success means evidence completed. It does not mean accepted skin,
a saved model, a completed shape repair or owner visual approval.
