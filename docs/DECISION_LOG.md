# Frozen decision log

These decisions remain in force until deliberately reopened with new evidence and an explicit update to this file.

## Product boundary

- Required target: distributable/runtime independence, not total independence from development tools.
- Blender, Git/GitHub, Python, Node/npm, TypeScript/Vite/Vitest/Playwright, GPT, and Claude may be used as development tools if their implementation/content is not shipped as prohibited production runtime or creative content.

## Character and provenance

- V15f is finished as a legacy/reference benchmark only. Do not resume production development on it.
- The imported/high-detail V5-V15f/CORNER_FINAL lineage is not eligible as the final first-party production character.
- MakeHuman-derived built-in anatomical body data is not eligible for the final first-party production path.
- ORIGINAL v1 is the clean-room first-party production character line.
- ORIGINAL v1 must originate independently; no legacy geometry, topology, UV, weights, materials, bind matrices, or projection transfer.
- The O1 procedural scaffold is a starting scaffold/evidence item, not finished production anatomy.
- `hgpt_canonical_v4_original` is the independent first-party production rig target.
- Preserve the project-owned 63-bone hierarchy/names/semantics, but use independently authored v4 rest dimensions rather than legacy-fit numerical transforms.

## Runtime

- Direct Zustand has been replaced by the project-owned store.
- React/ReactDOM source migration is complete: production source imports are pinned at zero and no production TSX is required.
- React/ReactDOM packages may remain temporarily while the retained R3F/Drei peer ecosystem and physical-device package gate remain open; package retention does not authorize source use.
- Three.js replacement may proceed through deterministic math/rig/IK/GLB layers before final renderer/package retirement, but biomechanics and acceptance thresholds remain fixed.
- Runtime migration order remains: Drei/R3F -> React/ReactDOM -> Three.js last, unless evidence requires an explicit change.
- Do not remove a dependency solely to lower the count. Live imports and required parity gates must pass first.
- Exercise mechanics must not be altered to hide renderer/model migration defects.

## Verification

- Physical visual/input parity remains a real gate; unit tests do not substitute for it.
- Blender materialisation and subjective anatomy review must not be claimed from a cloud-only run.
- Release remains deny-by-default until first-party assets/runtime are genuinely approved.
- No guard, threshold, test, or allowlist may be weakened merely to obtain a pass.

## AI collaboration

- The repository is authoritative, not GPT memory, Claude memory, or chat history.
- GPT and Claude follow the same operating contract, reference rules, quality stack, and tests.
- Old branches and historical handoffs are non-authoritative unless the current handoff explicitly names them.

## ORIGINAL v1 roadmap and review policy — 2026-10-01

Owner-authorised roadmap phases 0–12 and shared terminology are recorded in
`docs/ORIGINAL_V1_HIGH_DETAIL_MASTER_PLAN.md`. R2 remains the pinned comparison
baseline and canonical v4 remains frozen at 63 bones. High-detail Phase 5 awaits
stable deformation/freeze; early O7 shorts do not mean Phase 7 completion.

Review snapshots are non-blocking by default. Pending visual review never becomes
acceptance by timeout or numerical optimisation. Safe reversible local experiments
and read-only diagnostics proceed while review remains pending. Frozen rig/pose,
baseline/gate changes or contradictory lineage stop only the affected task.
Final production approval requires explicit final owner acceptance and every
provenance, anatomy, topology, clothing, deformation/contact, runtime/QA and
standalone release gate. Production-control tools cannot set approval flags.

## ORIGINAL v1 pre-freeze owner decisions — 2026-10-02

These decisions supersede the earlier unresolved-owner-decision wording for the affected model work.

- The owner accepts the five inherited R2 shoulder/torso minima regressions on the r38 continuation as an explicitly documented DEVELOPMENT trade-off. R2 itself remains untouched; thresholds and comparison tolerances remain unchanged. The accepted values are a development floor, not a quality target.
- Before Phase 4 freeze, newly identified functional correctness defects must be resolved or classified from real r38 evidence: reverse-bending distal fingers in flexed grips; incorrect push-up palm support; incorrect push-up wrist orientation/extension; incorrect push-up toe/forefoot support; and the overhead shoulder/axilla webbing/pinch.
- Finger direction, push-up palm/wrist support and push-up forefoot/toe support are not deferred as Phase 5 cosmetic work. They are pre-freeze correctness tasks.
- Shoulder/axilla must be classified before freeze. If deformation/weight/support based, repair it pre-freeze; if mechanically sound and only coarse surface anatomy, document and defer its surface-form refinement to Phase 5B.
- Athletic/training shoes are approved as a later first-party clothing item, expected under Phase 7, but cannot be used to conceal an unresolved barefoot toe/forefoot contact failure.
- The detailed execution contract is `docs/work_packages/PHASE_3_PRE_FREEZE_OWNER_CORRECTIONS_20261002.md`.

## External movement reference policy — 2026-10-02

- The owner authorises use of suitable external human exercise imagery/video as **reference-only development evidence** for ORIGINAL v1 deformation and exercise validation.
- This is intended to improve human-movement correctness at each exercise checkpoint and help distinguish pose/contact/rig/deformation failures from later surface-anatomy work.
- The policy is defined in `docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md`.
- External reference may inform generic observations and project-owned validation rules, but must not contribute copied geometry, topology, coordinates, weights, bind data, materials, textures, motion-capture data, authored animation curves or person-specific body proportions.
- For the current pre-freeze work it is required for finger flexion, push-up palm/wrist support, push-up forefoot/toe support, and shoulder/axilla classification.
- Prefer source links/timecodes and project-authored observations in repository evidence rather than storing third-party media.
- The long-term goal is to convert these observations into first-party checkpoint/QA criteria so standalone runtime validation does not depend on external reference access.

## Skeleton correctness takes priority over freeze — 2026-10-02

- The owner explicitly authorises reopening and correcting the ORIGINAL v1 skeleton/rig if direct evidence shows that any part of its functional human movement is wrong.
- The project must not preserve an incorrect rig merely because Phase 2 was previously marked complete or frozen.
- Before Phase 4 deformation freeze, the skeleton/rig must pass a dedicated skeleton-only movement validation with the mesh hidden, supported by external human anatomical/biomechanical reference under `docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md`.
- Validation must cover not only rest hierarchy but functional motion: local axes, rotation direction, joint limits/ranges, coupled motion, left/right symmetry and continuous motion through representative exercise ranges.
- Current priority areas include fingers/thumbs, wrist/hand support, toes/forefoot, shoulder/clavicle/scapula behaviour, plus representative elbow, hip, knee and ankle motion.
- If a defect is in pose/constraint logic, fix that layer. If a defect is in rest orientation/local axes or another rig property, create an isolated audited rig correction and rerun all downstream deformation/contact evidence that depends on it.
- Preserve the 63-bone semantic contract, names and hierarchy where possible. A structural hierarchy/bone-count change requires direct evidence that the existing structure cannot represent required human movement and must be treated as a deliberate, fully audited revision rather than a cosmetic edit.
- Once skeleton-motion validation passes, record a new skeleton-motion lock/freeze identity. Subsequent skinning/anatomy work should assume that locked rig and reopen it only if new direct evidence proves a true rig defect.
- Correct skeleton mechanics take precedence over schedule or preserving earlier freeze labels. The intent is to pay the cost now rather than build skinning, anatomy and clothing on a flawed foundation.
## Bone sufficiency and 3D anatomical proxy — 2026-10-02

- Before the skeleton-motion lock, audit whether the current 63-bone rig has enough functional and deformation degrees of freedom for the intended exercise library.
- Bone count is not protected for its own sake. If multiple-source anatomy/biomechanics evidence and project motion/deformation evidence show that an extra anatomical or helper/deform bone is genuinely required, add it as a new audited rig revision and rerun dependent evidence.
- In particular, evaluate generic twist/deformation helpers for upper arm, forearm, thigh and shin/calf; shoulder/thorax helper controls; forefoot/toe expressiveness; and palm/thumb support. Do not add helpers automatically or create exercise-specific hacks.
- A separate 3D anatomical skeleton mesh is not required to drive the skin. A project-owned, non-production 3D anatomical proxy is approved as a validation/debug tool for pelvis, rib cage/sternum, scapulae, long bones and joint centres.
- The rib cage should inform thoracic volume, shoulder-girdle placement and torso mechanics, but individual rib deform bones are not presumed necessary. Validate simpler thorax/spine/scapula/clavicle plus generic corrective deformation first.
- Use multiple independent reputable external references under `docs/SKELETON_HUMAN_MOVEMENT_AND_BONE_SUFFICIENCY_POLICY.md`; do not copy external anatomical meshes or assets.

