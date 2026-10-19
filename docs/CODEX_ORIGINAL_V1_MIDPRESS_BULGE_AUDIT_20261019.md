# Mid-press body bulge: read-only R47/R51 investigation

Owner feedback, 19 October 2026: the body appears to bulge halfway through the
exercise. This investigation changes no model, candidate, source response,
deformation function, frozen asset, test assertion or acceptance threshold.
R51 remains rejected and unsaved; R41 remains the latest saved model.

## Reproduction and attribution

Inspected the actual R47/R51 matched press video and R51 native frames. The
upper-side/back surface swells then pulls inward during the lift. This appears
in R47 and remains in R51. The torso-wide visible effect must not be equated
with the single worst vertex in the existing motion test.

Reconstructed R47 from the original author function and immutable R51 source.
Its marked target matches the stored actual R47 target to 2.29e-13 mm. The
unchanged back-motion mask has a worst additional frame-acceleration magnitude
of 3.556880 mm for reconstructed R47 and 2.073693 mm for R51, against the existing
0.5 mm guard. Native R51 measurement is 2.074110 mm. The worst R51 vertex is
21317, rest position (-0.195541, 0.090208, 1.384987) m, at frame18/40,
t=0.45, approximately110.824 degrees elevation. These are mesh coordinates,
not changed bone/joint positions.

The response chain is `original_review_r43_sampling.basis()` clamped CubicSpline
-> integer-degree increments -> `original_review_r43_native.install()` ->
unchanged S7 drivers/pose and native skinning. The R41 baseline shapes remain
piecewise-linear; only the added body increment has this cubic interpolation.
The spline has negative blending weights. With zero increments at95 and110
degrees and nonzero later increments, it creates an early outward excursion
before the intended inward correction. In the original back-motion mask R51
adds up to2.076870 mm outward before110 degrees. The source baseline is held
identical in the ablation, so this added excursion is attributable to the
increment/interpolation rather than an altered skeleton or camera.

This is a demonstrated contributor, not proof that interpolation alone explains
every visible torso bulge. Later outward increments remain even after replacing
the blend, and the source control trajectories themselves need investigation.

## Rejected interpolation-only probes

Changed only how R51's existing seven added increments are interpolated. The
original R41 response, original poses, source increment coordinates and original
motion mask stay fixed. Recovered exact active integer-degree weights from the
stored affine response with maximum coefficient residual1.28e-16. This reproduces
the unchanged motion metric exactly. These are affine diagnostic probes, with
no Blender render, model save or candidate promotion.

| Measurement | Existing cubic | PCHIP probe | Linear probe |
|---|---:|---:|---:|
| Outward increment before110 degrees |2.076870mm|0mm|0mm|
| Maximum additional frame acceleration |2.073693mm|3.689935mm|3.744889mm|
| Maximum dense material increment |42.852828mm|42.544211mm|42.544211mm|
| Maximum marked-pose geometry change within motion mask |0mm|0.174497mm|0.231788mm|

Both replacements remove the early excursion but make the worst motion failure
worse. Neither is a fix. The marked geometry-change measurement is not the
approved full-outline test; no outline pass is inferred from that number.
These probes do not validate folds, contacts, all83 native samples or13 movement
benchmarks. R51's existing failures remain unchanged and recorded.

A separate single-vertex SLSQP probe held the marked world point fixed and tried
to enforce the unchanged motion bound using only its five editable source keys.
It failed after309 iterations; retained diagnostic excess1.661959mm. It was
discarded. A failed local solve is not a proof of infeasibility, and fixing an
interior point is stronger than preserving the approved outer outline.

## Next correction boundary

The R51 search retained unsafe states by reducing an aggregate repair score;
that does not enforce smooth motion as a hard condition at each accepted state.
A justified next experiment must address the time course and spatial distribution
jointly, evaluate actual intermediate frames and keep the unchanged0.5mm motion
guard and1mm actual-approved-outline guard. It must also eliminate new contacts,
reversed faces and excessive crease/stretch. Do not simply replace the spline,
increase fitting time or weaken a test. No next geometry candidate is created by
this audit. Changes to protected anchors,110/166 controls, skeleton, distal arm,
weights, topology or editable anatomical scope require separate consideration
and any applicable owner approval.

## Reproduce

Download/hash-verify run39172099330 artifact12153660809,
`original-v1-r51-review` (ZIP SHA256
`d148d451c17714c0407c0134080b53f992fe4e11c7541a6d9deea56747865742`).
Use the extracted `tmp/r51-response/source.npz` and `solved.npz`:

```sh
python scripts/audit_original_review_midpress_bulge_20261019.py SOURCE.npz SOLUTION.npz OUTPUT.json
```

Runtime: NumPy2.3.5/SciPy1.17.0. Source SHA256
`2a6c01cf7eacd3d1ceb47ae9f131f76dd0487fce5d3518d5cd1df65bc059fa8d`.
Audit output and rejected-probe measurements are in
`docs/midpress_bulge_evidence_20261019/`. No private reference photo/trace is used.
Actual existing media remains in
`ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r51_study_20261018/`:
R47_R51_full_outline.jpg, R47_R51_marked_l/r.jpg,
R47_R51_press_comparison.mp4 and shoulder_press_r51.mp4.

Conclusion: root-cause investigation progressed; body bulge and surface repair
remain unresolved. No new accepted shape, native render/video or saved model.
