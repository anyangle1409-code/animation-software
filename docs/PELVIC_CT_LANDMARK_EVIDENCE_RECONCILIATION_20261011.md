# Pelvic CT landmark evidence reconciliation — 11 October 2026

Status: SOURCE/SEMANTIC REVIEW ONLY. Seven accepted osseous landmarks:0/7.
Source skeleton governs geometry. No meshes, coordinates, masks or canonical
assets changed; readiness remains0READY/9PARTIAL/3BLOCKED.

## Primary methods checked against the existing contract

Imai2019 defines the S1 superior-endplate centre by bilateral and
anteroposterior division on identified endplate anatomy, not by a sacral
component centroid. Measurements use an APP-aligned3D bone model; scanner
axes cannot substitute for that frame. The primary paper's Methods and Fig.1
are readable in the [archived article PDF](https://d-nb.info/1193894271/34)
(DOI10.1186/s13018-019-1165-2, printed pages2–3).

The2019 hip-coordinate study selects articular surface nodes before fitting a
sphere for the head centre. It distinguishes APP using pubic-tubercle
landmarks from the PSIS-based ISB frame. Its methods are visible in the
[primary article's indexed text](https://pmc.ncbi.nlm.nih.gov/articles/PMC6800649/).
Direct page opening returned a browser challenge; full-page visual verification
was not obtained. This limitation is retained, not treated as an atlas review.

The following mapping is a project interpretation of those methods and the
existing feature contract, not new anatomical acceptance:

| Required features | Existing candidate review cue | Evidence still missing |
|---|---|---|
| Bilateral osseous ASIS (2) | Group1 elongated lateral profiles6–36 | Correctly identified bony surfaces and independently selected ASIS vertices; no substitution of an iliac blade or skin/inguinal proxy |
| Bilateral pubic tubercles (2) | Group2 anterior-medial profiles around60–69 | Distinct osseous tubercle identities; symphyseal midline and prior central pixel are not bilateral tubercles |
| S1 superior-endplate centre (1) | Group1 central transition17–22 | Verified S1 level and endplate rim in3D; the interval is a navigation hypothesis, not a plane label |
| Bilateral femoral head centres (2) | Group2 rounded candidate profiles48–59 | Independently delineated articular head surfaces separated from pelvic surfaces, followed by3D fits; axial ring centres are not accepted joint centres |

No atlas-to-NLM feature correspondence was established in this step.
Published cohort measurements are not geometric displacement targets.

## Reconciliation with preserved Work evidence

Read-only inspected live heads:
- calibrated source extraction: a3d000ce8135081d2cffb676d5ac4e60e3a9da96;
- hip HU bridge:678c8c03a56ab2c0972fef448cde4d6649b417c8.

The bridge source plane cvm1873f maps exactly to viewer frame54, group2,
scanner S=-481mm. Its image SHA is
bd594b35035a60d8e88d67da7ec6b387b3361ddcd73bcfe5324b0ed9a3575a4d;
header SHA is
b7643af29278b0ac3e345f61517001d9463554ddbb7bec2aa0289e633aa4a86d.
Both match the dense candidate ledger. There is no source-plane disagreement.

The existing bridge rejection record states the proposed right and left
head/socket seeds can be linked by thresholded intensity paths contained in
this plane. That does not prove fusion, contact or correct anatomical labels.
The existing ten-point triage also rejects seven original seeds at300HU.
These are inherited rejection findings, not recalculated here; no completed
source download, connectivity scan or solver was repeated.

Preserve original candidate pixels and their labels as hypotheses. Never
snap them to bright neighbours, promote a largest component, or interpret a
HU route as the joint surface. The four exact prior pixels at frame54 are:
right hypotheses (270,175)/(257,151), left hypotheses
(270,342)/(257,366), expressed as original(row,column), not project coordinates.

## Fresh targeted verification

On unchanged CT viewer branch abaacc61:
- feature observation contract:24/24 tests PASS,0.048s;
- APP frame contract:23/23 tests PASS,0.163s;
- tests include rejecting skin proxies, bad feature identities, unsupported
  approval claims, coplanar/tiny head fits and invalid frame geometry.
These verify software guards using synthetic/frozen inputs, not real anatomy.

Master checkpoint66fa1b79796f402769c9d513dc6bc44551fd4dcf passed all three
CI jobs in run38095971380. Full inherited regression suite remains known red.

## Next executable action

Reuse the existing hip-bridge branch's private three-slice review-plate tool
and unchanged tests. Locate or build the private source-pinned
cvm1870f/1873f/1876f plate with the four original hypotheses visibly marked,
without importing unmerged code into another agent's checkout. Compare
markers with the original axial images and neighbouring frames; keep all
labels unaccepted and require qualified independent anatomical corroboration.
The saved82-frame Blender viewer needs no rebuild or repeated render sweep.
No medical-source bytes, review plates or private Blender outputs enter Git.
