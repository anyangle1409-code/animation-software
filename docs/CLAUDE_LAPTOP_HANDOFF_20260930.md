# Claude laptop handoff — 2026-09-30

## Verified handover checkpoints

Standalone/runtime recovery checkpoint:
- branch: `handoff/standalone-v4-shadow-safe-20260930`
- exact green SHA: `0a5b90544e08574ddbdf02b51be116339fbc8c2f`
- Standalone prep verification run `36740155156`: **PASS**
- Browser viewport smoke run `36740155224`: **PASS**
- state: accepted v3 runtime default, canonical v4 guarded in shadow, ORIGINAL
  v1 assets dormant/blocked.

Model/deformation validation checkpoint:
- branch: `claude/original-v1-blender-o2-20260929`
- exact green SHA: `956e78f1563cb0019f1969469a83c223dd42146a`
- ORIGINAL v1 deformation validation run `36740868657`: **PASS**
- validation includes the full R2 two-equipment grip evidence, full Priority-1
  shoulder subset, candidate-status contract, GLB structural audit, repair
  queue ownership and Python syntax for the new Blender shoulder-weight audit.

Later documentation-only handoff commits may sit above the green model
checkpoint; do not confuse that with a model/asset state change.

## Purpose

Use the laptop/Blender session to continue the isolated ORIGINAL v1 character
candidate. Do not spend the session restarting completed runtime-dependency work
or trying to activate production assets.

There are two separate tracks:

1. **Standalone/runtime track**
   - Main working branch: `work/standalone-first-party-audit-20260927`.
   - Safe recovery branch created before this handoff:
     `handoff/standalone-v4-shadow-safe-20260930`.
   - On the safe branch, the accepted v3 rig is the live runtime default and
     canonical v4 remains in guarded shadow mode.
   - The v4 code/data and proportion-adaptation work are preserved.
   - ORIGINAL v1 production GLBs remain dormant and unapproved.

2. **Blender/model track — use this for the laptop session**
   - Branch: `claude/original-v1-blender-o2-20260929`.
   - Last observed HEAD before handoff:
     `bc7f90ac25fe5ce20d6c20ef675a6c714a41ff11`.
   - If remote HEAD is newer, **do not reset or overwrite it**. Read the newer
     commits/handoff first and continue from the newest state.

## First commands on the laptop

From the repository root:

```bat
git fetch --all --prune
git switch claude/original-v1-blender-o2-20260929
git pull --ff-only
git status --short
git rev-parse HEAD
```

Do not merge `work/standalone-first-party-audit-20260927` into the model
branch and do not merge the model branch wholesale into standalone.

Then run the guarded repo/model preflight:

```bat
PREFLIGHT_CLAUDE_ORIGINAL_V1.bat
```

It verifies the branch, current candidate-status contract, pinned R2 evidence and
repair-queue ownership before any Blender edit. Stop and investigate if it does
not pass.

For the first Blender open, Claude can use:

```bat
OPEN_ORIGINAL_V1_O4_GUARDED.bat
```

That runs the same preflight and opens only the expected O4 candidate Blend.

## Read these before opening/editing Blender

1. `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`
2. `ORIGINAL_V1_CANDIDATE_STATUS.json`
3. `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json`
4. `ORIGINAL_V1_WORK/candidates/DEFORMATION_BASELINE_R2.json`
5. `ORIGINAL_V1_WORK/candidates/O4_CANDIDATE_BUILD.json`
6. `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md` only if O1/O2 provenance/recovery
   context is needed; it is not the active repair task.

## Current verified model state

Asset target:
- `HomeGymPT_Male_ORIGINAL_v1`

Rig target:
- `hgpt_canonical_v4_original`
- 63 bones

Current stage:
- independently authored O4 bound candidate;
- O7 shorts candidate exists;
- candidate bare/dressed GLBs are structurally self-contained;
- candidate assets are **not production-approved**.

Pinned R2 deformation baseline:
- development blockers: **54**
- production blockers: **133**
- unmapped development blockers: **0**
- next repair priority: **1 — shoulder / upper torso**

Known equipment grip blocker:
- `curl_handle`: 5.93 mm max penetration on each hand
- `pullup_bar`: 5.93 mm max penetration on each hand
- development limit: 2.0 mm
- production limit: 1.0 mm

## Laptop task — Priority 1 only first

Before the first shoulder weight edit, capture the current weight evidence:

```bat
AUDIT_ORIGINAL_V1_SHOULDER_WEIGHTS.bat ^
  ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE.blend ^
  r2_before_repair
```

Then repair shoulder/upper-torso deformation before moving to hands.

Priority-1 pose set includes:
- `press_bottom`
- `press_top`
- `press_top_rhythm`
- `squat_bottom` arm position
- `pullup_hang`
- `pullup_hang_rhythm`
- `pullup_top`
- `pullup_bar`

Work on the O4 candidate Blend. Preserve:
- the 63-bone v4 structure;
- clean-room geometry/provenance;
- existing accepted exercise biomechanics;
- explicit project-authored weights only.

Do not change rig structure merely to hide a deformation problem.

## Required repair loop

For each meaningful Blender revision:

1. save it as a new numbered candidate/checkpoint rather than overwriting
   evidence from another revision;
2. run the targeted shoulder check with a fresh label:

```bat
RUN_ORIGINAL_V1_REPAIR_CHECK.bat shoulder path\to\candidate.blend shoulder_r3
```

or use the convenience wrapper:

```bat
RUN_ORIGINAL_V1_SHOULDER_CHECK.bat path\to\candidate.blend shoulder_r3
```

3. inspect the generated renders and
   `comparison_vs_R2.json`;
4. reject the candidate if any baseline pose/region gains a gate failure or
   materially worsens a severity metric;
5. after a promising shoulder repair, regenerate the full pose report and
   repair queue before declaring Priority 1 clear.

The comparator deliberately does not use a blended score: improvement in one
region cannot cancel a new regression elsewhere.

## Do not fabricate grip metadata

The final runtime promotion path will require scene extras under `homeGymPT`
with:
- `assetId: "HomeGymPT_Male_ORIGINAL_v1"`
- `rigId: "hgpt_canonical_v4_original"`
- `offsetFrame: "hand-v2"`
- finite left/right `gripFrameOffsets`
- finite left/right `handleGripOffsets`
- an ORIGINAL-v1-specific `gripSolutionId`

Do **not** invent these during Priority 1.

Only author them after Priority 2 hand/grip work clears the contact/deformation
gates and the values are measured from ORIGINAL v1 itself. Do not reuse a
legacy/V-series grip solution or tune the model to the generic runtime fallback.

The candidate GLB exporter is already configured with `export_extras=True`
for future exports; the currently committed candidate GLBs were not changed by
that script update.

## Legacy/reference boundary

V8–V15f and other historical material may be used only for:
- identifying failure modes;
- understanding what previously looked wrong/right;
- setting qualitative quality expectations.

Never copy:
- geometry;
- topology;
- weights;
- bind matrices;
- rig transforms;
- materials/textures;
- garment geometry;
- grip/calibration data;
- other implementation data

from V8–V15f, MakeHuman, Meshy or any third-party/reference asset into
ORIGINAL v1.

## Standalone/runtime warning

Do not copy the current candidate GLBs into `public/characters/`.

Do not set:
- `ORIGINAL_V1_PROMOTION_CONTRACT.json` to approved;
- `male_character`, `male_shorts` or `canonical_rig` to
  `first_party_approved`;
- ORIGINAL v1 as the live/default runtime character.

The final standalone promotion is intentionally exact-hash and deny-by-default.
Only approved production artifacts will later be copied from one pinned model
commit; the model branch itself will never be merged wholesale.

A v4 live-runtime activation was attempted on 2026-09-30 but full CI exposed
parity issues, so the safe handoff state keeps v3 live and v4 in shadow until
both legacy parity and v4 behavioural compatibility are green on the same
exact commit.

## Before the laptop/battery session ends

Do not leave useful Blender work only on the laptop.

At minimum:

1. save the newest numbered Blend candidate;
2. generate the targeted/full reports that exist at that point;
3. update `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md` with:
   - exact new candidate name/hash;
   - what changed;
   - what improved;
   - what still fails;
   - exact next repair priority;
4. commit only relevant model/evidence/handoff files;
5. push `claude/original-v1-blender-o2-20260929`;
6. report the exact pushed HEAD.

Do not claim production approval from a render-only improvement or from a
structural GLB pass.
