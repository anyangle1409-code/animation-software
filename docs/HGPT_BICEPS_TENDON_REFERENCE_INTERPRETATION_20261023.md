# Home Gym PT — upper-arm anatomical reference interpretation and muscle-motion pilot

Date: 2026-10-23
Status: **source-backed design interpretation; no native muscle geometry / anatomical binding / physiological simulation approved**.

## Purpose and provenance

The owner supplied six illustrative examples: an elbow-flexion biceps/triceps antagonism diagram; layered biceps long-/short-head-and-tendon rendering; a biceps long/short origin and radial insertion diagram; a forearm/upper-arm muscle atlas; a two-head front-torso biceps render; and an infographic explaining the biceps. These images express desired **educational intent and visible modelling style**, not an authoritative 3D geometry source. No user images, image textures, branded marks or traced muscle shapes are copied into the repository or proprietary app; check rights before future publication.

**Core user requirement:** for every real named muscle, know where it attaches, how it relates to neighbouring structures, what changes during joint motion, and how visible overlying skin should plausibly respond. The final first-party model should look like a natural human both when idle and in exercise; anatomical mode is a separately switchable teaching layer.

## Which reference ideas to adopt

- Preserve full gross anatomy: scapula, clavicle, humerus, radius, ulna, joints, tendons, distinct upper-arm superficial vs deep muscle layers.
- Split biceps into a **long head** and **short head** with independent proximal tendon/attachment routes, sharing a distal insertion complex. Do not model as two isolated straight cylinders or copy one illustration's exact arbitrary fibre strips.
- Biceps long-head proximal origin: **supraglenoid tubercle of scapula**; tendon traverses shoulder region and bicipital groove. Short head: **coracoid process of scapula**. Distal insertion: **radial tuberosity**, with a **bicipital aponeurosis** continuous with forearm fascia. Textbook-level regional descriptions require landmark-accurate review before coordinates can be accepted; native body `_l`/`_r` suffixes are NOT anatomical-side bindings.
- The brachialis **lies deep to biceps**, originates in the distal/anterior humerus and inserts on proximal ulna/coronoid region, contributing elbow flexion independent of forearm supination.
- Brachioradialis contributes to elbow flexion and lies along lateral forearm, particularly visually relevant near a neutral grip. Radius rotation/supination changes distal biceps tendon route; it is not just elbow flexion.
- Triceps has **three heads**: long head from infraglenoid scapula (spans shoulder and elbow); lateral and medial heads arise from posterior humerus, converging distally on the **olecranon of ulna**.
- Separate hard skeletal motion from muscle length and activation. During resisted elbow flexion biceps/brachialis may shorten while activated; during controlled *lowering* they may lengthen **while still activated**. Triceps can stabilize/co-contract. The image's binary “biceps contracted / triceps relaxed” is introductory, NOT an activation algorithm.
- Preserve tendon visually as a narrower, comparatively nonbulging structure versus muscular belly. Anatomically grounded shape/fibre orientation matters; avoid ballooning or a fixed rigid volume shortcut as a substitute for validation.

## Diagram caveats — avoid importing errors

1. A muscle shown thick in a **posed** arm does not prove neural excitation or true fibre/tendon length. Joint angle, load, grip, tempo, eccentric force, co-contraction and individual geometry change behaviour.
2. Educational diagrams simplify tendon splitting, fascial structures, overlapping heads and under-the-skin anatomy. The six images are not uniform camera viewpoints, scale or specimen accuracy.
3. Some infographic labels are misspelled/inconsistent, and some stylized colours/exposed muscle borders exaggerate separations. Do **not** scrape diagram labels or trace outer silhouettes into model coordinates.
4. An anatomical diagram is a *guide to candidate features*, never independent validation of origin/insertion coordinates on our 77-bone authoring rig.
5. Do not assume radial-tuberosity tendon insertion travels to ulna; the brachialis and triceps use ulnar insertions; biceps inserts on **radius** plus aponeurosis.
6. Do not infer fixed muscle activation from the joint position. OpenSim separates excitation, activation, fibre/tendon length and force, which must not be collapsed into a single visual slider.

## Source-backed muscle contract (descriptions only, not solved local binding points)

| Permanent muscle head ID | Proximal anatomical attachment | Distal anatomical attachment | Dominant interaction | Layer / skin |
|---|---|---|---|---|
| `hgpt.muscle.biceps_brachii_long.L/R` | supraglenoid tubercle/scapula, long tendon | radial tuberosity and aponeurotic complex | elbow flexion and forearm supination; shoulder-spanning | superficial; *reviewed* capped skin response only |
| `hgpt.muscle.biceps_brachii_short.L/R` | coracoid process/scapula | radial insertion/bicipital aponeurosis complex | elbow flexion and supination with long head | superficial; *reviewed* capped skin response only |
| `hgpt.muscle.brachialis.L/R` | anterior/distal humerus | proximal ulna/coronoid process | elbow flexion independent of pronation/supination | deep to biceps; do NOT directly deform outer skin |
| `hgpt.muscle.brachioradialis.L/R` | lateral supracondylar ridge/distal humerus | distal radius/styloid region | elbow flexion, especially neutral forearm | superficial forearm region only |
| `hgpt.muscle.triceps_long.L/R` | infraglenoid tubercle/scapula | olecranon/ulna | elbow extension, shoulder contribution | posterior arm; reviewed |
| `hgpt.muscle.triceps_lateral.L/R` | posterior humerus (superior to radial groove) | olecranon/ulna | elbow extension | posterior arm; reviewed |
| `hgpt.muscle.triceps_medial.L/R` | posterior humerus (inferior to radial groove) | olecranon/ulna | elbow extension | deep/posterior; constrain direct skin influence |

IDs are intended to match the immutable muscle vocabulary from [PR #124](https://github.com/anyangle1409-code/animation-software/pull/124); verify registry membership for each proposed ID before any future programmatic binding. All seven heads named above were independently checked against the current PR124 120-record registry: biceps long/short, brachialis, brachioradialis and `triceps_long`, `triceps_lateral`, `triceps_medial` each have both `.L` and `.R` records. The `triceps_brachii_*` forms are **not** registered permanent IDs and must not be used as runtime bindings. Never create new aliases automatically or substitute muscle names without registry validation. **Every rig-local anchor and actual mesh representation is UNRESOLVED.**

## A reusable biceps curl rule (phase-specific, not a medical prediction)

| Phase | Joint motion | Elbow flexors | Triceps |
|---|---|---|---|
| Neutral/rack | relaxed elbow angle, grip-specific rotation | possible light stabilizing activation | possible stabilizing co-activation |
| Concentric curl | controlled elbow flexion with humerus relatively stationary | active; paths typically shorten under the tested curl variant | antagonist/stabilizer; not assumed always OFF |
| Top hold | elbow nearly fixed against gravity/load | active *isometrically* as appropriate to load; tendon/fascicle states not inferred exactly | may stabilize |
| Eccentric lowering | elbow extends under controlled load | **may remain strongly active while lengthening**, depends on load/variant | may stabilize; not automatically the prime mover |

For rotation/supination variants, treat radioulnar orientation explicitly rather than assuming the elbow-flexion position uniquely defines biceps contraction. For actual mechanism do not equate muscle-tendon path shortening with fibre shortening if compliant tendon is involved.

## Minimal native Blender pilot — should only proceed after source/anchor approval

1. **Confirm source identity first:** one anatomical-side-resolved, topology-validated model with approved shoulder/elbow/radioulnar joint centres/axes, unchanged source SHA256 and copy-preservation guard. Existing V14 reconstruction and shoulder motion fail those gates.
2. Bind and review long-head and short-head biceps proximal patches separately, with real radius insertion, bicipital tendon/aponeurosis, and bone-local via/wrap points; attach deeper brachialis and posterior triceps later in clearly layered collections. Do not use mesh weight centroids as actual anchors.
3. First test **zero-activation, moving skeleton** at flexion/rotation poses; muscle paths follow real joints/tendons and never tunnel through humerus/radius/ulna. Then test **fixed elbow angle, variable visual activation** without moving bone positions.
4. Combine the two independent controls with a conservative rest-relative *superficial-only* skin cage. Compare before/after same-camera plain-skin, muscle-only, translucent-skin and fascia/tendon views across setup, midpoint, peak contraction, controlled lowering and return.
5. Report path-length direction, contact/clearance, skin silhouette deviation, muscle volume and possible self-intersections; require clean images at front/side/back/three-quarter, not one flattering view. Require native motion quality thresholds and human anatomy/visual review, with rollbacks.
6. Record/reuse `hgpt.exercise.biceps_curl.bilateral.v1` from existing `exercise_contracts.json`, not per-exercise duplicated anatomy. Test both anatomical sides independently. Keep any candidate new, isolated, separately approved and non-production.

## Recommended independent sources (not copied geometry)

- NCBI StatPearls — Arm Muscles, regional origins/insertions/function: https://www.ncbi.nlm.nih.gov/books/NBK554420/
- NCBI StatPearls — Biceps anatomy and complexity of head/distal tendon: https://www.ncbi.nlm.nih.gov/books/NBK519538/
- NCBI StatPearls — Triceps long/lateral/medial heads and olecranon: https://www.ncbi.nlm.nih.gov/sites/books/NBK536996/
- OpenSim Muscle Editor — fixed, via, moving and wrap attachment points: https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53090145
- OpenSim musculoskeletal model paper — muscle path forces and independent excitation/activation: https://pmc.ncbi.nlm.nih.gov/articles/PMC4397580/

Scientific sources establish plausible regional anatomy and conceptual modelling constraints. They do NOT validate exact coordinates or demonstrate that our current Blender model has accurate arms. No original files, muscle geometry, runtime implementation or source artifacts changed.

## Owner-reviewed elbow transition requirement

The user specifically identified an abrupt, excessively narrow upper-arm-to-elbow silhouette in the existing model, despite educational anatomy illustrating overlapping deep/superficial tissue. This is a **visual concern**, not yet an independently measured diagnosis in the pinned reconstruction. It must be turned into reproducible visual and topology measurements, not assumed to be one missing muscle.

Test hypotheses independently: (1) missing brachialis-derived deep volume, (2) misplaced/too-long distal biceps muscle belly or tendon, (3) inadequate brachioradialis/forearm transition, (4) upper-arm/elbow vertex-weight falloff, (5) unsuitable joint skinning and corrective keys, (6) elbow flexion/forearm-supination path or scale/pose presentation.

**Acceptance design:** compare matched front/back/side/three-quarter camera renders at elbow 0/45/90/120° and forearm neutral/supinated; calculate cross-sectional perimeters or radii at fixed anatomically verified humeral/ulnar/radial offsets; identify over-pinching relative to the rest baseline, not a guessed ideal circumference. Preserve elbow pit and distal tendon narrowing, but require anatomically plausible medial/lateral continuity under the skin. Overlay true superficial/deep muscle geometry when independently fitted, and ensure skin remains smooth without cylindrical segments or visible seams. No body sculpt or new muscle binding is approved by this finding.
