# Remaining regional anatomy gates — reconciled11October2026

This is a work queue, not a new canonical readiness declaration. Source skeleton
governs geometry; r95skin fit, synthetic tests, private intensity components and
population means do not independently approve anatomical targets.

Authority unchanged: `ORIGINAL_V1_WORK/anatomy/canonical_freeze_readiness_v1.json`,
SHA256 `461927ae811a3572946bf8ae2f6a502cc85949890594b2ce26b7b63fedcfffea`.
All12region identities/statuses counted independently:0READY/9PARTIAL/3BLOCKED.
Claude's readiness addendum/blocker matrix read, preserved unchanged. No c005,
approved runtime adapter, skeletal rescaling, pose/production acceptance or merge.

## Region-by-region completion gates

| Region | Status | Still needed before geometry/region approval |
| --- | --- | --- |
| Shoulder girdle | PARTIAL | Endpoint-matched clavicle/scapula; absolute SC/AC/GH centres; compatible neutral thorax and acromion/notch/C7 evidence |
| Spine | PARTIAL | Matched per-level AP depths/endplate frames; standing segmental angles; disc-facing envelopes/clearance and coupled C2–S1 alignment |
| Ribs | BLOCKED | Complete proximal/distal centreline, independently mapped 3D orientation and demographics; rib head/tubercle/cartilage/sternal contacts |
| Forearm | PARTIAL | Independently matched radius/ulna endpoints and target semantics; DRUJ/wrist centre/pronation axis; no runtime-suffix anatomy assumption |
| Carpus | BLOCKED | Eight bones in one accepted wrist frame; envelope axes and radiocarpal/intercarpal contacts; image/surface units/registration |
| Hand | PARTIAL | Wrist/carpus first; endpoint-compatible M2–M4 targets, thumb CMC layout and independently supported fingertip endpoints |
| Pelvis | PARTIAL | Os coxae/SI/pubis/sacral geometry; seven independently accepted landmarks, full bone coverage and source-to-HGPT registration |
| Lower-limb long bones | PARTIAL | Femur/tibia endpoint reconciliation; fibula endpoints; patella/trochlea surfaces and independently sourced contact path |
| Tarsus | BLOCKED | Accepted common-frame bone envelopes and subtalar/talonavicular/calcaneocuboid/naviculocuneiform/TMT contacts |
| Forefoot/toes | PARTIAL | Endpoint/stature-aware M3–M5/toe targets and heel-to-toe skeletal/soft-tissue partition; no uniform shortening |
| Head/neck fixed | PARTIAL | Cranial/facial envelope, full mandible landmarks, independently matched hyoid/C3 placement and tilt |
| Humerus | PARTIAL | GH–EJC vs maximum-length endpoints and stature-conditioned evidence; humeral head/trochlea/capitulum consistent with joint centres |

These summaries retain the authority's unresolved semantics; they are not an
assertion that any one new source will resolve every gate. Full regression also
remains non-green:1097tests/20failures/41errors/1skip historical expanded baseline,
and C003numeric reconstruction unresolved. Do not rerun completed expensive solvers.

## Completed evidence: do not reacquire or confuse with readiness

- Female201original CT arrays1700..1900: two-decoder calibration/grid verified,
  all firstviews complete, whole intensity mask independently checked, native
  source timeline and21source-bound intensity tiles saved/reopened/verified.
  Named bones/coverage/landmarks/registration not accepted; female subject stays
  separate from the normal1.82m male target. Tile closing faces remain artificial.
- Male82source frames:43/39acquisition groups retained; nativeviewer verified.
- BoneHub54source topology/LPS inventory and wrist/foot30mesh/44pair diagnostics,
  complete bounded pixel/label streams and11small-component33plane firstreview
  completed. HUtransform/accepted units/grid-to-surface registration unresolved;
  do not delete small fragments or interpret centroids as joint landmarks.
- Runtime-chirality/multicontrol evidence and135sweeps completed; these are not
  physiological movement or skeletal geometry approval.
- Thoracic2011front/back body-height table already recovered on preserved
  branches. The old authority's access/missing-table sentence is now historical,
  NOT a reason to duplicate recovery. Do not rewrite the historical authority.

## Preserved independent thoracic/rib source checkpoints

`codex/independent-thoracic-body-primary-table-20261010`
at`c712bc8afe39c5a6b999d9eea7f29f5b7d5f08fb`:
`docs/ORIGINAL_2011_THORACIC_VERTEBRAL_AP_WEDGE_RECHECK_20261010.md` read.

`codex/thoracic-primary-body-wedge-evidence-20261010`
at`0dc7174b9fede23a63f0f484ebc7cc24998ac3ac`:
source verifier and reconciliation document read. Exact pinned verifier evaluated
read-only against its own pinned input blobs:13rows(C7+12thoracic),12existing
average-height matches,PASS;0degrees computed, no geometry/anatomy acceptance.
This fresh targeted check is not a rerun of the11-test CI suite or a new table.
Remaining: matched sagittal APdepths/endplate geometry and compatible standing
cohort/pose. No angle from height difference alone or uniform43.7deg distribution.

`codex/rib-orientation-source-preflight-20261010`
at`909c44ffcce743930a5b98880e1d3dbdd2b0d989`:source preflight read; sequential
orientation remains a frame hypothesis, out-of-plane coefficients/proximal rule
and actual rib contact surfaces are absent. No branch merged or overwritten.

## Standing-angle source access checkpoint

Finoco et al., DOI`10.1007/s00586-025-09392-w`, PMID41047402, identity confirmed
through [publisher](https://link.springer.com/article/10.1007/s00586-025-09392-w)
and [PubMed](https://pubmed.ncbi.nlm.nih.gov/41047402/).
Publisher: online6October2025, volume35pages2226–2235(2026); preview/subscription
only. Abstract describes645mixed-sex volunteers, not a182cm male target. No
fulltext/Table6values read or transcribed, no fulltext bytes acquired.

Author-institution [SAM record](https://sam.ensam.eu/handle/10985/26922?locale-attribute=fr)
lists`IBHGC-ESJ-VERGARI-2025.pdf`,11.02MB, embargo end6April2026. Its offered
PDF link returned403; landing metadata does not prove accessible fulltext.
The author's [HAL publication list](https://cv.hal.science/cvergari) identifies
`hal-05304370v1`; [record](https://hal.science/hal-05304370v1) returnedAnubis
AccessDenied. No paywall/bot restriction bypass, login, purchase or settings change.

Ruling: do not fabricate Table6from abstract percentages or assume a promised
PDF's contents. Cost: standing-angle gate remains unresolved. Preserve exact
identity/access result so subsequent automation does not hammer the same endpoints.

## Next executable action

Do not repeat completed CT/Blender/mask/table investigations or these denied
fulltext requests while state is unchanged. On another primary standing-angle
source (e.g.Sebaaly2021 DOI`10.1007/s00586-020-06670-7` or Bernhardt1989
DOI`10.1097/00007632-198907000-00012`), first inspect existing source ledgers,
then verify official accessible fulltext/table/cohort/endpoints before intake.
If inaccessible, move to another region's matched primary source or reversible
source-bound candidate diagnostics; no physiology or canonical promotion.

Other open plan task: bilateral runtime forearm skin stress is NOT yet measured;
existing script is forearm_l only despite its header. Do not rerun the completed
left side or claim bilateral results without source r95identity and genuine right
selection. This checkpoint did not change the script or run additional skin tests.

Masterdf6f28ec09693a074af82bb1a9b7b691740adaa5 all3CIchecksPASS,
run38100980368. All3local linked worktrees clean before metadata edit; no source
branch changes detected on fetch. Battery18% observed; no power settings changed.
