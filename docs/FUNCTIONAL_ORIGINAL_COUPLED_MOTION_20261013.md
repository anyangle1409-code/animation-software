# W1/W2 original-body coupled-motion diagnostic — provisional

Separate `codex/functional-original-coupled-motion-20261013`, stacked on
reviewed PR109 head `afe02ca65e31ab21ad6c65ed341c7cc80297884c`. The PR48
owner decision at `f9d4ca0f`, Claude work and later Lane G software remain
preserved. No source blend, medical byte, private render or Chat contract is
changed.

## What changed and what passed

The existing 67-bone runtime rig receives a guarded deterministic 0–160 degree
diagnostic. At 0/90/160 it applies a smooth project-authored clavicle/scapula
response, then fixes each upper-arm shaft to absolute humerothoracic elevation
in a 40-degree anterior scapular plane. F-SIDE-001 remains deliberate. The 29
PR109 guides follow their existing one-weight runtime attachments. The 206-bone
source stays at rest and does not drive the unchanged 17,946-vertex male.

Five pure tests and five actual Blender 5.2.1 tests pass: required samples,
nonlinear progression, finite guards, bilateral absolute humeral direction,
progressive guide movement, source remaining at rest, fail-before-mutation,
sampled body deformation and unchanged sole runtime driver. Twenty-eight
pure/inherited tests pass with the documented `PYTHONPATH`.

Six new 900 px full-body views were rendered only at changed 90 and 160 degree
poses (front/side/rear); neutral was deliberately not repeated. JSON still
measures 0/90/160. Private directory:
`C:/Users/Mark/Documents/Codex/hgpt-functional-original-coupled-motion-v1-20261013/`.
Manifest SHA-256:
`4efa972da7a8068d91d47bbf11554aaf6a506cb7887b797e9223085a4935d06a`.
All six PNG hashes match. Source blend SHA-256 remains
`670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56`.

## Reference comparison and defects

Ludewig et al. 2009 (PMID 19181982; doi:10.2106/JBJS.G.01483) reports the
expected coupled directions in 12 asymptomatic adults using bone-fixed sensors:
clavicular elevation/retraction/posterior rotation and scapular upward rotation/
posterior tilt during elevation. Its common plotted range ends at 120 degrees,
so it does not validate 160. Reported average SC posterior rotation (~31°) and
AC posterior tilt (~19°) are non-exceedance checks at 120°, not copied curves.
Hallaceli et al. 2004 (PMID 15103474) supports increasing scapular rotation at
higher elevation but is not treated as a direct fit.

Inspection of 90 front and 160 rear confirms broad elevation and framing while
exposing unresolved defects: blades are coarse, oversized and triangular;
thorax contact is unsolved; ribs remain steep and coil-like; humeral axial
rotation is not anatomically fitted. Sampled maximum skin movements (0.287 m at
90 and 0.381 m at 160) are displacement diagnostics, not quality scores. No
contact solver, breathing, accepted placement, fitted axes, accepted human
comparison, muscle sliding, deformation acceptance, clinical approval, GLB
approval or production approval exists.

## Exact next action

Correct rib surface and blade scale/placement using qualified references, then
add anatomical-frame humeral rotation and quantify shoulder/axilla volume loss,
collapse and self-intersection. Preserve this diagnostic without unchanged
rerenders.
