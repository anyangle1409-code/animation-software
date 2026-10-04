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


## Skeleton-motion validation executed; pose definition P2 and rig revision rev2 — 2026-10-02 (Claude, laptop session)

- Decision basis: direct skeleton-only evidence (`ORIGINAL_V1_WORK/candidates/repair_checks/skeleton_lock_r38/`): the 63 rig bones are structurally sound (0 audit flags, mirror/axis error 0, rest identical to the v4 payload to 5e-7 m) but the stress-pose CONSTRUCTION produced anatomically wrong joint motion. Each defect was proven with a read-only audit before anything was changed.
- Defects corrected in a new stress-pose definition **P2** (P1 preserved verbatim and pinned in `ORIGINAL_V1_PRODUCTION_CONTROL.json:pose_definition_history`): reversed distal finger joint (−55 deg, −85 on handle grips) and reversed thumb IP (hinge axis re-derived per curled segment); push-up wrist 88 deg radial deviation (degenerate pronation target); toes bent the wrong way in push-up/lunge; no humeral axial rotation in elevated poses (elbow hinged sideways, forearm carried 85 deg of twist); squat ankle plantarflexed / knee behind ankle; push-up hands 0.29 m above the floor (plank angle now solved so palms and toe pads touch together); rest thumb pointing into the floor in the push-up.
- Because P2 changes what every hand/arm pose measures, R2 stays the pinned baseline of the P1 epoch (candidates r1..r38) and a new baseline **P2B1** (r38 re-measured under P2, 5 development failures) pins the P2 epoch (candidates r39+; numbers r39/r40 were exploratory iterations and are preserved under `superseded_exploratory_P2_0/`). R2, thresholds and comparison tolerances are unchanged. `baseline_epochs` in the production control selects the baseline per candidate.
- Bone sufficiency: axial-twist stress test justified **rig revision rev2** = 63 + 8 deform helpers (upperarm/forearm × tw0/tw1 × l/r), closed-form drive `scripts/original_v1_twist_helpers.py`, identity when there is no twist. Thigh/shin twist, palm/thumb helpers, hallux/lesser-toe split, rib bones and extra shoulder/thorax helpers were considered and rejected (documented in the lock record).
- Skeleton-motion LOCK recorded for rig rev2 on candidate r41 (see `docs/ORIGINAL_V1_SKELETON_MOTION_LOCK.md`). Reopen only on direct evidence of a rig defect.
- The five inherited R2 shoulder/torso minima remain an owner-accepted DEVELOPMENT trade-off for the P1 epoch and are not reopened; under P2 the shoulder minima are measured fresh.

## Owner re-validation of r41 (toes, shoulder); P3, rig rev2c, re-lock - 2026-10-02 (Claude)

- The first skeleton lock (rev2) was withdrawn the same day on owner review: push-up foot/toes and shoulder/axilla were not convincing. Record: `docs/ORIGINAL_V1_PUSHUP_FOOT_AND_SHOULDER_REVALIDATION_20261002.md`.
- Toes: compared with three barefoot push-up/chaturanga photographs of different people and foot/toe literature; the ankle already matched; r41 over-flexed the toe 8 deg (tip lifted). Pose P3 lays the toe flat. No toe rig change; a hallux split is not justified (documented trigger: Phase 5F individual toes).
- Shoulder: the plain press/pull-up poses held the girdle still (166 deg glenohumeral-only). P3 applies an interval-dependent scapulohumeral rhythm to every elevated-arm pose. The scapula bone pivoted about the AC corner and swung the plate 2.4x too far: pivot relocated 35 % toward the tail (rig rev2c). Upper-arm twist helpers REJECTED (worse under realistic poses); forearm helpers kept.
- Stress-pose epochs: P1 (R2) -> P2 (P2B1) -> P3 (P3B1, candidates r42+); P1/P2 preserved and pinned.
- Skeleton RE-LOCKED as rev2c on r45. The remaining shoulder problem is classified as a linear-skinning limit at the axilla (tent / tear frontier r45, r46, r47); a generic joint-angle-driven corrective is justified and prepared (trigger and design in the re-validation record), not implemented.

## Shoulder corrective implemented; r49-r55 - 2026-10-02 (Claude)

- Design (`docs/ORIGINAL_V1_SHOULDER_CORRECTIVE_DESIGN.md`) implemented: two shape keys per candidate (`HGPT_SHOULDER_CORR_L/R`) added to r48, driven by humerothoracic elevation theta (smoothstep 40..150 deg, derived from the r48 arc audit) times the abduction fraction in the trunk frame; mirror-symmetric by construction; runtime spec `ORIGINAL_V1_WORK/shoulder_corrective_<rN>.json`; 1491 left-owned vertices declared before the solve. Solver `scripts/optimize_original_v1_shoulder_corrective.py` (numpy only).
- r49 (theta only) and r50 produced squat self-intersections; r51 (tight anchoring) raised p99; r52/r53 cleared the development gates but renders still showed tent/sheet and axilla tears; r54 (looser tail bounds) failed 2 p99 gates and crumpled; **r55** (smoothness weight 300, hi 3.6) = **0 development failures**, torso edge max <= 3.66 (was 5.12/6.34/5.84), volume 0.998-1.043 with <= 0.8 % step between arc samples, no L/R mismatch (asymmetry 0), torso drift max 0.136 m (r48 0.188).
- Honest status: r55 is NOT accepted as a visual solution. Overhead poses still show small sliver tears at the armpit pit and a crumpled lateral torso; vs P3B1 it has 31 comparator regressions, notably self-intersections in the pull-up poses (4 -> 98, 0 -> 134) and press_top (95 -> 178) - all under the 200 gate. Per the owner principle (do not optimise merely for tests) Phase 3 exit and the Phase 4 freeze were NOT run on it.
- Finding: the arc audit used to ignore shape keys; fixed (it now evaluates the keys). Worst-edge diagnostic shows no over-stretched edge (<= 3.65), so the pit spikes are thin triangles folding, a topology/weight limit at the axilla pit, not edge stretch.
- Next options (owner-level or next session): (a) add a face-area/fold barrier plus second driver (scapular rotation) to the corrective; (b) a first-party axilla-pit weight/topology edit (new declared mask) for the ~40 pit vertices; (c) accept r55 as a development trade-off and freeze. Current evidence candidate for review: r55 (sha256 CCAEF8BA1FDDE161B9E5769175B7576EEB88D96F4C99E41CDD0147041A93BBD7).

## Local shoulder/axilla repair r56-r73 and CI repair - 2026-10-03 (Claude)

- **CI repaired (exact SHA green).** The two final-freeze failures were fixture/contract integration, not the Phase 9 requirement: the final-freeze fixture now builds a contract-real candidate-bound `PHASE9_VALIDATION_RECEIPT.json` with the Phase 9 test fixture and binds all five Phase 9 checks to it (single-receipt rule unchanged); a negative test guards it. A second, CI-only failure appeared once newer evidence existed: `ORIGINAL_V1_EXECUTION_ORCHESTRATION.json` hard-coded the r55 pipeline command while production control names the current candidate's repair command. It reproduces only without local Blends (clean clone). Run 466 on `3b1009b1` = success; the clean-clone replay of all 55 CI commands passed.
- **Parallel lineage from r48 (this session, before the live remote head was merged):** r50-r54 -> r55 (smoother corrective) -> r56-r60 (face-area, fold and roughness barriers; weight solver gets the same barriers, presets o45/o46) -> r61/r62 (o45 weights + wrist band) -> r63 (+corrective) -> r66/r67 (barrier saturation: no gain) -> r68 (Option B: LOCAL knot weight edit, 168 vertices declared before the solve) -> r69 (re-fitted corrective). r65 (tight anchoring) and r67 are preserved failures.
- **Finding that drove B:** after the barriers the only structural defect left was a knot of mixed clavicle/upper-arm weights at the front shoulder junction. Option A alone saturated (r66 vs r67), so B was applied locally.
- **Guarded pipeline from r69:** r70 refused (default 1-ring mask 302 vertices > cap 180; r55 would also exceed it), r71 refused (all trials dropped an edge minimum by 0.09-0.12 vs tolerance 0.02). Added only OPTIONAL knobs (`AXILLA_PIT_RINGS`, `AXILLA_PIT_HOLD_REGION_MIN`, `AXILLA_PIT_CONTACT_GUARD`); no cap, tolerance or selection rule changed. r72 (hold family) then r73 (contact-guarded) were produced; r73 has 0 development failures and 0 strict regressions versus its direct parent r72.
- **Milestone capture:** the fixed shared exercise frame cropped the 1.81 m P3 push-up plank (never captured before). Added an explicit measured per-pose frame for `pushup_bottom` (not auto-fit), test-pinned; partial crop preserved.
- **Scapular second driver investigated, not needed:** at equal elevation the scapular rotation differs by about 13 deg between plain and rhythm poses; torso edge stretch differs by 1.2 before the corrective and 0.19 after it.
- **Status of r73:** development failures 0; strict regressions vs P3B1 23 (self-intersections about 100-134 in overhead poses, wider arm/torso ranges - all inside every gate); declared-face audit LOCAL_FACE_REVIEW_REQUIRED (<= 2 flipped faces per arc sample at mid-arc, no collapsed face); end-pose renders still show one small pointed tip at the front pit top; mid-arc renders look natural. NOT eligible for Phase 4: P3B1 is the tent-flap/torn-web state, so closing the armpit necessarily raises contact/self-intersection and arm/torso range metrics versus it. Reaching zero regressions needs an owner disposition (or a re-pinned epoch baseline, which is a comparator change and therefore owner-only).
- **Next:** (1) owner disposition of the 23 strict P3B1 regressions; (2) optionally another contact-guarded/area-weighted local trial family from r73 targeting the mid-arc flipped faces (needs higher hinge weight than the sweep's fixed 20000); (3) Phase 4 only if production control selects `ENTER development freeze validation`.

## Local axilla repair r74-r76 and the visual gap - 2026-10-03 (Claude)

- **Cause of r73's last flipped faces found and fixed.** They occurred only at arc samples that are odd multiples of 1/16 (0.5625, 0.6875, 0.8125); the pipeline's trial dump trained on 0.25..0.875 step 0.125 only. New OPTIONAL knob `AXILLA_PIT_ARC_FRACTIONS` trains on the same 1/16 grid the audit measures (default unchanged).
- **r74 refused (preserved).** Dense training removed every flip in all six trials but every trial broke a selection rule: edge-minimum drop 0.03-0.14 (tolerance 0.02) and edge-maximum rise about 0.16 (tolerance 0.1).
- **r75 refused (preserved).** Added regional-minimum/maximum guards and a separate strong guard weight; no effect, because the selection rule is measured over the MASK edges of each pose, not over whole-mesh regions (region-scope bounds allowed local edges to rise much further).
- **r76 selected and applied.** New `--hold-scope local` (bounds from the mask edges of each pose; margins min 0.015 < 0.02, max 0.08 < 0.1; guard weight 1e6) plus the contact guard. Result: 0 development failures; 0 strict regressions versus the direct parent r73; declared-face audit LOCAL_FACE_NUMERIC_CLEAR (0 flipped, 0 below the signed-area floor, 0 below the area floor, minimum area ratio 0.81); 23 strict regressions versus P3B1 (unchanged). Only the declared 18 left-owned vertices changed (shape-key diff against r73: 18/18, weights, topology and Basis identical).
- **Continuation decision recorded through the verified tool** (`verify_original_v1_continuation_decision.py` -> CONTINUATION_DECISION_VERIFIED; fragment copied unchanged into production control by `scripts/apply_original_v1_continuation_fragment.py`). Classification STRICT IMPROVEMENT versus the direct parent r73 only; retained as the EXPERIMENTAL continuation, not anatomical acceptance, no baseline promotion, Phase 4 not authorised.
- **Honest visual finding.** Real full-body and close-up renders: tears, slivers and crumpling are gone and the right-hand cusp is shorter than r69/r73 but not removed. At overhead poses the shoulders still read as unnatural: a rounded front-shoulder bulb, over-stretched pectoral skin that looks like padded flanges, and a deep scoop under the arm. The pipeline's face audit does not measure this. Roughness is slightly higher than r69 (press_top rough vertices: torso 4 -> 24, shoulder 0 -> 6, worst value 0.9 -> 1.2 edge lengths, introduced by the first local step r72), not visibly significant.
- **Exploratory v18 (no candidate).** A much tighter corrective stretch bound (2.6) improves predicted torso edge maxima only about 10 percent (press_top 3.09 -> 2.85, pullup_hang 3.11 -> 2.61); see `repair_preparation/exploratory_corrective_v18_hi2p6/`. The corrective alone cannot reach physiological stretch (about 1.5-1.6) in the axilla web.
- **Tooling notes.** The pipeline's step 5 (milestone review capture) requires a clean working tree but steps 1-4 write evidence first, so the review/closure/disposition steps must be run after committing (`RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat <r>`, `RUN_ORIGINAL_V1_CANDIDATE_CLOSE.bat <r> <axilla_r>\candidate_closure.json`, `RUN_ORIGINAL_V1_AXILLA_PIT_DISPOSITION.bat <r> <parent>`).
- **Next, in order of evidence:** (1) owner disposition of the 23 strict P3B1 regressions (accept as documented trade-off or re-pin the epoch baseline - both comparator-level and owner-only); (2) a declared local TOPOLOGY/weight refinement of the axilla web and anterior shoulder (new mask, new candidate) aimed at the visual flanges/scoop, since the corrective alone is saturated; (3) Phase 4 only if production control selects `ENTER development freeze validation`.

- **CI ordering rule (learned from red runs 463-469, 474, 475):** the status treats the newest complete full-evidence candidate as current, and `test_candidate_bound_local_repair_precedes_freeze_reconciliation` plus the orchestration test require production control (`active_local_repair`, `continuation_decisions`) and `ORIGINAL_V1_EXECUTION_ORCHESTRATION.json` to name that same candidate. Therefore push a candidate's evidence and its control/orchestration records in the SAME commit (or keep the evidence uncommitted until its decision is recorded). Every red run above was an evidence-only commit; the following commit that recorded the decision was green. A clean clone (no local Blends) reproduces CI exactly: `git clone -b <branch> <repo> <dir>` then run the workflow's commands there.

## Phase 3 sub-phase evidence and the shoulder-top collision finding - 2026-10-03 (Claude)

- **Strict regressions attributed, not assumed.** `repair_checks/axilla_r76/p3b1_regression_attribution.md`: of the 23 regressions versus P3B1, 9 are inherited from the anchored shoulder weights (the tent-flap fix), 8 from the weights plus a further corrective contribution, 4 added by the corrective, 2 in poses outside the shoulder set; all are inside every development gate (smallest margin 0.141). The largest family is shoulder-region self-intersection.
- **Self-intersections located and measured.** In every overhead pose they are all shoulder-region pairs, mirror-symmetric, inside a posed box of about 5 x 10 x 5 cm at the top of each shoulder; about 90 percent are clavicle-driven skin crossing upper-arm-driven skin; median depth 1.5-1.7 cm, up to 4.8 cm; 112 of 132 pairs are 3 cm or more apart at rest (different sheets). The remote's face audit does not measure this.
- **r77 refused (preserved).** Collision-zone declaration `repair_preparation/r77_axilla_pit_declared/` (264 left vertices, filtered to shoulder/torso/neck pairs; the unfiltered 538-vertex declaration is kept as superseded) with a new anti-penetration barrier in `optimize_original_v1_shoulder_corrective.py` (`--w-pen`). Numeric pre-apply selection rejected every trial: the barrier took its side reference from the REST pose, but at rest the arm underside and the shoulder-top skin are not facing each other, so about a third of the constrained pairs started on the wrong side (443,743 of 1,356,043) and the solve distorted the surface. No candidate created. The correct formulation needs sidedness from physics (arm-driven web inside clavicle-driven skin) or from the last non-penetrating arc sample of the same pair.
- **3B/3C/3D/3E evidence for r76** (`docs/ORIGINAL_V1_PHASE3_SUBPHASE_EVIDENCE_r76.md`): hands/fingers 0 gate failures and 0 regressions, values identical to P3B1; grip penetration 1.63 mm (gate 2.0) and 269 contact vertices (gate 20) on every bilateral row; wrist push-up hand minimum 0.24 versus 0.119 in P3B1; hip/leg 0 regressions; rig structure hash and helpers verified; finger flexion and continuous joint kinematics flag nothing; floor contact exact; twist stress worst edges 0.93/0.91/0.94/0.50; an independent re-run of all 15 poses reproduces the committed evidence exactly.
- **Phase 3 exit:** blocked only by the 23 shoulder-attributed strict regressions. Phase 4 preflight stays PHASE4_BLOCKED.

## Shoulder-top crossing: two more refused approaches and what is left - 2026-10-03 (Claude)

- **The crossing is transversal, not a one-sided poke-through.** `scripts/measure_original_v1_si_sidedness_blender.py` on r76 (press_top, rhythm, pullup_hang, rhythm): the upper-arm-driven sheet is outside the clavicle-driven sheet in about half the intersecting pairs and inside in the other half, medians about 0, and the outward normals are nearly perpendicular (median cos -0.06 to -0.33). So no single push direction resolves it; a displacement corrective cannot fix it and a rest-pose side reference is wrong for it (r77 refusal).
- **o48 collision-resolving weights refused (r78/r79, `repair_preparation/refused_r78_r79_o48_collision_resolving_weights/`).** Self-intersections P3B1 / r62 / r79: press_top 95 / 137 / 250, press_top_rhythm 54 / 148 / 298, pullup_hang 4 / 116 / 66, pullup_hang_rhythm 0 / 126 / 84, squat_bottom 108 / 138 / 154; 4 development failures. The solver's own per-round intersection counts rose in the press poses (462/530). Manifests moved out of the candidate manifest folder so the status tool does not read a refused experiment as an incomplete candidate (the Blends stay, labels stay reserved).
- **State after this session:** r76 remains the experimental continuation (0 development failures, 0 regressions versus its parent, numeric-clear declared faces). Sub-phases 3B, 3C, 3D, 3E are clear on the measured evidence (docs/ORIGINAL_V1_PHASE3_SUBPHASE_EVIDENCE_r76.md). Phase 3 cannot exit while production control counts the 23 shoulder-attributed strict regressions versus P3B1; Phase 4 preflight stays PHASE4_BLOCKED.
- **What would actually change the picture (all need a decision, none is a quick experiment):** (1) owner disposition of the 23 regressions - P3B1 is the tent-flap/torn-web reference (14 gate failures), so a disposition record or a re-pinned epoch baseline are comparator-level choices; (2) a first-party re-topology of the shoulder-top / axilla web (more resolution and a smoother clavicle-to-humerus weight ramp where the two sheets interleave) as a declared-mask candidate; (3) shoulder helper bones, which would reopen the locked rev2c skeleton and is only justified by direct skeleton evidence.

## r80: smoothing the shoulder-top weight ramp cuts the strict P3B1 regressions from 23 to 13 - 2026-10-04 (Claude)

- **Cause found in the weights.** In the declared collision zone (528 vertices) the clavicle/upper-arm weight jumps between neighbouring vertices 0.102 on average (p90 0.188, max 0.664), a gradient of 0.062 per cm versus 0.024 per cm over the whole shoulder zone: the two skin sheets rotate very differently over a very short distance, so they cross. This replaces the earlier (wrong) displacement-only and collision-barrier explanations.
- **Smallest controlled change.** `scripts/smooth_original_v1_weights_zone.py` diffuses the weights of exactly the declared zone (12 iterations, lam 0.5; boundary fixed, mirror-symmetrised, top 4 influences). Declaration committed before the edit (`repair_preparation/r80_collision_zone_weight_smoothing_declared`). Weights-only probes on r68 (3, 6 and 12 iterations, metrics-only): self-intersections fall steadily with iterations; the shoulder minimum edge ratio in pull-ups breaks the gate (0.09-0.14) until the corrective is refitted.
- **r80 = smoothed weights + refitted corrective** (corr_v19; mask declared before the solve; same barriers as r69). Full 15-pose evidence: 0 development failures. Strict regressions versus P3B1 **13** (was 23); versus r76 7 small compressions, all inside the gates. Self-intersections P3B1 / r76 / r80: press_top 95 / 132 / 58 (now below P3B1), press_top_rhythm 54 / 112 / 74, pullup_hang 4 / 102 / 40, pullup_hang_rhythm 0 / 126 / 48, squat_bottom 108 / 138 / 100 (below P3B1). Continuous arc: torso edge max 3.10, min 0.471, volume 0.994-1.042 with max step 0.8 percent. Attribution of the 13 (`repair_checks/axilla_r80/p3b1_regression_attribution.md`, reference = r68 metrics-only): 6 weights plus corrective, 5 weights, 1 corrective, 1 outside the shoulder poses. Thin margin: squat_bottom shoulder minimum edge ratio 0.178 (gate 0.15).
- **Recorded** as a TRADEOFF_OR_REGRESSION continuation (parent r68 weights lineage), evidence and control in the same commit. Not a Phase 4 candidate: 13 strict regressions remain.
- **Next technically justified step:** a second declared iteration on the same lever (stronger or wider smoothing of the clavicle/upper-arm ramp, e.g. more iterations or one extra ring, then a corrective refit) aimed at the remaining self-intersections and the arm/torso minimum-edge compression; or an owner disposition of the remaining 13.

## r81: widening the smoothed zone removes every shoulder self-intersection regression - 2026-10-04 (Claude)

- **Lever pushed one step further.** r80's 528-vertex zone had fixed boundary vertices that capped how far the clavicle/upper-arm weight ramp could widen. The zone was dilated by 2 mesh rings (834 vertices, declaration committed before the edit; `declare_original_v1_dilated_weight_zone.py`). Weights-only probes on r68 (metrics-only): k=12 barely differs from r80's zone (pull-up SI 40/64), k=30 reaches press_top 58, rhythm 72, pullup_hang 0, hang_rhythm 0, squat 82 before any corrective (shoulder min edge ratio 0.123/0.131 in two press poses, to be recovered by the corrective refit).
- **r81 = k=30 dilated smoothing + refitted corrective (corr_v20).** Full 15-pose evidence: 0 development failures; strict regressions versus P3B1 **12** (r80 13, r76/r69 23). Self-intersections P3B1 / r80 / r81: press_top 95 / 58 / **16**, press_top_rhythm 54 / 74 / **12**, pullup_hang 4 / 40 / **0**, pullup_hang_rhythm 0 / 48 / **0**, squat_bottom 108 / 100 / 82 - every shoulder self-intersection regression is gone. Arc (17 samples): torso edge max 3.58, min 0.490, volume 0.984-1.039, max step 0.8 percent. Corrective audit CLEAN (asymmetry 0).
- **Remaining 12** (`repair_checks/axilla_r81/p3b1_regression_attribution.md`; all inside the gates, smallest margin 0.032): compression-type minimum-edge-ratio drops (press_bottom torso 0.526 vs 0.698; press_top arm 0.702 vs 0.78; press_top_rhythm arm 0.621 vs 0.679; pull-up arm 0.688/0.727 vs 0.865/0.838; pullup_top torso 0.654 vs 0.693; squat arm 0.383 vs 0.597, shoulder 0.182 vs 0.244), squat volume deviation 0.050 vs 0.044 and edge_ratio_p01 0.579 vs 0.613, push-up self-intersections 164 vs 158 (outside the shoulder poses, unchanged since r48). 7 inherited from the anchored weights, 3 added by the corrective, 1 mixed, 1 outside.
- **Process fix:** the classifier now handles the volume-deviation metric. Evidence and control were committed together (CI ordering rule).
- **Next technically justified step:** attack the compression family (minimum edge ratio): more smoothing iterations or a relaxed/targeted corrective compression floor in the arm/torso regions, declared before the edit; or owner disposition of the remaining 12.

## r83: regional hold guards on the corrective cut the strict P3B1 regressions from 12 to 7 - 2026-10-04 (Claude)

- r83 = r81's weights + the corrective re-solved with regional hold guards (cannot lower a region's minimum edge ratio or raise its maximum beyond the weights-only pose). 0 development failures; strict regressions versus P3B1: **7** (r81 12). Self-intersections press_top 32 / rhythm 28 / pull-ups 0 / squat 82 (P3B1 95 / 54 / 4,0 / 108). Trade versus r81: +16 shoulder self-intersections in the two press poses, pull-up volume deviation 0.005 to 0.012.
- Remaining 7 (epair_checks/axilla_r83/p3b1_regression_attribution.md): press_top arm min 0.745 vs 0.78, pullup_top torso min 0.669 vs 0.693, push-up SI 164 vs 158 (outside 3A), and four squat items (arm min 0.383 vs 0.597, shoulder min 0.182 vs 0.244, volume deviation 0.050 vs 0.044, p01 0.579 vs 0.613) inherited from the dilated-zone weights (r68 weights give squat arm 0.529).
- Refused beside it: r84 probe (hold margin -0.1, lifting every region minimum: 14 regressions, 4 development failures).
- Tooling fixes: `original_v1_epoch_baseline.py` had an unterminated backslash string; the evidence runner needs `BLENDER_EXE` set and `NoDefaultCurrentDirectoryInExePath` unset.
- Next: a declared weights change limited to squat arm/shoulder skin, or owner disposition of the remaining 7.

## r83 retained; r85 squat-local weight blend rejected on numerical screening; helper-bone analysis - 2026-10-04 (Claude)

**Retained state.** r83 (SHA `bc26867409df7514be9a18bb97e75f6cf8171df8e0f99a9d69648acbe3752b6d`), HEAD at the time `31e8fb68` plus the r85 evidence commit. 0 development failures; 7 strict P3B1 regressions; Phase 3 open (`unresolved_regressions`), Phase 4 locked. 3B/3C/3D/3E development-clear. r83 is the known-good fallback. P3B1 not re-pinned; nothing accepted on the owner's behalf; skeleton rev2c untouched.

**The seven (candidate vs P3B1; tolerance; gate margin) and their origin** (`repair_checks/axilla_r83/p3b1_regression_attribution.md`):

| # | pose / metric | r83 | P3B1 | tol | dev-gate margin | origin |
|---|---|---|---|---|---|---|
| 1 | squat_bottom arm region min edge ratio | 0.383 | 0.597 | 0.02 | 0.233 | weights (dilated smoothing zone) |
| 2 | squat_bottom shoulder region min | 0.182 | 0.244 | 0.02 | 0.032 | weights |
| 3 | squat_bottom volume deviation | 0.0500 | 0.0438 | 0.005 | 0.050 | weights |
| 4 | squat_bottom edge_ratio_p01 | 0.579 | 0.613 | 0.02 | 0.179 | weights |
| 5 | press_top arm region min | 0.745 | 0.780 | 0.02 | 0.595 | weights (pre-corrective 0.749) |
| 6 | pullup_top torso region min | 0.669 | 0.693 | 0.02 | 0.519 | added by the corrective (pre 0.680) |
| 7 | pushup_bottom self-intersecting pairs | 164 | 158 | 5 | 36 | legacy / outside the shoulder poses, unchanged since r48 |

Origin tally: 5 weights, 1 corrective, 1 legacy push-up.

**Squat-local experiment (r85, declared before the edit, rejected).** `repair_preparation/r85_squat_local_weight_blend_declared/` (declaration of 382 vertices, hypothesis, stop condition, scripts, outputs, README). A continuous blend of the smoothed weights back toward r68 weights in the squat-critical sub-zone (numpy LBS verified to 4e-7 m) lifts the squat arm minimum to at most 0.523 (needs 0.577) and the shoulder minimum to at most 0.226 (needs 0.224) only at strengths that add a squat shoulder stretch regression of +0.17 to +0.33 (tolerance 0.1) and a press_top_rhythm arm minimum drop of 0.026-0.049. Hard reverts (height cut, local radius) show the same frontier or worse (shoulder minimum 0.117). Squat volume and p01 are not touched by the sub-zone. No strictly preferable candidate exists, so no Blender candidate or full evidence was produced; r83 retained and the stop condition applied (no further tweaking).

**Evidence that the local skin-weight mechanism is at its frontier.** Weights-only: r68 weights give squat arm 0.529 / shoulder 0.229 but press_top self-intersections 153 / rhythm 168 / pull-ups 126 / 134; dilated k=30 weights give the press/pull-up gains but squat 0.383 / 0.182; shoulder-only k=60 (r82) removes the intersections but loses arm/torso compression; continuous partial blends (r85) interpolate between the two and cannot reach both sets of thresholds. The squat constraint (the same skin that must be smoothed for the shoulder-top intersections must stay near-rigid for forward-flexed arms) is a trade-off of one weight field serving two arm-motion families.

**Key finding: the shoulder corrective is inactive in the squat.** In squat_bottom humerothoracic elevation is 125.9 degrees but the trunk-frame abduction fraction (the corrective's gate) is 0, so the corrective changes nothing there; the four squat regressions are pure skin weights. A second, non-skeletal corrective key driven by shoulder FLEXION (forward elevation) could displace the squat arm/shoulder skin without touching weights or the skeleton.

**Is a helper-bone mechanism technically justified?** Not yet. The measured gap is explained by an unused degree of freedom (the missing flexion-gated corrective), which is a much smaller intervention than a skeleton change; helper bones are justified only if a flexion-gated corrective, solved under the existing barriers and the regional hold guards, cannot lift the squat arm/shoulder minima to P3B1 - 0.02 without regressing the press/pull-up poses.

**Smallest possible skeleton intervention (NOT implemented, needs owner authorisation).** Two mirrored deltoid/shoulder-volume helper bones (e.g. `deltoid_l/r`), parented to the upper arm (or clavicle), no animation keys, driven by a constraint from the humerus swing so they counter-rotate half the forward flexion; ~380 vertices reweighted around the deltoid. Rig rev2c -> rev2d: 69 bones / 68 deform.
- Blast radius: the locked skeleton (67/66), every pinned baseline that records bone counts or rig hashes (R2, P2B1, P3B1 epochs), the final-freeze and rig-structure audits, the standalone/export engine (new bones and constraint), CI fixtures that assert 67/66, joint-limit and twist-stress audits, hand/grip/wrist/hip evidence (re-run to show no change), determinism and export checks.
- Validation required: new rig revision declared and committed before the edit, a fresh epoch baseline decision by the owner (re-pin is owner-only), the full 15-pose suite plus arc audits, sub-phase 3A-3E reports, rig-structure/floor-contact/joint-kinematics/twist audits, determinism replay, CI replay, and review imagery.

**Recommended next action:** (1) owner decision on whether to authorise a flexion-gated second corrective (no skeleton change; new driver, apply/audit/runtime-spec changes, declared mask, 15-pose evidence); (2) only if that fails the same strict comparison, owner decision on helper bones or on a documented disposition of the remaining seven.