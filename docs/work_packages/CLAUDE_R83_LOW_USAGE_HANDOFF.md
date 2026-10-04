# Claude low-usage handoff — r81 → r83

## Read this first

Claude weekly usage is scarce. Do not rediscover Phase 3 history. Do not repeat r82. Do not run expensive full evidence until a focused probe earns it.

Authoritative retained state at preparation time:
- retained candidate: **r81**
- r81: **0 development failures**, **12 strict P3B1 regressions**
- r82: **REFUSED** (17 strict regressions despite eliminating shoulder intersections)
- 3B/3C/3D/3E: clear
- 3A: only Phase 3 blocker
- Phase 3: not cleared
- Phase 4: not begun

Before execution, fetch the live model branch and preserve any work newer than the preparation base. If live work has already superseded this package, reconcile; never overwrite/revert/force-push.

## Prepared tools

- `scripts/declare_original_v1_p3b1_minratio_zone.py`
  - deterministic, read-only, comparator-aligned local mask declaration
- `scripts/restore_original_v1_weights_zone.py`
  - deterministic local restoration solution; no Blend mutation
- `docs/work_packages/R83_EXECUTION_MATRIX.json`
  - alpha matrix and rejection rules
- `docs/work_packages/R83_R81_P3B1_CLOSURE_PREP.md`
  - evidence/attribution rationale

## Minimal Blender strategy

### 0. Protect r81
Never overwrite the r81 Blend/intermediate. New numbered research candidates only.

### 1. One read-only r81 dump
Use the existing `dump_original_v1_o4_pose_skinning_blender.py` against the retained r81 weights intermediate/correct candidate as appropriate. Include the focused pose set:
`press_top,pullup_hang,pullup_hang_rhythm,squat_bottom,press_bottom,pullup_bar,pullup_top,press_top_rhythm,pushup_bottom`.

If the corrective shape key makes this dump unsuitable for weight-only attribution, dump the committed `r81_weights_intermediate.blend` for the weight experiment and retain the full r81 report as the final comparator/sentinel.

### 2. Declare the local zone before editing
Initial targets should cover the weight-owned/mixed min-ratio blockers:
`press_top/arm pullup_hang/arm pullup_hang_rhythm/arm squat_bottom/arm squat_bottom/shoulder press_bottom/torso pullup_top/torso`.
Use a conservative declaration (top 8 edges, 1 ring). Inspect declaration size/bbox; if unexpectedly broad, stop and diagnose rather than applying.

### 3. Reference selection
Do NOT assume a reference. Choose the nearest committed pre-smoothing/retained weight state that:
- has the identical rest mesh and bone columns,
- is first-party,
- predates the r81 smoothing that introduced the inherited min-ratio regressions,
- does not import refused r78/r79/r82 state.
Record its SHA/name.

If no trustworthy compatible reference dump exists, create exactly one read-only dump from that committed candidate. Do not reconstruct weights by guesswork.

### 4. Cheap alpha generation outside Blender
Generate local restoration solutions for alpha **0.10, 0.20, 0.35** first.
Do not start with seven candidates.

### 5. Focused Blender probes only
Apply each solution to a new disposable research candidate and test only the focused poses/sentinel necessary to rank it.

Rank lexicographically:
1. development failures = 0 (mandatory)
2. preserve r81 shoulder self-intersection success (mandatory)
3. fewer strict P3B1 regressions than 12
4. improve the seven inherited min-ratio rows
5. minimise new regressions / total weight displacement

Immediately reject a candidate that fails (1) or (2).

### 6. Refine only around a winner
If 0.10/0.20/0.35 shows a monotonic useful direction, test at most two bracketing values from:
`0.05, 0.15, 0.25, 0.50`.
If none improves r81, stop. Do not keep sweeping.

### 7. Corrective refit only once
Only the best weight candidate gets a corrective refit. The corrective must specifically guard:
- press_top_rhythm arm min ratio
- squat_bottom volume deviation
- squat_bottom p01
- mixed squat_bottom arm min ratio
while preserving the shoulder intersection gains.

### 8. Full evidence only for earned candidate
Run the full 15-pose package, determinism, sub-phase evidence, manifests and review imagery only after focused probes show a strict improvement over r81 with development gates intact.

## Stop conditions

Stop and preserve evidence rather than spending usage if:
- no first-pass alpha improves r81;
- reference compatibility is uncertain;
- local restoration reintroduces shoulder-top crossings;
- a development blocker appears;
- solving would require weakening a gate/baseline/test;
- a newer live branch candidate already supersedes r81/r83.

## Phase 3 / Phase 4

Do not declare 3A clear because development failures are zero. Strict Phase 3 exit evidence must genuinely satisfy the project's existing gate.

Only after 3A–3E and full Phase 3 exit evidence pass may Phase 4 Development Freeze begin. Phase 4 is not production approval.

## Commit discipline

Commit/push:
1. declaration + source/reference hashes;
2. first-pass probe table (including rejected candidates);
3. selected/refused decision;
4. corrective refit evidence if earned;
5. full evidence if earned;
6. updated authoritative handoff/status.

Small recoverable commits. No force push. No rebase that discards other-agent work.
