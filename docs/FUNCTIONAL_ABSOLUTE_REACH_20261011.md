# W1/W3 absolute arm-direction correction — provisional

Parent PR69 c8fb99d63a49bfb0c61ab8894bf1b64068c1fdb7 all4CI SUCCESS.
Shared plan PR48 f9d4ca0f unchanged; G4j02243c5d fetched and preserved.
Separate branch `codex/functional-absolute-reach-20261011`; no source/body
assets overwritten, no Lane G code changed. Source c004 record SHA256
99500d94e06c66ca489bdaccc0345446f98794946254c5e592d9449696f396c1 unchanged.

## Primary human-motion comparison and bounded decision

[Ludewig et al2009](https://pmc.ncbi.nlm.nih.gov/articles/PMC2657311/)
DOI10.2106/JBJS.G.01483, PMID19181982, studied twelve asymptomatic adults
using bone-fixed sensors. Their scapular-plane task was40degrees anterior
to the coronal plane. They distinguish humerothoracic from glenohumeral
angles and define axial rotation using epicondylar anatomical axes.
Their common plotted elevation range ends at120degrees; these data do not
validate our160degree endpoint or universal loaded movement limits.

Comparison with our implementation: PR68/69's parameter rotates from rest,
not absolute HT. The new separately authored profile makes shaft direction
explicit relative to world-down, in the experimental40degree plane.
No paper figures, participant bytes, or scan meshes copied into assets.
Clavicle/scapula coupling remains the existing authored hypothesis, not
a fit to cohort trajectories. No clinical axial-rotation or rhythm claim.

## Executed verification and actual images

3new native tests observed missing-feature FAIL then PASS; invalid input
refused before mutation, bilateral absolute elevation/plane, rest/record
identity, segment lengths and GH attachment verified. A first test wrongly
equated scapular control tail with GH: record says inferior angle, so test
corrected to the rigidly transformed source GH, not a tolerance relaxation.
Inherited2thorax native +3thorax pure +7shoulder pure PASS; no1097full-suite
rerun (known historical20fail/41errors/1skip remains).

Actual Blender5.2.1 generated nine800px front/side/rear PNG at0/90/160,
new private scene and row-major native control matrix samples:
`C:/Users/Mark/Documents/Codex/hgpt-functional-absolute-reach-v1-20261011/`.
Native SHA25682b8785277ae1107dc9ed7dc282c6f3884fe3cf5362d0a3d3cc1ab138946f192.
All10generated file hashes checked independently and match manifest.
160degree measured HT159.99998929degrees bilaterally. Old unchanged20pilot
views and six context views not rerendered locally; CI retains regression
tests but skips unchanged context images for this topic.

Actual90side and160front inspected: horizontal forward component at90,
superior arm shafts at160; broad coarse blades and steep upper rib paths
remain visibly defective. No claim of correct scapular contact or full human
silhouette. Still upper shoulder/thorax only, no elbows/hands/skin/muscle.
`human_reference_compared:false` means no photo/video pose-match acceptance;
the methodological paper comparison above is partial, not a human-motion PASS.

Next: independent code review/exact-headCI, then correct authored thorax/
scapula surfaces and local anatomical axes, extend full-body skeleton/original
skin around the skeleton. Historical0READY/9PARTIAL/3BLOCKED unchanged; all
anatomy/contact/clinical-motion/production approvals false. No newGLB export;
existing PR68 asset stays provisional; consume newer G4j compatibility scope.
