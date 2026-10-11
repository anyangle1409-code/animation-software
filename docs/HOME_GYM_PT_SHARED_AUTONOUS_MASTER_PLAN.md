# HOME GYM PT — SHARED AUTONOMOUS MASTER PLAN
**Single shared instructions file for ChatGPT Work (laptop) and ChatGPT (independent GitHub development)**

**Version:** 1.0 · 11 October 2026 · **Authoritative execution plan, not an anatomical measurement authority**
**Canonical location:** `docs/HOME_GYM_PT_SHARED_AUTONOMOUS_MASTER_PLAN.md` on branch `codex/shared-autonomous-master-plan-20261011` in `anyangle1409-code/animation-software`.
**Project repositories:** `anyangle1409-code/animation-software` (anatomical master, original human body, animation engine); `anyangle1409-code/PT-App` (independent first-party app).
**Development rule:** This file coordinates execution. The separately audited primary scientific sources, machine-readable anatomy, freeze readiness JSON, tests and original scans remain the **evidence authorities**. If a status or checkpoint here is older than the live GitHub branch, fetch/reconcile the live evidence first; do not overwrite newer work.

> **Owner goal:** A fully original, anatomical-skeleton-first male human model, realistic under a broad range of exercise movements and loads, supported by a project-owned animation/rendering runtime and app. No purchased/third-party character, no redistributed third-party exercise clips or third-party runtime dependency in the released product. Blender, scientific papers, source CT reference material and development-only tools may still be used during development subject to rights and provenance controls.

---

## 0. ALWAYS-ON STARTUP / RESTART PROCEDURE — RUN FIRST ON EVERY INVOCATION

1. Fetch LIVE GitHub heads and PR/CI activity before any edit, especially Work's [PR #26](https://github.com/anyangle1409-code/animation-software/pull/26), independent engine [PRs #41](https://github.com/anyangle1409-code/animation-software/pull/41), [#42](https://github.com/anyangle1409-code/animation-software/pull/42), [#43](https://github.com/anyangle1409-code/animation-software/pull/43), [#46](https://github.com/anyangle1409-code/animation-software/pull/46), Work CT [#44](https://github.com/anyangle1409-code/animation-software/pull/44), Work Windows [#45](https://github.com/anyangle1409-code/animation-software/pull/45), Claude's active skeleton branches, and recently committed documentation. Do not assume branch heads or earlier checklists are current.
2. Read THIS ENTIRE FILE plus, for anatomy, `docs/COMPLETE_HUMAN_SKELETON_LIVE_TRACKER_20261007.md`, `docs/REGIONAL_ANATOMY_REMAINING_GATES_20261011.md`, `docs/MASTER_AUTONOMOUS_HANDOFF_20261010.md`, `docs/MASTER_AUTONOMOUS_EXECUTION_20261010.json`, and `ORIGINAL_V1_WORK/anatomy/canonical_freeze_readiness_v1.json` from their latest relevant branches. Do not treat a file missing from the current checkout as nonexistent; check the authoritative branch.
3. Check local Git status, uncommitted files, active Blender processes, downloaded **private** reference assets, CPU/memory/disk space and existing generated artifacts before starting expensive operations. Keep source images/CT and sensitive subject records outside public Git. Never silently discard another agent's uncommitted work.
4. Reconcile exact checkpoint SHAs, PRs and test outcomes. An earlier passing CI run does not prove a newer head is green. For a red test, classify **pre-existing versus caused by the current change**. Use targeted tests and a bounded failure reproducer before any full suite rerun.
5. Choose the **highest-priority executable** item from the assigned lane below for which required evidence and tooling exist. Complete one bounded subtask with a measurable test/artifact, then continue to the next subtask **without requesting routine user approval**.
6. Each completed subtask must leave a durable Git checkpoint: branch, commit SHA, changed paths, commands, relevant CI run/results, source IDs and hashes when applicable, PASS/FAIL/SKIP plus exact unresolved limitations. If unable to push from a laptop, save a clearly named local commit/log and resume publishing at next available session. Never say a task is complete when only scripts or documentation were written but required real execution did not occur.
7. When a source is inaccessible, evidence is inadequate, CI is blocked, laptop hardware is unavailable, or quota is exhausted: log the exact blocker; **do not invent data or repeat identical failed requests**. Switch to the next independent unblocked item. Stop only when no safe/executable item remains, resources/tools are genuinely unavailable, or the current session ends.
8. When invoked again after any quota reset, repeat steps 1–7, recover current live heads and continue from the latest actual checkpoint. **A prompt cannot independently restart a stopped ChatGPT Work or Claude session, wake the laptop, bypass quota, or promise overnight background operation.** Use platform-supported persistent automation only if actually enabled; never claim it is.

### Safety and collaboration invariants

- The **anatomical skeleton is the authority**. Source-validated bones/joint locations set the target; mesh, muscles, deformers and skin must follow them. Do not distort or rescale bones to fit the skin or a renderer's test cylinder.
- Preserve frozen **a003** baseline, noncanonical **c001–c004** candidates and audited historical outputs. **c005 is NOT accepted**. Never convert provisional measurements/threshold voxels, foreign-cohort averages or scripted synthetic models into approved anatomical geometry.
- No force push, history rewrite, destructive rebase or overwrite of another agent's branch. Use independent worktree and **separate topic branch/draft PR** for substantial changes. Do not merge to main, rewrite accepted owner decisions or change legacy V-series while in this programme.
- GitHub is the handoff mechanism: actual commits + linked targeted CI + compact status comment on Work PR #26 or current agreed coordination PR. Never rely on an invisible chat transcript.
- Source rig/body may have a left/right naming reversal. Preserve PR #27/#29 chirality evidence; do not infer anatomical left from `*_l`, Blender axis labels or bare source filenames. Explicitly verify frame, coordinates and handedness.
- External scientific evidence/source 3D scans are **development evidence, not automatically approved proprietary output assets**. Track licensing, redistribution rights, origin and isolation. **First-party** assertions must distinguish production app code, isolated renderer subsets, still-vendored studio, original body geometry, and temporary clips.
- Clinical/anatomical approval needs appropriately qualified independent review and original body-specific corroboration when the source requires it. Passing a unit test or generating a Blender render is not equivalent to correct anatomy or realistic deformation.
- Escalate to the owner only for a genuinely unavoidable policy/medical rights decision, proprietary release approval, a destructive change, or an unresolvable conflict requiring a choice. Otherwise make **reversible, conservative progress** and leave blockers explicit.

---

## 1. LIVE BASELINE — SNAPSHOT VERIFIED 11 OCTOBER 2026 (RECHECK WHEN USED)

| Area | Confirmed starting point | Acceptance boundary |
| --- | --- | --- |
| Master tracker | **Phases 0–5 gates PASS**: 206 conventional adult bones; 427 joint/contact entities; 30 semantic frame definitions; 44 mechanics profiles. Phase 5 runtime naming/chirality interpretation has reopened detail. | These are inventories/reference atlases, **not** validated body geometry |
| Phase 6 | **CP1 / Gate 6 OPEN**, a003 audited comparison baseline; no accepted corrected master target. | This is the primary programme blocker |
| Regional freeze | **0 READY / 9 PARTIAL / 3 BLOCKED** across 12 regions. | Keep independent source-based review gates |
| Phase 7 | Structural anatomical master exists: 206 bones, 427 joint markers, 51 landmarks. | Structure verified only; bone positioning NOT passed |
| Phases 8–9 | Solver core and **135** isolated diagnostic sweeps exist, with known gaps and physiology/provenance caveats. | Gates 8/9 NOT passed |
| Phases 10–13 | Natural whole-body functional motion, derived runtime rig, physiological mesh deformations, app export/performance. | Gates 10–13 NOT passed |
| Current Work lane | `codex/source-skeleton-blender-measurements-20261010`, PR #26; snapshot head `b8fcb6470347044bfd3b749bfbc84a8989573260` (DO NOT treat as immutable live head). | Work may update after this file was written |
| Completed source processing | Female separate-subject **201** original CT slices first-reviewed and calibrated, corresponding native Blender timeline plus **21** bounded intensity slabs; male/pelvis **82** source frames with two acquisition groups and native viewer; BoneHub 54 source surfaces, 30 wrist/foot meshes and 44 candidate proximity pairs; 2011 C7–T12 posterior/anterior vertebral heights. | Not source-registered human landmarks, accepted bone surfaces or corrected canonical targets. **Do not repeat these acquisition/review loops** |
| Full regression | Work records inherited expanded baseline **1,097 tests / 20 failures / 41 errors / 1 skip**; root-cause classification needed. | Do not claim all-green based on passing targeted CI |
| First-party app | PT-App's audited branch has **zero npm runtime and development dependencies**; temporary **304 third-party exercise video clips** intentionally remain until replacements are proven. | No customer-ready original animation package |
| First-party rendering | Isolated original WebGL2 skeletal GPU PR #41; indexed triangle/four-weight CPU LBS PR #42; strict restricted GLB importer PR #43; explicit GLB-to-rig numerical bind check PR #46. Browser/Node proofs verified on *synthetic meshes*, not original human. | Regular animation studio still depends on **Three.js** through one gateway; not removed |
| Original body | `HomeGymPT_Male_ORIGINAL_v1`, planned `hgpt_canonical_v4_original`. | No accepted first-party production model / full-body movement & surface deformation approvals |

**Evidence cross-check:** Region checklist `docs/REGIONAL_ANATOMY_REMAINING_GATES_20261011.md` (on Work source branch); owner skeleton-first decision `docs/SKELETON_FIRST_PRODUCTION_POLICY_20261008.md`; Work PR #26; original master tracker. Source status is deliberately not a percentage-complete estimate.

---

## 2. ASSIGNMENT / OWNERSHIP — PREVENT DUPLICATE WORK

### LANE W — ChatGPT Work on laptop (PRIMARY CRITICAL PATH; owns Blender and human anatomy)

Work owns anatomical evidence intake, **source-to-HGPT coordinate registration**, 206-bone/joint frame correction, original Blender model construction, natural human movement and physical visual validation. Claude, if active, may work only on separate explicitly coordinated anatomical subtasks and must publish independent evidence, never silently rewrite Work's accepted baseline.

Work must **NOT** duplicate GPT's first-party WebGL renderer/GLB binary parsing work from PRs 41/42/43/46. Work may consume their interfaces only after acceptance and may offer integration requirements via PR comments.

### LANE G — ChatGPT in this chat / independent GitHub session (owns FIRST-PARTY SOFTWARE)

Own original native renderer and application integration readiness independent of still-unapproved anatomical geometry. Build on PRs 41→42→43→46, on **independent new branches/draft PRs**. Use original procedural synthetic meshes and clearly identified mock fixtures until provenance/mesh/rig exports are validated. Own dependency inventory, first-party material/normal/UV/texture primitives, multi-mesh data loading, multi-bone palette/performance/robustness, native camera/scene inputs, automated app-interface adapter, offline checks, and device/browser test contracts.

Lane G must **NOT** edit Work's CT source, canonical bone geometry, Blender worktree, frozen scientific figures, movement amplitudes or human-model mesh candidates; never claim a synthetic tube/test triangle looks human.

### Coordination handshake

- **Work consumes:** stable types and acceptance reports from independently verified renderer PRs, not arbitrary WIP code. Work supplies *metadata only*, such as actual model export schema, model-native bone names, inverse-bind conventions, mesh count/vertex attributes, neutral posture, canonical frame and rights/approval evidence (not confidential CT/medical bytes).
- **GPT consumes:** those schema facts and source-approved joint IDs only when published; extend the first-party loader/rendering tests to meet real model **without moving the model bones**.
- Each lane posts a brief checkpoint on Work PR #26 (or newer central PR when Work moves): `LANE, task ID, input HEAD, output branch/commit, tests/CI, source scope, decisions, blockers, next task`.
- The **single runbook file** is the durable shared policy/task map. Avoid concurrently editing this file. For new milestones, post timestamped progress to the active lane's PR/ledger, then propose any necessary runbook change on a **separate PR** and reconcile newer updates before accepting it.

---

## 3. LANE W EXECUTION QUEUE — STEP BY STEP, IN DEPENDENCY ORDER

**W0 — Preserve and triage before new work (repeated on session entry)**

Fetch current GitHub and local Work/Claude states; inspect PR #26, #44 and #45, updated master JSON, original source hashes, unresolved open local work and real CI. Verify what truly happened since latest checkpoint. Confirm no required source file is accidentally absent from an isolated checkout. Correct targeted regressions caused by Work's own changes; classify inherited red suite by root cause without repeating full 1,097-test run unnecessarily. Evidence: targeted test logs, exact SHA and open issues.

**W1 — CLOSE PHASE 6 / CP1 SOURCE REGISTRATION (highest priority; can parallelize independent regions)**

Complete unverified **source-pinned anatomical landmarks, patient physical coordinate frames and HGPT skeleton registration**. Use real Blender 5.2.1 and original source evidence. Reuse existing CT viewers and source pixel/header/volume/surface inspections; **no rebuilding existing 201-slice, 82-frame, 21-slab, 54-STL or 30+44 pair audit**. Do not treat HU-only blobs/synthetic meshes as named bone surfaces. Record patient sex/cohort/stature/posture, source grid/pixel centre, laterality, millimetres/metres and uncertainty. Validate landmarks with a genuinely independent method and qualified review where required.

Critical anatomical subqueue, choosing an evidence-ready item rather than endlessly querying a blocked paper:
- **W1A pelvis/hip/sacrum:** accepted full paired os coxae & sacral geometry, **seven independent landmarks**, source→rig frame transforms, socket/femoral head centres and sacroiliac/hip joint relations. 82-frame pelvis viewer and the separate female201 set remain separate cohorts.
- **W1B spine / rib cage / shoulder coupled frame:** standing per-level cervical→sacral alignment, T1–T12 endplate AP depths and vertebral angles from actual source; consistent SC/manubrium/AC/GH centres, scapula and rib contacts. Keep unresolved Finoco Table 6 behind access blocker; do not fabricate its values, derive individual angles from body front/back heights alone, or distribute global kyphosis uniformly.
- **W1C wrist/hand/forearm:** eight carpals in a matched frame, radial/ulnar head/DRUJ and wrist/CMC sources, bone-envelope and articular contact evidence. Use earlier source-pinned 30 original mesh/44 nearest-vertex checks as *relative candidates only*; they are not clinical cartilage gaps or verified mm measurements.
- **W1D ankle/foot:** tarsal joint surfaces, subtalar/talonavicular/tarsometatarsal contacts, foot bone dimensions and stature-aware forefoot partition.
- **W1E remaining regions:** long bones, knee/patella, humerus, head/neck, digit lengths, ribs and rib/cartilage contacts against the 12-region authoritative gate ledger. Never mark a region READY because a different region made progress.

For every region: `original evidence → source ID/hash/definitions → independent second check → 3D coordinates & uncertainties → joint/surface/contact validation → candidate only → explicit region gate evidence`. **Freeze only when accepted by the controlling anatomical gate**, not because scripts are green. If blocked on external primary literature, work a different source/region; do not continuously repeat access-denied requests.

**W2 — Correct and freeze the anatomically validated skeleton (depends on W1 region evidence)**

Keep a003 immutable; create reversible named candidate on separate branch/Blender file only for proven measurements, verify 206 identities/427 markers and 12 regions, plus actual joint separation, left/right frame, symmetry, stance, rib/spine coupling, shoulder girdle, realistic lengths and connected joint centres. Use source-specific renders and numerical comparisons in at least front, side, rear and full raised-arm/deep-flexion postures. Independently validate candidate against original sources. Do not promote `c005` or mark Phase 6/7 passed until all requirements are genuinely met.

**W3 — Complete native joint solvers and isolated bone motions (Phase 8/9)**

After appropriate anatomy is validated, finish cervical/thoracic/lumbar disc coupling, SC/AC/GH and scapulothoracic rhythm, rib-sternum movement, pronation/supination, individual wrist/carpus, thumb opposition, SI/pelvis, patella/TFJ and ankle/foot followers/contact. Verify all relevant DOFs, neutral/rest transitions and physically sourced ROM/load context. Retain existing 135 sweeps and their tests; expand missing distinct controls and confirm mirrored anatomical laterality, reversible state, joint-centre trajectory, limits and hierarchy. Unsourced exercise peak angles remain quarantined (78 examples); no guessed amplitudes.

**W4 — Natural whole-body exercise behaviour (Phase 10)**

Only after the relevant anatomical/solver gates: use first-party authored exercises plus independent real human photo/video and scientific evidence, both unloaded and with representative resistance/contact. Cover squat/lunge/hinge, curl/row/press, push-up/plank/pull-up, hand support/grip, rotation/overhead, stance/foot mechanics and compound poses **beyond the initial five exercises**. Check kinetic chain, load-sensitive posture, floor/equipment contact, joint limits, anatomy-specific soft tissue clearance, breathing/rib contribution, physical reference frames and source-grounded motion. Fail and log visually implausible cases; tests alone do not certify realism.

**W5 — ORIGINAL-v1 production human model + anatomical runtime skeleton (Phase 11/12)**

Fit *original project-authored* mesh to accepted anatomical skeleton; correct chest/axilla/shoulder deltoids, torso, hand/thumb, hips, knee/patella, foot and overhead contours across broad representative poses. Record mesh/texture provenance/rights, weights, normal/UV topology, bind-pose transforms, IDs, deformation shapes and independent image/video comparative evidence. Derive a compact runtime rig only if equivalence to anatomical master is proven. Export a genuinely original test GLB **without privately sourced medical content or restricted third-party geometry**. Provide source GLB schema/metadata and immutable hashes to LANE G (do not require manual user transfer if tooling allows). Do not claim anatomically/production ready prior to full-body validation.

**W6 — Joint integration and release validation (Phase 13, shared signoff)**

Collaborate with LANE G on accepted model/native software integration and end-to-end original exercise generation in PT-App. Performance/fps/CPU/GPU/memory/GLB size/influences and offline tests on target hardware; app UX including mobile text focus; verify no third-party runtime/services/creative assets ship, all temporary 304 clips are genuinely replaced **before deleting** them from the app distribution. Run all project/release guards; record exact first-party legal/provenance boundary and distribution checks.

**W7 — Completion report (last milestone, only after evidence)**

Produce human-readable final report with phase gates 0–13, each of 12 anatomical regions, per-joint proof, primary source identifiers, Blender artifacts, motion video comparisons, tests and remaining limitations. Declare DONE only with all gates and original user-required realistic movement validated, zero undesired third-party runtime/assets and on-device app integration acceptance. Otherwise report precisely what is NOT done.

---

## 4. LANE G EXECUTION QUEUE — PARALLEL, FIRST-PARTY RUNTIME

**G0** Sync LIVE PRs 41/42/43/46 and original animation-studio vendor inventory; check CI against *latest* exact head, note any Work feedback. Read this file. Maintain non-production synthetic test baselines.

**G1 — Native mesh feature parity** Add truly first-party **multi-primitive and multi-mesh** bounded geometry data representations, canonical node/skin hierarchy support (without invented transforms), source-owned material/normal/UV attributes and safe CPU/GPU buffers/shaders. Incrementally extend strict GLB importer; every new supported feature must have positive real-WebGL and adversarial negative tests. Preserve existing reject-unknown and memory bounds. Do not weaken security checks to make arbitrary GLBs load.

**G2 — Efficient project-owned skinning** Develop and compare GPU palette skinning against prior four-weight CPU LBS for controlled poses, correct normals and weights, large indexed models and multiple bones. Validate bind/world palette, hierarchical transforms and handedness with an explicitly verified first-party rig. Do not claim full human skinning from synthetic tubes.

**G3 — Studio/runtime independence** Replace remaining Three-backed scene, camera/orbit interaction, picking, equipment, animation rendering, shading/lighting/shadow/material and lifecycle on reversible feature switches with browser screenshots and parity tests. Preserve existing production character viewer until all functions work. Defer uninstalling `three` and setting the guard threshold to zero until the full editor tests and actual accepted human-character parity pass.

**G4 — App/engine integration contract** Define zero-network on-device first-party interface for `exercise text command → authored exercise spec/constraint solver → pose frames → skeletal skin → rendered exercise` and typed first-party model asset/hashes, offline fallbacks, cancellation/device resource limits. Run fake/synthetic integration tests now; real ORIGINAL-v1 GLB only after W5 model acceptance. PT-App existing zero-npm-dependency shell must stay intact.

**G5 — Release dependency clearance** Inventory npm/vendor runtime, build-time-only tooling, embedded external media, generated licenses/provenance; test offline/browser/mobile packaging with explicit definitions. Once W5/W6 parity is verified, replace/remove remaining vendor gateway, temporary animations, packaged external assets, reject third-party dynamic requests and verify full standalone release. Git history rights review separate from installed bundle; do not rewrite shared Git history casually.

**G6 — Acceptance notes** Post each verified incremental PR and CI/test/synthetic-only boundary on Work PR #26 (or current central PR). Coordinate actual ORIGINAL-v1 asset schema without asking Work to redo finished renderer research or move bones for skinning.

---

## 5. SHARED GATES / ACCEPTANCE RULES

| Milestone | Evidence required to declare PASS |
| --- | --- |
| Gate 6 — canonical body fit | Validated source geometry and physically registered 12-region coordinate frames; independent second review; zero outstanding unapproved anatomical region; corrected Blender skeleton candidate accepted |
| Gate 7 — master geometry | Verified 206/427 structural inventory **plus** correct accepted placements, laterality and physical joint/surface relationships |
| Gate 8–9 — anatomy dynamics | Source-supported coupled contact/follower mechanics; coverage of all required bone motions and mirrored transforms; isolated rig tests pass with no quarantined unsourced peaks promoted |
| Gate 10 — functional biomechanics | Whole-body broad exercise poses under load/contact, real-world comparative observations, correct kinetic chain, body-wide realistic geometry and movement; source/posture-dependent limits |
| Gate 11–12 — character & skin | Original human mesh asset provenance, weights/correctives, full-body visual deformation and anatomical master↔runtime correspondence tested |
| Gate 13 — shipped app | Validated first-party 3D engine/GLB original model; performance on target phone; offline animation generation; no external runtime libs/services/temporary clips shipped; release tests PASS |

**Task state vocabulary:** `NOT_STARTED`, `ACTIVE`, `PARTIAL`, `BLOCKED_EVIDENCE`, `BLOCKED_TOOLING`, `VERIFIED_CANDIDATE`, `READY_FOR_REVIEW`, `APPROVED` (only with genuine authority), `DONE`. Never convert `PARTIAL` to `APPROVED` because a synthetic GPU test, raw HU mask or CI pipeline passed.

### Time/usage efficiency

- Prefer one meaningful working code/geometric proof over a pile of documentation-only status commits.
- Never repeat previously hashed source scans/CT image acquisitions/201 frame first reviews, repetitive vendor-source denial retries, 135 sweeps or large full regression scans unless new material evidence justifies it.
- After a source blocker, switch to another region (W) or independently executable rendering feature (G). Avoid research loops. Use free/open primary tables only where accessible and scientifically compatible.
- Run light targeted CI first, then browser/Blender tests, then full regression only at meaningful integration boundaries.
- Keep changes small, reversible, CI-backed and clearly attributed to their owning lane.

---

## 6. COMPLETION / HANDOFF MESSAGE FORMAT (POST TO CENTRAL PR WHEN CHECKPOINTING)

```text
HOME GYM PT — <WORK|GPT> — <YYYY-MM-DD time zone> — <W1A|G2|...>
LIVE INPUT: <branch + exact SHA>; checked other agents' heads <yes/no>
DONE: <genuinely executed result; what changed>
EVIDENCE: <primary source IDs / local private-path indicator / model asset identity>
VERIFY: <commands; numerical results; Blender/browser result; GitHub Actions URL>
OUTPUT: <branch + commit SHA + PR>; SAFE TO REUSE: <paths/interfaces>
GATES: <unchanged or exact evidence-based changes, approver>
BLOCKED: <facts still missing; never invent>
NEXT: <highest priority dependency-respecting executable task>
```

**Automatic continuation policy:** On every active session continue the next unblocked task, committing progress and avoiding interruptions for routine status. For restarts/recovery after limits, the user may launch a new Work session with the simple prompt below; no tool here can guarantee it reawakens by itself.

**Short Work prompt (copy only the sentence, not this entire file):**

`Read the shared master plan on branch codex/shared-autonomous-master-plan-20261011 at docs/HOME_GYM_PT_SHARED_AUTONOMOUS_MASTER_PLAN.md in anyangle1409-code/animation-software. Execute LANE W step by step from live GitHub and laptop checkpoints; keep working autonomously, verify and commit each task, skip blocked items, preserve GPT's independent LANE G, and resume from the latest checkpoint whenever this session restarts. Do not request routine input.`
