# ORIGINAL v1 O4 deformation handoff

## Purpose

This is the current model-quality handoff for `HomeGymPT_Male_ORIGINAL_v1` on
`claude/original-v1-blender-o2-20260929`.

It supersedes the older assumption that work stopped at O2 neutral anatomy.
The branch now contains an O4 bound candidate, O7 shorts candidate, bare/dressed
candidate GLBs, pose deformation reports and grip reports. None of those
candidate assets are production-approved.

The standalone runtime branch remains separate. Do **not** merge this branch
wholesale into `work/standalone-first-party-audit-20260927`.

## First-party boundary

Use only independently authored ORIGINAL v1 geometry, the project-owned
`hgpt_canonical_v4_original` rig, stock Blender modelling/weighting tools and
committed project scripts.

Historical V8–V15f work is **reference-only**. It may inform:

- failure cases;
- visual quality expectations;
- acceptance criteria;
- abstract biomechanical lessons;
- which regions deserve stress testing.

It must not contribute copied vertices, coordinates, topology, skin weights,
bind matrices, materials, textures, garment data or other implementation data.

Important historical lessons carried forward:

- V8 was the accepted knee visual baseline, so knee silhouette and deep-flexion
  behaviour remain explicit review targets.
- V9–V14 hand experiments exposed palm, fingertip, thumb/web and grip failure
  modes; ORIGINAL v1 must solve those independently and prove them under load.
- The accepted shoulder/clavicle skeleton correction showed that remaining
  forward-shoulder/overhead defects were mesh/skin problems, so shoulder
  deformation is a primary O4 gate.
- V15f remains a visual/reference benchmark only.

## New deterministic acceptance layer

The branch now has:

- `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json`
- `scripts/evaluate_original_v1_deformation_report.py`

The acceptance specification defines two profiles:

1. `development_blocker` — catches deformation severe enough that cosmetic
   polish or promotion should stop.
2. `production_target` — stricter target for a later production candidate.

These numerical checks do **not** replace owner/anatomy review and do not prove
exercise biomechanics. The Blender pose script deliberately uses stress poses,
not the runtime exercise solver.

### Run the current report

```bat
python scripts\evaluate_original_v1_deformation_report.py ^
  ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  --grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  --profile development_blocker ^
  --require-group core_five ^
  --markdown-out ORIGINAL_V1_WORK\candidates\deformation_acceptance_r2.md
```

Use `--report-only` while iterating if a non-zero exit code would interrupt
the Blender workflow.

Before promotion, repeat with:

```bat
python scripts\evaluate_original_v1_deformation_report.py ^
  ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  --grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  --profile production_target ^
  --require-group core_five
```

## Current candidate status

Against the newly recorded `development_blocker` profile, the current R2
candidate has **54 failed checks**. This is expected evidence that O4 requires
repair; it is not a regression in the standalone software.

Highest failing poses by check count:

| Pose | Failed checks |
|---|---:|
| press_top_rhythm | 7 |
| pullup_hang_rhythm | 6 |
| press_top | 5 |
| pullup_top | 5 |
| curl_peak | 4 |
| press_bottom | 4 |
| pullup_hang | 4 |
| curl_handle | 4 |
| lunge | 3 |
| row | 3 |
| grip | 3 |
| pullup_bar | 4 |
| squat_bottom | 1 |
| pushup_bottom | 1 |

Most frequently implicated regions in the development-blocker failures:

| Region | Failed checks |
|---|---:|
| hand | 19 |
| finger | 11 |
| shoulder | 10 |
| torso | 4 |
| pelvis | 1 |
| grip_l | 2 |
| grip_r | 2 |

The R2 report contains two equipment-contact poses, and both currently fail
penetration on both hands: `curl_handle` and `pullup_bar` are each **5.93 mm**
versus the **2.0 mm** development limit and **1.0 mm** production target.
The expanded coverage raises the pinned development baseline from the earlier
52-check count to **54**; no threshold was weakened.

Neutral remains an important control: it reports volume 1.0, zero compressed
or stretched edges under the current stress thresholds, and zero
self-intersections.

## Machine-readable candidate status

`ORIGINAL_V1_CANDIDATE_STATUS.json` is now the compact current-state contract
for the model branch. It deliberately keeps `production_approved: false` and
separates verified candidate evidence from open gates.

`scripts/verify_original_v1_candidate_status.py` recomputes the status from:

- O1 clean-room provenance;
- O2 rig provenance;
- the 63-bone v4 payload;
- O4 bind metadata;
- O7 shorts metadata;
- both committed candidate GLBs;
- R2 deformation and equipment-grip reports;
- the automatic repair queue.

GitHub Actions run **36715570852** passed this status contract. Current verified
state remains:

- overall: **candidate_not_production**
- development deformation: **BLOCKED — 54 failed checks**
- production deformation: **BLOCKED — 133 failed checks**
- repair ownership: **complete — 0 unmapped**
- next repair priority: **1 / shoulder**
- candidate GLB structure: **PASS (candidate-only)**
- owner neutral-anatomy review: **pending**
- runtime integration: **pending**
- release promotion: **blocked**

A safety diff from Claude's original candidate-export checkpoint
`34a8c9e55e120a0443df30ce3ffdcb9c7b52a48f` confirms this verification batch
changed only validation, CI, status and handoff files. It did **not** modify the
body mesh, skin weights, shorts geometry, committed candidate GLBs or
standalone runtime implementation.

## Candidate GLB structural audit

The committed bare/dressed review exports now have an independent,
Blender-free structural audit:

`scripts/audit_original_v1_candidate_glbs.py`

GitHub Actions run **36715160223** passed the audit for both files.

Current evidence:

| Check | Bare | Dressed |
|---|---:|---:|
| SHA-256 matches export manifest | PASS | PASS |
| glTF/GLB version | 2.0 | 2.0 |
| Expected v4 bones | 63 | 63 |
| Bone hierarchy / skin joint set | PASS | PASS |
| Mesh nodes | 1 | 2 |
| Skins | 1 | 1 |
| Images | 0 | 0 |
| Textures | 0 | 0 |
| Animations | 0 | 0 |
| External buffer/image URIs | 0 | 0 |
| Legacy/reference token hits | 0 | 0 |

Bare:
`ba0f88e59099a699d89529892ab219d13eb49225c2339fc3b5e465248de51623`
(1,023,324 bytes).

Dressed:
`2a3fbc5812a56c21725f5834467035b33862643af2607d5945a520ba322b0cba`
(1,121,604 bytes).

The bare export contains only
`HGPT_ORIGINAL_V1_SKIN_CANDIDATE`. The dressed export contains that skin
material plus `HGPT_ORIGINAL_V1_SHORTS_FABRIC_CANDIDATE`; both are
texture-free numeric materials.

This does **not** approve either GLB for production. It proves only that the
current committed review exports are structurally self-contained, match their
manifest, carry the expected ORIGINAL-v4 rig and show no audited legacy-name or
external-resource contamination. Deformation, anatomy, garment quality,
clean-room history and release promotion remain separate gates.

## Automatic repair queue

The repair order is now machine-readable in `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json`
and can be regenerated from any pose report:

```bat
python scripts\build_original_v1_repair_queue.py ^
  ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  --profile development_blocker ^
  --require-complete-ownership ^
  --markdown-out ORIGINAL_V1_WORK\candidates\repair_queue_r2.md
```

For pinned R2 the expected state is:

- acceptance failures: **54**
- unmapped blockers: **0**
- next repair priority: **1**
- Priority 1 owns **15** current failed checks
- Priority 2 owns **38**
- Priority 3 owns **3**
- Priority 4 owns **1**
- Priority 5 currently owns **0** development-blocker failures

Some failures intentionally appear in more than one repair group when a
pose-global metric spans regions. The queue is an ownership plan, not a blended
score.

Use the grouped read-only runner for each stage:

```bat
RUN_ORIGINAL_V1_REPAIR_CHECK.bat shoulder
RUN_ORIGINAL_V1_REPAIR_CHECK.bat hand
RUN_ORIGINAL_V1_REPAIR_CHECK.bat hip
RUN_ORIGINAL_V1_REPAIR_CHECK.bat pushup
RUN_ORIGINAL_V1_REPAIR_CHECK.bat row
```

Work only the lowest-numbered `BLOCKED` priority. After a repair, regenerate
the queue from the new full pose report. Do not move to a later priority merely
because its renders look better; the earlier priority must clear its owned
development blockers without regression first.

## Repair order

Do not polish the face, materials or shorts before the higher-priority
deformation blockers are resolved.

### Priority 1 — shoulder girdle / overhead deformation

Target poses:

- `press_bottom`
- `press_top`
- `press_top_rhythm`
- `pullup_hang`
- `pullup_hang_rhythm`
- `pullup_top`

Current examples:

- `press_top` shoulder minimum edge ratio: **0.094**
- `press_top` shoulder maximum edge ratio: **9.089**
- `pullup_hang` shoulder maximum edge ratio: **8.987**
- rhythm variants produce torso stretch up to **8.317**
- rhythm volume rises to about **1.13**, beyond the current development range

Work first on weight distribution and deformation support across
clavicle/scapula/deltoid/upper-arm/upper-torso transitions. Preserve the
63-bone rig structure unless a separate rig defect is independently proven.

### Priority 1 measured R2 targets

Do not spend the first Blender iteration rediscovering which shoulder poses are
worst. The pinned R2 report already establishes the following development
blockers:

| Pose | Current blocker(s) |
|---|---|
| `press_top` | shoulder max **9.089**, shoulder min **0.094** |
| `pullup_hang` | shoulder max **8.987** |
| `pullup_bar` | shoulder max **8.987** |
| `press_top_rhythm` | shoulder max **8.283**, shoulder min **0.143**, torso max **8.317**, volume **1.1309** |
| `squat_bottom` | shoulder max **8.053** |
| `pullup_hang_rhythm` | shoulder max **7.907**, torso max **8.317**, volume **1.1361** |
| `press_bottom` | shoulder max **6.414** |
| `pullup_top` | shoulder max **5.169**, self-intersections **216** |

Development-blocker targets:

- regional maximum edge ratio: **≤ 5.0**;
- regional minimum edge ratio: **≥ 0.15**;
- whole-body volume ratio: **0.90–1.10**;
- self-intersecting face pairs: **≤ 200**.

Suggested Blender order inside Priority 1:

1. `press_top` — largest shoulder stretch and the only severe shoulder collapse;
2. `pullup_hang` / `pullup_bar` — nearly identical high-elevation stretch;
3. rhythm poses — fix shoulder/torso volume interaction without regressing the
   static overhead poses;
4. `squat_bottom` arm position;
5. `press_bottom`;
6. `pullup_top` — clear both the remaining shoulder stretch and the
   self-intersection excess.

This ordering is diagnostic only. Priority 1 is not clear until the full
owned-pose set passes the development blocker and the regression comparator
reports no material worsening elsewhere.

### Before the first shoulder weight edit

Capture the current project-authored weight distribution once:

```bat
AUDIT_ORIGINAL_V1_SHOULDER_WEIGHTS.bat ^
  ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend ^
  r2_before_repair
```

The audit is read-only. It reports shoulder/torso/arm vertex counts,
normalisation error, influence counts, dominant bones, cross-side contamination
and distance-banded mean weights around each upper-arm head.

The current O4 binder used:

- region permissions that allow shoulder vertices to use
  `spine_02/spine_03/neck + clavicle/scapula/upperarm`;
- three general neighbour-smoothing passes;
- an additional shoulder joint zone of **160 mm radius / 14 iterations**;
- maximum four influences per vertex.

Those facts are **diagnostic context, not a prescription**. Do not simply add
more smoothing because the shoulder stretches. First use the audit plus the
pose evidence to determine whether the defect is:

- too-wide/too-soft ownership across the axilla/deltoid transition;
- too little stable torso/scapula support;
- too much upper-arm ownership near the torso;
- a sharp permission/region boundary;
- topology that cannot support the required fold/elevation;
- or a combination.

After a meaningful repair, rerun the audit with a new label (for example
`shoulder_r3`) so the weight change is reviewable alongside the deformation
comparison.

Do not rerun the original O4 binder over the repaired candidate as a shortcut:
that would recreate the generated weights and can destroy manual evidence.

### Priority 1 repair-cycle command

For shoulder-only iteration, use the read-only targeted runner:

```bat
RUN_ORIGINAL_V1_SHOULDER_CHECK.bat
```

By default it tests the current O4 candidate with:

- `press_bottom`
- `press_top`
- `press_top_rhythm`
- `pullup_hang`
- `pullup_hang_rhythm`
- `pullup_top`

It writes a fresh evidence folder under
`ORIGINAL_V1_WORK/candidates/repair_checks/shoulder_current/`, renders only
those poses, and compares them with the matching poses from pinned R2 using
both gate-count and severity-regression protection.

For a different candidate or evidence label:

```bat
RUN_ORIGINAL_V1_SHOULDER_CHECK.bat path\to\candidate.blend shoulder_r3
```

Never reuse an existing label; the runner refuses to mix evidence directories.

### Priority 1 session log — 2026-09-30 (laptop, Claude)

**Status: Priority 1 still BLOCKED. No repaired candidate accepted.**
`DEFORMATION_BASELINE_R2.json` is unchanged and R2 remains the comparison
anchor.

Lineage note: the local `HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend` hashes
to `d89dedb5…44a4`. That is the O7-shorts record hash, i.e. the exact file the
R2 evidence was produced from. `f0cfa84c…` in the baseline is the earlier bind
hash. This is consistent lineage, not drift.

The read-only baseline audit is at
`repair_checks/weight_audits/shoulder_weights_r2_before_repair.json`. Audit
artefact: `HGPT_UNDER_SHORTS` (the shorts mask group) is counted as a bone, so
the torso shows weight-sum error 1.0 and 5 influences. The deform weights
themselves are normalised with at most 4 influences. The audit script should
skip `HGPT_*` groups; it was not edited this session.

Diagnosis (from edge probes run after the pose test): every 5–9.7× stretched
edge in `press_top` and its rhythm variant sits in the axilla vault, at rest
approximately x ±0.17–0.18, y 0.02–0.07, z 1.40–1.415. Those vertices have
weight split roughly evenly (.38/.33/.29) across
`upperarm`/`scapula`/`spine_03`, so when the arm elevates they are pulled three
ways.

Repair tool (first-party, operates only on this candidate's own weights):
`scripts/repair_original_v1_o4_shoulder_weights_blender.py <source> -- <new.blend> <preset>`.
It refuses to overwrite and writes a `<new>.json` record with parameters and
hashes. It has four operations:

- **A:** raises upper-arm share on the lateral deltoid cap;
- **B:** moves back-of-shoulder scapula weight toward spine;
- **D:** harmonic (Laplacian) blend of the axilla vault;
- **C:** a gentle permission-bounded band smooth.

Results on the shoulder subset (R2 = 34 failed checks). Candidate `.blend`
files are git-ignored; the `.json` records and `repair_checks/shoulder_rN/`
evidence are committed.

| Cand. | Change | Failed | Regressions | Note |
|---|---|---:|---:|---|
| r3 | A .82 + B keep .40 + band 10 it | 30 | 9 | too much smoothing |
| r4 | A + B .60 + axilla D (all regions) | 30 | 19 | D on arm verts hurts |
| **r5** | A + B .50 + D (shoulder/torso only) | **29** | 8 | best count |
| r6 | r5 without A | 31 | 4 | axilla collapse returns |
| r7 | r5 without B | 30 | 8 | B is harmless/helpful |
| r8 | narrower/weaker A (.55) | 33 | 8 | |
| r9 | A .65 | 34 | 7 | |
| **r10** | r5 + A tapered toward acromion (z 1.47–1.545, ×0.55) | 32 | **5** | best balance |
| r11 | taper z 1.49–1.55, ×0.75 | 31 | 7 | rhythm collapse |
| r12 | r11 with A .76 | 31 | 5 | rhythm collapse |

What improved (r5/r10/r12 alike), shoulder maximum stretch:

| Pose | Before | After |
|---|---:|---:|
| press_top | 9.09 | 5.94 |
| pullup_hang / bar | 8.99 | 5.88 |
| squat_bottom | 8.05 | 5.27 |
| press_bottom | 6.41 | 4.30 |
| pullup_top | 5.17 | 3.52 |
| press_top_rhythm | 8.28 | 6.64 |
| pullup_hang_rhythm | 7.91 | 6.51 |

Torso maximum in the rhythm poses fell from 8.32 to 5.03, and rhythm volume
fell from 1.131/1.136 to 1.097/1.103. `press_top` shoulder minimum rose from
0.094 to 0.123–0.194.

What still fails or regresses:

1. Shoulder maximum is still above 5.0 in all overhead poses (5.3–6.6).
2. A single-edge **shoulder minimum** near the acromion/deltoid top is very
   sensitive to the operation A taper:
   - r10 fixes both rhythm poses but drops `pullup_hang`/`pullup_bar` to 0.107;
   - r11/r12 fix `pullup_hang` but drop the rhythm poses to 0.07–0.09.

   A height-only taper cannot satisfy both. The next attempt should localise
   the compressed edge with the stretch/min probe for both pose families and
   blend that small patch harmonically, like operation D, instead of tapering.
3. `squat_bottom` volume deviation is 0.0373 → ~0.043 in every run using
   operation A, just over the 0.005 tolerance. Likely cause: the cap raise
   moves lateral deltoid volume with the arm. Test restricting A to z > ~1.42,
   or compensating with B.
4. Self-intersections in the rhythm poses sometimes rise (r5: 110 → 150). r10
   kept them at the baseline.

**Next step:** start from preset `r10`, add a localised harmonic patch for the
acromion compressed edge, and address the squat volume drift. Never reuse an
evidence label; the next label is `shoulder_r13`.

### Priority 2 — hands / fingers / thumb / equipment grip

Target poses:

- `curl_peak`
- `grip`
- `curl_handle`
- `pullup_bar`
- `pullup_top`

Current examples:

- hand minimum ratio down to **0.070**
- hand maximum ratio up to **5.387**
- finger minimum ratio **0.086–0.113**
- repeated finger/hand self-intersections
- dumbbell-handle penetration **5.93 mm** on each side

Repair finger-chain weighting, MCP/PIP/DIP support, thenar/thumb web and palm
weight distribution. Do not solve grip by enlarging the handle tolerance or by
copying any V-series hand data.

### Priority 3 — hip / pelvis / groin / deep flexion

Target poses:

- `squat_bottom`
- `lunge`

Current examples:

- lunge torso minimum ratio **0.121**
- lunge torso maximum ratio **7.2**
- lunge pelvis maximum ratio **7.559**
- squat torso minimum ratio **0.173**
- squat torso maximum ratio **4.204**

Correct pelvis/upper-thigh/torso weights and, only if required by evidence,
supporting topology. Re-test shorts only after the body deformation is stable.

### Priority 4 — push-up loaded wrist/hand chain

Target pose:

- `pushup_bottom`

Current development blocker:

- hand minimum ratio **0.139**

The production profile also exposes arm, hand, shoulder, foot and torso issues.
Treat this as a loaded-contact deformation test, not merely a silhouette pose.

### Priority 5 — row and extended movement families

Resolve after priorities 1–4. Use the extended pose group to make sure fixes do
not simply overfit the five core exercises.

## Iteration rule

For each repair batch:

1. Start from the latest clean candidate checkpoint.
2. Change only the minimum necessary region/weights/topology.
3. Re-run the relevant pose subset first.
4. Run the deformation evaluator using `development_blocker`.
5. Compare counts and worst regional ratios with the previous checkpoint.
6. Reject a change if it improves one pose by creating a worse blocker in
   another required pose.
7. Once a region clears the development profile, run the full core-five group.
8. Do not declare production readiness until the `production_target` profile,
   provenance checks, human anatomy review, runtime contacts/movement, dressed
   review and standalone release gates all pass.

## Regression protection

After a repaired Blender candidate produces a new pose report, compare it with
the previous accepted checkpoint instead of looking only at the new total:

```bat
python scripts\compare_original_v1_deformation_reports.py ^
  ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  ORIGINAL_V1_WORK\candidates\pose_test_report_r3.json ^
  --baseline-grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json ^
  --candidate-grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_r3.json ^
  --profile development_blocker ^
  --json-out ORIGINAL_V1_WORK\candidates\deformation_compare_r2_r3.json
```

The comparator deliberately does **not** use one blended quality score. It
returns `REGRESSION` if any existing pose or grip gains failed checks, even
when another pose improves. This prevents an apparent global improvement from
hiding a newly damaged shoulder, hand, hip or contact.

The exact current comparison anchor is pinned in `ORIGINAL_V1_WORK/candidates/DEFORMATION_BASELINE_R2.json`, including the candidate SHA-256, report blob SHAs and the 54-check development baseline. Do not silently replace that baseline; create a new numbered baseline only after an explicitly accepted improvement.

## Future production runtime metadata — do not fabricate yet

The standalone promotion path now requires the final production GLBs to carry
project-owned scene extras under `homeGymPT`. This is deliberately a **future
production gate**, not something to fake on the current R2 candidate.

Required final fields:

- `assetId: "HomeGymPT_Male_ORIGINAL_v1"`;
- `rigId: "hgpt_canonical_v4_original"`;
- `offsetFrame: "hand-v2"`;
- finite `gripFrameOffsets.l` and `gripFrameOffsets.r`;
- finite `handleGripOffsets.l` and `handleGripOffsets.r`;
- an ORIGINAL-v1-specific `gripSolutionId` that exists in the first-party
  runtime solved-grip table.

The current standalone solved-grip table intentionally contains **no
character-specific rows**. Do not reuse any legacy/V-series hand solution.

The candidate export script now sets Blender's `export_extras=True` for
**future** exports, so custom properties can pass through to glTF extras once
they are legitimately authored. The committed candidate GLBs are unchanged by
that script change.

### When to author the grip metadata

Do this only after Priority 2 hand/grip work has produced evidence that meets
the deformation/contact gates:

1. repair finger/palm/thumb weights and geometry;
2. achieve the equipment penetration/contact thresholds on
   `curl_handle` and `pullup_bar`;
3. measure each hand's grip/contact frame and handle centre from ORIGINAL v1
   itself;
4. generate an ORIGINAL-v1-specific solved grip row from those measurements;
5. record the exact values as scene `homeGymPT` custom properties;
6. export with extras and verify the standalone production metadata gate.

The generic runtime `anatomicalGripOffset` is only a fallback. **Do not**
treat its current ±25 mm / 85 mm values as the final ORIGINAL v1 solution and
do not tune the model to fit that fallback.

## Integration rule

The candidate branch is intentionally divergent from the latest standalone
software branch. When an asset eventually passes:

- bring across only specifically approved ORIGINAL v1 assets, provenance,
  reports and required first-party authoring/validation scripts;
- do not merge old runtime/framework code from this branch;
- run the standalone release/third-party gates again on the exact resulting
  commit;
- replace the temporary procedural fallback only after the production asset is
  explicitly approved.

## Next Blender session

Claude should begin with **Priority 1 shoulder deformation**, then Priority 2
hands/grip. Do not spend the next session on new exercise features, facial
detail, material polish or further third-party migration work.

The immediate objective is simple:

> reduce the current development-blocker failures without weakening the gates,
> while keeping ORIGINAL v1 independently authored and preserving the clean
> standalone runtime boundary.
