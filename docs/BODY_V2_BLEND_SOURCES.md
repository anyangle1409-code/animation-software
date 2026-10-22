# Body v2 – where the .blend files come from and how to rebuild them

These are the .blend files from the Claude Code session on branch `claude/home-gym-pt-animation-txux66`:

| Name | What it is | Size |
|---|---|---|
| `body_v2.blend` | v13s / **w8** finished body | ~200 MB |
| `body_v2_legs.blend` | v14a, new legs and feet | ~200 MB |
| `body_v2_rebuilt.blend` | R120 clean-rebuild experiment | ~300 MB |

None of them is committed. Each file is over GitHub's 100 MB per-file limit, mostly from the 79 corrective shape keys on about 220,000 vertices. Git LFS was not available in the session. All of them can be rebuilt exactly from files that are in this repository.

## Source

The input is `ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend` (5.1 MB).

It is tracked in this repository at commit `025d5f28` ("R57: execute full unsaved native pose, geometry, benchmark and comparison tests"), which is on `origin/codex/r57-local-s7-temporal-study-20261020`. Check that commit out as a separate worktree, here called `R57SRC`:

```
git worktree add ../r57src 025d5f28
```

The builder also imports these scripts from that checkout's `scripts/`:
- `build_original_review_candidate_r17_blender.py`
- `build_original_movement_benchmarks_blender.py`
- `original_v1_review_candidate_drives.py`

## Requirements

- Blender 5.x as the Python module `bpy`. The session used the `bpy` 5.2 wheel with Python 3.13.
- numpy and scipy.
- scikit-image, for the marching cubes in the feet and the rebuild. It needs `lazy_loader` and `packaging`.

## Commands

Run these from `scripts/body_v2/` on this branch.

1. **w8 / v13s finished body.** About 15 minutes. Add `R76_RENDER=1` for the builder's own renders.
   ```
   V2_SAVE_BLEND=1 python3.13 build_body_v2_sculpt_blender.py -- ../../../r57src OUT_W8 2.0
   ```
   This writes `OUT_W8/body_v2.blend`. The V2 shape is baked into the basis, every corrective shape key moves with it, and the edited rig and skin weights are kept. The defaults are the v13s/w8 settings.

2. **New legs and feet (R119).** About 10 minutes with renders, or 4 minutes with `V2_LEGS_RENDER=0`.
   - For v14a/v14b exactly as reviewed: default settings.
   - For the legs-only base that the rebuild uses: `V2_TORSO_RELIEF=0 V2_PEC_JUNCTION=0`.
   ```
   python3.13 legs_v2_blender.py -- OUT_W8/body_v2.blend ../../../r57src OUT_LEGS
   ```
   This writes `OUT_LEGS/body_v2_legs.blend`.

3. **Clean rebuild of the torso, arms and shoulders (R120).** This is an experiment and is still being validated.
   ```
   python3.13 rebuild_v2_blender.py -- OUT_LEGS/body_v2_legs.blend ../../../r57src OUT_RB
   python3.13 render_v2_blender.py  -- OUT_RB/body_v2_rebuilt.blend ../../../r57src OUT_RB
   ```

## What is in each file

- **Body object** `HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE`:
  - an armature modifier, plain linear-blend skinning;
  - 77 vertex groups;
  - 79 shape keys (Basis plus the correctives, driven by `original_v1_review_candidate_drives.drive`).
- **Rig** `HGPT_CANONICAL_V4_ORIGINAL`. Its edits are listed in `skeleton_edits.json`.
- **Display pose.** The standing pose used for every review image is: upper arms out 16° (`upperarm_r` Z −16°, `upperarm_l` Z +16°) and elbows bent 6° (forearm X −6°). Then call `drives.drive(rig, body)`.

## Change log

The full history and the reasoning behind each change are in `docs/CLAUDE_SHOULDER_R58_HANDOFF_20261020.md` (sections "Draft v13s", "v14a" and "v14b"). Review images are in `review-assets/body_v2/`.
