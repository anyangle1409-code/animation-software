# Whole-Body Human Deformation Recovery Design

## Purpose

Recover ORIGINAL v1 from the owner-rejected r95 shoulder, chest, axilla and grip result, then establish a validation system that proves the entire model behaves plausibly across natural human movement instead of a small exercise list.

The model is for exercise demonstration and generation. It must remain first-party, deterministic and auditable. Real-human images, videos and published research are development evidence only; they are never copied into geometry or shipped as dependencies.

## Owner-defined success

- Skeleton motion is anatomically plausible across the natural movement envelope.
- Coupled joints move together: humerus, scapula, clavicle and thorax for arm elevation; pelvis, hip, knee, ankle and trunk for lower-body movement.
- Surface anatomy, skin folds, soft-tissue compression and regional volume change plausibly through motion.
- The model generalises to movements and exercises that were not individually hand-tuned.
- Every important claim is supported by real-human or published biomechanical evidence.
- Visual anatomical failure blocks completion even if numerical gates pass.
- No Critical or High issue may remain open at a phase exit.

## Scope decomposition

This is architectural work and must be delivered as sequential, independently reviewable packages.

1. **Evidence and validation foundation** — reference manifests, movement primitives, visual issue ledger and fail-closed phase rules.
2. **Shoulder/chest/axilla foundation recovery** — replace the r95 compensation stack with anatomically supported weights/topology and then refit generic correctives.
3. **Hands/grip/wrist recovery** — prove load-bearing grip, thumb opposition, finger conformance and wrist load path.
4. **Trunk/spine/scapular coupling** — flexion, extension, lateral flexion, axial rotation, bracing and loaded reach.
5. **Hip/pelvis/groin/glute recovery** — flexion, extension, ab/adduction, rotation and unilateral loading.
6. **Knee/ankle/foot recovery** — deep flexion, dorsiflexion, planted contact and load transfer.
7. **Whole-body combined movement certification** — transitions, reversals, cycles, contacts and unfamiliar exercise compositions.

Each package creates a new candidate, preserves its parent, and cannot hide defects under owner dispositions.

## Selected approach

Use an anatomical-foundation rebuild, not another r95 corrective.

The weights-only r95 surface produces a large lateral axilla/torso wing. The abduction corrective folds it inward and creates the deep scoop. The scapular corrective narrows it but leaves a pointed flap. Combining them trades the wing for the owner-rejected trench, membrane and pec collapse. The correction stack is compensating for an incorrect support structure.

The shoulder package therefore changes the foundation in this order:

1. define anatomical anterior-fold, posterior-fold, deltoid/pec transition, thoracic-wall and scapular support zones;
2. add only the support topology needed to represent those zones continuously;
3. solve local weights against the real coupled skeleton motion;
4. validate the weights-only result throughout the elevation/rotation arc;
5. fit minimal generic motion-driven correctives only for residual soft-tissue behaviour;
6. run the whole affected movement and regression matrix.

## Rejected approaches

### Continue Phase 5 sculpting on r95

Rejected because added neutral anatomy cannot repair weights-only winging and can make the underlying movement failure harder to see.

### Add another local shape key to r95

Rejected because r49-r95 already demonstrates migrating trade-offs. A further patch would stack onto a faulty base and would not generalise.

### Accept the r95 limitation

Rejected by the owner. Numerical development margins do not make the visible result anatomically acceptable.

## Evidence architecture

Every movement primitive and anatomical region receives a manifest containing:

- source URL or repository-owned capture ID;
- source type: primary biomechanical study, anatomical publication, photo or video;
- subject/build and camera-angle diversity notes;
- movement phase and approximate joint configuration;
- externally observable landmarks and surface changes;
- permissible conclusion and uncertainty;
- licence/use note proving the source is development-only;
- reviewer status.

No single subject defines the model. Measurements become ranges or qualitative invariants unless the evidence supports a precise value.

Initial shoulder evidence must include direct-bone or validated 3-D kinematic studies for clavicle/scapula/humerus coordination and multiple real-human visual references for anterior/posterior axillary folds through elevation, flexion, abduction and rotation.

## Validation architecture

### Movement primitives

- Upper body: flexion, abduction, horizontal push/pull, vertical push/pull, internal/external rotation, elbow flexion/extension, pronation/supination.
- Trunk: flexion, extension, axial rotation, lateral flexion and bracing.
- Lower body: squat, hinge, lunge, single-leg stance, hip rotation, knee flexion and ankle/foot articulation.
- Combined: reach, carry, crawl, hang, floor push, loaded pull and unilateral loading.

### Sampling

Each primitive includes start, intermediate, end, reversal and repeated-cycle frames. Shoulder elevation is sampled through at least 0°, 30°, 60°, 90°, 120°, 150° and maximum, in flexion and abduction, with internal/external rotation variants.

### Views

Front, front three-quarter, side, rear three-quarter, rear and region close-ups are fixed and hash-bound. Both sides are captured when symmetry is relevant.

### Layer isolation

For high-risk poses the harness records:

- skeleton-only joint values;
- weights-only surface;
- each corrective independently;
- combined production deformation;
- per-zone displacement, strain, signed area, volume and contact changes;
- activation continuity through the arc.

### Issue ledger

Every issue has a stable ID, body region, movement, evidence, severity, reproduction, causal layer, declared repair scope, status and regression evidence. A phase verifier refuses completion while any Critical or High issue is open or while required visual review is pending.

## Shoulder package boundaries

### Immutable inputs

- r95 remains the comparator and is never overwritten.
- The first-party provenance boundary remains unchanged.
- The active P3B1 numerical baseline and all tolerances remain unchanged.
- The 67-bone `hgpt_canonical_v4_original` revision remains unchanged unless direct skeleton evidence proves a separate rig defect and the owner explicitly opens a rig package.
- Historical Phase 4 records remain intact as evidence of the superseded decision.

### Permitted candidate changes

- declared local shoulder-yoke/axilla support topology;
- declared local weight changes using existing permitted bones;
- new or refitted generic motion-driven shoulder correctives;
- diagnostic and validation tooling;
- evidence manifests, issue ledger and status/control records.

### Forbidden shortcuts

- exercise-name-driven shape keys;
- copied third-party geometry, weights or coordinates;
- threshold relaxation or baseline replacement;
- overwriting r95;
- accepting a numerical pass without visual review;
- hiding an open issue in a non-blocking owner-review field.

## Data flow

1. Evidence manifests define observable expectations and uncertainty.
2. The movement matrix poses the frozen rig through generic primitives.
3. Layer diagnostics locate the causal deformation boundary.
4. A repair declaration freezes the candidate parent, vertex/face zone, permitted bones, intended topology change and stop conditions.
5. A new candidate is built and audited against the declaration.
6. Numerical, visual and motion-arc evidence is generated from the production path.
7. The ledger is updated only from committed evidence.
8. Phase control advances only when issue severity, evidence completeness and regression rules all pass.

## Failure handling

- If a trial fails, preserve its declaration and evidence; do not stack another fix on it.
- If three trials move the defect or create new coupled failures, stop and reconsider the package architecture.
- If source evidence conflicts, encode the observed range and test multiple plausible subjects rather than selecting a convenient value.
- If a render path omits a driver or modifier, mark all affected visual evidence invalid and regenerate it.
- If power or execution is interrupted, the latest pushed commit and candidate hashes are the only authoritative restart state.

## Testing

- Unit tests for evidence manifests, issue-ledger state transitions and fail-closed phase selection.
- Blender smoke and candidate-identity checks.
- Pixel-stable or landmark-stable camera/render reproduction checks.
- Skeleton kinematic tests across the primitive matrix.
- Layer-isolation diagnostics with deterministic activation/displacement output.
- Topology, weight-scope, symmetry, influence-count and provenance audits.
- Full numerical development and production-target reports.
- Arc continuity, self-intersection, contact and volume tests.
- Mandatory human anatomical review against the reference manifests.

## First implementation package

The first package is limited to evidence/diagnostic infrastructure and the shoulder/chest/axilla foundation. It must produce:

- a committed real-evidence manifest schema and initial shoulder manifest;
- a committed whole-body issue ledger containing the owner-identified defects;
- a read-only corrective-layer/arc diagnostic;
- a fail-closed visual-rejection override that supersedes, but does not rewrite, the historical r95 Phase 4 record;
- a declared shoulder-yoke repair scope;
- a new numbered candidate and complete evidence, or a documented refusal if the declared approach cannot satisfy the gates.

Hands/grip and the remaining body packages begin only after the shoulder package has a stable, reviewable foundation, while their already-open issues remain visible in the master ledger.
