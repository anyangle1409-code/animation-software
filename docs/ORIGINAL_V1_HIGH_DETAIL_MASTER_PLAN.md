# ORIGINAL v1 high-detail master production plan

This is the single authoritative high-level model roadmap for
`HomeGymPT_Male_ORIGINAL_v1`, rig `hgpt_canonical_v4_original`, on
`claude/original-v1-blender-o2-20260929`. It does not replace executable gates.
Read this plan, `ORIGINAL_V1_HIGH_DETAIL_STATUS.json`, the generated daily status,
and `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md` at every pickup. The runtime
migration is a separate branch/track; never merge this model branch wholesale.

## Shared language and authority

PHASE is a numbered roadmap section. CANDIDATE is a named experimental revision.
BASELINE is the pinned R2 comparison state, never automatically replaced.
EXPERIMENTAL does not mean accepted. DEVELOPMENT CLEAR means the relevant coarse
gates pass; it does not mean production-approved. OWNER REVIEW is a visual
checkpoint; OWNER ACCEPTED and OWNER REJECTED require an explicit owner record
bound to a candidate SHA. PRODUCTION APPROVED is reserved for Phase 12.
REGRESSION is any material worsening beyond the committed comparison tolerances;
STRICT IMPROVEMENT requires improvement without material predecessor regressions.
TRADE-OFF preserves improvements and regressions separately. REVIEW SNAPSHOT is
non-blocking by default. FREEZE protects structure from casual changes.

Priority: live source/executable evidence, current model handoff, this roadmap,
generated status/ledger, task packages, historical documentation. The old
`ORIGINAL_V1_CANDIDATE_STATUS.json` verifies the R2/export checkpoint, not latest
r29 deformation; it remains intact for its existing verifier. O1/O2/O4/O7 are
historical authoring stage labels, not roadmap phase numbers.

## Current reconciled state

Evidence checked at source HEAD `77d065ccf83ab8ebaafb57b96f356c7168d10590`.
Phases 0–2 are development foundation COMPLETE (neutral owner review pending).
3A is DEVELOPMENT CLEAR, with five inherited R2 severity regressions still
visible and unresolved for strict freeze/promotion. 3B is ACTIVE: r28 has 8
failures and no regression versus r26; r29 has 7 failures but 12 regressions
versus r28. r29 is the execution candidate, not a new baseline or accepted model.
r30/o22 has no valid completed output. 3C has four 5.93 mm penetration failures.
3D passes coarse development checks but has the R2 hand-max severity regression
1.915 → 2.032. 3E has three lunge failures (pelvis max 7.559, torso min 0.120,
torso max 7.200). Actual renders are not committed at this checkpoint; never
substitute synthetic previews. Existing O7 shorts and GLBs are early candidates,
not Phase 7 completion or exports of r29.

## Phase contract

COMPLETE means all named exit evidence exists, is tied to exact candidate hashes,
and passes the required checks. A development foundation can be complete while
non-blocking owner review is pending; visual acceptance is separately mandatory
before final production promotion. Later phases are NOT complete from a script
existing, an optimiser finishing, a lower global failure count, or a nice render.

| Phase / current state | Entry and dependencies | Tasks / subphases | Exit criteria and COMPLETE meaning | Owner review |
|---|---|---|---|---|
| 0 First-party foundation / provenance — COMPLETE development | Blank O1 source and independently authored inputs | Preserve blank-source history; audit authoring boundary; record every source and operation | Verified O1 provenance and independent v4 lineage; no legacy/third-party transfer; ongoing gate on every candidate | Provenance evidence visible; non-blocking |
| 1 Base human form — COMPLETE development | Phase 0 | Proportions, bilateral body, neutral landmarks, O2 numeric health | O2 numeric gate passed; reproducible checkpoint; no claim of high-detail or visual acceptance | Neutral anatomy pending, non-blocking |
| 2 Production skeleton / rig fit — COMPLETE development, frozen | Phases 0–1 | 63-bone v4 hierarchy/rest dimensions and candidate binding fit | Payload/rig checks pass; joints fit body; rest/hierarchy protected; new evidence required to reopen | Joint-fit snapshot, non-blocking |
| 3 Core deformation — ACTIVE | Phases 0–2; unchanged R2 and gates | 3A shoulders/upper torso CLEAR; 3B hands/fingers ACTIVE; 3C grip/thumb BLOCKED; 3D wrist/push-up REFINEMENT; 3E hip/pelvis/groin/deep flexion BLOCKED | Full required stress-pose coverage, zero development blockers; region-local repairs and full comparisons; inherited regressions explicitly retained | Each meaningful candidate, non-blocking |
| 4 Development deformation freeze — NOT STARTED | Phase 3; zero blockers plus resolved material regressions or explicit evidence-backed owner disposition (no threshold change) | Reproduce all 15 poses; provenance/topology/weight audits; pin a separate development freeze record without replacing R2 | All required evidence complete, zero development failures, comparisons and lineage reconciled; freeze hash and edit boundaries recorded | Freeze snapshot non-blocking; unresolved subjective disposition blocks affected change only |
| 5 High-detail anatomy — NOT STARTED | Phase 4 sufficiently stable and freeze recorded | 5A torso; 5B shoulders; 5C arms; 5D hands; 5E pelvis/legs; 5F feet; 5G head/neck. Follow anatomy spec and packages | Each region independently authored, landmarks/silhouette documented, no deformation regression; owner reviews recorded; unresolved visual reviews remain tracked | Each region/milestone non-blocking; irreversible subjective choices deferred |
| 6 Final topology / surface quality — NOT STARTED | Stable Phase 5 region checkpoints | Manifold/normal/degenerate checks; loops; surface continuity; symmetry; counts and displacement audits | Healthy final mesh, documented intentional exceptions, complete regression evidence; no destructive remesh without correspondence evidence | Topology/surface board non-blocking |
| 7 First-party clothing — NOT STARTED (early O7 candidate exists) | Stable final body topology | Original shorts construction, coverage, thickness, seams, body clearance and full dressed deformation | Independent garment provenance; dressed/bare parity and no unexplained clipping in all poses | Dressed neutral/exercise boards non-blocking |
| 8 Materials / presentation — NOT STARTED | Phases 5–7 | Original numeric materials; legible lighting; controlled render cameras and app-distance appearance | Self-contained approved material inputs; no third-party textures; repeatable display evidence | Presentation snapshot non-blocking |
| 9 Production deformation validation — NOT STARTED | Phases 4–8; final body/clothing hashes | production_target profile; full movement envelopes, continuous motion samples, legitimate contact classification | Zero required production failures with no hidden intersections; contacts classified explicitly; all audits candidate-bound | Motion/contact board non-blocking |
| 10 Real animation-runtime integration — NOT STARTED | Phase 9 and standalone runtime available | Approved asset-only transfer; own measured grip frames/solution; real solver, contacts, smoothness and export round-trip | Real exercise engine evidence passes; standalone audits pass on exact integration commit; no old runtime code imported | Real runtime/export views non-blocking |
| 11 Automated visual QA — NOT STARTED | Stable render/runtime protocol | Project-authored references, deterministic camera/pose comparisons, detection of silhouette/crop/contact defects | Reproducible QA reports; coverage and limits stated; numerical QA never substitutes for owner anatomy acceptance | QA evidence visible, non-blocking |
| 12 Production freeze / promotion — NOT STARTED | All previous required gates; explicit owner acceptance of final exact candidate | Verify production gate packet, release/first-party audits, freeze final assets/rig/metadata and record authorised promotion | Every required gate explicitly passes for final SHA; final owner acceptance; controlled release promotion record | Final owner acceptance mandatory |

## Frozen structures and prohibited shortcuts

- R2 (`DEFORMATION_BASELINE_R2.json`), acceptance thresholds/comparison tolerances,
  exercise stress-pose definitions and 63-bone canonical-v4 rest/hierarchy are
  frozen. Never rebase a metric to erase a regression.
- No copied V-series geometry, coordinates, weights, topology, UVs, bind data,
  materials or textures; no projection, shrinkwrap, nearest-surface transfer,
  imported character/scan/image assets or third-party add-ons. Historical lessons
  are abstract reference only. Stock Blender is an authoring tool, not runtime.
- Existing GLBs describe their own export checkpoint; never relabel them r29/r30.
- Do not weaken the 2 mm development / 1 mm production grip gate, alter handle
  frames or frozen poses to manufacture a pass, or mark production from a score.
- Do not restart 3A merely to polish. Its inherited strict regressions remain a
  freeze issue; diagnose evidence and request a scoped decision if frozen tools
  would need change. Continue unrelated safe work.

## Execution order and coordination

1. Fetch live branch, compare HEAD, preserve newer work. Run session preflight.
2. Regenerate status/dashboard/ledger; use the next-action selector. Initially
   run existing `RUN_ORIGINAL_V1_R30.bat`, then full R2/r29/r28 comparisons.
3. Collect read-only remaining diagnostics. Repair wrist locally, diagnose and
   repair permitted thumb/local geometry without changing frozen rig/pose, then
   repair lunge. Hand recovery precedes these; a failed r30 cannot auto-supersede.
4. Commit each candidate manifest, solution/provenance, complete reports,
   comparisons, audits, review manifest/images and current state. Blender binaries
   stay local under existing policy; hashes and reproducible inputs are committed.
5. Before each commit/push recheck live HEAD. If it advanced, stop stale edits,
   read changed evidence and reconcile without force push or blind overwrite.
6. Each agent reads/updates the same files and names. No independent thresholds,
   baseline promotion or competing plan. Keep runtime work on its separate track.

## Review without stopping work

REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Generate real images into named
`review/visual_<revision>/` folders with candidate/source hashes, same cameras,
scale, lighting, pose/crop and labels. Record `owner_review: pending`; commit and
push useful images and continue safe diagnostics/docs or independent reversible
work. Do not treat a missing render as visual acceptance.

Pause the affected work only on explicit PAUSE, rejection of its direct parent,
subjective irreversible anatomy choice with no safe parallel work, a frozen
rig/baseline/gate change, or contradictory evidence threatening lineage. Final
production approval requires explicit final owner acceptance. Pending routine
reviews never silently become accepted.

## Repo-side implementation sequence

- [x] Roadmap and authority links; verify against r28/r29/R2 evidence.
- [x] Shared evidence parser, immutable candidate history, machine status and
  deterministic phone dashboard; test incomplete/stale/conflicting evidence.
- [x] Next-action selector and read-only Windows session preflight; test collision,
  dirty/stale branch, source hashes and missing tools; do not launch modelling.
- [x] Phase 3/5 execution packages, original anatomy and visual protocol.
- [x] Mesh/weight snapshot audits and future fail-closed promotion verifier;
  test distant edits, cross-side weights, false/missing/stale approval evidence.
- [x] Verify deterministic regeneration and existing model gates, commit/push
  logical batches; state Windows/Blender checks not executed in cloud.

## Repo-side preparation completion — 2026-10-01

These ticks describe prepared repository controls, not model phase completion.

| Package | Prepared output | Remaining execution boundary |
|---|---|---|
| [✅] A | This master roadmap | Future candidate/phase evidence updates |
| [✅] B | Evidence-derived high-detail status | Regenerate after each committed candidate |
| [✅] C | Deterministic daily phone dashboard | Actual Blender evidence comes from laptop |
| [✅] D | Historical candidate ledger including R2/rejected/intermediate states | Never remove historical rejection evidence |
| [✅] E | Read-only Windows session preflight | Real Windows/Blender/power availability not tested in cloud |
| [✅] F | Ordered next-action selector / NEXT runner | Prints exact task; no automatic promotion |
| [✅] G | 3B–3E local repair packages | Execute candidate experiments on laptop |
| [✅] H | Shared non-blocking review contract | Owner decisions must be truthfully recorded |
| [✅] I | Actual render-source manifests and previous/new SVG board generator | Recapture real renders; full rear/anatomy coverage still needed |
| [✅] J | 22-region original anatomy specification | Phase 5 remains not started |
| [✅] K | Seven Phase 5 regional modelling packages | Do not execute before stable foundation/freeze |
| [✅] L | Raw model snapshot exporter and mesh/weight change audit | Blender snapshot execution and candidate correspondence |
| [✅] M | Fail-closed production eligibility verifier/workflow | All final gates and owner acceptance remain open |

Verification: 63 Python unittest cases pass; generated outputs reproduce exactly;
pinned R2 verifier, R2/export candidate status verifier, candidate GLB structural
audit and documentation hygiene pass. ORIGINAL-v1 Python syntax checks pass;
original stress-pose AST remains identical apart from metadata-only import.
No Windows/Blender execution, new candidate render or runtime integration was
claimed. Repo controls use standard Python/project-owned code; no runtime
package or production asset dependency was added.

### Capture tooling preparation checkpoint — 2026-10-01

The optional milestone capture workflow is now prepared: a 57-view bare-body plan,
`RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat`, verified publication/phone index, and
milestone previous-versus-new comparison mode. See the visual review specification
for exact commands and limitations. No actual milestone capture is claimed; no
Phase 5 modelling or phase completion is inferred. Pending snapshots remain
NON-BLOCKING, and the current deformation next task remains r30 on the laptop.

### Intermediate exit evidence contract — 2026-10-01

Phases 4–11 require the explicit check/source contract documented in
`docs/ORIGINAL_V1_PHASE_EXIT_EVIDENCE.md`; a bare candidate-bound PASS marker is
insufficient. The Phase 4 execution package is prepared under docs/work_packages.
Its numeric replay uses the existing frozen poses without renders and must match
all primary metrics under the same candidate/script/Blender identities. No freeze
or later phase has been executed on r29, and R2 remains pinned. This contract checks
record integrity; every referenced domain test still must genuinely pass.

## Staged GPT preparation before Blender — 2026-10-01

These stages take preparation off Claude; they do not complete model phases.
Check back with the owner after each published stage. Routine snapshots remain
NON-BLOCKING. The actual next deformation action remains RUN r30 on the laptop.

| Stage | Preparation | State / boundary |
|---|---|---|
| 1 | Phase 3 source-verified diagnostic brief from existing probes, wired into the existing runner | PREPARED; real probes still require laptop Blender |
| 2 | Candidate-bound local edit/audit policy drafts; verified probe IDs stay inspection references with no automatic edit permission | PREPARED; r29 drafts await actual probes and a declared local mask |
| 3 | Later Phase 6–11 execution packages and evidence commands using existing exit contracts | PREPARED; domain-tool gaps explicit, all phases remain NOT STARTED |
| 4 | Snapshot-based Phase 6 surface audit using the candidate's own raw geometry | PREPARED; actual snapshots and remaining domain reviews still required |
| 5 | Revision-isolated candidate GLB export with exact source/settings hashes and collision refusal | PREPARED; actual Blender capture/validation required, no model acceptance |
| 6 | Named raw garment snapshots, body-mask receipts and source-bound pair diagnostics, reusing existing change/surface audits | PREPARED; actual Blender capture remains open |
| 7 | Evaluated static dressed stress-pose clearance/intersection evidence plus matched bare/dressed review capture | PREPARED; actual Blender execution, contact classification and continuous dressed motion remain open |
| 8 | Deterministic sampled dressed movement ranges with exact per-sample raw contact evidence and explicit classification template | PREPARED; actual Blender execution, real classification, push-up/equipment paths and runtime-specific refinement remain open |
| 9 | First-party contact source bridge for real push-up endpoints, hand-driven dumbbells and fixed pull-up rack sockets | PREPARED; source semantics/hashes only, actual live-runtime capture remains Phase 10-bound |
| 10 | Live standalone runtime discovery, cross-branch semantic comparison and incomplete real-engine evidence harness contract | PREPARED; current runtime HEAD is not exact-SHA green and actual Phase 10 execution remains blocked by Phase 9/final assets/runtime gates |
| 11 | Deterministic first-party mask visual QA, immutable reference registry, coverage plan and capture-mismatch separation | PREPARED; no real Phase 10-approved runtime captures/references exist yet, owner anatomy acceptance remains mandatory |
| 12 | Final technical promotion packet, exact packet-bound receipt and two-key owner-authorised production-freeze verifier | PREPARED; no current candidate can pass and verifier never mutates production state |

Stage 1 verifies candidate/script identity, exact target/bilateral coverage,
finite measurements and agreement with the primary rounded metrics. It lists
pre/post-close penetration, contact counts, exact edge IDs and measured weights.
These are observations: no cause, permitted mask, geometry repair or model phase
completion is inferred. No fake diagnostics or review images are produced.

Stage 3 packages: `docs/work_packages/PHASE_6_TOPOLOGY.md`,
`PHASE_7_CLOTHING.md`, `PHASE_8_MATERIALS.md`, `PHASE_9_PRODUCTION_DEFORMATION.md`,
`PHASE_10_RUNTIME.md` and `PHASE_11_AUTOMATIC_QA.md` in that same directory.
Apply `LATER_PHASE_EXECUTION_CONTRACT.md` and `LATER_PHASE_TOOLING_READINESS.md`
with each. Existing static/capture tools provide bare-body evidence only; missing
dressed, continuous-motion, runtime and visual detectors remain open. Phase 10
may validate a candidate in an isolated runtime fixture under that branch's policy;
production asset allowlist/loader promotion stays exclusively in Phase 12.

Stage 4 surface evidence tooling is documented in
`docs/work_packages/SURFACE_AUDIT_PROTOCOL.md`. It reports topology/geometry
findings from real raw snapshots without repairing geometry or awarding a gate
PASS. Unknown shading normals, intersections and joint-support review stay open.

Stage 5 export tooling: `docs/work_packages/CANDIDATE_EXPORT_PROTOCOL.md`.
It isolates candidate exports and binds source/settings/bytes, preserving historical
GLBs. Next GPT preparation stage: candidate-bound dressed evidence tooling; current
laptop deformation action remains RUN r30. No later model phase is executed.

Stage 6 raw garment foundation: `docs/work_packages/GARMENT_RAW_EVIDENCE_PROTOCOL.md`.
Actual snapshots require Blender; no garment modelling or Phase 7 completion is
claimed. Next GPT preparation: evaluated dressed pose/contact and matched review
capture. Current laptop task remains RUN r30.

Stage 7 evaluated dressed evidence: `docs/work_packages/DRESSED_EVALUATED_EVIDENCE_PROTOCOL.md`.
It reuses the frozen pose functions directly, measures full-body/garment evaluated
surface relationships on all 15 stress poses and captures source-bound matched
bare/dressed review pairs without changing the pose definitions or approving
contact. Actual Blender execution is still required. Next GPT preparation is a
continuous dressed range/contact sampler with explicit per-frame contact
classification; current laptop deformation task remains RUN r30.

Stage 8 continuous dressed-range evidence: `docs/work_packages/DRESSED_RANGE_CONTACT_PROTOCOL.md`.
The project-owned plan samples six declared stress-pose paths at 21 points per
segment, preserves exact body/garment face-pair and floor-vertex evidence, and
creates a source-bound per-sample classification record. It deliberately leaves
unsupported push-up and moving-equipment paths open rather than inventing them.
Actual Blender execution and evidence-backed classifications are still required;
current laptop deformation priority remains RUN r30.

Stage 9 contact source bridge: `docs/work_packages/CONTACT_SOURCE_BRIDGE_PROTOCOL.md`.
It verifies the project-owned exercise/contact source facts that Stage 8 correctly
left unsupported: real push-up Top↔Bottom endpoints and fixed hand/toe contacts,
hand-matrix-driven dumbbell attachment, and fixed pull-up rack/socket locks. It
records exact source hashes and fails on semantic drift, but does not execute the
solver or copy runtime motion into Blender. The live standalone runtime must still
be rediscovered and bound at Phase 10. Current laptop deformation priority remains
RUN r30.

Stage 10 runtime discovery/harness preparation: `docs/work_packages/RUNTIME_DISCOVERY_HARNESS_PROTOCOL.md`.
The authoritative standalone branch was resolved to `work/standalone-first-party-audit-20260927`; current source shows v4 active, but its live HEAD e3a7d915... is not a green integration checkpoint because focused skeleton parity failed by 0.02 m and downstream gates did not run. The new read-only verifier compares a separate clean runtime checkout against the Stage 9 contact semantics, hashes every source, detects source-vs-handoff discrepancies and never edits either branch. `ORIGINAL_V1_RUNTIME_EVIDENCE_TEMPLATE.json` remains INCOMPLETE until real Phase 10 execution. Current laptop deformation priority remains RUN r30.

Stage 11 automated visual QA preparation: `docs/work_packages/VISUAL_QA_PROTOCOL.md`.
The first-party detector binds immutable source images to standard-library PGM masks, verifies source/mask hashes and dimensions, detects missing/cropped expected regions, measures connected components and neutral symmetry, and computes matched silhouette IoU/XOR/centroid/bounds only when capture identities match. Capture-setting drift becomes CAPTURE_MISMATCH rather than a model regression. `ORIGINAL_V1_VISUAL_QA_REFERENCE_INVENTORY.json` is intentionally empty until actual owned captures exist. No external vision service/reference corpus is used and no QA score can approve anatomy. Current laptop deformation priority remains RUN r30.

Stage 12 final-freeze preparation: `docs/work_packages/PHASE_12_PRODUCTION_FREEZE.md`.
The existing technical promotion verifier now binds successful receipts to the exact
promotion-packet SHA/candidate/runtime identities. The new final-freeze verifier
revalidates that packet, every Phase 4-11 exit report, final asset bytes, Phase 9
model commit, Phase 10/11 runtime commit, current deformation state and a separate
explicit OWNER AUTHORISED PRODUCTION FREEZE record. Even full eligibility remains
non-mutating with production_approved=false; actual release is a separate controlled
asset-only/runtime operation followed by exact-SHA release re-verification. Current
laptop deformation priority remains RUN r30.


### Post-preparation execution orchestration — 2026-10-01

Repository-side Stages 1-12 are prepared. This does **not** add Roadmap Phase 13.
Use `ORIGINAL_V1_EXECUTION_ORCHESTRATION.json`,
`docs/ORIGINAL_V1_EXECUTION_ORCHESTRATION.md` and
`RUN_ORIGINAL_V1_EXECUTION_PLAN.bat` to map the evidence-derived current state onto
one critical-path node and the relevant prepared support tools. The orchestrator is
read-only: it validates that all Stage 1-12 support artifacts exist, checks the
critical-path graph, compares the r30 node against the existing next-action
selector and prints safe parallel work without launching Blender or advancing a
phase. At the current expected r29 / Phase 3B state, the actual model action remains
`RUN_ORIGINAL_V1_R30.bat` after live preflight.
