# HOME GYM PT — SHARED AUTONOMOUS MASTER PLAN
**Single shared instructions file for ChatGPT Work (laptop) and ChatGPT (independent GitHub development)**

**Version:** 1.1 · 11 October 2026 · **OWNER-UPDATED: exercise-realistic anatomical shapes + movement-first production track** · Authoritative execution plan, not a scientific measurement authority
**Canonical location:** `docs/HOME_GYM_PT_SHARED_AUTONOMOUS_MASTER_PLAN.md` on branch `codex/shared-autonomous-master-plan-20261011` in `anyangle1409-code/animation-software`.
**Project repositories:** `anyangle1409-code/animation-software` (anatomical master, original human body, animation engine); `anyangle1409-code/PT-App` (independent first-party app).
**Development rule:** This file coordinates execution. The separately audited primary scientific sources, machine-readable anatomy, freeze readiness JSON, tests and original scans remain the **evidence authorities**. If a status or checkpoint here is older than the live GitHub branch, fetch/reconcile the live evidence first; do not overwrite newer work.

> **Owner goal, reaffirmed 11 Oct 2026:** An entirely original male human character whose **proportions, joint mechanics, whole-body exercise movements and mesh deformations visibly and biomechanically match real humans**, including loaded exercises. Bones that materially affect human form and articulation must have **anatomically plausible curves, volumes and contacts**, especially the S-curved clavicle, moving 3D scapula and shoulder ball-and-socket, naturally curved spine/rib cage, pelvis, knee, forearm, hand and foot. Do not confuse straight *animation control rods* with physically straight *bones*. Avoid unnecessary CT-level detail on tiny bones where there is no material effect on movement, appearance or equipment interaction. Preserve a first-party app, renderer and creative character with no shipped third-party runtime, services or redistributed exercise clips. Blender and scientifically sourced reference material remain permitted development tools subject to rights.

---

## OWNER DECISION — 11 OCT 2026: FUNCTION-FIRST, SHAPED BONES, NO ARTIFICIAL RESEARCH BOTTLENECK

**This section supersedes the original W1→W5 production-task order and the assumption that every one of the 206 source bone surfaces / all 12 clinical freeze regions must be individually certified before Work can build and visually test a human.** It does **not** retroactively pass legacy Gates 6–13, approve a003/c001–c004/c005, reject useful scientific research, or permit unsourced anatomy to be called verified.

- **One anatomical truth; two representations:** (A) **anatomical shape layer**, made from project-authored, source-informed curved/volumetric bone guides and visible shape constraints at relevant joints, and (B) **kinematic/control rig**, which may use straight rods and fewer controls for efficient motion. Both must agree on joint centres, reference frame, segment lengths, axes, tracking and left/right identity. Do **not** physically bend rig controls merely to imitate bone curvature; do not force original skin to dictate skeleton positions.
- **Shoulder is a mandatory early pilot:** model a plausible *S-curved clavicle centreline and envelope*, a broad, thorax-conforming triangular scapula with glenoid/acromion/coracoid reference regions, distinct SC/AC/GH centres, humeral head and space for clavicle/scapulothoracic motion. Build a neutral and progressive overhead-elevation **with whole scapulohumeral coordination**, then test mesh deltoid/axilla/chest shapes. A curved clavicle by itself does NOT give correct motion or mesh deformation. The preserved c004 straight display rods are not curved clavicles or anatomical surfaces.
- **Whole-body shape priorities:** realistic vertebral/rib cage curvature, pelvis/hip sockets, forearm radius-ulna rotation, knee/patella tracking, ankle/foot articulation and hand/digit/grip envelopes. Detail each to the extent it materially changes silhouette, contact, joint mechanics or deformation; do not spend sessions modelling invisible micro-contours of every skull/carpal/tarsal bone.
- **Move the real Blender mesh/rig prototype forward NOW:** Work may build a new explicitly **PROVISIONAL FUNCTIONAL CANDIDATE** on a **separate** branch/.blend from accepted historical records, using defensible existing anchors and bounded assumptions marked with confidence. Prototype neutral/compound/overhead movements and full-body skinning **before** comprehensive source-surface registration is finished. It is not the accepted canonical skeleton or release character. Record assumptions, known defects, visual findings and tests; do not mutate the frozen a003, c001–c004, legacy V models, r95 original body or scientific ledgers.
- **Evidence threshold proportional to risk:** source-check essential posture/joint centres, coupling, loaded joint limits, contact and realistic movement; independently compare captured representative poses against real anatomical photos/video and suitable scientific motion evidence. Keep deeper CT, source-patient 3D registration, all-206 surfaces and specialist review **only** where required for a consequential ambiguity/defect or any stronger anatomical/clinical claim. Open research gate remains visibly open and must NOT be labeled PASSED.
- **Do not claim perfection from finite tests:** thousands of future text-described exercises cannot be exhaustively certified. Cover a broad human-motion basis (overhead/reach, press/pull, hinge, squat/lunge, push-up/plank, hang/grip, twist, locomotion/stance) across full time trajectories and plausible load/ground/equipment variations; enforce joint/continuity/collision/contact invariants plus reference-pose comparisons, and flag unsupported movements rather than animate unrealistically.
- **Work owns geometry/Blender/motion/mesh**, GPT owns GLB/WebGL/native engine/app (no duplicate source research). At each bounded milestone publish portable **front/side/rear/three-quarter/overhead PNG or video visual proof** (unless restricted; then private and clearly note inaccessible), concise objective test results, and a branch SHA. Share high-level original GLB rig metadata to GPT ASAP, without sharing private CT bytes.
- **Priority against wasted usage:** 1) existing useful geometry, sources and QA, 2) shoulder/high-impact skeleton candidate, 3) actual first human mesh+rig deformation, 4) broad functional exercises, 5) targeted failure-driven research. NO repeated 201/82-slice imports, 21-slab studies, 54 surface acquisitions, 135 old sweeps or hundreds of cosmetic micro-checks with no new evidence.

**Release interpretation:** the app must have convincing anatomically informed movement and deformation; it is not a clinical skeleton product. The **historical 0 READY / 9 PARTIAL / 3 BLOCKED regional-source-freeze status stays true** until independently updated. New functional build/review gates below are *separate* from those original scientific acceptance labels.

---

## 0. ALWAYS-ON STARTUP / RESTART PROCEDURE — RUN FIRST ON EVERY INVOCATION

1. Fetch LIVE GitHub heads and PR/CI activity before any edit, especially Work's [PR #26](https://github.com/anyangle1409-code/animation-software/pull/26), independent engine [PRs #41](https://github.com/anyangle1409-code/animation-software/pull/41), [#42](https://github.com/anyangle1409-code/animation-software/pull/42), [#43](https://github.com/anyangle1409-code/animation-software/pull/43), [#46](https://github.com/anyangle1409-code/animation-software/pull/46), Work CT [#44](https://github.com/anyangle1409-code/animation-software/pull/44), Work Windows [#45](https://github.com/anyangle1409-code/animation-software/pull/45), Claude's active skeleton branches, and recently committed documentation. Do not assume branch heads or earlier checklists are current.
2. Read THIS ENTIRE FILE **starting with the OWNER DECISION above** plus, for anatomy, `docs/COMPLETE_HUMAN_SKELETON_LIVE_TRACKER_20261007.md`, `docs/REGIONAL_ANATOMY_REMAINING_GATES_20261011.md`, `docs/MASTER_AUTONOMOUS_HANDOFF_20261010.md`, `docs/MASTER_AUTONOMOUS_EXECUTION_20261010.json`, and `ORIGINAL_V1_WORK/anatomy/canonical_freeze_readiness_v1.json` from their latest relevant branches. Do not treat a file missing from the current checkout as nonexistent; check the authoritative branch.
3. Check local Git status, uncommitted files, active Blender processes, downloaded **private** reference assets, CPU/memory/disk space and existing generated artifacts before starting expensive operations. Keep source images/CT and sensitive subject records outside public Git. Never silently discard another agent's uncommitted work.
4. Reconcile exact checkpoint SHAs, PRs and test outcomes. An earlier passing CI run does not prove a newer head is green. For a red test, classify **pre-existing versus caused by the current change**. Use targeted tests and a bounded failure reproducer before any full suite rerun.
5. Choose the **highest-priority executable** item from the assigned lane below for which required evidence and tooling exist. Complete one bounded subtask with a measurable test/artifact, then continue to the next subtask **without requesting routine user approval**.
6. Each completed subtask must leave a durable Git checkpoint: branch, commit SHA, changed paths, commands, relevant CI run/results, source IDs and hashes when applicable, PASS/FAIL/SKIP plus exact unresolved limitations. If unable to push from a laptop, save a clearly named local commit/log and resume publishing at next available session. Never say a task is complete when only scripts or documentation were written but required real execution did not occur.
7. When a source is inaccessible, evidence is inadequate, CI is blocked, laptop hardware is unavailable, or quota is exhausted: log the exact blocker; **do not invent data or repeat identical failed requests**. Switch to the next independent unblocked item. Stop only when no safe/executable item remains, resources/tools are genuinely unavailable, or the current session ends.
8. When invoked again after any quota reset, repeat steps 1–7, recover current live heads and continue from the latest actual checkpoint. **A prompt cannot independently restart a stopped ChatGPT Work or Claude session, wake the laptop, bypass quota, or promise overnight background operation.** Use platform-supported persistent automation only if actually enabled; never claim it is.

### Safety and collaboration invariants

- The **anatomically informed skeleton is the authority**, not the old mesh. Use defensible source joints and plausible bone shapes as the working production basis; independently label provisional geometry and retain historical scientific freeze requirements separately. Skin, muscles, corrective deformations and runtime rig follow joint/shape targets, not vice versa. Do not warp the skeleton to fit an old mesh or synthetic cylinder.
- Preserve frozen **a003** baseline, noncanonical **c001–c004** candidates and audited historical outputs. **c005 is NOT accepted**. Never convert provisional measurements/threshold voxels, foreign-cohort averages or scripted synthetic models into approved anatomical geometry.
- No force push, history rewrite, destructive rebase or overwrite of another agent's branch. Use independent worktree and **separate topic branch/draft PR** for substantial changes. Do not merge to main, rewrite accepted owner decisions or change legacy V-series while in this programme.
- GitHub is the handoff mechanism: actual commits + linked targeted CI + compact status comment on Work PR #26 or current agreed coordination PR. Never rely on an invisible chat transcript.
- Source rig/body may have a left/right naming reversal. Preserve PR #27/#29 chirality evidence; do not infer anatomical left from `*_l`, Blender axis labels or bare source filenames. Explicitly verify frame, coordinates and handedness.
- External scientific evidence/source 3D scans are **development evidence, not automatically approved proprietary output assets**. Track licensing, redistribution rights, origin and isolation. **First-party** assertions must distinguish production app code, isolated renderer subsets, still-vendored studio, original body geometry, and temporary clips.
- Where claiming clinically/medically accurate anatomy or adopting medical source geometry, retain the original qualified-source/independent-review gate. **Functional provisional prototypes do not require all-206 clinical surface approval before being visually tested.** Passing unit tests or making a Blender render is not proof of movement/mesh realism.
- Escalate to the owner only for a genuinely unavoidable policy/medical rights decision, proprietary release approval, a destructive change, or an unresolvable conflict requiring a choice. Otherwise make **reversible, conservative progress** and leave blockers explicit.

---

## 1. LIVE BASELINE — SNAPSHOT VERIFIED 11 OCTOBER 2026 (RECHECK WHEN USED)

| Area | Confirmed starting point | Acceptance boundary |
| --- | --- | --- |
| Master tracker | **Phases 0–5 gates PASS**: 206 conventional adult bones; 427 joint/contact entities; 30 semantic frame definitions; 44 mechanics profiles. Phase 5 runtime naming/chirality interpretation has reopened detail. | These are inventories/reference atlases, **not** validated body geometry |
| Phase 6 | **CP1 / historical anatomical Gate 6 OPEN**, a003 audited comparison baseline; no accepted corrected master target. | Blocker for *clinical-source freeze*, **NOT** for separately labeled working mesh/rig prototype |
| Regional research freeze | **0 READY / 9 PARTIAL / 3 BLOCKED** across 12 regions. | Status belongs to detailed scientific source acceptance, NOT a measure of functional prototype progress |
| Phase 7 | Structural anatomical master exists: 206 bones, 427 joint markers, 51 landmarks. | Structure verified only; bone positioning NOT passed |
| Phases 8–9 | Solver core and **135** isolated diagnostic sweeps exist, with known gaps and physiology/provenance caveats. | Gates 8/9 NOT passed |
| Phases 10–13 | Natural whole-body functional motion, derived runtime rig, physiological mesh deformations, app export/performance. | Gates 10–13 NOT passed |
| Current Work lane | `codex/source-skeleton-blender-measurements-20261010`, PR #26; snapshot head `b8fcb6470347044bfd3b749bfbc84a8989573260` (DO NOT treat as immutable live head). | Work may update after this file was written |
| Completed source processing | Female separate-subject **201** original CT slices first-reviewed and calibrated, corresponding native Blender timeline plus **21** bounded intensity slabs; male/pelvis **82** source frames with two acquisition groups and native viewer; BoneHub 54 source surfaces, 30 wrist/foot meshes and 44 candidate proximity pairs; 2011 C7–T12 posterior/anterior vertebral heights. | Not source-registered human landmarks, accepted bone surfaces or corrected canonical targets. **Do not repeat these acquisition/review loops** |
| Full regression | Work records inherited expanded baseline **1,097 tests / 20 failures / 41 errors / 1 skip**; root-cause classification needed. | Do not claim all-green based on passing targeted CI |
| First-party app | PT-App's audited branch has **zero npm runtime and development dependencies**; temporary **304 third-party exercise video clips** intentionally remain until replacements are proven. | No customer-ready original animation package |
| First-party rendering | Isolated original WebGL2 skeletal GPU PR #41; indexed triangle/four-weight CPU LBS PR #42; strict restricted GLB importer PR #43; explicit GLB-to-rig numerical bind check PR #46. Browser/Node proofs verified on *synthetic meshes*, not original human. | Regular animation studio still depends on **Three.js** through one gateway; not removed |
| Original body | `HomeGymPT_Male_ORIGINAL_v1`, planned `hgpt_canonical_v4_original`. Provisional r95 character and 206-control c004 skeletal *diagnostics* exist. | No accepted first-party full-body shape, motion and skin deformation approvals; work may now test a separate provisional prototype |
| Latest Lane G verified prototypes | G1d source normals PR #57 and G2c native GPU normal/position parity PR #58, real Chromium 132/132 Node tests and 3/3 CI jobs at tested implementation head. | Synthetic source meshes, not the human model, PBR materials, mobile device or full studio Three.js removal |

**Evidence cross-check:** Region checklist `docs/REGIONAL_ANATOMY_REMAINING_GATES_20261011.md` (on Work source branch); owner skeleton-first decision `docs/SKELETON_FIRST_PRODUCTION_POLICY_20261008.md`; Work PR #26; original master tracker. Source status is deliberately not a percentage-complete estimate.

---

## 2. ASSIGNMENT / OWNERSHIP — PREVENT DUPLICATE WORK

### LANE W — ChatGPT Work on laptop (PRIMARY CRITICAL PATH; owns Blender and human anatomy)

Work owns **anatomically plausible curved bone-shape references, an efficient source-grounded animation rig, real Blender human mesh/weights/correctives, joint centres/axes/coupling, full-body natural motion and visual functional testing**. Complete historical CT-to-HGPT registration **only when it changes major geometry/mechanics or for stronger medical claims**; retain its unresolved clinical research track. Claude, if active, may work only on separate explicitly coordinated anatomical subtasks and must publish independent evidence, never silently rewrite Work's accepted baseline.

Work must **NOT** duplicate GPT's first-party WebGL renderer/GLB binary parsing work from PRs 41/42/43/46. Work may consume their interfaces only after acceptance and may offer integration requirements via PR comments.

### LANE G — ChatGPT in this chat / independent GitHub session (owns FIRST-PARTY SOFTWARE)

Own original native renderer and application integration readiness independent of still-unapproved anatomical geometry. Continue from verified independent PRs 41→42→43→46→49→51→53→55→57→58 and newest HEAD, on **independent new branches/draft PRs**. Use original procedural synthetic meshes and clearly identified mock fixtures until provenance/mesh/rig exports are validated. Own dependency inventory, first-party material/normal/UV/texture primitives, multi-mesh data loading, multi-bone palette/performance/robustness, native camera/scene inputs, automated app-interface adapter, offline checks, and device/browser test contracts.

Lane G must **NOT** edit Work's CT source, canonical bone geometry, Blender worktree, frozen scientific figures, movement amplitudes or human-model mesh candidates; never claim a synthetic tube/test triangle looks human.

### Coordination handshake

- **Work consumes:** stable types and acceptance reports from independently verified renderer PRs, not arbitrary WIP code. Work supplies *metadata only, as soon as the provisional rig schema exists*, including model bone-name mapping, pose/rest transforms, inverse-bind conventions, mesh count/vertex attributes, neutral posture, source frame, provisional-vs-accepted status and rights/approval evidence (not confidential CT/medical bytes).
- **GPT consumes:** declared *provisional* rig/schema facts for nonrelease compatibility tests, and *approved* IDs only for final character certification; extend the first-party loader/rendering tests to meet actual model **without moving bone centres**. Never mistake early schema compatibility for anatomical approval.
- Each lane posts a brief checkpoint on Work PR #26 (or newer central PR when Work moves): `LANE, task ID, input HEAD, output branch/commit, tests/CI, source scope, decisions, blockers, next task`.
- The **single runbook file on coordination PR #48** is the shared authority. Owner-authorized coordinator updates may amend that branch with exact current file/blob SHA after checking live head; implementation or anatomy agents must not edit this file concurrently. Post milestone checkpoints on the workstream PR, propose other plan changes separately, and read owner decision before relying on any older phase list.

---

## 3. LANE W EXECUTION QUEUE — REAL HUMAN SHAPE + MOTION FIRST

**W0 — Live sync and preserve (every active session).** Verify Work/Claude/coordination PR heads, local .blend/private-source availability and uncommitted changes; preserve all historical a003, c001–c004, c005-unaccepted, old r95 and legacy V data. Inspect existing 206 controls, 427 markers, 135 diagnostic motion sweeps and existing 201 CT / 82 CT / BoneHub source evidence **without rerunning finished audits**. Classify relevant existing failures rather than rerun the whole 1,097-test suite. Record exact SHAs and scope.

**W1 — Define a practical *functional anatomical shape and rig target*, immediately.**
- Keep detailed 206-bone atlas as **reference only**; use a lean explicit animation/control hierarchy where sufficient for visible, natural human motion, with traceable anatomical IDs, correctly mapped laterality and joint centres. Distinguish curved 3D *bone volumes* from straight control sticks.
- Use source-informed adult male proportions; verify total height, shoulder width, arm/forearm/hand chain, realistic foot length, bilateral stance, thorax/pelvis spatial alignment. Preserve c004's known spine disc, rib, clavicle and upper-limb defects in the defect ledger.
- **First pilot: shoulder girdle and upper torso** — S-shaped clavicle with appropriate anterior/posterior bend, scapula as broad thorax-facing blade, distinct SC/AC/GH centres and glenoid orientation, humeral head/neck placement, sternum and ribcage guides. Keep curvature **shape-layer separate** from kinematic controls. Test coupled clavicle elevation/retraction/rotation, scapular upward rotation/tilt and glenohumeral motion in actual Blender through progressive overhead reach. No guessed universal 2:1 scapular rhythm or invented medically exact surface.
- Also represent curved spine/ribs, pelvis/hip, forearm twist, knee/patella, ankle/foot and hand/grip geometry at movement-relevant fidelity. The original authored human geometry must not derive from redistributed scan meshes.
- **Evidence:** source/assumption/confidence table for each *functional* high-impact joint; front, side, rear and three-quarter overview plus shoulder close-up in neutral and 0/45/90/full overhead stages. Keep a list of consequential unresolved areas; do not call provisional data approved.

**W2 — Build the first *fully visible* anatomical skeleton + human mesh prototype NOW (in parallel with targeted W1 research).**
- Create a **new reversible PROVISIONAL_FUNCTIONAL_v1 .blend** and independent work branch, **not** an overwrite of old/a003/c004/r95 source or production body. Use shape guides for bony features plus a compact logical control rig. Keep coherent rig-to-shape transformations in rest and pose; prove side mappings, joint continuity and representative segment lengths.
- Fit an original authored male mesh **around the plausible skeleton**. Add anatomical shoulder/chest/armpit, spine/torso/pelvis and limb/hand/feet bulk; seed deform weights and correctives early. A source-derived CT reconstruction is not the production mesh. Preserve all original-rig assets and rights metadata separately.
- Publish phone-viewable **actual Blender screenshots** (front/side/back/3/4 plus detailed shoulder neutral/overhead) through a safe GitHub PR artifact/path if allowable, retaining restricted files privately. Every image must identify candidate version and known defects. Do not present a concept-art image, flat-line proxy or synthetic tube as the final body.
- Target usable **shape + controls + skin** before spending further time on tiny internal bone articular micro-shapes. At each failure choose a targeted anatomy/biomechanics check rather than indefinite full clinical atlas intake.

**W3 — Verify human movement comprehensively, not only five preauthored examples.**
- Build a reusable exercise *movement test matrix* spanning overhead press/reach/throw-like rotation; press/push-up; pull/row/hang/pull-up; squat/lunge; hip hinge/deadlift; single-leg/stance; spine flex/extend/rotation; forearm pronation/supination; grip/finger/thumb; calf/ankle/foot-toe/locomotion. Include unilateral and bilateral, cross-body, loaded vs unloaded and appropriate floor/equipment contact.
- Compare **actual whole-frame sequences** at neutral, early, mid, peak and return against real human reference photos/videos and accessible research: segment/joint location, scapulohumeral coupling, trunk stabilisation, pelvis/hip, knee/patella, forearm/wrist, gripping, balance/foot support. Check source-defined active/passive limits in context; do not claim numerical dynamics without external force/torque evidence. Retain 78 previously unsupported peak-angle values as unapproved.
- Use numerical joint-trajectory, nonpenetration, equipment/floor locking, temporal continuity, mirrored laterality, ROM and repeatability tests **plus** independent view-by-view visual assessment. Record every objection as a concrete reproducible regression with the expected human reference. Do not claim unrestricted exercise correctness from a small fixture set.

**W4 — Fix realistic soft-tissue deformation at all moving joints, especially shoulders.**
- Validate the **actual body mesh** on overhead, shoulder press, pull-up, push-up, flexed elbow, grip, squat, hip hinge, deep knee, ankle/toe and twisting frames. Correct clavicle/deltoid/pec/axilla transitions, scapula sliding, arm/forearm twist volume, ribcage, abdominal and hip mass, knees/patella, hand/thumb, calf and foot; shorts/cloth when applicable.
- Use verified weighting, joint-volume preservation, corrective shapes and motion-dependent soft-tissue controls as appropriate; no popping/collapsing/spiking/severe intersections or implausible silhouettes. Bone curvature **alone** never substitutes for deformation correctives. Check side-by-side measured screenshots/video and independent reference comparison from at least front, side, rear, overhead.
- Advance to higher-resolution character only when the existing functional low/medium-res candidate behaves credibly over a broad motion basis. Keep exact defect/test artifact links to avoid repeating previously reviewed poses.

**W5 — Convert verified prototype into original production model + rig metadata.** Refine model proportions, source-safe bone shape guides, weights, UVs, normals, materials, correctives and bone naming. Where a material anatomical uncertainty affects joint centres, clearance or deformation, use targeted source research/CT/qualified review to resolve it. Freeze only the **functionally validated production rig and authored model** with explicit limitations; separately leave scientific 206-bone gates open unless independently closed. Export rights-cleared original GLB with model/rig SHA, control↔bone map, bind/rest space, mesh/skin/normal/UV/material metadata and test pose set to Lane G. Do NOT silently promote c005 or claim medically verified 206 surfaces.

**W6 — Joint end-to-end tests with GPT / PT-App.** Integrate accepted original GLB into the independent native WebGL2 animation engine using Lane G's agreed schema. Exercise text→first-party solver→real full-body motion→mesh/skin→mobile renderer without network dependency. Test offline and actual device frame-rate/memory, meaningful representative exercise coverage, user-facing app UX, and replacement of all 304 temporary third-party clips **only after** originals are shown to work. Hold shipped distribution to strict rights/dependency tests.

**W7 — Concise, evidence-linked finish report.** Report functional gates and exact original scientific gate statuses separately. Include real Blender and mobile clips, unresolved movement/deformation cases, sources for consequential joints, coverage matrix, PR SHAs and CI. No false claim of thousands of exercises tested or of formal clinical validation.

**Blocking rule:** Detailed 12-region/206-bone CT surface registration and complete joint cartilage reconstruction remain research tasks **only** and must not prevent W2/W3 iterative mesh-and-motion testing. Conversely, do not ignore a demonstrable abnormal joint position, shoulder clearance failure, unsafe loaded ROM, rig side inversion or severe mesh defect simply to go faster. Every provisional decision is reversible and auditable.

---

## 4. LANE G EXECUTION QUEUE — PARALLEL, FIRST-PARTY RUNTIME

**G0** Sync LIVE PRs 41–58 and later software successors plus original animation-studio vendor inventory; check exact HEAD and actual CI, note Work's first provisional **functional rig schema** as soon as available, and keep synthetic vs real-human evidence distinctly labeled. Read the owner decision above, not any obsolete W1 blockade.

**G1 — Native mesh feature parity** Add truly first-party **multi-primitive and multi-mesh** bounded geometry data representations, canonical node/skin hierarchy support (without invented transforms), source-owned material/normal/UV attributes and safe CPU/GPU buffers/shaders. Incrementally extend strict GLB importer; every new supported feature must have positive real-WebGL and adversarial negative tests. Preserve existing reject-unknown and memory bounds. Do not weaken security checks to make arbitrary GLBs load.

**G2 — Efficient project-owned skinning** Retain CI-verified four-weight GPU palette position parity (#55) and source NORMAL/normal-shader parity (#57/#58); next implement appropriate material/texture/normal/skin deformation features, larger indexed meshes and hierarchical palette mapping on source-owned test fixtures. As soon as W2 publishes the *provisional* human rig/GLB metadata, test loader/bind/skin compatibility under **PROTOTYPE ONLY** status without waiting for full CT freeze. Do not claim finished human deformation from synthetic triangles.

**G3 — Studio/runtime independence** Replace remaining Three-backed scene, camera/orbit interaction, picking, equipment, animation rendering, shading/lighting/shadow/material and lifecycle on reversible feature switches with browser screenshots and parity tests. Preserve existing production character viewer until all functions work. Defer uninstalling `three` and setting the guard threshold to zero until the full editor tests and actual accepted human-character parity pass.

**G4 — App/engine integration contract** Define a zero-network first-party interface `exercise text → validated exercise specification/constraints → pose frames → skinned scene → animation output` with model-hash/rig-map schema, offline fallbacks, cancellation/resource limits and equipment interactions. Run synthetic tests now, **then load Work's clearly marked W2 provisional real-human GLB to discover integration defects early**; reserve release/pass claims for W5 accepted original character and W6 end-to-end phone tests. Preserve PT-App's zero-npm shell.

**G5 — Release dependency clearance** Inventory npm/vendor runtime, build-time-only tooling, embedded external media, generated licenses/provenance; test offline/browser/mobile packaging with explicit definitions. Once W5/W6 parity is verified, replace/remove remaining vendor gateway, temporary animations, packaged external assets, reject third-party dynamic requests and verify full standalone release. Git history rights review separate from installed bundle; do not rewrite shared Git history casually.

**G6 — Acceptance notes** Post each verified incremental PR and CI/test/synthetic-only boundary on Work PR #26 (or current central PR). Coordinate actual ORIGINAL-v1 asset schema without asking Work to redo finished renderer research or move bones for skinning.

---

## 5. SHARED ACCEPTANCE — NEW PRODUCTION GATES VS UNCHANGED SCIENTIFIC GATES

**Do not conflate these two trackers.** The 2026-10-07 detailed research phases 0–13, Phase-6 CP1 and twelve-region source-freeze status remain historical scientific acceptance checks. In particular **0 READY / 9 PARTIAL / 3 BLOCKED remains unchanged** at this plan edit; provisional functional work does not change its labels or approve c004/c005. The new practical product build gates below allow actual character development and failure-finding to start sooner.

| New functional gate | Evidence required |
| --- | --- |
| **F0 — Anatomical structure and proportions, provisional** | Recorded adult stature/proportions, major joint positions/axes, correct left/right and kinematic connectivity; credible source-led S-curved clavicle and 3D scapula shape guides, trunk/spine, pelvis, limbs, hand/foot; neutral multi-view Blender candidate with known-defect list |
| **F1 — First shaped skeleton + original visible skin prototype** | New unmerged/isolated Blender candidate with source-aware bone shape layer, working compact control rig, original body mesh/weights, neutral + incremental arm-up visual evidence and exported provisional rig/GLB schema; explicitly not medically or production approved |
| **F2 — Motion biomechanics** | Independent video/photo/biomechanics comparisons of start/mid/peak/return trajectory across all major movement families, plausibly loaded variants, joint coupling, symmetry, contact, collision, ROM/continuity; issues recorded and major defects fixed; unsupported moves fail safely |
| **F3 — Full-body mesh deformation** | Real mesh with shoulder/scapula/clavicle/axilla, spine/rib/torso, forearm/hand/grip, pelvis/hip, knee/patella, ankle/foot corrections shown in actual Blender reference-aligned renders/videos; no gross deformation artifacts in covered motion basis |
| **F4 — Original GLB ↔ first-party runtime parity** | Actual original authored rig/skin/model exports pass strict loader/binding/skinning/material and offline exercise playback parity; quantified rendering or numerical comparisons and source/rights manifest; synthetic-only CI is inadequate |
| **F5 — App/device release** | App Store target device/browser tests, performance/battery/memory, original exercise clip replacement, full offline runtime, no prohibited third-party shipped runtime/services/assets and release regression acceptance |

**Separately**: historical research **Gate 6/7** still means independently reviewed source-specific anatomy/206-427 coordinates, **Gates 8/9** deep coupled atlas dynamics, **Gate 10** research-grade functional comparisons, **Gates 11/12** model proof, **Gate 13** shipped integration. They may advance later on their actual evidence but are **not prerequisites** to beginning W2 provisional prototyping. Nor does completing F0/F1 by itself prove real human movement (F2) or deformation (F3).

**Task states:** `NOT_STARTED`, `ACTIVE`, `PARTIAL`, `BLOCKED_EVIDENCE`, `BLOCKED_TOOLING`, `VERIFIED_PROTOTYPE`, `READY_FOR_REVIEW`, `ACCEPTED_FUNCTIONAL` (with actual evidence), `APPROVED_RESEARCH` (original research authority only), `DONE`. Never promote provisional movement or synthetic GPU numbers to research approval.

### Time / usage efficiency — mandatory

1. **No repeat research runs** for already verified CT 201/82, 21 slabs, BoneHub 54 source surfaces/44 pairs, historical 135 diagnostics, failed paywall queries or large suites unless a *specific new consequential defect* makes it necessary.
2. **Prefer a real Blender visible result and documented motion/deformation correction over one more theoretical report.** Choose high-impact motion/geometric problems ahead of low-impact tiny bone-detail geometry.
3. Before every new task, read latest Work/GPT CI and file hashes; preserve separate branches and build on already verified code. Reuse tests/artifacts; change only the assigned lane. Stop repeated unsuccessful tool calls and switch to a different unblocked subtask.
4. Validate in layers: cheap specific unit checks → actual Blender/browser functional visual comparison → full integration/regression suite **at meaningful milestones**. Don't burn usage rerunning unchanged red suites.
5. Each checkpoint: 3–8 concise lines with task ID, exact SHA, actual evidence/CI, limitations, next step. Supply phone-viewable safe images or hosted GitHub Actions artifacts whenever possible, not only local file paths.
6. Work must not replicate Chat's first-party WebGL/GLB tasks; Chat must not refit Work's skeleton, CT or original human. Share metadata/contracts and solve integration problems from each side.

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

`Read v1.1 of docs/HOME_GYM_PT_SHARED_AUTONOMOUS_MASTER_PLAN.md on branch codex/shared-autonomous-master-plan-20261011 in anyangle1409-code/animation-software. Follow the 11 Oct owner decision: LANE W now prioritises anatomically shaped shoulder/full-body skeleton, original human mesh and realistic movement/deformation prototypes; historical 206-bone CT freeze remains separate. Fetch latest Work/GPT heads, preserve all old candidates, work continuously through W0–W7 with real Blender tests/screenshots, commit and report each genuine milestone, and do not duplicate GPT's renderer/software lane or request routine input.`
