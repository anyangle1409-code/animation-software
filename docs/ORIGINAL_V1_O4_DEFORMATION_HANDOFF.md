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

A follow-up probe confirmed that every regressing shoulder minimum (r10
pull-up hang 0.107, r12 rhythm 0.07/0.09) is on the same few edges, at rest
approximately (±0.22–0.25, y 0.00–0.10, z 1.50–1.535). Those vertices carry
upperarm ~.4–.6, clavicle ~.1–.4 and scapula ~.2–.4.

I then tried operation E, a harmonic blend of that acromion patch (radius 50 mm,
80 iterations):

| Cand. | Change | Failed | Regressions | Note |
|---|---|---:|---:|---|
| r13 | r10 + E | 33 | 7 | minima 0.12–0.17, all still just under baseline |
| r14 | r5 + E | 33 | 9 | worse |

Smoothing the acromion weights spreads the fold rather than removing it.
Conclusion: under linear-blend skinning with this topology, the deltoid top
folds in overhead elevation whatever the weights. The fix is likely one of:

- a pose-independent redistribution of upperarm vs clavicle/scapula along the
  acromion that is tested per pose family;
- a topology/edge-flow change (extra loop across the deltoid top), which the
  iteration rule allows only if evidence requires it;
- corrective shape keys, which are out of scope until approved.

(The r3–r14 hand-tuned presets are superseded by the multi-pose optimiser
below.)

### Priority 1 session log — 2026-09-30 evening (laptop, Claude): multi-pose weight optimiser

**Status: Priority 1 still BLOCKED, but it now owns 3 failures instead of 15.**

- Best candidate: `r21`, file
  `ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r21.blend`
  (git-ignored, reproducible; see below).
- Hashes:
  - candidate SHA-256 `16d5f3fd0d47f7be91e231230039294059d948f32f9ddd3eb0114664f4f5afd7`;
  - parent (R2 evidence file) `d89dedb5…44a4`;
  - weight solution `weight_solutions/o10.npz`, SHA-256
    `4ae61cb8014b89beb9adcb6d6a4ff0215deb9414f0779874236b8000c3c0c90d`.
- Not accepted by the comparator: 7 small regressions, listed below.
- `DEFORMATION_BASELINE_R2.json`, `ORIGINAL_V1_CANDIDATE_STATUS.json` and every
  promotion/approval flag are unchanged. The 63-bone rig is unchanged; the
  apply script refuses any other rig. Mesh, shorts and non-zone vertices are
  untouched.

**Diagnosis added this session:**

1. **Torso back tear.** The R2 rhythm torso maximum of 8.32 is not at the
   shoulder. It is on the back midline (x = 0, y ≈ 0.14, z 1.22–1.39). Those
   vertices were weighted about 0.31 to *both* `scapula_l` and `scapula_r`, so
   the two blades rotating apart tore the midline. The fix moved that weight
   to `spine_02`/`spine_03`.
2. **Axilla vault stretch.** The overhead stretch came from the three-way
   `upperarm`/`scapula`/`spine_03` split already noted above.
3. **New self-intersections come from buckling on the acromion ridge.** When a
   repair reduced stretch, the deltoid-cap skin (x ≈ ±0.24–0.28, z 1.44–1.52)
   buckled into the acromion top (z 1.51–1.54). The colliding faces were
   13–90 mm apart at rest and 1–5 mm apart when posed.

**Method (all first-party, operating only on this candidate's own
mesh/weights and the v4 rig):**

1. `scripts/dump_original_v1_o4_pose_skinning_blender.py` dumps the rest mesh,
   weights and per-pose skinning matrices for all 15 stress poses. It reuses
   the pose test's own pose code and verifies that numpy linear-blend skinning
   reproduces Blender's evaluated mesh (max error below 1 µm in every pose).
2. `scripts/optimize_original_v1_o4_shoulder_weights.py` solves the weights of
   2,826 zone vertices. The zone is both shoulders within 240 mm of the
   glenohumeral joint, plus every upper-body vertex carrying scapula weight.
   The solve is L-BFGS over softmax-parameterised weights (always normalised,
   only permitted bones), then pruned to 4 influences and polished. It
   optimises against **all 15 poses at once** with:
   - hinge barriers at the gate margins (stretch ≤ 4.3, compression ≥ 0.24);
   - per-pose, per-region no-regression bounds against R2;
   - a whole-body volume barrier;
   - count-aware p99/p01 budgets;
   - a dihedral fold barrier;
   - a signed facing-sheet separation barrier against self-intersection;
   - smoothness and closeness to R2.

   Every term was gradient-checked.
3. `scripts/apply_original_v1_o4_weight_solution_blender.py` writes a solution
   into a new numbered candidate and refuses to overwrite. It keeps the scene
   stage tag `hgpt_candidate = O4_bind`, which the read-only audit requires, and
   records `hgpt_candidate_revision` plus the parent SHA. (r15–r20 were saved
   before this fix and carry their own name as the tag, so the audit refuses
   them; r21 is r20's exact weights with the correct tag.)

Reproduce r21:

```bat
blender --background --factory-startup ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend --python-exit-code 1 ^
  --python scripts\apply_original_v1_o4_weight_solution_blender.py -- ^
  ORIGINAL_V1_WORK\candidates\weight_solutions\o10.npz ^
  ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_<new>.blend
```

**Candidate history (shoulder subset; R2 = 34 failed checks):**

| Cand. | Solution | Failed | Regressions | Note |
|---|---|---:|---:|---|
| r15 | o3 (projected gradient) | 23 | 17 | first multi-pose solve; self-intersections +64 |
| r16 | o5 (L-BFGS + no-regression bounds) | 23 | 8 | |
| r17 | o6 (+ distance barrier, p99 guard) | 23 | 10 | the distance barrier misses the collisions |
| r18 | o7 (+ signed barrier) | 23 | 16 | p01/p99 regressions |
| r19 | o8 (count-aware p99/p01) | 23 | 6 | |
| **r20 / r21** | **o10** (stronger fold barrier) | **22** | **7** | best; p99 regressions gone |

(o9, a 300 mm zone, was predicted no better and was not applied.)

**r21 exact before → after (R2 → r21):**

| Pose | Shoulder max | Shoulder min | Torso max | Volume | Self-int. | p99 |
|---|---:|---:|---:|---:|---:|---:|
| `press_bottom` | 6.414 → **3.169** | 0.577 → **0.548** | 2.569 → **2.425** | 1.0312 → **1.0301** | 196 → **196** | 1.559 → **1.568** |
| `press_top` | 9.089 → **4.337** | 0.094 → **0.232** | 3.974 → **3.57** | 0.9993 → **0.9958** | 174 → **202** | 1.679 → **1.721** |
| `press_top_rhythm` | 8.283 → **4.323** | 0.143 → **0.236** | 8.317 → **4.062** | 1.1309 → **1.083** | 110 → **110** | 1.977 → **2.013** |
| `squat_bottom` | 8.053 → **3.987** | 0.184 → **0.237** | 4.204 → **4.204** | 0.9627 → **0.9604** | 42 → **33** | 1.745 → **1.776** |
| `pullup_hang` | 8.987 → **4.307** | 0.15 → **0.23** | 3.888 → **3.515** | 1.0055 → **1.0022** | 147 → **121** | 1.675 → **1.705** |
| `pullup_hang_rhythm` | 7.907 → **4.243** | 0.202 → **0.265** | 8.317 → **3.979** | 1.1361 → **1.0892** | 110 → **110** | 1.962 → **1.977** |
| `pullup_top` | 5.169 → **2.697** | 0.694 → **0.674** | 2.086 → **2.018** | 1.0271 → **1.0266** | 216 → **216** | 1.521 → **1.496** |
| `pullup_bar` | 8.987 → **4.307** | 0.15 → **0.23** | 3.888 → **3.515** | 1.0056 → **1.0022** | 146 → **120** | 1.664 → **1.678** |

**Full-coverage evidence for r20 (same weights as r21):**

- Every repair group was run: `shoulder_r20`, `hand_r20` (with grip),
  `hip_r20`, `pushup_r20` and `row_r20`.
- All 14 stressed poses were merged into
  `repair_checks/full_r20_merged_pose_report.json`. `neutral` is omitted; it is
  the rest pose and cannot change with weights.
- Development-blocker failures: **54 → 42** (`full_r20_deformation_acceptance.md`).
- Repair queue (`full_r20_repair_queue.md`):

  | Priority | Owned failures |
  |---|---:|
  | 1 | **3** (was 15) |
  | 2 | 38 |
  | 3 | 3 |

  Ownership is complete. Push-up, row and grip contact show no regressions.

**Remaining Priority 1 blockers:**

- `press_top` self-intersections 202 (gate ≤ 200).
- `press_top_rhythm` p99 2.013 (gate ≤ 2.0).
- `pullup_top` self-intersections 216. Unchanged from R2: 106 elbow/arm pairs
  plus 110 finger pairs, outside the shoulder zone. It probably needs elbow and
  finger work (Priority 2 territory) rather than shoulder weights.

**Remaining comparator regressions (why r21 is not accepted).** The
tolerances are 0.02 for a minimum drop and +5 for self-intersections:

| Pose / region | Metric | R2 | r21 |
|---|---|---:|---:|
| `press_top` | self-intersections | 174 | 202 |
| `press_bottom` / shoulder | region minimum | 0.577 | 0.548 |
| `press_bottom` / torso | region minimum | 0.943 | 0.889 |
| `press_top` / torso | region minimum | 0.886 | 0.837 |
| `press_top` / neck | region minimum | 1.000 | 0.978 |
| `pullup_top` / torso | region minimum | 0.883 | 0.861 |
| `squat_bottom` / arm | region minimum | 0.606 | 0.585 |

Every one of these minima still passes the gate comfortably (≥ 0.548 against
0.15). The optimiser shows this is a genuine multi-pose trade-off. The small
arm weights on the front-chest/axilla vertices that stop overhead tearing move
a 12 mm chest edge by centimetres in other poses. Even very stiff penalties
(3e4) could not hold all bounds together with the collision barriers.

**Weight audit** (`weight_audits/shoulder_weights_shoulder_r21.json`):

- All 976 left/right shoulder vertices have exactly 4 normalised influences
  (R2: 98 had 3).
- Max weight-sum error 4e-8 (R2: 1e-5).
- Cross-side contamination: 0.
- The top-25 weight-gradient edges are unchanged from R2 (torso front,
  outside the zone), so no new abrupt seams were introduced.

**Decision needed from the owner.** This is a genuine decision point, not a
routine step. Either:

- (a) accept that region minima may fall by more than 0.02 when they stay far
  above the gate, making r21's remaining blocker the press_top
  self-intersection (+28); or
- (b) keep the strict rule, in which case the next step is topology.

The weights alone have not removed the acromion buckling.

**Next exact repair task:**

1. Warm-start the optimiser from `o10.npz` and target only `press_top`
   self-intersections (≤ 179) and rhythm p99 (≤ 2.0). One option is to
   restrict the facing-sheet barrier to the acromion/deltoid-cap region with a
   larger search radius.
2. If that fails, add one edge loop across the top of the deltoid
   (first-party topology edit) and re-dump. The optimiser and apply tools work
   on any O4_bind candidate.

The next evidence label is `shoulder_r22`.

### Priority 1 session log — r22–r24 (targeted collisions + support loop)

**Status:**

- Priority 1 is still BLOCKED. No candidate is accepted.
- The accepted baseline remains pinned R2. `DEFORMATION_BASELINE_R2.json`,
  `ORIGINAL_V1_CANDIDATE_STATUS.json`, all thresholds and all approval flags
  are unchanged.
- Production approval remains **false**.
- The 63-bone rig is unchanged; every script refuses any other rig.

**New evidence tooling:**

- `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat <rN> [prior]` runs the full pipeline for
  one candidate:
  - every repair group: `shoulder`, `hand` (with grip), `hip`, `pushup`, `row`;
  - a neutral rest-pose control (`neutral_<rN>`), so all **15** poses are
    covered;
  - `scripts/merge_original_v1_repair_group_reports.py`, which runs the
    committed evaluator and repair queue, then the comparator against pinned
    R2 and against the prior candidate (on common poses).

  Outputs are `repair_checks/full_<rN>_*`.
- `scripts/tritri_original_v1.py`: numpy triangle-triangle intersection test.
  It agrees with Blender's counts to within one pair of the change: press_top
  shoulder +27 triangle pairs vs Blender +28 quad pairs, and the same drop
  pattern in pull-up hang.
- Optimiser additions:
  - `prox_mode="tritri"`: constraints from the triangle pairs that newly
    intersect versus R2, keeping each vertex on its R2 side of the other
    triangle's plane;
  - `--init-dump`;
  - `--r2-report`: bounds, percentiles and volume targets taken from the
    pinned R2 report, for topology-changed meshes;
  - `zone_regions`;
  - `polish_rounds`: collision re-detection interleaved with the 4-influence
    polish.
- `scripts/add_original_v1_o4_shoulder_support_loop_blender.py`: a
  first-party loop cut of the closed, symmetric 120-edge **shoulder-yoke**
  ring. The ring is found from this mesh's own topology; its crossing edges
  are 12–48 mm and run neck/trapezius → acromion.
  - Mesh stays all-quad: 17,946 → 18,066 vertices, 17,944 → 18,064 faces.
  - Original vertex order and positions are verified unchanged.
  - New vertices get averaged endpoint weights (top 4, renormalised) and
    their endpoint's region.

**Candidate lineage and results.** All are full 15-pose evidence against
pinned R2 (54 failed checks). Parent is `…CANDIDATE.blend` (d89dedb5…)
unless stated.

| Cand. | What | SHA-256 | Failed | Regr. vs R2 | P1 owned | Verdict |
|---|---|---|---:|---:|---:|---|
| r20/r21 | o10 (previous session) | 16d5f3fd… (r21) | 42 | 7 | 3 | rejected (best "fewest regressions") |
| r22 | o11 = o10 + tritri collision constraints (`o11.npz` 6a21396d…) | c32eb0ac93b35eed… | 40 | 11 | **1** | rejected: collisions moved to pullup_hang/bar and rhythm; neck and chest minima |
| r23a | loop cut on R2 weights (intermediate, reference for o12) | b0772b4cef72472a… | — | — | — | intermediate only |
| r23b | loop cut on r21/o10 weights (warm start for o12) | 561f796f97c52def… | — | — | — | intermediate only |
| r23 | r23a + o12 re-solve on the looped mesh (`o12.npz` 98173520…) | e2fad42252988643… | 40 | 12 | 1 | **rejected: the support loop does not help** (6 regressions vs r22) |
| r24 | o13 = o11 with neck vertices kept at R2 + collision-checked polish (`o13.npz` e36e4bfc…) | 78de365042c930f8… | 40 | 11 | 1 | rejected; best weights-only balance (vs r22: 1 regression, 11 improvements) |

Reproduce any candidate:

```bat
blender --background --factory-startup <parent>.blend --python-exit-code 1 ^
  --python scripts\apply_original_v1_o4_weight_solution_blender.py -- ^
  ORIGINAL_V1_WORK\candidates\weight_solutions\oNN.npz <new>.blend
```

- The parent is `r23a_loop_R2w` for r23.
- `r23a`/`r23b` come from the loop script run on `…CANDIDATE.blend` and
  `…_r21.blend` respectively.

Re-solve r24:

```bat
python scripts\optimize_original_v1_o4_shoulder_weights.py <dump.npz> o13.npz --preset o13 --init o11.npz
```

The dump comes from `scripts\dump_original_v1_o4_pose_skinning_blender.py` on
the parent. Logs are saved next to each solution
(`weight_solutions/oNN.log`).

**r24 exact before → after (R2 → r24):**

| Pose | Shoulder max | Shoulder min | Torso max | Volume | Self-int. | p99 |
|---|---:|---:|---:|---:|---:|---:|
| `press_bottom` | 6.414 → **3.205** | 0.577 → **0.545** | 2.569 → **2.362** | 1.0312 → **1.0307** | 196 → **196** | 1.559 → **1.559** |
| `press_top` | 9.089 → **4.335** | 0.094 → **0.188** | 3.974 → **3.53** | 0.9993 → **0.9962** | 174 → **181** | 1.679 → **1.688** |
| `press_top_rhythm` | 8.283 → **4.33** | 0.143 → **0.236** | 8.317 → **4.06** | 1.1309 → **1.0837** | 110 → **118** | 1.977 → **1.945** |
| `squat_bottom` | 8.053 → **4.224** | 0.184 → **0.237** | 4.204 → **4.204** | 0.9627 → **0.9607** | 42 → **42** | 1.745 → **1.758** |
| `pullup_hang` | 8.987 → **4.305** | 0.15 → **0.238** | 3.888 → **3.46** | 1.0055 → **1.0027** | 147 → **162** | 1.675 → **1.683** |
| `pullup_hang_rhythm` | 7.907 → **4.245** | 0.202 → **0.269** | 8.317 → **3.974** | 1.1361 → **1.0898** | 110 → **110** | 1.962 → **1.945** |
| `pullup_top` | 5.169 → **2.737** | 0.694 → **0.654** | 2.086 → **1.967** | 1.0271 → **1.027** | 216 → **216** | 1.521 → **1.501** |
| `pullup_bar` | 8.987 → **4.305** | 0.15 → **0.238** | 3.888 → **3.46** | 1.0056 → **1.0027** | 146 → **161** | 1.664 → **1.667** |

**Remaining r24 regressions against R2.** Every one still passes its gate:

| Pose | Metric | R2 → r24 | Gate |
|---|---|---:|---:|
| `press_top` | self-intersections | 174 → 181 | ≤ 200 |
| `press_top_rhythm` | self-intersections | 110 → 118 | ≤ 200 |
| `pullup_hang` | self-intersections | 147 → 162 | ≤ 200 |
| `pullup_bar` | self-intersections | 146 → 161 | ≤ 200 |
| `press_bottom` / shoulder | region minimum | 0.577 → 0.545 | ≥ 0.15 |
| `press_bottom` / torso | region minimum | 0.943 → 0.889 | ≥ 0.15 |
| `press_top` / torso | region minimum | 0.886 → 0.823 | ≥ 0.15 |
| `pullup_hang` / torso | region minimum | 0.891 → 0.870 | ≥ 0.15 |
| `pullup_bar` / torso | region minimum | 0.891 → 0.870 | ≥ 0.15 |
| `pullup_top` / shoulder | region minimum | 0.694 → 0.654 | ≥ 0.15 |
| `pullup_top` / torso | region minimum | 0.883 → 0.860 | ≥ 0.15 |

Push-up, row, hip and grip-contact groups show no regressions for r22–r24.

**The last Priority-1-owned failure is not a shoulder failure (proven).**
`pullup_top` self-intersections are 216 in R2 and in every candidate. A
location probe in Blender maps every intersecting face pair back to rest
positions:

- **110** pairs are hand/finger faces on both sides (rest z < 0.95);
- **106** pairs are faces whose nearest joint is the **elbow**
  (`forearm_l` head z 1.19);
- **none** are at the shoulder.

The repair queue owns this under Priority 1 only because `pullup_top` is a
Priority-1 pose and self-intersection is a pose-level metric. It must be
fixed by elbow-fold and finger work, not by shoulder weights. It is not hidden
or reclassified here; the queue still reports it.

**Conclusions from r15–r24:**

1. Multi-pose weight optimisation clears every shoulder/torso gate: stretch,
   collapse, volume and p99. The remaining shoulder issue is purely the strict
   no-regression comparison.
2. The comparator regressions are a genuine trade-off. Stopping the overhead
   tear needs arm weight on the front-chest/axilla skin, which lowers some
   chest-edge minima in other poses. Removing new acromion/deltoid collisions
   in one overhead pose re-creates them in another (r22: press_top fixed,
   pullup_hang/bar +11).
3. The minimal first-party supporting loop (r23) does not remove the buckling.
   It adds resolution to the fold rather than preventing it.
4. Neck-region vertices must keep R2 weights (r24 removes all neck
   regressions).

**Decision needed from the owner (unchanged, now with more evidence).**
Neither weights nor the minimal topology loop achieve zero comparator
regressions against R2. Options:

- (a) Accept a documented trade-off candidate. r24 is the best balance:
  every Priority-1 gate cleared except the proven elbow/finger `pullup_top`
  collisions. Its remaining regressions are listed above, every one still
  inside its gate. The acceptance tolerances must not be changed silently: if
  approved, record the decision and pin a new numbered baseline, as the R2
  baseline file prescribes.
- (b) Keep the strict rule and try heavier first-party tools, which need
  approval:
  - corrective shape keys driven by upper-arm elevation (currently out of
    scope);
  - a larger shoulder retopology (more than one loop);
  - adding twist/helper bones would change the frozen rig and is **not**
    allowed.

**Priority 2 groundwork (read-only; no hand edits made).** In R2, the hand
failures are identical in `grip`, `curl_peak` and the press poses, because
they share the same finger-closing pose:

| Location | Metric | Weight split |
|---|---|---|
| Ring-MCP knuckle crease (rest ≈ −0.199, 0.039, 0.83) | min **0.070** | ring_01 / hand / metacarpal_ring |
| Index/middle PIP creases (2 mm edges) | min 0.113 / 0.140 | ~0.6/0.4 between phalanges |
| Thumb web | max **5.39** | skin split ~50/50 between `metacarpal_index` and `thumb_01` |
| Push-up wrist crease | min 0.139 | forearm / metacarpal split |

The same exact-LBS optimiser can take a hand zone. The grip poses
(`curl_handle`, `pullup_bar`) must be re-dumped after each candidate, because
their finger closure is solved against the handle. Do not start this until
the Priority-1 decision above is made, per the repair-order rule.

**Next recommended action:**

1. Owner chooses (a) or (b).
2. If (a): run `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat` on the chosen candidate,
   record the decision in the decision log, pin `DEFORMATION_BASELINE_R24.json`,
   then start Priority 2 with the hand-zone optimiser.
3. If (b): prototype elevation-driven corrective shape keys on a candidate
   copy, evaluated by the same full pipeline.

The next labels are `r25` / `shoulder_r25`.

### Owner decision recorded — strict rule kept

The owner kept the strict no-regression rule:

- r24 is **not** accepted and no new baseline is pinned.
  `DEFORMATION_BASELINE_R2.json`, thresholds and approval flags are
  unchanged.
- r24 stays the best **experimental** shoulder candidate, with the trade-offs
  listed above.
- Shoulder-only optimisation stops for now. Heavier shoulder topology and
  pose-driven shape corrections are not authorised.
- The rig stays frozen.
- Work moves to Priority 2 (elbow, hands, fingers, thumb, wrist, grip),
  warm-started from r24 and preserving its shoulder gains.

### Priority 2 session log — r25–r28 (hands / fingers / thumb / wrist / elbow)

**Status:**

- No candidate is accepted under the strict rule. Every candidate built on
  r24 inherits r24's shoulder/torso minima regressions (by owner decision
  these are not being re-optimised).
- Production approval remains **false**.
- Best experimental candidate: **r26**. See the r28 addendum below.

**Ownership check (r24, Blender probe).** Every intersecting face pair was
mapped back to rest positions:

| Pose | Elbow | Hand/finger | Shoulder |
|---|---:|---:|---:|
| `pullup_top` | 106 | 110 | **0** |
| `curl_peak` | 152 (+6 elbow–wrist) | 110 | 0 |
| `curl_handle` | 152 (+6 elbow–wrist) | 108 | 0 |
| `grip` | 42 | 110 | 0 |

All finger pairs are at the **PIP** creases of all four fingers (pinky 32,
the others 26, both hands).

**Tools added** (all first-party, operating only on this candidate's own
weights):

- Optimiser `zone_mode="hand"`:
  - zone = hand/finger/thumb vertices plus a 50 mm forearm wrist band, both
    hands, disjoint from the r24 shoulder zone;
  - permitted bones = existing, plus same-side hand-chain bones whose head
    lies within 40 mm.
- Optimiser `zone_mode="elbow"`: arm vertices within 120 mm of the elbow,
  excluding the shoulder and hand zones; `upperarm`/`forearm` only.
- `tt_resolve`: every current colliding triangle pair must separate
  outward-to-outward, which fixes collisions already present in R2.
- `strict_both`: no-regression bounds are the stricter of the pinned R2
  report and the base candidate.
- `symmetric`: exact left/right symmetry by construction (mirror-averaged
  gradients, iterates and supports).
- `scripts/symmetrize_original_v1_o4_weights.py`: mirror-average an existing
  candidate's weights.

**Symmetry finding.** R2 is exactly symmetric: maximum mirror L1 weight
difference 0.002. r24 was not: 109 vertices above 0.05, max 0.36, because the
earlier optimiser solved each side independently. r25 had 283 vertices above
0.05. Cross-side contamination is **0** in every candidate.

**Candidates.** All have full 15-pose evidence
(`RUN_ORIGINAL_V1_FULL_EVIDENCE.bat`); R2 has 54 failed checks, r24 40.

| Cand. | What | SHA-256 | Failed | Regr. vs R2 | Regr. vs prior | Verdict |
|---|---|---|---:|---:|---|---|
| r25 | r24 + `o14` hand-zone solve (`o14.npz` 2790ce66…) | 27541152… | **8** | 10 | 1 vs r24 (push-up hand max 1.915 → 2.083) | rejected |
| **r26** | r25 mirror-averaged (`sym_r25.npz` c8d3eaa7…) | **ae18941e…** | **8** | 8 | **0 vs r25** (15 improvements) | best experimental |
| r27 | r26 + `o17` symmetric hand solve (`o17.npz` 0aae7b7f…) | 86afebea… | 8 | 8 | 9 vs r26 (hand max 3.495 → 4.248) | rejected |

Solver-only evidence, not promoted to candidates:

- `o16` / `o18` elbow solves: curl_peak elbow collisions oscillate or don't
  move (172 → 158/175/164/170 triangle pairs), and press_top arm minimum
  regresses by 0.03.

**r26 exact before → after (R2 → r26), hand/finger/collisions/grip:**

| Pose | Hand min | Hand max | Finger min | Self-int. | Grip pen. (mm) |
|---|---:|---:|---:|---:|---:|
| `curl_peak` | 0.07 → **0.244** | 5.387 → **3.495** | 0.113 → **0.239** | 268 → **210** | – |
| `press_bottom` | 0.07 → **0.244** | 5.387 → **3.495** | 0.113 → **0.239** | 196 → **138** | – |
| `press_top` | 0.07 → **0.244** | 5.387 → **3.495** | 0.113 → **0.239** | 174 → **128** | – |
| `grip` | 0.07 → **0.244** | 5.387 → **3.495** | 0.113 → **0.239** | 152 → **94** | – |
| `pushup_bottom` | 0.139 → **0.24** | 1.915 → **2.082** | 1.0 → 1.0 | 156 → **142** | – |
| `pullup_top` | 0.07 → **0.244** | 5.387 → **3.495** | 0.113 → **0.239** | 216 → **158** | – |
| `row` | 0.07 → **0.244** | 5.387 → **3.495** | 0.113 → **0.239** | 110 → **52** | – |
| `curl_handle` | 0.334 → 0.337 | 1.514 → 1.457 | 0.086 → **0.234** | 266 → **198** | 5.93 → 5.93 |

r26 remaining development failures (8):

| Priority | Failures |
|---|---|
| 1 | **CLEAR** (0 owned) |
| 2 | `curl_peak` self-intersections 210 (158 elbow + 52 finger); grip penetration 5.93 mm on both hands in `curl_handle` and `pullup_bar` (4 checks) |
| 3 | `lunge` (3, untouched) |

r26 regressions vs R2 (8):

- 5 inherited r24 shoulder/torso minima;
- `press_top` p99 1.679 → 1.751 and `pullup_hang` p99 1.675 → 1.739;
- `pushup_bottom` hand max 1.915 → 2.082.

**Proven blockers that weights cannot fix:**

1. **Grip penetration (5.93 mm, gate 2.0).**
   - The deepest vertices are the **thumb IP crease** (thumb_02/03): 29
     finger-owned vertices are already 4.7 mm inside the handle *before* any
     finger closes.
   - At that point the whole hand is rigid with the forearm, so the positions
     are weight-independent.
   - The pose script's closing search protects only initially-outside
     vertices, so closing the thumb pushes them to 5.93 mm.
   - Fixing it needs either a thumb rest pose clear of the handle placement
     (the thumb bones are part of the frozen rig) or a change to the frozen
     evaluation pose. **Owner decision required;** the evaluation script was
     not changed.
2. **Elbow flexion contact** (`curl_peak` elbow 152–158 pairs). The colliding
   faces are forearm-front vs biceps-front skin 2.6–24 cm apart at rest, in
   genuine contact at about 140° flexion. Two elbow solves (o16, o18) could
   not reduce it. It needs soft-tissue compression, meaning corrective shapes,
   not authorised.
3. **PIP crease residue** (52 pairs after the hand solve, from 110). The
   colliding faces are ~2 mm apart at rest, across the tight crease loop at
   each PIP, folding over each other at the pose's 88° PIP bend. o17 made no
   further progress (106 triangle pairs held flat). A minimal local fix would
   widen or relax the tight crease loop (geometry slide, not new topology);
   not attempted.

`curl_peak` passes the gate if either the elbow or the PIP residue drops by
10 pairs.

**r28 — best experimental candidate.**

- r28 = r26 + `o19`, a symmetric hand re-solve on the r26 base: stricter of
  the R2 and r26 bounds, 0.03 max margin, 10× fold barrier.
  `symmetric: max L1 twin difference 2.8e-16`.
- SHA-256 `68889eefeb5e22e9bf8c5f96209f8b5440a3d11e501313b3b32a06274509515d`.
- Full 15-pose evidence: **8 failed checks**, Priority 1 CLEAR,
  **0 regressions vs r26** (13 improvements), **6 regressions vs R2**:
  - the 5 inherited r24 shoulder/torso minima;
  - `pushup_bottom` hand max 1.915 → 2.067 (inside the 5.0 gate).
- The p99 regressions of r25–r27 are gone.
- Hand max ≈1.95 in the gripping poses (R2 5.39; thumb web relaxed).
- Cross-side contamination 0; exact left/right symmetry in the hand zone.
- PIP-crease residue unchanged (≈104 triangle pairs). This is the third solve
  (o14, o17, o19) on that plateau.

Rebuild r28 (parent r26; r26 comes from r25 with `sym_r25.npz`, r25 from r24
with `o14.npz`):

```bat
blender --background --factory-startup ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r26.blend --python-exit-code 1 ^
  --python scripts\apply_original_v1_o4_weight_solution_blender.py -- ^
  ORIGINAL_V1_WORK\candidates\weight_solutions\o19.npz ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_<new>.blend
```

Verify:

```bat
RUN_ORIGINAL_V1_FULL_EVIDENCE.bat <rN> r26
```

Review artifacts (regenerate with
`python scripts\build_original_v1_candidate_review.py`):

- `ORIGINAL_V1_WORK/candidates/review/candidate_review.md`;
- `candidate_metrics.csv`;
- `candidate_summary.json`.

Local candidate `.blend` files (git-ignored) are in
`C:\Users\Mark\Documents\animation-software\repo\ORIGINAL_V1_WORK\candidates\`.
Each `HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_rNN.json` manifest records its
SHA-256 and parent SHA.

Battery at the r28 checkpoint: 89%, discharging (no AC), runtime estimate
unavailable.

**PIP crease repair (minimal local geometry, evidence-based).** Three weight
solves (o14, o17, o19) plateaued at ~104 PIP-crease triangle pairs.

- A numpy LBS test on r28 weights showed that evenly re-spacing each finger's
  PIP crease rings removes **all** finger/hand collisions in
  grip/curl_peak/press/row: 106 → 0 triangle pairs, and curl_handle 52 → 42.
- `scripts/relax_original_v1_o4_pip_crease_rings_blender.py` does this
  first-party:
  - the mesh's own rings within ±12.5 mm of each PIP head are re-spaced
    evenly between fixed end rings;
  - each vertex slides along its own mesh column (piecewise-linear), so it
    stays on the original surface;
  - no topology, weight, UV, material or rig change; exact mirror symmetry is
    checked.
- **r29a** (intermediate) = r28 relaxed: 672 vertices, max 2.05 mm, SHA-256
  `bec7a83c46c557b438bb6140ba9d8700b93abf894a5afa2c88a9cccf329f1677`.
- With r28's weights the relaxed crease concentrates palm-side compression
  (finger min 0.239 → 0.080 in the numpy test). The weights are therefore
  re-solved on r29a with `o21` (= o20 settings: symmetric, collapse floor
  0.17, max margin 0.02, stricter of the R2 and r29a bounds).
- `o20` (the same settings on the r28 geometry) was stopped unfinished; it is
  superseded.

**r29 result (evaluated).**

- r29 = r29a + `o21`. SHA-256
  `d9b24e75fa6f2eb4c8999787fd925d5986f236691e00c9d251be3f0f061d7574`.
- Full 15-pose evidence: **7 failed checks**, the fewest so far.
  **`curl_peak` now passes**: its PIP-crease collisions are gone, leaving only
  the elbow contact.
- Regressions vs R2: **6**, the same set as r28 (5 inherited r24
  shoulder/torso minima, `pushup_bottom` hand max 1.915 → 2.032).
- Regressions vs r28: **12**, with 11 improvements:
  - finger min 0.239 → 0.193 (0.169 in the handle poses), still far above the
    0.15 gate and R2's 0.113/0.086;
  - `pushup_bottom` self-intersections 144 → 150 (R2 156).
- **Verdict:** r29 is a trade-off against r28, not a strict improvement. It
  removes a gate failure but lowers finger minima that r28 had raised.
  - r28 stays the "no regression vs prior" best.
  - r29 is the "fewest failures" experimental candidate.
  - Neither is accepted; production approval remains false.

**Remaining development failures (r29, 7):**

- grip penetration 5.93 mm × 4: proven weight-independent (thumb IP inside
  the handle before closing). Needs an owner decision on the thumb rest
  pose vs the frozen grip pose script.
- `lunge` × 3: Priority 3, not yet started.

**Next exact action:**

1. Recover r29's finger minima toward r28 while keeping `curl_peak` clear:
   run a symmetric hand re-solve on the r29 base with `lo=0.24` (o19
   settings), warm-started from o21, which gives r30.
2. Evaluate with `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat r30 r29` and compare with
   r28.
3. The push-up hand-max regression (wrist extension) still needs a
   wrist-only solve.
4. Then start Priority 3 (`lunge` pelvis/torso), which is untouched.

**Session stop — battery checkpoint (2026-10-01).**

- `o22` (the r30 finger-minimum recovery) was started on the r29 base and
  **stopped deliberately, unfinished**.
- Battery was 44% and discharging ~1%/min with no AC, too little to finish
  the ~45 min solve plus the ~25 min evidence run. The solver cannot resume
  mid-run, so no partial o22 output exists and none was used.
- All candidates, weight files, logs, evidence and review artifacts up to r29
  are committed.
- No solver or Blender process was left running.

To resume:

```bat
python scripts\optimize_original_v1_o4_shoulder_weights.py <r29 dump.npz> o22.npz --preset o22 --r2-report ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json
```

- The r29 dump comes from `scripts\dump_original_v1_o4_pose_skinning_blender.py`
  on `…_CANDIDATE_r29.blend`.
- Then apply `o22.npz` onto `…_r29.blend`, giving `r30`.
- Then run `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat r30 r29`.
- Compare with both r28 and r29.

**Candidate status at stop:**

| Candidate | Status | Notes |
|---|---|---|
| r24 | experimental (best shoulder) | unchanged |
| r26 | experimental | superseded by r28 |
| r28 | experimental (best "no regression vs prior") | 8 failures; 6 regressions vs R2 |
| r29 | experimental (fewest failures) | 7 failures; 6 regressions vs R2; trade-off vs r28 |

Rejected: r15–r23, r25, r27. None are accepted. **Production approval
remains false.** `DEFORMATION_BASELINE_R2.json`, the thresholds and all
approval flags are unchanged.

**Owner decisions still pending (not taken here):**

1. Grip penetration: the thumb rest pose vs the frozen handle-grip pose
   script (weights cannot fix it; proven above).
2. Elbow flexion contact in `curl_peak`: now within the gate in r29, but
   still weight-limited if it regresses.
3. The r24 shoulder trade-offs, which every later candidate inherits, keep
   strict acceptance impossible without new authorised shoulder tools.

Battery at final checkpoint: 44%, discharging (no AC).

**Earlier resume steps (kept for reference), if r29 had not been evaluated:**

1. If `weight_solutions/o21.npz` is missing, re-run:

   ```bat
   python scripts\optimize_original_v1_o4_shoulder_weights.py <r29a dump.npz> o21.npz --preset o21 --r2-report ORIGINAL_V1_WORK\candidates\pose_test_report_r2.json
   ```

   The dump comes from `scripts\dump_original_v1_o4_pose_skinning_blender.py`
   on `…_r29a_pip_relax.blend`.
2. Apply `o21.npz` onto `…_r29a_pip_relax.blend`, giving
   `…_CANDIDATE_r29.blend`.
3. Run `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat r29 r28`.
4. Accept r29 as the new best experimental candidate only if it has no
   regression vs r28. Watch `curl_peak` (expected to pass ≤ 200), `pushup`
   self-intersections (o21 round 1 raised push-up wrist pairs 74 → 100 triangle
   pairs) and the finger minima.

Battery at this checkpoint: 66%, discharging (no AC), falling ~1%/min. Battery at the r29 checkpoint: 54%, discharging (no AC).

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

## Repo-side r30 preparation — 2026-10-01

Prepared without opening or modifying Blender candidates:

- `RUN_ORIGINAL_V1_R30.bat` now automates the exact r29 -> r30 step already
  specified above: dump r29, solve `o22` warm-started from `o21`, apply into
  a new r30 candidate, run all 15 evidence poses, compare r30 with R2/r29/r28,
  rebuild the generated candidate review and collect a compact visual review.
- `scripts/collect_original_v1_review_images.py` copies 17 selected renders
  from the full evidence directories into
  `ORIGINAL_V1_WORK/candidates/review/visual_r30/` with a SHA-256 manifest.
  This makes the latest state reviewable from GitHub/phone without committing
  every diagnostic render.

These helpers do not modify thresholds, the pinned R2 baseline, approval flags,
existing candidate assets, rig structure or exercise pose definitions. They
only make the already-authorised next experiment deterministic and easier to
review. The generated r30 candidate must still be judged by the unchanged
comparators and remains non-production unless separately approved.

## Repo-side remaining-blocker diagnostics — 2026-10-01

Prepared after the battery stop, without modifying any Blender candidate:

- \`scripts/analyze_original_v1_pose_dump.py\` reads a temporary pose-skinning
  dump and reports the exact worst mesh edges, rest/posed midpoints, mirror
  partner and current top bone weights for:
  - \`pushup_bottom / hand / max\`;
  - \`lunge / pelvis / max\`;
  - \`lunge / torso / min\`;
  - \`lunge / torso / max\`.
- \`scripts/probe_original_v1_grip_penetration_blender.py\` measures
  \`curl_handle\` and \`pullup_bar\` before and after the existing finger-close
  solve, including the deepest vertices, regions, weights and handle frames.
  This is specifically intended to distinguish a rest-pose/handle-placement
  conflict from a skin-weight problem without relaxing the 2 mm gate.
- \`RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat <rN>\` runs both probes
  read-only and deletes its temporary NPZ dump. It writes only compact
  JSON/Markdown evidence under
  \`repair_checks/remaining_diagnostics_<rN>/\`.

These tools do not author a repair. They make the next wrist/grip/lunge change
evidence-led and local, and preserve the current R2 baseline and all thresholds.

After r30 evidence is complete, run:

\`\`\`bat
RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat r30
\`\`\`

If r30 is rejected and work remains on r29, use \`r29\` instead. Do not use a
diagnostic result to mark a candidate accepted; it only identifies where the
next edit should be made.

### Resume/provenance safeguards added after the battery stop

- `scripts/verify_original_v1_local_candidate.py` now checks a local
  git-ignored candidate against its committed JSON manifest before long work.
- `RUN_ORIGINAL_V1_R30.bat` verifies the exact r29 SHA-256 before starting
  o22 and safely regenerates its disposable pose dump if an interrupted session
  left one behind. It still refuses to overwrite any existing o22 solution or
  r30 candidate.
- the r30 runner now also writes a deterministic trial summary against both r29 and r28, classifying only experimental comparison status (strict improvement / non-regressing / trade-off); it never sets production approval.
- `RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat` also verifies the selected
  local candidate hash before collecting evidence.
- new skinning dumps record the exact source candidate SHA-256 and file size;
  the edge diagnostic carries that hash into its JSON/Markdown output.

This is intended to prevent stale-local-file drift and wasted battery/compute.
It does not change any candidate, optimiser thresholds, acceptance limits or
promotion state.

## Next Blender session

Current state entering the next laptop session:

- Priority 1 shoulder work is clear at the development gate in the current
  experimental lineage; do not restart the earlier shoulder search.
- r28 remains the best no-regression-vs-prior experimental hand candidate.
- r29 has the fewest development failures (**7**) and clears `curl_peak`, but
  trades away some finger minimum margin relative to r28.
- production approval remains false.

Run this first:

```bat
RUN_ORIGINAL_V1_R30.bat
```

Then inspect the generated R2/r29/r28 comparisons and the compact
`visual_r30` review before deciding whether r30 supersedes either r28 or r29.

If r30 is acceptable under the existing gates, continue in this order:

1. isolate the `pushup_bottom` wrist-extension hand-max regression with a
   wrist-only solve; do not reopen the whole hand zone unnecessarily;
2. resolve the proven weight-independent 5.93 mm grip penetration by reviewing
   the ORIGINAL-v1 thumb rest pose versus the frozen grip pose script — do not
   hide it by relaxing tolerance;
3. start Priority 3 `lunge` pelvis/torso work, which remains untouched;
4. only after those development blockers are resolved, proceed to production
   profile, anatomy, garment, runtime-contact and release-approval gates.

Do not spend the next session on new exercise features, facial/material polish,
or unrelated third-party migration work.

The immediate objective remains:

> reduce the remaining development-blocker failures without weakening the gates,
> while keeping ORIGINAL v1 independently authored and preserving the clean
> standalone runtime boundary.


## Shared production-control pickup — 2026-10-01

The authoritative high-level roadmap is now
`docs/ORIGINAL_V1_HIGH_DETAIL_MASTER_PLAN.md`. Read latest
`ORIGINAL_V1_HIGH_DETAIL_STATUS.json`, generated
`docs/ORIGINAL_V1_DAILY_STATUS.md` and `ORIGINAL_V1_CANDIDATE_LEDGER.json`.
The old `ORIGINAL_V1_CANDIDATE_STATUS.json` intentionally remains the verified
R2/export checkpoint contract; its shoulder-first instruction is historical.
The new dashboard recomputes the complete r29 evidence: **7 failures**, four grip
penetrations and three lunge failures, with **6 separate strict regressions vs R2**.
It preserves r28/r29 comparisons and every rejected experimental checkpoint.

Use `RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat`, then `RUN_ORIGINAL_V1_NEXT.bat`.
`PREFLIGHT_CLAUDE_ORIGINAL_V1.bat` delegates to the new preflight. Next remains
`RUN_ORIGINAL_V1_R30.bat`; no r30/o22 output has been produced by cloud preparation.
Follow `docs/ORIGINAL_V1_PRODUCTION_CONTROL_QUICKSTART.md` and the Phase 3 packages.

REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. The earlier blanket owner-decision
wording for grip is superseded for safe read-only diagnosis and reversible local
geometry experiments authorised by the owner. Frozen rig rest, handle/pose or gate
changes still require a scoped evidence-backed decision. Never change them to
manufacture a pass; continue wrist/lunge and other safe work while such a decision
is unresolved. Routine image review never pauses autonomous work.

Prepared tools/specs: phase 3B–3E and 5A–5G packages, full anatomy and visual-board
specifications, Windows session checks, mesh/weight snapshot/change audits, actual
image source manifests/comparison SVGs, and fail-closed future production eligibility.
The pose renderer now records source SHA/camera/settings/image hashes; metrics and
stress-pose definitions are unchanged. Existing local renders without those source
manifests stay historical and must be recaptured under fresh labels for verified
comparison. Compact repair coverage is not full milestone view coverage.

No geometry, weights, candidate binaries, rig/rest, R2, threshold/tolerance,
production flags, existing GLBs or runtime code was changed. The Phase 5 packages
are preparation only. Windows/Blender execution and real runtime integration remain
laptop/future gates; cloud tests do not close them.

### Production-control verification evidence

- Full Python unittest discovery: **63 passed**.
- Generated high-detail status/ledger/dashboard exact reproduction: **PASS**.
- Pinned R2 integrity: **PASS**; original R2/export status contract: **PASS**.
- Existing bare/dressed candidate GLB structural audits: **PASS**.
- Documentation manifest/hygiene and diff whitespace: **PASS**.
- ORIGINAL-v1 Python syntax and unchanged stress-pose definition AST: **PASS**.
- Windows preflight APIs, Blender captures/snapshots and real runtime: **NOT RUN**
  in cloud; they remain their own execution gates.

Prepared A–M outputs and their remaining execution boundaries are ticked in the
master plan. Automated CI now checks production-control safety cases, exact
regeneration, frozen baseline, candidate/export structure and doc classification.
The r30 runner calls session preflight and regenerates high-detail status after
successful evidence collection. Full-evidence iteration now stops immediately if
any group fails, preventing a later group from concealing an earlier failure.
No completed r30 exists and current r29 remains experimental with seven blockers.

### GPT production-control follow-up — 2026-10-01

Live source HEAD checked: `753a96d88c3ebd5a64c972633f18affe333b4d0b`.
Model state remains experimental r29 / seven development failures; R2 and gates
remain frozen. Corrected the full-evidence fail-fast behavior: measured inherited
regressions are report-only during collection, while execution errors still stop.
Direct targeted checks remain strict. New full merges require complete six-group
source-bound evidence and reject conflicting overlapping poses, mixed script or
candidate identities, and output collisions. Repeated status generation now retains
new incomplete candidates even after writing their ledger entries. 72 Python tests
pass; no laptop/Blender execution or new candidate result is claimed.

### Interrupted-run inspector — 2026-10-01

Prepared `scripts/inspect_original_v1_interrupted_run.py` for an already-created
numbered candidate. It verifies local blend/solution/parent identities, reports
verified versus missing evidence groups and prints existing capture/merge commands.
It never mutates outputs, reruns the optimiser or claims environment authorization.
Incomplete/conflicting groups and full-output collisions stop instructions while
preserving files. The Phase 3B package and shared quickstart explain pickup.
78 Python tests pass; the preceding evidence-runner commit also passed GitHub
production-control CI. Current candidate remains r29; r30 is still unexecuted here.

### Candidate source-chain and byte preservation — 2026-10-01

Live source HEAD: `0f83d1ec4612789344f9dc00119425423e2473ce`. New full candidates
from r30 onward require the merger's source receipt and committed six-group report /
render-source JSON pairs. Status recomputes source hashes, candidate/script identity,
coverage, overlapping metrics and exact merged-row agreement before selection.
Historical pre-r30 evidence remains unchanged. Cloud numeric lineage verification
does not imply visual inspection of local full-resolution PNGs.

Added targeted Git attributes preserving ORIGINAL-v1 evidence/JSON and frozen rig
source bytes. A Git fixture with core.autocrlf=true reproduced hash-changing newline
conversion before this fix and proves byte-preserving add/checkout afterward.
No geometry, weights, rig, pose definitions, thresholds or R2 baseline changed.

Validation: 85 Python tests pass; exact generated r29 status, pinned R2, existing
candidate GLB structural audit and repository documentation hygiene remain valid.
Real r30 creation/rendering and Windows Blender execution remain laptop tasks.

### Full milestone visual capture preparation — 2026-10-01

Live source HEAD checked: `a04b9041e7ba77d292b94e406dd539ccb2d5d5cd`. Prepared
`RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat`, a deterministic 57-view plan and opt-in
capture/publishing mode. The existing stress renderer gains camera-only milestone
mode after the frozen metrics/pose section. Original pose definitions, candidate
geometry/weights, rig, R2 and gates remain unchanged. The runner captures bare
neutral/rear/anatomy/exercise views, guards fixed whole-body framing against crop,
verifies source/image identities and creates a phone-friendly review README.

Published compact/milestone snapshots are checked against original capture manifests
and image bytes, then appear in the daily dashboard as pending NON-BLOCKING reviews.
Milestone comparison boards use actual copied images and preserve capture mismatch
warnings. 92 Python tests pass; no actual milestone renders are claimed. Blender
execution/camera usefulness still require the laptop. r29 remains experimental with
seven development failures. The next deformation action remains RUN r30.

### Mesh/weight audit identity hardening — 2026-10-01

Live source HEAD: `24c7fddd96a9ec8832e0237444962370f039f881`. Snapshot schema 2
now records 63 bone rest records/roll matrices, rig/body coordinate frames, scene
unit scale and ignored non-deform groups. The audit requires exact parent/child
policy hashes, metre units and unchanged frames/rig-rest identity before local
deltas. Unknown weight bones, invalid/non-finite policy limits and invalid IDs
are refused. Parent-and-child region masks prevent relabelling distant edits out
of scope; region-label changes remain visible. These tools only collect evidence.
No model/rig/gate/baseline changes or production approval occur. Preserve earlier
snapshot formats as history and export new files; Blender execution remains local.

Validation: 99 Python tests pass; generated status still verifies r29 / seven
failures. The preceding milestone-capture commit passed both GitHub checks.

### Intermediate phase exit / replay preparation — 2026-10-01

Live source HEAD checked: `02364bf6aac1b111f8d1fccbe74e65729cfaf178`. Added explicit
Phase 4–11 exit contracts and INCOMPLETE template mode. Empty PASS markers, missing
checks, failing/duplicate checks, unbound evidence, wrong identities and external
paths cannot complete a phase. Phase 12 remains reserved for final production gates.

Prepared the Phase 4 work package and source-bound 15-pose numeric replay checker.
Metrics-only capture reuses the existing Blender renderer through the established
preflight/capture checks, emits no fake review images and never saves the Blend.
Replay requires matching candidate/script/Blender/invocation identities, complete
coverage and exact metrics. Frozen pose/metric functions, rig, gates and R2 remain
unchanged. 119 Python tests pass; actual Blender replay remains unexecuted here.
r29 remains EXPERIMENTAL with seven development failures; next action remains r30.

### Final export / promotion evidence binding — 2026-10-01

Live source HEAD checked: `9f5dda6d25e2ddff118e234c6377bbd0c97906b6`. The future
promotion verifier now requires exactly two distinct bare/dressed exports and
the same content/lineage inventory in every gate and the explicit owner record.
Changing export bytes invalidates earlier evidence even with an unchanged Blend
SHA. Check IDs and source references must be unique; each check binds verified
raw evidence listed in its gate. Commands must be text and timestamps must be
ISO with a timezone. Added INCOMPLETE packet/report template mode; it executes
no gates and never infers acceptance. Contract verification does not replace
domain tools or authenticate the owner. Routine review remains non-blocking.

Validation: all 129 Python tests pass; template creation and subsequent refusal
were exercised, generated r29 state and pinned R2 remain valid. No candidate,
geometry, weights, pose definition, frozen structure or gate threshold changed.
Actual model execution remains on the laptop; next task remains RUN r30.

### Staged GPT preparation: Stage 1 diagnostic brief — 2026-10-01

Live source HEAD checked: `a44ce05468feb3b46f36a865a120a27bd790c4be`. Read the master
plan and prepared a source-verified Phase 3 brief from the existing grip/edge
probes. The remaining-diagnostics runner now emits it as step 4, without another
Blender run. It records exact measured pre/post-close penetration, contact counts,
handle frames, extreme edges and inspection IDs; candidate/script identities,
required coverage and agreement with full rounded metrics are checked. It does
not infer causes, authorise vertex masks, edit models or claim visual evidence.

139 Python tests pass. Without actual probe files the utility returns STOP and
writes no fabricated report. Real Windows/Blender probes remain unexecuted here.
Generated state remains experimental r29 / seven blockers; R2 remains pinned.
Next GPT preparation stage: candidate-bound local edit/audit policy templates.
Next actual deformation action remains RUN r30 on the laptop.

### Staged GPT preparation: Stage 2 local intent/audit drafts — 2026-10-01

Live source HEAD checked: `92bc122b5f618fe0b789191a4a5d5df19a6db671`. Added a
deterministic preparation generator for 3C, 3D and 3E using the existing diagnostic
validation and mesh/weight audit tools. Generated r29 example folders under
`ORIGINAL_V1_WORK/candidates/repair_preparation/`. Each binds the exact parent,
leaves child hash/correspondence/permission lists incomplete, preserves original
draft hashes and records AWAITING_PROBES honestly. Verified probe IDs, when present,
remain inspection references; they never populate edit permissions automatically.

Before editing, record a separate minimal local intent. Afterwards link the actual
child/operation history and audit the same intended mask; never broaden permission
retrospectively. Drafts cannot act as completed audit policies. Regenerate for the
post-hand-recovery continuation candidate; r29 drafts do not bypass r30.

149 Python tests pass. No Blender work, mesh/weight changes, candidate acceptance,
phase completion or baseline/gate change occurs. Current model remains experimental
r29 / seven blockers. Next GPT preparation stage: Phase 6–11 execution packages.
Next actual deformation task remains RUN r30 on the laptop.

### Staged GPT preparation: Stage 3 Phase 6–11 packages — 2026-10-01

Live source HEAD checked: `61689f5119aab4ee619940ddfabe9176201f03b5`. Prepared six
later-phase execution packages plus a shared contract and tooling-readiness table.
Each defines entry/dependencies, permitted/frozen scope, real tests/renders,
regression/rejection conditions, exact exit-check IDs, publication and continuation
while routine reviews remain pending. No later phase is executed or marked complete.

Inspected scripts/CLI coverage: full pose/milestone capture is bare only; early
shorts construction uses nearest-body weights; old GLB export names can overwrite
history; scaffold/structural/browser audits have limited scope. Packages do not
misrepresent these as dressed, production topology, continuous or runtime gates.
Missing domain tools remain explicit GPT preparation tasks. Model-branch application
code is not transferred; candidate runtime testing must use an isolated fixture and
its live commit/policy, while production promotion stays in Phase 12.

Verified package check coverage against the executable exit contract, real command
paths/flags/group names, deterministic current status, pinned R2 and documentation
hygiene. Existing 149-test suite remains passing from Stage 2; this stage is docs
only and adds no executable behaviour. Current model remains experimental r29 / seven
blockers, next laptop task RUN r30. Next GPT tooling stage: raw-snapshot surface audit.

### Staged GPT preparation: Stage 4 raw surface audit — 2026-10-01

Live source HEAD checked: `12fa9307ba1611fe6a5f4da3c8c0e4c5c1e689cb`. Added a
standard-Python, read-only raw schema-2 surface audit with candidate-manifest binding
and collision-refusing JSON/Markdown output. It reports edge incidence, vertex-link
pinches, winding conflicts, connected shells, signed-volume hints, duplicate/repeated
faces, degeneracy/nonplanarity, raw unused/coincident vertices and explicit reflected
coordinate/face symmetry coverage. Exact IDs/regions and diagnostic precision are
preserved; no nearest-surface matching, model repair, gate PASS or approval occurs.

Actual shading normals, self-intersection, joint-support/anatomy, posed deformation
and garment/runtime checks remain unresolved. No actual candidate snapshot/report
is claimed. A synthetic 10,000-face grid tested runtime scaling only, without model
evidence. Raw snapshots still require Blender on the laptop.

168 Python tests pass, including 19 surface/CLI cases with known defects, source
hashes, collisions, aliases and invalid inputs. Generated state, pinned R2 and
documentation hygiene verify unchanged. Current model remains experimental r29 /
seven blockers; next actual deformation task RUN r30. Next GPT tooling stage:
revision-isolated candidate GLB export preparation.

### Staged GPT preparation: Stage 5 isolated candidate exports — 2026-10-01

Live source HEAD checked: `a52b71660a8c7a181eec3291c705dde44efa3034`.
Prepared a revision-isolated REST bare/dressed exporter using the existing Blender
script, exact source manifest/candidate/exporter hashes, explicit stock settings,
GLB identity extras, output collision refusal and scene restoration. Added a
laptop runner, evidence-only preflight and standalone receipt verification using
the existing structural GLB auditor. Historical shared exports remain untouched;
old no-argument export now refuses. See `work_packages/CANDIDATE_EXPORT_PROTOCOL.md`.

Source-byte preservation now includes ORIGINAL-v1 Python files so Windows/cloud
hashes agree without newline conversion. Frozen pose content, rig, R2, geometry,
weights and thresholds are unchanged. Preserve existing laptop work; the protocol
explains safe fresh-checkout handling of already-converted source files.

182 Python tests pass, including 13 export tests with mocked Blender REST/selection
and failure restoration, collision/identity/settings checks, and a Git autocrlf
byte round trip. Actual Blender capture, bundled-exporter compatibility and repeat
export determinism are unexecuted. No actual new GLBs, images, production gate or
model-phase completion is claimed. Current model remains EXPERIMENTAL r29 / seven
blockers; next actual deformation task RUN r30. Next GPT preparation stage:
candidate-bound dressed evidence tooling.

### Staged GPT preparation: Stage 6 raw garment evidence — 2026-10-01

Live source HEAD checked: `17c59e47a61f79e3f4f44cf940374b4c6bc34c4a`.
Extended the existing schema-2 snapshot script with explicit --garment capture;
body remains the default. Shared capture code records exact named mesh/scope,
source manifest/candidate/script/helper hashes, source commit/command/time, raw
non-deform coverage weights and partial ordered MASK/ARMATURE modifier settings.
Added standard-Python same-candidate body/garment pair verification and raw-weight
diagnostics; reuse existing surface/change audits rather than inventing duplicates.
Different garment/rig coordinate frames leave cross-side diagnosis unresolved.

See `work_packages/GARMENT_RAW_EVIDENCE_PROTOCOL.md` for exact laptop commands,
source preservation and explicit garment/frozen-body policy requirements. No actual
candidate snapshots, posed clearance, dressed images, garment construction or
Phase 7 completion are claimed. Full evaluated modifiers/shape keys/normals, actual
Blender API compatibility and dressed contact/motion still need separate evidence.

198 Python tests pass, including 16 garment cases covering raw capture/wrapper,
missing garments, source/candidate/rig mismatches, mask rows, nonfinite weights,
coordinate frames, receipt hashes and output preservation. Generated state,
pinned R2, frozen pose/rig and historical exports remain unchanged. Current model
remains EXPERIMENTAL r29 / seven development blockers; next laptop task RUN r30.
Next GPT preparation: evaluated dressed pose/contact and matched review capture.


### Staged GPT preparation: Stage 7 evaluated dressed evidence — 2026-10-01

Live source HEAD checked before this stage: `58ce9706efb5dc4abe733b68cb319536321889cf`.
Prepared a Blender-only evaluated body/garment evidence capture that invokes the
authoritative stress-pose script in metrics-only mode and reuses its returned
`POSES` functions directly. No pose definitions, R2 baseline, gates, rig/rest,
candidate assets or approval flags are changed. All 15 static poses record raw
body/garment cross-surface intersection counts, bidirectional minimum surface
distances, garment floor evidence and a pose-state hash while the body visibility
mask is disabled for clearance evaluation.

The same execution captures matched bare/dressed real-image pairs with one fixed
camera state per pair: neutral front/rear/side/3/4, waist/hem/seat close-ups and
clothing-relevant exercise extrema. A standard-Python verifier binds candidate,
raw Stage 6 pair, source scripts, pose evidence and image bytes and refuses
mismatched camera pairs, incomplete pose/view coverage, non-finite metrics,
candidate drift, output collisions or any approval/phase-complete claim.

See `work_packages/DRESSED_EVALUATED_EVIDENCE_PROTOCOL.md` and
`RUN_ORIGINAL_V1_DRESSED_EVIDENCE.bat`. Eight fail-closed unit cases cover the
pure verifier; Blender-facing execution remains unrun here and must occur on the
laptop against real candidate bytes. Raw intersection/distance evidence is not
legitimate-contact classification and does not pass Phase 7. Continuous dressed
motion, full modifier/shape-key/custom-normal inventory, garment provenance and
owner acceptance remain open. Current model remains EXPERIMENTAL r29; next actual
deformation task remains RUN r30. Next GPT preparation: continuous dressed
range/contact sampling and explicit per-frame contact classification.


### Staged GPT preparation: Stage 8 continuous dressed range/contact — 2026-10-01

Live branch was rechecked after Stage 7 before this work. Added
`ORIGINAL_V1_DRESSED_RANGE_PLAN.json`, a Blender-only sampled range capture,
a standard-Python fail-closed verifier/classification tool, tests and
`RUN_ORIGINAL_V1_DRESSED_RANGE.bat`. The sampler reuses only authoritative
frozen stress-pose waypoint states and interpolates armature/bone transforms with
linear translation/scale plus quaternion slerp. Six project-owned paths are
sampled at 21 points per segment with shared endpoints de-duplicated.

Each sample preserves exact body/garment intersecting face pairs and pair hash,
bidirectional nearest-surface distances, floor-penetrating body/garment vertex
IDs, near-floor vertex IDs and a pose-state hash. Body masking is disabled for
measurement. The generated contact-classification record represents every sample
and domain; real findings default to UNCLASSIFIED. LEGITIMATE_CONTACT and
UNEXPLAINED_DEFECT require source-bound evidence notes and cannot alter raw IDs,
counts or hashes. No classification grants a production PASS.

The plan explicitly refuses to fabricate continuous push-up motion because the
frozen set has no compatible top/support endpoint, and it does not invent moving
equipment transforms for curl/pull-up. Those remain open for independently authored
or real-runtime evidence. This is finite model-range sampling, not proof of runtime
biomechanics or unsampled intervals. Phase 9 remains NOT STARTED. Current model is
still EXPERIMENTAL r29; next actual deformation action remains RUN r30.


### Staged GPT preparation: Stage 9 first-party contact source bridge — 2026-10-01

Rechecked the live model branch after Stage 8, then inspected the existing
project-owned push-up, curl, pull-up and equipment attachment sources. The missing
continuous-contact semantics already exist in the exercise/runtime layer, so this
stage does not duplicate them as new Blender poses or trajectories.

Added `ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.json`,
`scripts/original_v1_contact_source_bridge.py`, fail-closed tests,
`RUN_ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.bat` and the protocol under work_packages.
The bridge verifies exact current source bytes and authored facts: push-up Top and
Bottom root states with world-locked floor hands and planted toes; bicep-curl
dumbbells attached rigidly to each real evaluated hand matrix through the grip
socket; and pull-up motion against a static squat-rack with equipment socket locks.

This is source evidence only. `runtime_executed=false`, no candidate/model asset is
changed, no Blender stress-pose definition is added, no old V-series implementation
data is used, and no Phase 9/10 PASS is inferred. The model branch is not declared
the live standalone runtime. Phase 10 must rediscover the actual runtime commit,
compare these semantics, then capture the real solver/equipment/contact frames.
Current model remains EXPERIMENTAL r29; next actual deformation action remains RUN r30.


### Staged GPT preparation: Stage 10 live runtime discovery/harness — 2026-10-01

Resolved the standalone authority from its own CURRENT_HANDOFF/PROJECT_AUTHORITY:
`work/standalone-first-party-audit-20260927` is the active runtime branch; the
separate handoff branch is not a development target. At discovery its live HEAD
was `e3a7d915079f018acbfd8198655f623ea7831fbf`, 25 commits beyond the handoff's
last fully verified `27ac3697d47bbcf32c9e94e674707f8e4b1eb5c3` checkpoint.

Current runtime source/contract shows canonical v4 active even though some handoff
prose still says v3 is live. Source plus executable contracts take precedence.
The exact live runtime HEAD is not green: Standalone prep run 36739619686 failed
two `firstPartySkeleton.parity.test.ts` assertions at 0.02 m root/root-tail
parity after v4 reactivation; downstream full suite/build/audits did not run and
browser smoke run 36739619753 was cancelled. No test/threshold was weakened.

Prepared `ORIGINAL_V1_RUNTIME_DISCOVERY_CONTRACT.json`,
`scripts/original_v1_runtime_discovery.py`, fail-closed tests,
`RUN_ORIGINAL_V1_RUNTIME_DISCOVERY.bat`,
`ORIGINAL_V1_RUNTIME_EVIDENCE_TEMPLATE.json` and
`work_packages/RUNTIME_DISCOVERY_HARNESS_PROTOCOL.md`. Discovery requires a
separate clean runtime checkout at current remote HEAD, reruns Stage 9 contact
semantics against it, verifies actual v4 source/contract state and hashes all
cross-branch sources. A changed runtime HEAD gets UNKNOWN CI rather than inheriting
the snapshot. The evidence template is INCOMPLETE only. No runtime code, model
asset, rig, threshold or approval state was changed. Current model remains
EXPERIMENTAL r29; next actual deformation action remains RUN r30.


### Staged GPT preparation: Stage 11 deterministic automated visual QA — 2026-10-01

Rechecked the live model branch after Stage 10 and prepared a first-party visual
QA layer without changing model/rig/poses or requiring an external vision model.
Added `ORIGINAL_V1_VISUAL_QA_CONTRACT.json`,
`ORIGINAL_V1_VISUAL_QA_COVERAGE_PLAN.json`,
`ORIGINAL_V1_VISUAL_QA_CAPTURE_TEMPLATE.json`, an empty explicit reference
inventory, `scripts/original_v1_visual_qa.py`, fail-closed fixture tests,
`RUN_ORIGINAL_V1_VISUAL_QA.bat` and `work_packages/VISUAL_QA_PROTOCOL.md`.

Actual source PNGs remain immutable owner-review evidence. Automated checks use
separate project-owned 8-bit PGM masks bound to the same candidate/asset/runtime,
source-image and capture identities. The standard-library detector verifies hashes
and dimensions, fails missing expected-visible masks or prohibited edge crops,
measures connected components and neutral horizontal symmetry, and computes
matched silhouette IoU/XOR/occupancy/centroid/bounding-box deltas. Unequal camera,
view, pose/frame, renderer, colour-management, crop or dressed settings produce
CAPTURE_MISMATCH and no regression metrics. Unsupported domains remain UNKNOWN.

The reference inventory is empty by design and deny-by-default: only versioned
actual project-authored captures may later be added; pending owner review is not
acceptance and references are never silently replaced. Synthetic masks are test
fixtures only. The existing 57-view board remains model visibility planning, not
runtime proof. Real Stage 11 execution still waits for Phase 10 exact runtime/model
assets and frames. No production approval is inferred. Current model remains
EXPERIMENTAL r29; next actual deformation action remains RUN r30.


### Staged GPT preparation: Stage 12 final production freeze/promotion gate — 2026-10-01

Rechecked the live model branch after Stage 11 and prepared the final fail-closed
release boundary without changing any asset, baseline, rig, runtime allowlist or
approval flag. The existing technical promotion verifier is retained and hardened:
its eligibility receipt now binds the exact promotion-packet path/SHA, final
candidate SHA and exact target runtime commit, with unit coverage.

Added `ORIGINAL_V1_FINAL_FREEZE_CONTRACT.json`,
`scripts/verify_original_v1_final_freeze.py`, fail-closed tests,
`RUN_ORIGINAL_V1_FINAL_FREEZE_CHECK.bat` and
`work_packages/PHASE_12_PRODUCTION_FREEZE.md`. Final-freeze verification requires
the exact successful promotion packet+receipt, exact bare/dressed asset bytes,
every Phase 4-11 exit report, Phase 9 source commit equal to the final model commit,
Phase 10/11 bound to the final runtime commit, current zero-failure/no-regression
state, and a separate explicit OWNER AUTHORISED PRODUCTION FREEZE record that binds
the exact assets/runtime/promotion evidence. OWNER ACCEPTED visual approval remains
a separate prerequisite inside the promotion packet.

A successful final-freeze receipt still has `production_approved=false` and does
not edit a loader/allowlist or merge branches. Actual production activation must
be a separate controlled owner-authorised asset-only operation on the verified
standalone runtime, followed by exact-SHA standalone/browser/release/first-party
audits and an immutable release freeze record. Current r29 cannot pass this gate:
Phase 3 remains active, failures/regressions remain and Phases 4-11/runtime/owner
final evidence are incomplete. Next actual deformation action remains RUN r30.


### Post-preparation execution orchestration — 2026-10-01

After completing repository-side preparation Stages 1-12, added a single
read-only cross-phase execution map rather than inventing a Roadmap Phase 13.
`ORIGINAL_V1_EXECUTION_ORCHESTRATION.json` maps the real critical path from the
current 3B/r30 work through Phase 12 and the separate controlled release. The
runner `RUN_ORIGINAL_V1_EXECUTION_PLAN.bat` performs normal session preflight,
checks generated status, validates all Stage 1-12 support artifacts and prints
the current critical-path node, relevant prepared support and explicitly safe
parallel work. It does not launch Blender, edit evidence, choose subjective
repairs, complete phases or promote production.

The current expected selector agreement is still `RUN_ORIGINAL_V1_R30.bat` for
r29 / Phase 3B. If live generated status or the existing selector differs, the
orchestrator stops instead of recommending stale work. Re-run it after each
meaningful committed candidate/evidence transition. No model geometry, weights,
rig, R2 baseline, stress poses, thresholds or runtime branch were changed.


### Remaining deterministic tooling-gap closure — 2026-10-01

After the Stage 1-12 preparation/orchestration work, completed the remaining
high-value repo-side gaps that could reduce future Blender/session overhead:

- Phase 5: machine-readable ordered 5A-5G anatomy execution plan plus regional
  template/verifier/runner. Each region binds exact scope, focused poses, required
  views/artifacts/checks and 5B-5G must inherit from the previous verified regional
  candidate.
- Phase 6: authored joint-support template plus one-command raw/evaluated surface
  capture for manifold/symmetry, evaluated normals and exact non-adjacent BVH
  self-intersections. Joint support IDs are deliberately not inferred.
- Phase 7: detailed body/garment modifier, shape-key/driver, custom-normal,
  group/attribute/library/material/image scene capture plus explicit clean-room
  garment operation-history verifier and one-command future runner.
- Phase 8: strict numeric-only owned material provenance, shader/world/light/camera/
  renderer/colour-management capture, fixed real-render coverage plan and
  one-command scene verifier. Image textures/HDRIs/linked material resources are
  rejected; readability remains a real review.
- Visual QA: project-owned standard-Python z-buffer rasterizer and Blender adapter
  for source-bound PGM subject/body/garment/hand/foot/equipment masks. Final runtime
  masks still require the exact Phase 10 runtime frame/commit.
- Session close: `RUN_ORIGINAL_V1_SESSION_CLOSE.bat` detects unpushed commits,
  remote-ahead/divergence, dirty/stale generated state, orphaned/mismatched local
  Blends and undocumented partial candidates; it never commits/pushes/fetches or
  deletes evidence.

These are preparation/evidence controls only. None executes the current Phase 3
repair, changes geometry/weights/rig/R2/poses/thresholds, completes later phases
or grants production approval. Current actual model action remains RUN r30.


### Repository-side gap-closure pass — 2026-10-01

Prepared the remaining high-value non-Blender tooling that directly reduces future
Claude laptop setup: ordered Phase 5A-5G anatomy packet/lineage verification;
Phase 6 evaluated normals/BVH self-intersection capture plus explicitly authored
joint-support evidence; Phase 7 detailed garment scene/shape-key/modifier/library
capture plus clean-room operation ledger; Phase 8 strict numeric-material and
presentation-state capture with fixed app-distance review plan; first-party
z-buffer PGM mask generation for model-side visual QA; and a read-only end-of-session
checker for pushed/clean/partial recovery state. None of these tools execute later
roadmap phases early or alter current model evidence. Current actual action remains
`RUN_ORIGINAL_V1_R30.bat` after normal preflight.


### Final laptop-acceleration closure — 2026-10-01

Added candidate evidence closure, real-review package indexing, local Blend
identity inventory, combined candidate handoff summary, compact live Claude brief,
single read-only Claude start/end wrappers and an optional collision-safe local
Blend recovery-copy command. Session close now explicitly refuses a missing or
hash-mismatched current complete Blend. The backup destination must be outside the
repository and fresh; copied bytes are re-hashed and are recovery-only, never
production evidence. See `work_packages/LAPTOP_ACCELERATION_PROTOCOL.md`. Current
actual model work remains r29 / Phase 3B -> `RUN_ORIGINAL_V1_R30.bat`.


## Claude laptop session — 2026-10-01 (r30 → r32, Phases 3B / 3C / 3D, 3E in progress)

Authoritative current state is `ORIGINAL_V1_HIGH_DETAIL_STATUS.json` / `docs/ORIGINAL_V1_DAILY_STATUS.md`
(regenerate with `python scripts/build_original_v1_daily_status.py`, then `--check`). This section records what
this session did and why, so the next worker does not have to reconstruct it. R2, thresholds, comparator
tolerances, the 15 stress poses and the 63-bone rig are unchanged. **No candidate is accepted and production
approval is false.**

### Two tooling bugs found by the first real Blender runs (both fixed, frozen region untouched)

1. **Relative render path.** `pose_test_original_v1_o4_candidate_blender.py` received a *relative* output folder.
   Blender resolves a relative `render.filepath` against the drive root, Python against the working directory, so
   every render went to `C:\ORIGINAL_V1_WORK\...` (about 1,960 PNGs from earlier sessions are still there, outside
   the repository and never hash-bound) and the new capture hash read-back failed with `FileNotFoundError`,
   aborting the first r30 evidence run. Fix: one statement `OUT = OUT.resolve()` placed **after** the
   `# --- metrics` marker. An attempted fix above that marker was reverted: the
   `ORIGINAL_V1_PRODUCTION_CONTROL.json` `frozen_pose_definition` pin hashes everything before the marker and
   correctly refused it (`frozen stress-pose definition changed`).
2. **Grip probe.** `probe_original_v1_grip_penetration_blender.py` raised `IndexError` because the
   `HGPT_DRESSED_MASK` modifier was still active, so the evaluated mesh had fewer vertices than the body. Fix:
   disable the mask in memory (as the pose test does) before measuring.

Also: the session preflight required `scipy`, which no repository script imports; it now requires only `numpy`.

Local-only storage: `.git/info/exclude` (not committed) lists the full-resolution group renders
(`repair_checks/*/*.png`, hash-bound by the committed `render_source_manifest.json`) and the disposable
`weight_solutions/*_dump.npz`, so the session-close clean-tree check works without bloating the repository.
Folders renamed (never deleted) after aborted runs: `repair_checks/shoulder_r30_ABORTED_20261001_relative_render_path_bug_empty`
(empty) and `repair_checks/remaining_diagnostics_r30_PARTIAL_20261001_grip_probe_mask_bug` (valid edge probe output).

### Candidates this session (all with full 15-pose evidence via `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat`)

| Candidate | Parent | What | Failed (R2 54) | Strict regressions vs R2 | Versus direct parent | Status |
|---|---|---|---:|---:|---|---|
| r30 | r29 | `o22` symmetric hand re-solve (finger-minimum recovery) | 7 | 6 | IMPROVED, 0 regr.; vs r28: 1 regr. | TRADE-OFF; continuation decision recorded |
| r31 | r30 | `o24` wrist band, 970 verts | 7 | 5 | IMPROVED, 0 regr. (also 0 vs r29 and r28) | **evidence only**: declared scope exceeded the 3D envelope (28 thumb-region vertices, finger-bone weights) |
| r32 | r30 | `o26` **strict** wrist mask, 880 verts, arm+hand, 14 chain bones | 7 | 5 | IMPROVED, 0 regr.; vs r28: 1 regr. | TRADE-OFF; **current continuation**; in-scope audit |

r30 → r32 key metric: `pushup_bottom` hand max 2.096 → 1.912 (R2 1.915, tolerance +0.1); the push-up wrist
severity regression versus R2 is gone. The 5 remaining strict R2 regressions are the inherited shoulder/torso
minima (press_bottom shoulder/torso, press_top torso, pullup_top shoulder/torso). The single regression of r32
versus r28 is `pushup_bottom` self-intersections 144 → 154 (gate 200; R2 156).

**Process for each local repair (3D, 3E), as the work packages require:** generate the parent-bound drafts
(`prepare_original_v1_repair_policy.py`); **declare the mask on disk and commit it before any weight is solved**
(`optimize_original_v1_o4_shoulder_weights.py ... --declare-mask`); solve; apply to a NEW candidate
(`apply_original_v1_o4_weight_solution_blender.py`); check the solution vertices and bones equal the declaration;
run the full evidence; export before/after snapshots and run `audit_original_v1_changes.py` against a policy with
the SAME scope. r31 shows why: its metrics were the best, but auditing its scope against the package envelope
found thumb-region vertices and finger-bone weights, so a strict mask was declared and r32 was built instead.

r32 change audit (`repair_preparation/r32_3D_audit/change_audit_r30_to_r32.json`): mesh untouched (0 vertices
moved, topology and symmetry unchanged); exactly the 880 declared vertices and 14 declared bones changed; 0
unexpected vertices/bones; 0 cross-side weights; max 4 influences. **Known flag:** 229 vertices have raw
weight-sum error up to 1.5e-5 (tolerance 1e-6). They are identical before and after, all outside the mask, and
inherited from the original binder; this edit introduced none.

### Next exact action (evidence-selected, at HEAD of this section)

Generated state: current candidate **r35** (experimental, TRADE-OFF versus r28 only; 6 development failures; Priority 1
clear), `python scripts/select_original_v1_next_action.py` →

> **REPAIR grip/thumb** — Bilateral equipment penetration must satisfy unchanged gates —
> `docs/work_packages/PHASE_3C_GRIP_THUMB.md`

That action is **blocked on the owner decision recorded under "Phase 3C"** below (the penetration is proven
weight-independent; the remaining causes are frozen structure). Nothing was changed to bypass it. Independent safe
work that does not depend on that decision: the Phase 3E owner decision (below), and the repository test updates
listed under "Known repository test status". Phase 4 cannot start while any development failure remains
(6 now: lunge pelvis max, lunge torso max, and the four grip penetrations).

### Repository test status (UPDATED 2026-10-01, commit 745242e)

`python -m unittest discover -s scripts -p "test_original_v1_*.py"` passes (290 tests). The stale r29/r30-era fixtures were
rewritten to derive the live latest candidate and next free revision instead of hard-coding history; the safety checks
(stale candidate identity, wrong next action, missing evidence, forbidden phase advancement, missing local Blend identity,
protected-structure drift, false production approval) were kept and mutation-checked. The earlier note that these tests were
failing is obsolete.

### Phase 3C — grip / thumb: BLOCKED on a frozen-structure decision (evidence complete)

Evidence: `remaining_diagnostics_r32/grip_penetration.json` and `grip_weight_independence.json`.

- All four checks (curl_handle and pullup_bar, both sides) are **4.712 mm before any finger closes** and 5.928 mm
  after (closing adds 1.216 mm). Gates: 2.0 mm development, 1.0 mm production. 29 vertices are inside before
  closing and 90 after. The deepest 12 are all **thumb-region**, weighted on `thumb_02`/`thumb_03` (the IP segment).
- **Weight independence is proven, not assumed.** `scripts/probe_original_v1_grip_weight_independence_blender.py`
  builds the pose up to (not including) `close_on_handle` and compares the armature-space skinning matrices of all
  20 hand-chain bones: max deviation **4.8e-7**. With every bone carrying the same rigid transform, no
  re-weighting can move a vertex, so the pre-close depth cannot be repaired by weights.
- To pass 2.0 mm the deepest thumb vertices must clear the handle by **at least 3.93 mm** (4.93 mm for 1 mm).
- The remaining causes are all frozen structure: the thumb's rest geometry/orientation relative to the hand (rig),
  the hand pose built by `pose_curl_handle`/`pose_pullup_bar`, or the handle frame (`place_handle`: centre offset
  `HANDLE_RADIUS + 0.020` = 37 mm from the knuckle-midpoint plane, radius 17 mm, so the near surface is 20 mm off
  that plane while the thumb pad rests about 15 mm off it). A local thumb-pad reshape of 3.9 mm or more is *not*
  "minimal" and was not attempted: it is a visible anatomy change that needs an owner decision.

**Owner decision needed (3C):** (a) change the frozen handle frame/offset, (b) change the thumb rest orientation
(frozen rig) or the frozen hand pose, or (c) approve a first-party local thumb-pad reshape of about 4–5 mm (then
3C proceeds with the declared-mask process above). Nothing frozen was changed.

### Phase 3E — hip / pelvis / lunge: PARTIALLY repaired on r35 (1 of 3 lunge failures cleared, clean)

Cause measured (read-only, from the r32 dump): the lunge failures sit on the **midline** gluteal/groin/lower-back
strip. Vertices at x = 0 carry about 47/47 `thigh_l`/`thigh_r` with only 5–20 % `pelvis`, so opposite thigh swings
tear the strip (the same mechanism as the shoulder midline-scapula tear). The first declared mask (committed
`87fc9ad` before any solve) is `repair_preparation/r32_3E_pelvis_declared/pelvis_mask_declared_before_edit.json`:
945 pelvis/torso/leg vertices with 0.74 < z < 1.0 whose whole weight is on {pelvis, spine_01, spine_02, thigh_l,
thigh_r}, mirror-closed, covering all 54 measured lunge extreme-edge vertices; permitted bones are those 5.

**Candidates (parent r32; full 15-pose evidence each):**

| Cand. | What | Failed (R2 54) | Strict regr. vs R2 | vs r32 | Verdict |
|---|---|---:|---:|---|---|
| r33 | `o31`: blend of base and solver solution `o29`, torso α 0.25 / other α 0.25 | 6 | 6 | IMPROVED, 0 regr. | evidence only: squat volume deviation 0.0373 → 0.0423 = +0.005000000000000004 against the 0.005 tolerance (the blend scan stopped on the feasibility edge and compared unrounded volume; the report rounds to 4 decimals) |
| r34 | `o32`: same blend, α 0.25 / 0.20, built with explicit safety margins | 6 | 5 | IMPROVED, 0 regr. | **rejected**: its change audit found **350 cross-side vertices** (r32: 0; mean 0.000, max 0.016 opposite-thigh weight, solver leakage). Left/right isolation is a protected property |
| **r35** | `o33`: same blend projected onto left/right isolation (`--isolate-sides`) | **6** | **5** | IMPROVED, 0 regr. (also vs r30, r29) | **current continuation**; clean evidence AND clean audit |

r35 versus pinned R2: only the 5 inherited shoulder/torso severity regressions. Versus r28: 1 regression
(`pushup_bottom` self-intersections 144 → 154, gate 200). Lunge torso min 0.120 → **0.161 (passes)**; lunge torso
max 6.37 and pelvis max 7.24 still fail (gate 5.0). r35 change audit
(`repair_preparation/r35_3E_audit/change_audit_r32_to_r35.json`, scope = the frozen pre-edit intent): mesh untouched,
exactly the 945 declared vertices and 5 declared bones changed, 0 unexpected vertices/bones, **0 cross-side**,
symmetry unchanged, unnormalised vertices 229 → 133 (inherited ones now exact).

**Why the remaining two lunge failures were not cleared inside that mask — the measured frontier** (exact numpy LBS
model, versus pinned R2 excluding the 5 inherited; solver points before any blend):

| Point | Lunge failures left | New comparator regressions vs R2 |
|---|---|---|
| r35 (chosen) | pelvis max 7.24, torso max 6.37 | **0** |
| `o29` full | pelvis max 5.58 | 3: row leg min 0.822→0.800, squat p99 1.745→1.845, squat volume 0.9627→0.9534 |
| `o30` full | pelvis max 5.13 | 7 |
| `o28` full | pelvis max 5.05 | 8 (incl. lunge leg max 1.615→2.204, row torso min 0.434→0.392) |
| `o27` full | pelvis max 6.35 | 7 |

No solver point inside the first mask clears the pelvis max gate even when regressions are accepted, and every point
that reaches the torso-max gate costs squat volume/p99 headroom (R2 deviation 0.0373, tolerance +0.005).

Method notes for the next worker: `scripts/blend_original_v1_o4_weight_solution.py` blends a solver solution with the
base inside the declared mask, comparing exactly as the comparator does (rounded values, strict `>`, tolerances read
from `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json`) with explicit safety margins (ratio 0.001, volume 0.0001), and
`--isolate-sides` removes opposite-side weight. The optimiser gained `guard_mult` / `guard_p99_mult` (regression guards
weighted above gate bounds; gradient-checked 6/6 exact with the symmetry projection off — with it on, one of six
differs in sign because the loss is evaluated at an asymmetric perturbation while the returned gradient is
mirror-symmetrised). `o30` (percentile guard boost) was worse than `o29`; penalty tuning is not converging, so
selection is done by exact evaluation instead.

**Attempt 2 (finished, parent r35, no new candidate built):** a WIDER band declared and committed (`8087fdf`) before
any solve: `repair_preparation/r35_3E_wide_declared/pelvis_wide_mask_declared_before_edit.json`: 0.55 < z < 1.12,
pelvis/torso/leg, whole weight already on the same 5 chain bones, 1,701 vertices (strict superset of the first mask,
+756), same 5 permitted bones, covers all 56 measured r35 lunge vertices; solver-side left/right isolation
(`isolate_sides`; 0 cross-side vertices in every solution). The first band and r33/r34/r35 are untouched.

| Solve (same wide mask) | Lunge | Squat | Verdict |
|---|---|---|---|
| `o34` | torso min 0.245, torso max 4.05 (pass); pelvis max 6.03 (fail) | p99 1.876, volume 0.9542 break tolerance | exact blend scan vs r35: **only α = 0** is clean |
| `o35` (asks for squat-volume headroom, `vol_slack` −0.006) | torso min 0.245, torso max 4.41 (pass); pelvis max 6.00 (fail) | volume 0.9590 (headroom created) but squat p99 1.897 and lunge p99 1.408 break tolerance | best clean blend reaches only lunge torso max 5.69 (> 5.0): no gate beyond r35's |

Reading: r35 has exhausted the squat volume budget (squat volume 0.9578 against a limit of 0.9577); spending headroom
elsewhere then fails the 99th-percentile edge-stretch tolerance (+0.05) in the squat and lunge. The comparator's
p99 guard is the binding limit for any weight-only lunge repair, so the weight search was stopped. Both solves are
recorded (`weight_solutions/o34.*`, `o35.*`) and not applied.

**Owner decision needed (3E):** the two remaining lunge failures (pelvis max 7.24, torso max 6.37 on r35) cannot be
cleared by weights inside either declared mask without breaking comparator tolerances. Options: (a) accept r35's
partial 3E result and record an evidence-backed disposition for the two failures (no threshold change); (b) authorise
supporting geometry in the groin/gluteal strip (note: subdividing an edge with interpolated weights does not reduce
its stretch ratio, so a new loop only helps together with a re-solved gradient); (c) authorise a pose-driven
correction (shape keys) or a different scope. Phase 4 cannot start while any development failure remains.

## Claude laptop session — 2026-10-01 (continued): Phase 3C and 3E resolved on r38

Owner authorisations used: local first-party thumb-pad reshape (3C) and local first-party midline support geometry plus
constrained weight re-solve (3E). Process followed each time: declare the mask and frozen intent on disk and commit BEFORE any
edit; apply to a NEW numbered candidate (verification that edited set == declared set); full 15-pose evidence; comparisons vs
direct parent, r35, r32, r30, r29, r28 and pinned R2; before/after snapshots and change audit under a policy of the same scope.

| Candidate | Parent | Change | Dev failures | Result |
|---|---|---|---:|---|
| r36 | r35 | 3C: 186 thumb-region vertices moved radially (max 5.31 mm) so no thumb vertex is inside the frozen handle before closing (29 -> 0 inside) | 2 | grip penetration 5.93 -> 1.627 mm (gate 2.0; production target 1.0 not yet met); vs r35 IMPROVED, 0 regressions |
| r37 | r36 | 3E: midline relief groove, 38 vertices (declared 40), max 10 mm inward, core = 19 midline vertices stretched >3x in the lunge | 0 | lunge pelvis/torso max 7.24/6.37 -> 4.57/4.46; BUT squat volume deviation 0.0373 -> 0.0431 (comparator regression) |
| r38 | r37 | 3E: constrained weight re-solve (preset o35, declared 1701-vertex band, blend alpha torso 0.30 / other 0, isolated sides) | **0** | vs r37/r36/r35/r32/r30/r29 IMPROVED, 0 regressions; vs R2 only the 5 inherited shoulder/torso minima; vs r28 the single pushup self-intersection 144 -> 154 (gate 200) |

Reasoning for 3E: the midline cleft had zero rest separation, so hip flexion stretched it 6-7x; stretch ratio is roughly the
posed gap divided by rest length, so giving the cleft rest length (the groove) lowers it without changing weights. The groove
costs squat volume, which the later weight solve restores (squat volume now 0.9602 vs R2 0.9569). No joint-angle-driven
corrective deformation was needed, so the escalation stays prepared-only (not implemented).

Audits: r35->r36 only the 186 declared thumb vertices moved, weights/topology unchanged, symmetry 1.3e-4 mm.
r36->r37 38 vertices inside the declared mask, 0 unexpected. r37->r38 mesh untouched, 1308 weight rows changed inside the
declared mask, 0 unexpected vertices/bones, 0 cross-side, 0 over-influence. The blend tool now prunes to <=4 influences after
mirror averaging (r37 solution had 8 five-influence rows before that fix).

### Current state and what blocks Phase 3/4 now

r38 is the experimental continuation (classification TRADE-OFF only because of the one r28 comparison). It has **0
development failures**. The selector therefore says `RECONCILE freeze regressions`: the Phase 4 contract requires no
unresolved strict regressions, and r38 still carries the five inherited r24 shoulder/torso minima versus R2
(press_bottom shoulder 0.577->0.548 and torso 0.943->0.889, press_top torso 0.886->0.823, pullup_top shoulder 0.694->0.670
and torso 0.883->0.861; tolerance 0.02; all far above the 0.15 gate). The owner earlier kept the strict rule and stopped
shoulder-only optimisation; heavier shoulder topology or pose-driven corrections were not authorised. Nothing was done here to
bypass this. Phase 4 and Phase 5 were therefore NOT started.

**Owner decision needed:** (a) accept the five minima as a documented trade-off and pin a new numbered baseline (R2 file
untouched, tolerances unchanged), then run Phase 4 freeze validation on r38; or (b) authorise a further tool for the
shoulder/chest minima: a generic joint-angle-driven corrective shape (driven by shoulder elevation, deterministic,
first-party, not keyed to any exercise name) or local chest/shoulder geometry under the declare-mask process; or (c) allow
another weights-only attempt with the five minima as hard constraints on the r38 base.

## Claude laptop session — 2026-10-02: skeleton-motion validation, pose revision P2, rig rev2, LOCK

Authority: owner brief 2026-10-02 (skeleton first). Everything below is evidence-backed; see `docs/ORIGINAL_V1_SKELETON_MOTION_LOCK.md`,
`docs/ORIGINAL_V1_SKELETON_REFERENCE_EVIDENCE.md`, `docs/ORIGINAL_V1_SKELETON_JOINT_VALIDATION_MATRIX.md` (all 15 rows LOCKED), decision log entry of the same date.

**Findings.** The 63 rig BONES were sound (structure audit 0 flags; rest identical to the v4 payload to 5e-7 m). The stress-pose CONSTRUCTION was wrong:
distal finger joint bent backwards (−55°; −85° on handle grips) and thumb IP reversed (hinge axis re-derived per curled segment flips past 90°);
push-up wrist 88° radial deviation (degenerate pronation target); toes bent the wrong way (push-up, lunge); no humeral axial rotation in elevated poses
(elbow hinged sideways up to 107°, forearm carried 85° twist — this was the axilla/"webbing" cause: pose/rig construction, not weights/topology); squat
ankle plantarflexed (knee behind ankle); push-up hands 0.29 m above the floor; rest thumb pointing into the floor. The earlier skeleton-motion audit's finger check had the same
axis flaw (it never flagged the reversal and would flag a correct deep curl) — fixed.

**Corrections.** Pose definition **P2** (P1 preserved verbatim, both pinned in `ORIGINAL_V1_PRODUCTION_CONTROL.json`). Because P2 changes every hand/arm measurement,
baselines are now per stress-pose epoch (`baseline_epochs`): **R2** = P1 epoch r1..r38 (unchanged), **P2B1** = r38 re-measured under P2 (5 development failures) for r39+.
Evidence tools (`merge`, repair-check/full-evidence .bat, control) are epoch-aware. Rig **rev2** = 63 + 8 axial-twist helpers (`upperarm/forearm × tw0/tw1 × l/r`),
closed-form drive in `scripts/original_v1_twist_helpers.py` (inlined in `upd()` of the pose script); payload `ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2.json`,
structure hash `09d02e45…`. Rejected helpers (thigh/shin twist, palm/thumb, hallux split, ribs, shoulder/thorax) documented in the lock record.

**Lock.** `ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_twist_helpers.json` on candidate **r41** (SHA `19a3f9b4…`). Gates: rig structure 0 flags; fixed-axis finger/thumb 0 flags (r38/P1: 84);
continuous kinematics 9 samples × 15 poses with separate swing/twist interpolation 0 path flags; movement-envelope check 25 110 components 0 violations 0 L/R asymmetries (r38/P1: 412);
floor contact: push-up palm 3.6 mm / thumb pad 0 / toe pads 262 contact vertices. First-party anatomical proxy built (`proxy_r41/`): joint centres inside the skin, tibia/femur anterior-biased as anatomy predicts, scapula/clavicle inside the torso shell; no skeleton-level defect found.
Reopen only on direct evidence of a rig defect.

**Deformation state.** r41 (full evidence, P2): 2 development failures (press_top_rhythm p99 2.091; push-up hand min 0.119); vs P2B1 36 improvements / 16 regressions (arm-region
stretch ≤3.2, two volume deviations, small self-intersection increases). Forearm-only variant r42 (metrics-only): 0 regressions but the same 5 failures — the upper-arm helpers are what clear the shoulder minima.
Exploratory r39/r40/r42 evidence preserved in `ORIGINAL_V1_WORK/candidates/superseded_exploratory_P2_0/`.

**Next.** Weight re-solve on r41 with preset `o40` (declared mask `repair_preparation/r43_shoulder_arm_declared/`, 2820 vertices incl. helper stations), then the push-up wrist/hand minimum;
new candidate numbers start at r43. Then recompute status, run the Phase 3 exit contract and (if clear) the Phase 4 freeze. Repo test suite green with epoch-aware fixtures.
The standalone runtime TypeScript payload (`src/rig/canonicalV4Original.ts`) is NOT changed; moving it to rev2 is a separate prepared step (runtime must drive helpers as documented).


## Claude laptop session — 2026-10-02 (part 2): owner re-validation, P3, rig rev2c, re-lock, shoulder deformation frontier

Owner review of r41 withdrew the first lock (toes/forefoot and shoulder/axilla not convincing). Full record: `docs/ORIGINAL_V1_PUSHUP_FOOT_AND_SHOULDER_REVALIDATION_20261002.md`.

* **Toes.** Three barefoot push-up/chaturanga photographs of different people (Wikimedia Commons; links + observations only, nothing stored) + foot/toe literature. Ankle already matched (+22 rest-relative); r41's toe tip was lifted 8° → P3 lays the toe flat (toe axis 0.0°, 216 toe-owned contact vertices, palm 3.6 mm, thumb pad 0). Single toe control retained; hallux split not justified (Phase 5F trigger).
* **Shoulder skeleton.** The plain press/pull-up poses held clavicle/scapula still (166° glenohumeral-only). **P3** = interval-dependent scapulohumeral rhythm in every elevated-arm pose (scapula ≈ 60° at 166°; `*_rhythm` = 1.25× high-share subject; no fixed ratio). The scapula pivoted about the AC corner and swung the plate 2.4× too far → **pivot relocated 35 % toward the tail (rev2c, candidate r43)**.
* **Helpers.** Upper-arm helpers REJECTED (r41 17 failures vs 14 without, shoulder minimum 0.185→0.112/0.068 under realistic poses); forearm helpers kept (r42: 0 regressions, 7 improvements vs 63 bones). Rig rev2c = 63 + 4 forearm helpers = 67 bones; payload `ORIGINAL_V1_WORK/hgpt_canonical_v4_original_rev2c.json`, structure hash `aca64584…`.
* **Re-lock.** `ORIGINAL_V1_WORK/SKELETON_MOTION_LOCK_rev2_forearm_twist_only.json` on **r45** (all skeleton audits clean: structure 0 flags, motion 0, finger 0, continuous 0 path flags, envelope 25 110 components 0 violations). The first lock + its reopen record are preserved.
* **Epochs.** R2 (P1, r1..r38) → P2B1 (r39..r41) → **P3B1 (r42+, r42 under P3: 14 failures)**. P1/P2/P3 pose scripts are all committed and pinned.
* **Deformation under P3.** r42 14 failures → r45 5 → **r48 3** (torso max stretch in press_top 5.12 / press_top_rhythm 6.34 / pullup_hang_rhythm 5.84). The push-up hand minimum is cleared (wrist-band weights). The visual finding the gates missed: with a physiological scapular rotation the lateral-torso skin is dragged up as 0.2 m **tent flaps** (r45); hard trunk anchoring (r46) removes them but **tears the axilla web** (shoulder stretch 7.9); moderate anchoring (r47/r48) leaves reduced flaps with jagged edges. That frontier is the signature of a linear-skinning limit → a **generic joint-angle-driven corrective deformation is justified** (trigger: glenohumeral elevation > ~60°, full by ~150°, with scapular rotation; slide lateral-torso/axilla vertices toward trunk-driven positions and relax the web; first-party positions-level solve stored as a driven shape key). Prepared, NOT implemented (data-model change; needs an explicit design pass). Solver prior `w_trunk` (presets o43/o44) is committed.

**State.** Current candidate **r48** (SHA `251ed96c…`), 3 development failures vs P3B1, production approval false. Next action: design and author the elevation-driven axilla corrective (or test the support-loop mesh under P3), then re-solve and run the Phase 3 exit verifier; Phase 4/5 not started.

## Shoulder corrective implemented; r49-r55 - 2026-10-02 (Claude)

- Design (`docs/ORIGINAL_V1_SHOULDER_CORRECTIVE_DESIGN.md`) implemented: two shape keys per candidate (`HGPT_SHOULDER_CORR_L/R`) added to r48, driven by humerothoracic elevation theta (smoothstep 40..150 deg, derived from the r48 arc audit) times the abduction fraction in the trunk frame; mirror-symmetric by construction; runtime spec `ORIGINAL_V1_WORK/shoulder_corrective_<rN>.json`; 1491 left-owned vertices declared before the solve. Solver `scripts/optimize_original_v1_shoulder_corrective.py` (numpy only).
- r49 (theta only) and r50 produced squat self-intersections; r51 (tight anchoring) raised p99; r52/r53 cleared the development gates but renders still showed tent/sheet and axilla tears; r54 (looser tail bounds) failed 2 p99 gates and crumpled; **r55** (smoothness weight 300, hi 3.6) = **0 development failures**, torso edge max <= 3.66 (was 5.12/6.34/5.84), volume 0.998-1.043 with <= 0.8 % step between arc samples, no L/R mismatch (asymmetry 0), torso drift max 0.136 m (r48 0.188).
- Honest status: r55 is NOT accepted as a visual solution. Overhead poses still show small sliver tears at the armpit pit and a crumpled lateral torso; vs P3B1 it has 31 comparator regressions, notably self-intersections in the pull-up poses (4 -> 98, 0 -> 134) and press_top (95 -> 178) - all under the 200 gate. Per the owner principle (do not optimise merely for tests) Phase 3 exit and the Phase 4 freeze were NOT run on it.
- Finding: the arc audit used to ignore shape keys; fixed (it now evaluates the keys). Worst-edge diagnostic shows no over-stretched edge (<= 3.65), so the pit spikes are thin triangles folding, a topology/weight limit at the axilla pit, not edge stretch.
- Next options (owner-level or next session): (a) add a face-area/fold barrier plus second driver (scapular rotation) to the corrective; (b) a first-party axilla-pit weight/topology edit (new declared mask) for the ~40 pit vertices; (c) accept r55 as a development trade-off and freeze. Current evidence candidate for review: r55 (sha256 CCAEF8BA1FDDE161B9E5769175B7576EEB88D96F4C99E41CDD0147041A93BBD7).

NEXT ACTION (evidence-selected): RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat r55, then decide between options (a)/(b)/(c) above; r55 has 0 development failures but a visual armpit residual, so Phase 3 exit has not been run.

Status-selected next action: RECONCILE trial lineage (r49-r54 are preserved trial/exploratory candidates leading to r55; r55 is the current evidence candidate). After that, choose corrective option (a)/(b)/(c).
