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
  --grip-report ORIGINAL_V1_WORK\candidates\grip_test_report_r1.json ^
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
  --grip-report ORIGINAL_V1_WORK\candidates\grip_test_report_r1.json ^
  --profile production_target ^
  --require-group core_five
```

## Current candidate status

Against the newly recorded `development_blocker` profile, the current R2
candidate has **52 failed checks**. This is expected evidence that O4 requires
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
| pullup_bar | 2 |
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

The handle-grip report also fails both hands on penetration:
**5.93 mm** current versus **2.0 mm** development limit and **1.0 mm**
production target.

Neutral remains an important control: it reports volume 1.0, zero compressed
or stretched edges under the current stress thresholds, and zero
self-intersections.

## Repair order

Do not polish the face, materials or shorts before the higher-priority
deformation blockers are resolved.

### Priority 1 — shoulder girdle / overhead deformation

Target poses:

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
  --baseline-grip-report ORIGINAL_V1_WORK\candidates\grip_test_report_r1.json ^
  --candidate-grip-report ORIGINAL_V1_WORK\candidates\grip_test_report_r2.json ^
  --profile development_blocker ^
  --json-out ORIGINAL_V1_WORK\candidates\deformation_compare_r2_r3.json
```

The comparator deliberately does **not** use one blended quality score. It
returns `REGRESSION` if any existing pose or grip gains failed checks, even
when another pose improves. This prevents an apparent global improvement from
hiding a newly damaged shoulder, hand, hip or contact.

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
