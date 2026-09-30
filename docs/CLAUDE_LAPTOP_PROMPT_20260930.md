# Claude laptop session prompt — 2026-09-30

Copy/paste the prompt below into Claude on the laptop.

---

Continue working directly on my Home Gym PT animation-software repository and
take the ORIGINAL v1 Blender/model track as far as you safely can without
waiting for approval.

Repository:
`anyangle1409-code/animation-software`

MODEL BRANCH TO USE:
`claude/original-v1-blender-o2-20260929`

First:
1. fetch/pull and confirm the live remote HEAD;
2. never reset/overwrite a newer commit;
3. read `docs/CLAUDE_LAPTOP_HANDOFF_20260930.md`;
4. read `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`;
5. run `PREFLIGHT_CLAUDE_ORIGINAL_V1.bat`;
6. if preflight passes, use `OPEN_ORIGINAL_V1_O4_GUARDED.bat` to open the
   expected O4 candidate in Blender.

MAIN TASK:
Continue the independently authored
`HomeGymPT_Male_ORIGINAL_v1` /
`hgpt_canonical_v4_original` candidate.

Current pinned R2 state:
- 54 development deformation failures;
- 133 production deformation failures;
- 0 unmapped development blockers;
- next repair priority = 1, shoulder / upper torso.

Work Priority 1 first. Do not jump to cosmetic hand/detail work just because it
is visually easier.

Priority-1 evidence poses include:
- press_bottom
- press_top
- press_top_rhythm
- squat_bottom arm position
- pullup_hang
- pullup_hang_rhythm
- pullup_top
- pullup_bar

Repair the shoulder/upper-torso deformation in Blender while preserving:
- the frozen 63-bone canonical-v4 structure;
- clean-room/project-authored geometry;
- project-authored weights;
- existing exercise biomechanics and contact intent;
- deterministic candidate/evidence generation.

After every meaningful repair use a NEW evidence label, e.g.:

`RUN_ORIGINAL_V1_REPAIR_CHECK.bat shoulder path\to\candidate.blend shoulder_r3`

Reject a revision if it improves one area but introduces a new gate failure or
material severity regression elsewhere. Do not weaken thresholds to pass.

IMPORTANT FIRST-PARTY BOUNDARY:
Historical V8–V15f may be used only to understand previous failure modes and
quality expectations. Never copy geometry, topology, weights, bind matrices,
rig transforms, materials, garments, grip calibration or other implementation
data from V8–V15f, MakeHuman, Meshy or any third-party/reference asset.

Do not restart O2. The O4 deformation handoff is current.

Do not fabricate final grip metadata during Priority 1. The future
`homeGymPT` scene extras and ORIGINAL-v1-specific gripSolutionId must be
measured only after the Priority-2 hand/grip work clears its evidence gates.
Do not reuse a legacy grip solution.

Do not copy candidate GLBs into the standalone production paths and do not set
any release/promotion/component gate to approved.

STANDALONE TRACK:
Do not merge the model branch into the standalone branch. A frozen recovery
branch exists at:
`handoff/standalone-v4-shadow-safe-20260930`

Treat standalone/runtime changes as a separate track. The Blender session should
stay on the model branch unless a model task genuinely requires reading
standalone contracts.

AUTONOMY:
Work continuously until the laptop battery/session ends. Do not stop for routine
approval questions. Use your judgement within the constraints above.

BEFORE YOU FINISH:
1. save meaningful Blender revisions as new numbered candidates/checkpoints;
2. regenerate all evidence/reports available for the newest candidate;
3. update `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md` with exact candidate
   name/hash, changes, improvements, failures and next priority;
4. update machine-readable status/evidence only to facts actually proven;
5. commit relevant model/evidence/handoff files;
6. push `claude/original-v1-blender-o2-20260929`;
7. tell me the exact pushed HEAD and what remains.

Do not claim production approval from render quality alone. Keep candidate,
production and release states explicit.

---
