# ORIGINAL v1 human-body master plan

**Status:** AUTHORITATIVE for `HomeGymPT_Male_ORIGINAL_v1` body-quality progression  
**Asset:** `HomeGymPT_Male_ORIGINAL_v1`  
**Rig:** `hgpt_canonical_v4_original`  
**Production approval:** NO

This is the governing body-development plan for the ORIGINAL-v1 character.

It preserves the historical Phase 0-12 roadmap, candidate lineage, baselines and
freeze evidence, but it changes what those records mean operationally:

> **A numerical phase checkpoint does not prove that the character behaves like
> a real human. Human-body progression is now fail-closed on visual/anatomical
> motion evidence as well as numerical deformation evidence.**

The previous high-detail roadmap remains useful for implementation sequencing,
but it is subordinate to this document whenever the two differ on whether the
body is ready to progress.

---

## 1. Product target

The target is not merely a high-detail male mesh and not a small collection of
exercise-specific deformation fixes.

The target is an independently authored human character whose **entire body
moves and deforms plausibly across natural human movement**, so later exercises
can be composed from already-proven body mechanics.

The character must therefore satisfy all of the following:

- plausible skeleton and coupled-joint motion;
- anatomically coherent body volume through motion;
- natural soft-tissue sliding, compression and stretch;
- folds/creases that appear and disappear for mechanical reasons;
- continuous human silhouette through intermediate frames;
- believable hand/foot/equipment/floor load paths;
- no visual defect hidden by correctives, clothing, materials, lighting or crop;
- broad movement-family coverage, not validation only on a few exercises;
- real-human photos/video and biomechanics used as development evidence;
- numerical checks and visual/anatomical checks both required;
- final standalone runtime does not require third-party human media.

External human references are observation evidence only. They must never become
shipped geometry, scans, textures, weights, bind data or copied implementation.

---

## 2. Governing rule: foundation before cosmetics

A body region may not progress to high-detail sculpting simply because endpoint
metrics pass.

**Weights-only deformation must be anatomically plausible before corrective
shape keys are allowed to provide the final appearance.**

Correctives may refine a mechanically sound foundation. They may not be used to
conceal a fundamentally incorrect ownership/support structure.

If a visually obvious Critical or High anatomical defect is present, it blocks
the affected progression even when historical numerical gates are green.

---

## 3. Validation hierarchy

For every body region the preferred diagnostic order is:

1. **skeleton/joint motion** — are the bones and coupled joints moving correctly?
2. **weights-only skinning** — does the uncorrected surface already behave
   plausibly?
3. **corrective layers** — do correctives refine rather than conceal?
4. **topology/surface support** — can the mesh support the required compression,
   sliding and silhouette?
5. **contact/load path** — do external loads travel through the body coherently?
6. **intermediate-motion continuity** — no popping or transient collapse?
7. **real-human visual comparison** — is the result recognisably human through
   the movement?
8. **whole-body regression** — did the local repair break anything else?

Do not jump directly to sculpting or another corrective until the first failing
boundary is identified.

---

## 2A. Anatomical coupling is mandatory

The machine-readable attachment/shared-tissue authority is
`ORIGINAL_V1_ANATOMICAL_COUPLING_MAP.json`, with the human-readable contract at
`docs/ORIGINAL_V1_ANATOMICAL_COUPLING_CONTRACT.md`.

The joint-to-tissue trigger authority is `ORIGINAL_V1_JOINT_TISSUE_TRIGGER_MAP.json`: when a rig bone/joint family materially moves, every mapped coupling system is automatically required review scope for that sample.

This requirement is fail-closed:

- if a muscle/soft-tissue chain spans multiple attachment regions, every relevant
  attachment side must contribute to the deformation;
- the surface may not be dragged wholesale by one moving bone simply because that
  produces a numerically convenient result;
- weights-only deformation must preserve the shared attachment relationship before
  any corrective key is fitted;
- outbound, intermediate, endpoint and return frames are all required;
- every mandatory body region and movement family must be covered by at least one
  coupling system;
- any Critical/High coupling failure blocks dependent progression.

The user requirement is therefore encoded as an engineering rule: **movement of
one body part must propagate through all anatomically connected skin/muscle paths
that should respond, while tissue that should remain rooted must remain rooted.**

# 4. Body regions that must be proven

Every region below is mandatory. A neutral render alone never completes a region.

| Region | Required behaviour |
|---|---|
| **Head / neck / trapezius** | coherent cervical motion, head orientation, SCM/trapezius transition, no rigid collar/pinch |
| **Clavicle / shoulder / deltoid** | clavicle/scapula/humerus coupling, stable deltoid volume, plausible shoulder cap |
| **Chest / anterior axilla** | chest-rooted pectoral mass, natural anterior axillary fold, no trench/membrane |
| **Back / posterior axilla** | scapular drape, lat/teres support, natural posterior fold, no cape/flap |
| **Ribcage / abdomen / obliques / lumbar** | coherent torso volume through flexion/extension/rotation and bracing |
| **Upper arm / elbow** | changing biceps/triceps contours, natural elbow compression and release |
| **Forearm / wrist** | pronation/supination, taper, loaded wrist continuity and credible force path |
| **Palm / thumb / fingers** | non-uniform grip sequencing, thumb opposition, equipment conformance and contact |
| **Pelvis / groin / glutes** | deep hip flexion without groin tunnel, stable glute/thigh transition |
| **Thigh / knee** | quad/adductor/hamstring continuity, patellar/condylar silhouette, popliteal clearance |
| **Calf / ankle / Achilles** | dorsiflexion/plantarflexion continuity, Achilles support, no ankle cave/shear |
| **Foot / toes** | heel/arch/forefoot/toe behaviour, floor loading and toe articulation |

The anterior and posterior axilla are explicit regions, not incidental parts of
"shoulder".

---

# 5. Movement, not endpoint poses

Every relevant region must be inspected through motion, not just at rest and a
single endpoint.

Default motion sampling:

`start -> 25% -> 50% -> 75% -> end -> return`

Higher-risk joints require denser sampling where needed.

For the current shoulder/chest/axilla recovery, both sides must include
approximately:

`0° -> 45° -> 90° -> 120° -> 150° -> near-full overhead -> return`

The review must detect:

- temporary dents/collapse;
- shape-key overshoot;
- popping/snapping;
- changing left/right asymmetry;
- tissue that looks plausible only at the endpoint;
- folds that persist when compression is gone;
- loss of body volume or implausible transport of tissue.

---

# 6. Movement families that must be proven

Actual exercises are compositions of these primitives; they are not the only
proof of them.

## Upper body

- neutral shoulder control;
- shoulder flexion/elevation;
- shoulder abduction/elevation;
- internal/external humeral rotation;
- vertical push;
- vertical pull/hang;
- horizontal push;
- horizontal pull;
- elbow flexion/extension;
- forearm pronation/supination;
- wrist flexion/extension under load;
- cylindrical/equipment grip;
- grip release/opening.

## Torso

- neutral/braced trunk;
- flexion;
- extension;
- lateral bend;
- axial rotation;
- loaded hip hinge.

## Lower body

- squat/deep bilateral hip-knee flexion;
- split stance/lunge;
- hip flexion/extension;
- hip ab/adduction as needed by the movement envelope;
- knee flexion/extension;
- ankle dorsiflexion;
- plantarflexion;
- loaded foot/toe contact.

Where a production exercise does not yet provide a clean sample, use a
deterministic audit motion. Audit motions validate anatomy; they do not silently
become runtime exercise definitions.

---

# 7. Real-human evidence standard

High-risk movement must be backed by evidence from a combination of:

1. primary biomechanics/anatomy literature;
2. real-human photographs;
3. real-human motion/video or sequential images;
4. multiple subjects/body types where practical;
5. multiple views where one camera cannot establish the anatomy.

The project records **observations**, not copied geometry.

Examples of valid observations:

- the anterior axillary fold remains chest-rooted and changes angle as the arm
  elevates;
- scapular/clavicular contribution changes through the elevation arc rather than
  following one fixed ratio;
- PIP/DIP/MCP contribution changes with cylindrical grip diameter;
- wrist extension under push-up load changes the hand-to-forearm force path.

Reference uncertainty and cohort limits must be retained.

---

# 8. Fail-closed defect ledger

Every meaningful defect receives a stable ID and candidate-bound evidence.

Required severity classes:

### Critical
Visually impossible or mechanically broken anatomy/contact. Blocks progression.

### High
Clearly non-human deformation visible at ordinary review distance. Blocks the
affected region and all dependent progression.

### Medium
Secondary/close-view anatomical defect. Must be fixed or explicitly
dispositioned before production freeze.

### Low
Tertiary polish issue without meaningful anatomical/motion consequence.

A defect is not fixed because one render improves.

`FIXED_VERIFIED` requires:

- before evidence;
- candidate-bound repair scope;
- after evidence;
- relevant motion sweep;
- numerical regression checks;
- contact/load checks when applicable;
- no new Critical/High issue;
- owner-review state recorded separately.

---

# 9. Master production stages

These stages now govern body progression. Historical Phase 0-12 records map
inside them; they do not override them.

## Stage 1 — Human movement foundation **ACTIVE**

Prove the underlying mechanics before high-detail anatomy.

Tasks:

- diagnose skeleton vs weights vs corrective vs topology causes;
- repair foundational ownership/support;
- preserve existing contacts and accepted mechanics;
- prove intermediate-motion continuity.

**Current focus:** shoulder/chest/axilla foundation reopened from r95.

Exit:
- no Critical/High foundation defect in the validated region;
- weights-only deformation is plausible;
- any corrective layer refines rather than hides;
- motion sweep and regression evidence pass.

## Stage 2 — Whole-body regional proof

Apply the same standard to all mandatory body regions.

Exit:
- all mandatory regions have candidate-bound neutral, loaded/lengthened,
  compressed and intermediate evidence;
- no unresolved Critical/High regional defect.

## Stage 3 — Whole-body movement-family proof

Exercise the movement primitives listed above, including transitions and return
motion.

Exit:
- all mandatory movement families have evidence;
- no unresolved Critical/High movement-specific defect;
- whole-body silhouettes/contact remain credible.

## Stage 4 — Real-human evidence closure

Close reference gaps for every high-risk region/movement.

Exit:
- all mandatory evidence rows have source identity, permissible conclusions and
  uncertainty;
- no Critical/High issue remains unable to enter review merely because human
  evidence is missing.

## Stage 5 — High-detail anatomy

Only after Stages 1-4 are sufficiently clear.

Reuse the prepared sequence:

- 5A torso;
- 5B shoulders;
- 5C arms;
- 5D hands;
- 5E pelvis/legs;
- 5F feet;
- 5G head/neck.

High-detail work improves silhouette/landmarks and app-distance form. It must not
hide a deformation failure.

## Stage 6 — Final topology / surface quality

Finalize loops, joint support, manifold health, normals and surface continuity.

No destructive remesh or correspondence guess may erase evidence.

## Stage 7 — First-party clothing

Build original clothing only after the underlying body is stable.

Clothing must not hide a body defect and must preserve bare-body identity/contact.

## Stage 8 — Materials / presentation

Owned numeric/material inputs, repeatable cameras and presentation.

Lighting/materials may not be used to hide anatomy.

## Stage 9 — Production deformation validation

Run the final body/clothing through the complete production movement envelope,
including intermediate frames, reversals, contacts and load states.

Development-clear is not enough.

## Stage 10 — Animation-engine integration

Transfer only the validated first-party asset and required measured first-party
runtime data into the standalone engine.

Exercises should compose already-proven movement primitives rather than inventing
new body behaviour ad hoc.

## Stage 11 — Automatic self-review

Build deterministic checks for:

- joint limits/motion coupling;
- known anatomical transitions;
- silhouette/crop/contact defects;
- symmetry;
- movement continuity;
- known historical failure signatures.

Automated QA supports but never replaces final anatomical review.

## Stage 12 — Whole-body owner review

Review the exact candidate used by the production pipeline across the required
motion boards.

This is distinct from routine non-blocking snapshots.

## Stage 13 — Integration/release verification

Verify standalone/runtime/export parity, asset hashes, no third-party runtime or
character dependency, exact candidate identity and final QA evidence.

## Stage 14 — Production freeze

Only when all preceding required gates pass and the final exact candidate is
explicitly accepted may production promotion be authorised.

Production approval remains false until that controlled action.

---

# 10. Mapping from historical Phase 0-12

Historical evidence is preserved, not rewritten.

- historical Phases 0-2 -> provenance/base/rig inputs to Stage 1;
- historical Phase 3 -> important numerical deformation evidence inside Stage 1;
- historical Phase 4 r95 freeze -> immutable historical checkpoint, **not**
  current anatomical sign-off;
- historical Phase 5 -> now executes inside Master Stage 5 after Stages 1-4 clear;
- historical Phases 6-12 -> broadly correspond to Master Stages 6-14, with the
  new whole-body and owner-review gates inserted ahead of final promotion.

A historical green check does not override an open Critical/High issue.

---

# 11. Current project position

Current comparator:

- r95 SHA-256
  `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`

Current master stage:

> **Stage 1 — Human movement foundation**

Current subproblem:

> **Shoulder / chest / anterior axilla / posterior axilla foundation recovery**

Established findings:

- the owner-rejected appearance is reproduced exactly through the production
  deformation path;
- weights-only shoulder/torso deformation already contains a large wing/support
  failure;
- the existing r95 abduction/scapular correctives reduce that wing but trade it
  for trench/membrane/chest-volume defects;
- another cosmetic r95 patch is not the selected path;
- r95 remains immutable comparator evidence;
- the repair must rebuild the local shoulder-yoke/axilla support and weight
  ownership before new correctives are fitted.

Current blocking issues include the Critical/High items in
`ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json`.

---

# 12. Immediate execution sequence

1. Preserve r95 unchanged.
2. Run/read the shoulder deformation-layer diagnostic through the elevation arc.
3. Identify the first failing anatomical ownership/support zones.
4. Declare the smallest shoulder-yoke/axilla repair scope before editing.
5. Build a new numbered candidate; never overwrite r95.
6. Re-solve weights/support first.
7. Prove the weights-only surface through the arm-elevation sweep.
8. Only if the foundation is plausible, fit/refit generic motion-driven
   correctives.
9. Run full visual, numerical, symmetry, contact and whole-body regression
   evidence.
10. Close the associated issue-ledger rows only with committed closure evidence.
11. Continue Stage 1 region-by-region rather than jumping to cosmetic Phase 5.
12. After Stages 1-4 satisfy their gates, resume high-detail anatomy.

---

# 13. Non-negotiable project constraints

- no third-party character content in production;
- no copied V-series geometry/weights/topology/bind/material data;
- no threshold weakening or baseline re-pinning to manufacture a pass;
- preserve historical evidence;
- do not overwrite newer work;
- do not work from `main`;
- do not infer owner acceptance;
- do not infer production approval from scores;
- do not use clothing/material/lighting/crop to conceal body failures;
- do not call a movement proven from endpoints alone when the transition is
  unreviewed.

---

# 14. Authority and pickup rule

For ORIGINAL-v1 body/model work, read in this order:

1. live branch/source and candidate-bound executable evidence;
2. **this master plan**;
3. `ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json`;
4. `ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json`;
5. current generated/model status and recovery handoff;
6. historical high-detail roadmap and individual work packages.

If generated status says a later historical phase is next while this plan still
has an open Critical/High whole-body blocker, **the blocker wins**.

The next session must not silently revert to "Phase 5A next" merely because the
historical Phase 4 checkpoint exists.
