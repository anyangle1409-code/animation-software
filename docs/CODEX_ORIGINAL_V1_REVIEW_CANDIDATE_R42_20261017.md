# R42: owner-confirmed arm-to-body contour study

**REJECTED_NUMERIC_CHECKS. No R42 blend was saved or accepted.**

The owner confirmed the older reference's earlier turn from the straight arm
into the torso, retaining the newer arm and elbow. R42 tests that restoration
on immutable R41. Only body-side increments of S7 controls120/130/136/145 change.
Upper-arm/elbow material coordinates,110/156/166, front anchors and all non-S7
coordinates remain fixed. Canonical bones, production/V assets, Basis, topology,
weights and HGPT_SHOULDER keys are unchanged. Private photos are excluded.

| Native measurement | R41 | R42 study |
|---|---:|---:|
| Marked135.625-degree stretched triangles |19|15|
| Top166-degree stretched triangles |53|53|
| Maximum crushed triangles,41 benchmark-press samples |0|0|
| Front130-degree peak, left |23.122°|22.988°|
| Front130-degree peak, right |23.628°|23.562°|

The confirmed profile and unchanged rear-contour, bow/ridge, straight-arm and
front tests pass. However, six of83 native area samples fail:27/28/30/31/72/75.
Four samples have additional stretched triangles; two exceed the peak-area
severity allowance. Four new contact records (three distinct triangle pairs)
occur at press samples27/28,142.171°/145.264°. Reversed normals:0. This is a
regression and blocks acceptance. Maximum affine/native error:0.000318mm.

R42's45mm final material bound is specific to the confirmed contour restoration;
the measured maximum is36.275756mm. R41's0.75mm strain-only bound and tests remain
unchanged. Trial1 broad locks stalled near220 marked stretched triangles.
Trial2 narrow locks/5mm redistribution ended at187. Trial3's exact contour lock
and hard final-vector cap reached15, but exhausted1,000 iterations with the
failures above. No test was weakened or deleted. Native results supersede the
affine predictions. The original guarded model build and full13-benchmark suite
were not reached because feasibility failed.

Evidence: `ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r42_study_20261017/`.
It contains both-side marked-angle and120/130/135.625/145/156/166-degree matching
comparisons, an8-second press video, native geometry/JSON, every test log and
exit code, and the frozen delta. Source:`0b95a2ada8a8b52e8ac00b79e81bdabba76a1eed`.
Blender5.2.1 Actions run39073116321; artifact12115574670, ZIP SHA256
`45db8415c45616af0151138fd91b6409682656a101100740f32bf76c0138bb30`.
Reproduce with `.github/workflows/original-review-r42-study.yml`.

Before a fourth geometry approach, discuss a strict feasibility stage for the
remaining area/contact limits with the owner. Preserve the confirmed contour
and newer arm/elbow; use a new R43 folder if that approach is authorized. The
unactivated full-candidate pipeline draft is retained with the feasibility notes;
it is not evidence of a successful model build. No merge or force push occurred.
