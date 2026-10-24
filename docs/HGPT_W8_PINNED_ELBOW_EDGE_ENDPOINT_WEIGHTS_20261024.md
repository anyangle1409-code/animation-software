# W8 pinned elbow-region edge endpoints: static skin weights and stored shape keys
**24 October 2026 — read-only triage, NOT anatomical or skin-deformation validation**

## Why this audit is necessary

The previously verified W8 edge-continuity diagnostic identified four mesh-edge
outliers during the *existing shoulder press*. The extreme pose/rest ratios are
local mesh descriptors, not tissue strain or clinical limits. The next safe
question is whether the exact endpoint vertices have unusually different
**stored skin weights** or are affected by large **stored shape-key edge
geometry**. Neither observation alone can establish a deformation cause.

This audit reads the exact reconstructed W8 `.blend` in memory, with source
SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`.
It does not set any pose, activate any shape key, modify a vertex, save a
model, or change an acceptance threshold.

### Immutable edge targets

The edge identifiers below come from independently verified
[run 40060680693](https://github.com/anyangle1409-code/animation-software/actions/runs/40060680693),
native artifact `12547635497`, member `w8_elbow_edge_continuity.json`
(SHA256 `5fb76a15d8bcee051b7b1e2f3696c5cb692e247ca9268cd694aadf3217412df9`).

| Authored region suffix, NOT anatomical side | Shoulder-press sample | W8 vertex IDs | Archived pose/rest ratio |
|---|---:|---|---:|
| distal l | 0 | 15645, 53019 | 0.167612 |
| distal r | 0 | 17185, 44317 | 0.163126 |
| middle l | 6 | 29237, 71026 | 2.673372 |
| middle r | 6 | 32352, 71428 | 2.648593 |

**These numbers are historical pose evidence**, not recomputed by the new
static Blender audit. The audit confirms that each ID pair is still a real
triangle edge in the hash-pinned W8 topology and reports both endpoints'
rest body-local coordinates, complete positive vertex-group weights, total
weight, L1 weight-vector difference, shared positive groups, rest edge
length and the 12 stored shape keys with the largest absolute deviation
of their edge-length ratio from the Basis edge.

The stored key value is *not* a sampled shoulder-press activation value.
A key's stored geometry is not evidence that it fired in the archived pose;
its relative-key relationship is included to avoid silently assuming that
all keys use Basis as their actual deformation reference.

## How to reproduce from a phone

The existing [phone Blender workflow](../.github/workflows/phone-blender-workbench.yml)
opens the pinned W8 reconstruction in Blender 5.2.0 and invokes
`scripts/phone_blender/elbow_edge_endpoint_audit.py` from
`scripts/phone_blender/task.py`. The W8 inspection artifact should contain:

- `W8/w8_elbow_edge_endpoint_weights_and_keys.json`
- `W8/w8_elbow_edge_endpoint_weights_and_keys.md`

The diagnostic is deliberately W8-only: the vertex IDs must **not** be
reused on V14 or R120, which have different mesh topology. The report is
rejected if the W8 source SHA, edge membership, shape-key topology,
vertex groups or coordinates are invalid. Synthetic tests are in
`scripts/cloud_body_analysis/tests/test_elbow_edge_endpoint_audit.py`.

**Execution status at first commit:** the new seven-job
[run 40064463613](https://github.com/anyangle1409-code/animation-software/actions/runs/40064463613)
was PENDING. No cloud pass, real native measurements, artifact member
digest or output SHA256 is claimed until separately verified.

## What would justify the next stage?

1. Confirm the W8 native artifact and exact four-edge output with a
   successful cloud job, inspect the resulting JSON and verify the
   downloaded artifact SHA256 against GitHub's digest.
2. Compare the endpoint weight distributions with adjacent, non-outlier
   control edges in the same rest band, without selecting an arbitrary
   population-derived skin-strain threshold.
3. Cross-reference actual measured press sample 0/6/8 driver values
   and corrective-key activation before inferring which key could
   contribute. Do not infer causality from static stored deltas.
4. Establish anatomical side, humeral epicondyles, radius/ulna landmarks
   and true segment frames independently before calling an edge
   'elbow flexion', 'pronation' or ISB-calibrated.
5. Test shoulder/clavicle/scapula motion, elbow/forearm continuity,
   hip/knee/ankle/foot coupling and contact with neutral-return trajectories
   after verified segment axes and controlled native movement data exist.

## Scientific interpretation and unresolved gates

The [ISB upper-limb joint-coordinate recommendations](https://pubmed.ncbi.nlm.nih.gov/15844264/)
and [ISB lower-limb recommendations](https://pubmed.ncbi.nlm.nih.gov/11934426/)
are anatomical coordinate/reporting conventions; Blender bone names, weight
groups and local axes do not certify those frames. A
[2025 shoulder kinematics review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/)
describes variable scapular motion, so a fixed universal scapulohumeral
ratio must not be imposed. [CDC population ROM means](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html)
are descriptive, not hard rig limits.

All **46 anatomical landmark requirements remain unbound** and **0/19
generic movement tests are executed or approved**. The old shoulder press,
squat and grip acceptance failures remain. W8 archival mismatch and V14
two-vertex discrepancy remain unresolved. No muscle origin/insertion
attachment is authorized; permanent semantic muscle IDs remain intact.
Muscle highlighting is owner-deferred. Original `.blend` sources,
skeletal data, Claude-owned branches, production assets, PT-App and
`PT_MODEL_VERSION 1.0` are out of scope. No merge or deployment.
