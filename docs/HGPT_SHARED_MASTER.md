# HOME GYM PT — SHARED MASTER EXECUTION FILE

**Created:** 11 October 2026 (UK)  
**Project:** Home Gym PT — complete anatomically grounded ORIGINAL human character + autonomous first-party exercise engine and app  
**Repository:** `anyangle1409-code/animation-software`  
**Coordination branch:** `codex/hgpt-shared-master`  
**This file:** `docs/HGPT_SHARED_MASTER.md`  
**Owners:** **WORK** = laptop/Blender/anatomy/original model; **GPT** = independent engine/runtime/app integration and audit.  
**Execution mode:** Do real, independently checked work in dependency order, save GitHub checkpoints, continue to the next executable task without ordinary status interruptions. **Do not claim that an inactive or usage-limited session can restart itself.**

> **START / RESUME RULE:** On every new session, read this file **from the LIVE coordination branch**, then fetch the LIVE relevant work branch/PR and its source ledgers. Use the latest verified commits, never older checkpoint SHAs as commands to reset a branch. Select the highest-priority genuinely unblocked task in **your lane**. Work through the whole plan in order, with bounded alternative tasks when evidence is unavailable. At each real achievement, commit source/tests/evidence in your own branch, verify actual outputs, append a brief checkpoint in **Section 10** of this file if feasible, and continue. Keep all existing owner-reviewed safety/approval gates closed unless their documented acceptance criteria are independently met.

## 1. Owner's non-negotiable objective

Deliver a self-contained **Home Gym PT** application capable of generating and rendering accurate, convincing, full-body exercises from commands. All human anatomy must behave naturally under unloaded and loaded motion, not only the five original demos. The finished product should contain **no third-party runtime dependencies or third-party exercise videos/3D characters**, and should not rely on an external animation service.

- The **approved anatomical skeleton is the source of truth**. The original mesh, muscle volumes, skin weights, and animation controls must follow it; **never move bones to rescue a defective mesh**.
- Use independent authoritative primary anatomy, real source geometry where legally permitted for research, measurable Blender and on-device evidence. Reference studies, research CT, Blender and development-only tools can be used to *develop* an original asset; external reference geometry is **not automatically licensed or accepted for shipping**.
- Preserve historical recovery/legacy V-series, production branches, frozen `a003`, `c001`–`c004` records and owner-approved policy. Do not create/promote `c005` or switch production runtime before the required gates are passed. Do not merge candidate evidence as accepted clinical anatomy.
- Maintain source subjects separately. Do not substitute female-reference CT for the target adult male character or mix different source acquisition coordinate grids, units, laterality or cohorts without defensible measured registration.
- Never invent unknown 3D positions, movement amplitudes, lumbar/thoracic angles, contact surfaces, patient-specific registration, rights, provenance, performance or passing results.
- **No force-push, no destructive checkout, no rebase of someone else's active history.** Use separate branches/worktrees. Read current remote heads before writes. All PRs stay DRAFT until genuinely ready and reviewed.
- Keep original private CT, labelled slices and medical images outside public GitHub; publish only permitted source citations, hashes and anonymised numeric diagnostics. Never commit patient/third-party model assets or secrets.
- Approval and security decisions requiring explicit owner/qualified reviewer input cannot be bypassed; record as `OWNER_OR_EXPERT_GATE` and move to a different independent task. Routine development should not require user check-ins.

## 2. Current verified baseline (11 October 2026; refresh every time)

**Anatomical programme:** `docs/COMPLETE_HUMAN_SKELETON_LIVE_TRACKER_20261007.md` on `codex/whole-body-biomechanics-audit-20261007`, phases **0–13**. Early **Phase gates 0–5 passed** as *inventories/reference/static comparison*, with the Phase-5 side-binding issue reopened. 206 conventional bones, 427 articulation/contact records, landmark/ROM source atlases and baseline/rig gap analysis have been recorded. Structural 206-bone Blender `HGPT_ANATOMICAL_MASTER` candidate, solver scaffolding and 135 isolated mechanical sweeps exist, but they are **not accepted human movement**. **Phases/gates 6–13 remain unpassed.**

**Authority:** `ORIGINAL_V1_WORK/anatomy/canonical_freeze_readiness_v1.json`; do not replace it with optimistic counts in this checklist. At latest verified Work checkpoint: **12 regions = 0 READY / 9 PARTIAL / 3 BLOCKED**, Phase 6 / CP1 Gate 6 **OPEN**, no production-approved corrected skeleton. Master Work branch `codex/source-skeleton-blender-measurements-20261010`, PR **#26**, last checked `b8fcb6470347044bfd3b749bfbc84a8989573260` (subject to change).

**Work source ledgers:** `docs/MASTER_AUTONOMOUS_HANDOFF_20261010.md`, `docs/MASTER_AUTONOMOUS_EXECUTION_20261010.json` and `docs/REGIONAL_ANATOMY_REMAINING_GATES_20261011.md` on the latest live Work branch. Important achieved checkpoints NOT to redo:
- Source identity/privacy and bounded pixel/label tests; source-pinned original male CT and two separately identified male pelvic CT acquisition groups; PR **#44** 82-frame private Blender CT viewer, five CI jobs verified.
- Female independent original CT **201 slices 1700–1900**, exact pixel/header/HU provenance checks, completed first source-visual review, verified 201-frame Blender viewer, 201-source HU>=500 intensity mask, **21 bounded 3D source-intensity slabs** saved/reopened. These are **not labelled bones or approved landmarks**.
- BoneHub 54 source surface files audited, carpal/tarsal 30 source files and 44 geometric candidate pair checks (PRs #34/#38/#39); neither medical physical millimetres/contact nor registered joint centres approved.
- Original 2011 C7–T12 *anterior/posterior body-height table* recovered and cross-checked (PR #40 and related #30). Heights DO NOT determine 3D endplate wedge angles. Some full standing-angle studies remain inaccessible; never fabricate tables or keep retrying a known denied URL unchanged.
- `a003`, `c001`–`c004` are experimental/frozen safety baselines, not proof of biomechanical readiness. Unproven runtime left/right chirality evidence in PRs #27/#29. Work PR **#45** Windows path-reproducibility follow-up still requires final exact-head verification before any green claim.
- Historical expanded full regression record: approximately **1,097 tests / 20 failures / 41 errors / 1 skip**. This is a *known inherited failure baseline*, not success. Classify real current failures rather than waste laptop usage repeatedly running full expensive battery.

**Independent first-party engine lane (GPT):**
- PR **#41:** dependency-free native WebGL2 63-bone live skeleton; actual Chromium exercise playback verified, original Three viewer preserved.
- PR **#42:** first-party native indexed triangles and reference 4-weight CPU linear-blend skinning; actual synthetic source body sleeve driven by real FK/IK; editor build verified.
- PR **#43:** strict limited glTF2 embedded GLB geometry/skin binary decoder, original deterministic synthetic fixture, real browser path; deliberately not general-purpose model import.
- PR **#46:** explicit immutable GLB source skin-name ↔ canonical rig mapping and inverse-rest-bind compatibility safety; **58/58** direct JS tests, browser GLB→skin→WebGL2 passed; synthetic triangle only, **not** ORIGINAL-v1 human character acceptance.
- Original *animation studio* still declares **`three`** behind `src/core/threeRuntimeBoundary.ts` for normal character/scene features. **DO NOT delete package yet**. `PT-App` separate repo `anyangle1409-code/PT-App` has a prior first-party zero-npm-dependency app branch `work/first-party-standalone-audit-20260930`; re-audit live before claiming release. The **304 legacy exercise clips are TEMPORARY**, replaced only after approved first-party generated alternatives are working. Source asset redistribution requirements remain to be cleared.

**Nontrivial distinction:** A `READY` item in Work's execution JSON means a *tooling subtask* is ready; it is **not** a `READY` anatomical region. The 12-region authority alone determines anatomical freeze readiness.

## 3. Division of labour: never duplicate the other lane

| Responsible lane | Owns implementation | Must not duplicate or change |
| --- | --- | --- |
| **WORK (laptop)** | Evidence-grounded anatomical closure, private CT/source 3D inspection, real Blender bone/rig model, physical landmarks, joint constraints, Phase 6–10 progression, original male mesh topology/weights and deformation candidates | GPT's stacked first-party runtime PRs #41/#42/#43/#46 or `PT-App` dependency refactor. Never alter GPT renderer/source branches without a deliberate integration gate. |
| **GPT (this chat)** | First-party renderer/data loader/hierarchy/mesh/skin/material/animation/runtime integration, PT-App compatibility contracts, source/provenance/bundle audit, independent tests, safe character handoff interface | Work's private CT, actual Blender source, anatomy ground-truth/canonical approvals, bones or original character mesh positions. May READ Work evidence and post PR handoffs only. |
| **OWNER / qualified reviewer (only when necessary)** | External licenses, publication/rights determinations, final anatomical or appearance acceptance that cannot be established by tests, security/account approvals, release/publishing authorisation | No agent silently assumes approval. |

**Communication:** Publish meaningful findings as PR descriptions, tests/artifacts and a concise comment on **Work PR #26** when relevant. Both lanes can read this ONE shared file. Never rely on this chat being visible on the laptop. Re-check live branches before starting any work.

## 4. WORK execution queue — actual critical path, in order

**W0 — Initialise safely on each session (do first, quickly).**
1. Fetch latest GitHub refs; read this file, Work handoff/execution JSON, 12-region authoritative readiness, last source-validation commits, PRs #26/#44/#45 and any newer Work/Claude branches. Preserve uncommitted local Blender work, source files and dirty worktrees. Do **not** reset a branch to the stale hashes printed here.
2. Check laptop Blender/Python actually accessible and private source locations exist. If missing, switch to source-independent tests/other tasks; do not fabricate native Blender execution.
3. Select one smallest consequential unblocker and define **before starting** the source evidence, output artifact, test command, acceptance check and rollback/safety scope.

**W1 — Close Phase 6 source geometry and physical registration (highest priority; parallel independent regions allowed).**
1. Resolve original source voxel→physical scanner coordinates, pixel-centre and handedness; for BoneHub male source, confirm matched image ↔ labelled 3D surface/units via source-authoritative data rather than guessing STL units. Keep two acquisition groups distinct. When inaccessible, record precisely what is missing and shift to a region with usable independent evidence.
2. Independently measure **actual multi-slice 3D identified bone surfaces and joint landmarks**, including seven pelvis landmarks, source-provenance + physical tolerance. Avoid promoting intensity-only component masks, crowd-labelled fragments or mean population bone heights into anatomical truth. Prefer bounded review of known private CT viewers over repeated full download/processing.
3. Close coupled **pelvis ↔ sacrum ↔ spine ↔ ribs ↔ SC/AC/scapula/GH shoulder** landmark and joint-frame compatibility. Spine requires real endplate planes / AP depth / standing segmental orientation context, not body-height differences as angles; ribcage requires real 3D head/tubercle/sternum/contact. Resolve thorax and scapular frames **together** where interdependent.
4. Complete **carpal** and **tarsal** envelope/contacts in an accepted common physical frame and verify actual source osseous morphology (not just lower/upper AABB or vertex-only proximity); then distal hand/foot/forearm, limb endpoints and remaining head/neck/humerus.
5. For each region update its evidence and exact acceptance gate **only when all source, geometry, comparison, tolerance and independent reviewer criteria are met**. Target a first independently defensible READY region; **do not optimize number of regions marked READY** by relaxing standards. Retain `0 READY / 9 PARTIAL / 3 BLOCKED` unless authority changes legitimately.

**W2 — Correct and verify real `HGPT_ANATOMICAL_MASTER` in Blender (Phase 7 completion).**
- After region targets pass, make *reversible source-identified* Blender bone/joint-frame changes on isolated candidate revision. Skeleton controls mesh, never vice versa. Preserve anatomical naming/chirality policy and 206/427 source coverage; quantify endpoints/symmetry/contact/pose and compare to independent native/source images.
- Produce truthful before/after native renders and machine-readable bone transforms with file hashes; verify save/reopen and actual Blender execution. Keep candidate unmerged until anatomical region/owner approvals and independent comparisons pass.
- Record blocked geometry explicitly; do not issue an imaginary final corrected skeleton.

**W3 — Finish solvers and isolated movements (Phases 8–9).**
- Coupled spine/rib/shoulder mechanics; radius/ulna/DRUJ and wrist/carpus; hip/SI/knee/patella; hindfoot/midfoot/forefoot; thumb/opposition, special followers/contacts. Preserve sourced axes/ROM vs *test-only amplitudes*. Use legitimate source-specific frames, symmetry/chirality, drift, collision, support/contact and multi-plane checks.
- Reuse existing 135 mechanical sweeps; add **missing mechanisms/tests** rather than rerun the same passing sweeps. Distinguish axis/centroid proxy crossing from surface clearance, and test envelopes from actual clinical ranges.
- Classify/fix relevant inherited failures with source-specific minimal regressions. Only report full suite green when rerun proves it.

**W4 — Natural whole-body motion (Phase 10, after W1–W3 acceptance).**
- Test the whole movement universe rather than hard-coded few: squat/lunge/hinge, press/reach/row/pull-up/push-up, curl/loaded carry and grips, hip/knee/ankle/feet, weighted/posture transition, bilateral and floor contact. Compare motion and soft tissue to independently sourced human photos/video when feasible.
- Check joint coupling, physiological ranges, load, momentum/eccentric/concentric effects, body proportions and collision. A basic visually moving rig or 78 unproven exercise peak angles is NOT movement realism acceptance.

**W5 — ORIGINAL-v1 male character mesh (Phase 12; coordinate with GPT at real interface gate).**
- Produce original anatomy-following full-body mesh, matching neutral rest inverse binds and weights, with independently checked chest/axilla/deltoid/scapula/hip/patella/hand/foot deformation across natural movement. Flag mesh intersection, crease, compression, stretching and lost volume.
- Export only **approved, owned** candidate topology and test evidence; provide explicit rig bone names/order, bind matrices, coordinate convention, units, mesh groups/vertex weights/material list and source rights manifest to GPT via PR. No premature asset handoff based on a synthetic tube.

**W6 — Integrate, sign off and optimise (Phases 11–13 when gates passed).**
- Work and GPT compare approved anatomical master→runtime controls and actual exported GLB skin to the native rig-binding test. Reduce runtime rig only if loss/error is measured acceptable. Test CPU/GPU/memory/FPS and exercise rendering on target phones, offline.
- Never announce final release or remove working fallback until evidence of feature-equivalent native renderer and first-party export passes.

**Work fallback queue if W1 primary CT/standing-angle evidence inaccessible:** classify Windows c001/c002/c003 path regressions (PR #45), right-side forearm skin/chirality tests with real source basis, independent accessible foot/shoulder/hip primary data, bounded first-party source-coordinate checks, targeted automated code tests, revised independent review packets. **A blocker is not an instruction to stop**; log it and choose another meaningful unblocked subtask.

## 5. GPT execution queue — parallel, hardware-independent where practical

**G0 — Check live status, protect ownership.** Read PR #26 and the latest regional blockers, plus native code PRs #41/#42/#43/#46. Read this shared file. Create a new **separate branch/stacked draft PR** per coherent engine capability, reuse genuine verified tests, never modify Work's anatomical branch or stored CT/Blender files.

**G1 — Make first-party model-loading/rendering viable beyond synthetic tests.** Extend restricted GLB loader with *well-scoped* real-world 3D features: glTF joint hierarchy/world-rest resolution and mesh-node transforms **with explicit coordinate handling**, multiple safe mesh primitives and indices/weights; source-owned normals, basic materials/UVs as justified. Keep conservative, tested failure when unsupported. Full real ORIGINAL-v1 cannot pass until Work provides approved source-owned export.

**G2 — First-party full character GPU skinning and visual pipeline.** Implement owned GPU joint-matrix palette and indexed triangles; normals/tangents, material/lighting, multiple mesh groups, memory/performance budgets; camera/orbit/input/picking/equipment. Add deterministic exercise-bone-pose and WebGL2 device failure/regression tests. Distinguish synthetic proxy success from accepted human-body deformation.

**G3 — Complete PT-App integration boundary.** Inspect live `anyangle1409-code/PT-App` first-party branch before edits. Define safe, versioned first-party exercise/asset API; wire a strictly opt-in integration spike so the real app remains functional. Verify offline start, no network/external services, original model entitlement, performance and release provenance. Retain 304 temporary third-party clips until approved replacement equivalence; quarantine/remove from future distribution and audit rights/history separately.

**G4 — Retire old third-party software ONLY after proven parity.** Replace the remaining Three-based scene/skin/texturing/render/input features, then delete `three` dependency and single import gateway, re-run exact no-vendor production dependency/source/bundle audit, dynamic browser tests, real character comparison and all app smoke tests. Never claim zero-third-party finished merely because a test page requests none.

**G5 — Stage finished deliverables.** Run true performance on actual target hardware if available, otherwise label untested. Offer source-backed acceptance packets to Work/owner, not unsupported clinical/visual claims.

**G fallback if model export unavailable:** make one of hierarchy/multimesh/material/GPU LBS/strict tests genuinely better. Avoid endlessly producing isolated synthetic proof branches with no path to full product. Save completion evidence and dependencies to a PR comment or this single shared file.

## 6. Overall phases and clear gate criteria

| Phase | State as of baseline | What makes it PASS (do not weaken) |
| --- | --- | --- |
| **0–5** safety, 206-bone/427-joint and ROM atlas, static gap comparison | **Passed as inventory/definitions** | Preserve; separate reopened rig laterality binding; never misread as physically validated skeleton |
| **6** character-specific anatomical proportion/position fitting | **MAIN BLOCKER; OPEN** | Accepted independent regional geometry/landmark/endplate/contact/source frame evidence and compatible full master target |
| **7** 206-bone anatomical master | **STRUCTURE only** | Independently verified source-compatible 3D placement and final master Blender candidate |
| **8** joint solvers | **PARTIAL** | Whole required articulation coupling/followers/contact in sourced frames with validated test coverage |
| **9** isolated movements | **PARTIAL** | All required joints, bilateral/multiplane, contact and measured envelopes verified; not only 135 mechanical sweeps |
| **10** natural full-body exercises | **BLOCKED** | Independently validated realistic whole-body movement families, pose/load/contact/transition gates |
| **11** runtime rig derivation | **NOT PASSED** | Explicit measured anatomical master→runtime rig parity |
| **12** original skin/muscle/mesh | **NOT PASSED** | Realistic approved ORIGINAL-v1 topology, weights and full-body deformation across broad movements |
| **13** app export/performance | **NOT PASSED** | First-party model/engine/app integration, third-party asset removal, offline/mobile performance and release audit |

The above phases have prerequisites, but **G1–G3 software prototypes may proceed without W1 acceptance** if they never promote unapproved anatomy or assets. **Do not invent a percentage complete or completion date.**

## 7. Twelve anatomical regions — Work gate queue

Source of authority: the live `canonical_freeze_readiness_v1.json`, supplemented by `docs/REGIONAL_ANATOMY_REMAINING_GATES_20261011.md`; this is an operational snapshot only.

| Region | Baseline | Still unresolved |
| --- | --- | --- |
| Shoulder girdle | PARTIAL | Clavicle/scapula endpoints; SC/AC/GH 3D centres, acromion/notch/C7, thorax coupling |
| Spine | PARTIAL | Per-level AP depth/endplate frames, standing angle distribution, disc envelope and coupled C2–S1 |
| Ribs | BLOCKED | True 3D centreline, rib head/tubercle/cartilage/sternal contacts and population compatibility |
| Forearm | PARTIAL | Radius/ulna endpoints, DRUJ/wrist/pronation axis and chirality |
| Carpus | BLOCKED | 8-bone source-registered common frame, carpal envelopes and actual contacts |
| Hand | PARTIAL | Carpal dependency, M2–M4, CMC/thumb, metacarpals and fingertips |
| Pelvis | PARTIAL | 7 verified bony landmarks, SI/pubis/sacrum, source-to-HGPT coordinates |
| Lower-limb long bones | PARTIAL | Femur/tibia/fibula endpoints, patella/trochlea joint contacts |
| Tarsus | BLOCKED | Common-frame subtalar/midfoot joints, physical surface/contact evidence |
| Forefoot/toes | PARTIAL | M3–M5/toe/stature and skeletal versus soft-tissue proportions |
| Head/neck fixed | PARTIAL | Skull/mandible, hyoid/C3 location/tilt with matched sources |
| Humerus | PARTIAL | GH→elbow JCS vs osteometric length and joint-surface alignment |

**Zero ready** is acceptable until truly verified; no premature optimism.

## 8. Definition of DONE for each task and no-intervention algorithm

Run this algorithm **within the active session**:
1. **DISCOVER:** fetch remote, inspect new Work/Claude/GPT commits and this file; check branch, permissions, unstaged changes, source path and exact tests. Treat GitHub PR statuses and local Blender processes as separate facts; GitHub activity does not prove a still-running agent.
2. **CHOOSE:** pick highest-priority unblocked task in your lane. If task requires an inaccessible source/license, laptop capability, owner or independent professional acceptance, log a precise missing prerequisite and select another independent task.
3. **EXECUTE:** implement actual code, run real Blender (WORK only when present), collect primary evidence, meaningful tests, reproduction and reversibility. No fabricated downloads, metrics or analyses.
4. **VERIFY:** run narrow numeric/invariant tests, adversarial input checks, real native app/render/browser test where feasible, save artifacts and hashes, avoid data leaks. Check CI for **exact latest commit**, not yesterday's head.
5. **CHECKPOINT:** publish source files/test results/PR link and brief exact outcome + remaining blocker. Do not replace authority or give unsupported `READY`. Record current SHA, reproducible command, pass/fail and next step.
6. **CONTINUE** to the next priority task. Do not stop just because an individual source, download, solver, CI, laptop tool or expert acceptance is blocked. Skip with evidence and choose another task.
7. **STOP only** at a session/tool/usage/permission/safety boundary, or if every safe available task is genuinely blocked. Leave a restartable GitHub state. A prompt cannot force automatic relaunch after ChatGPT Work usage reset, app closure or laptop sleep; use only a genuinely available supported scheduler/restart mechanism, never claim it exists by default.

**A milestone is complete only if:** changed real source or substantive evidence exists; GitHub commit/pull request points to it; its verified actual checks passed, with exact run IDs; source identity and data rights controlled; no regressions/agent conflicts; and a clear explicit statement of what remains **not** validated.

## 9. Git cooperation / one-file update protocol

- This is the **single coordination file** both agents use. It lives only in GitHub on **`codex/hgpt-shared-master`**, independent of Work's and GPT's implementation branches. It does not supersede original scientific source ledgers, canonical readiness or CI output.
- **To read without checking out/changing your working branch:**  
  `git fetch origin codex/hgpt-shared-master && git show origin/codex/hgpt-shared-master:docs/HGPT_SHARED_MASTER.md`  
  Or read the URL `https://github.com/anyangle1409-code/animation-software/blob/codex/hgpt-shared-master/docs/HGPT_SHARED_MASTER.md`.
- Work may maintain a **separate worktree** for coordination if desired. Never checkout this branch over dirty Blender/local source work, never force push, never overwrite other lane's checkpoint.
- Before editing this file: fetch its **fresh live head**, append only your own dated line under Section 10, **preserve** the other lane and earlier entries, commit/push safely using the current branch head (or GitHub contents API current blob SHA). On a conflict, **re-fetch and combine both contributions**, never use last-write-wins. Substantive scientific/tool code belongs in its respective PR, not in this document.
- Mark a task `COMPLETE` only when linked verified evidence exists. Mark `PARTIAL`, `BLOCKED_SOURCE`, `BLOCKED_EXPERT`, `BLOCKED_HARDWARE` or `WAITING_OTHER_LANE` candidly. **Do not alter Sections 1–8 to claim completed anatomy from a tooling checkpoint**.
- If write access to this shared branch is unavailable, leave a PR comment on the relevant lane PR with a link to this file. Continue work; inability to edit this coordination file is **not** permission to change the other agent's branches.
- Both Work and this chat should check the latest shared file before any new substantive task, so progress survives conversations, laptop restarts and session splits.

## 10. Shared verified checkpoint log (append-only; most recent at end)

**2026-10-11 09:52 UK | COORDINATION SETUP | Baseline verified.** Work PR #26 HEAD `b8fcb647`; Work 12-region count **0 READY / 9 PARTIAL / 3 BLOCKED**. Latest independent engine source PR #46 HEAD `2b28404d` with verified **58/58** tests and Chromium synthetic GLB→rig→skinning→native WebGL2 pipeline. Both lanes have substantial implementation, neither the fully accepted original human model nor the total Three.js removal is done. **WORK NEXT:** begin W0 then W1 region acceptance tasks, use existing CT/Blender evidence and classify inherited failures without repeating captures. **GPT NEXT:** begin G0/G1, prioritize real model hierarchy/multiple mesh geometry and GPU-scene parity without waiting for approved human assets. This log is not a clinical release or complete engine signoff.

**Checkpoint line template to append (no fictional pass):**  
`YYYY-MM-DD HH:MM UK | WORK/GPT | Task W#/G# | BRANCH SHA | outcome + exact tests/Actions URL | accepted evidence vs remaining blocker | NEXT`

## 11. One-line Work handoff / easy restart

**Type this into ChatGPT Work (with GitHub access):**

> Read **PR for `codex/hgpt-shared-master`**, file **`docs/HGPT_SHARED_MASTER.md`** in **`anyangle1409-code/animation-software`**. Follow the **WORK lane** autonomously, step by step; fetch live changes, preserve GPT's renderer lane, implement and verify real Blender/anatomy progress, checkpoint GitHub, skip documented blockers and keep doing the next safe task without asking me for routine decisions. Resume from the latest shared checkpoint whenever a new session starts.

If the shared GitHub PR/file cannot be accessed, report the blocker exactly; do not substitute an unrelated old master plan or invent local source files.

---

**Owner acceptance rule:** the aim is a *correct, realistic and first-party* system, not an artificially green tracker. Work until truly independently verified; preserve every source, branch and clinical decision that genuinely remains open.
