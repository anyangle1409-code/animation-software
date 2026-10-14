# W3 option A — shoulder-top helper deformer: in-memory feasibility and best variant (Claude, 14 Oct 2026)

**What this is:** measurement only, to inform the owner + Lane G decision on the W3 proposal (A/B/C; `docs/CLAUDE_W3_SHOULDER_RUNTIME_CONTRACT_PROPOSAL_20261013.md` on `claude/master-execution-20261013`).
- It is **not** the review-only trial on a separate copy that the proposal asks the owner to approve.
- The helpers and reweighting exist only in memory; the a003 blend, the 67-joint rig, the weights and the GLB path are untouched.
- Nothing is approved.

**Scripts:**
- `scripts/diagnose_shoulder_helper_deformer_blender.py`: helper, reweighting, σmin, the coupled-sweep metrics of W2/W4, and the M1 press.
- `scripts/diagnose_shoulder_swing_twist_blender.py`: the motion decomposition.

**Reports:** `ORIGINAL_V1_WORK/anatomy/audit/claude_w3a/`.

## Set-up (per side; 67 → 69 deforming joints)

- **Helper bone:** `deltoid_helper_<s>`, with the upper arm's rest frame (same head, direction and roll, 40% length), parented to the scapula.
- **Drive:** 50% of the humeral motion relative to the scapula.
- **Reweighting:** in the W4 shoulder-top zone (1,312 vertices; 1,224 reweighted), a vertex with upper-arm weight wu and girdle weight wg moves 2·min(wu, wg) onto the helper. A 50/50 vertex becomes rigid at half the motion.

## Results (coupled 0–160° motion; collapse / pairs / stretch > 2 / body volume Δ %)

| Elevation | Original 67-joint | Helper, half **rotation** (copy rotation) | Helper, half **swing** (damped track) |
|---|---|---|---|
| 90° | 0 / 0 / 310 / +1.8 | 0 / 0 / 372 / **+5.2** | 0 / 0 / 374 / **+5.2** |
| 120° | 2 / 0 / 424 / −1.4 | 2 / 0 / 670 / +4.3 | 8 / 24 / 664 / +3.0 |
| 140° | 40 / 132 / 432 / −3.6 | **4 / 14** / 776 / +3.1 | 4 / 630 / 718 / −4.4 |
| 145° | 48 / 176 / 428 / −4.0 | 8 / 480 / 546 / **−7.1** (flip) | 4 / 574 / 694 / −5.9 |
| 160° | 42 / 444 / 400 / −5.0 | 4 / 504 / 470 / −7.1 | 10 / 658 / 536 / −7.0 |

**Zone conditioning** (smallest singular value of the blended matrices, worst over 90/120/140/160°):

| Variant | Minimum | Vertices < 0.1 | Vertices < 0.3 | Median |
|---|---|---|---|---|
| Original | 0.0041 | 100 | 282 | 0.676 |
| Half rotation | 0.191 | 0 | 8 | 0.802 |
| Half swing | 0.116 | 0 | 138 | 0.731 |

**M1 shoulder press, worst frame** (collapse / stretch / pairs; volume range):
- original: 48 / 438 / 462; −5.0 … +1.5%;
- half rotation: 8 / 776 / 504; −7.2 … +4.9%;
- half swing: 22 / 742 / 710; −7.0 … +4.9%.

## Why neither drive works as is — and what that means for option A

1. **A helper does fix the conditioning.** No zone vertex stays below σ 0.1, and collapse falls 5–10× wherever the drive is well defined (e.g. 140°: 40 → 4).
2. **But a half-rotation drive measured from this rest pose is not well defined overhead.**
   - Relative to the scapula, the upper arm turns 116° at 90° elevation and about 177° by 140°: the hanging A-pose rest plus the authored axial rotation.
   - Swing–twist decomposition about the humeral axis (`diagnose_shoulder_swing_twist_blender.py`): swing reaches 166° near overhead, where the twist is ill-defined. Twist runs 16° (110°) → 76° (130°) → 158° (140°) → −125° (150°) → −86° (160°).
   - So the half **rotation** flips sides past 180° (volume +3.1 → −7.1% between 140° and 145°).
   - The half **swing** leaves the helper up to 164° away from the upper arm in twist, and re-creates the shoulder-top folding (pairs 630 at 140°).
3. **Volume:** both variants inflate the region by about 3.4 percentage points at 90° (+1.8 → +5.2%). Rigid half-motion skin no longer shrinks, but it overshoots. The transfer fraction would have to be tuned against a volume target.

**Implication for the W3 decision (data, not a recommendation to approve):** a single half-motion helper referenced to the arms-down rest is not enough above about 130°. A viable option A needs one of the following, each still a 67 → 69+ joint contract change:
- a drive referenced to a mid-elevation frame;
- a two-stage helper;
- a continuously tracked (stateful) twist.

Option C (limit the press to 120° for now) is unaffected. Option B (a skinning change, e.g. dual-quaternion) avoids the half-rotation definition problem but changes the Lane G runtime.

## Reproduce

Each command is `PYTHONPATH=<bpy 5.2.1> python3.13 <runner opening the a003 blend> <script>`:
- `scripts/diagnose_shoulder_helper_deformer_blender.py -- --out <json>`, with `DRIVE = "swing"` (default) or `"rotation"`;
- `scripts/diagnose_shoulder_swing_twist_blender.py`.

The press runs reopen the source blend before each benchmark, so the "before" run is uncontaminated.


## Update, 14 Oct (later): continuous and mid-elevation-reference drives

All of this is in memory only. The 67-joint rig, weights, GLB path and a003 are untouched, and nothing is adopted.

**Drives tested** (`scripts/diagnose_shoulder_helper_deformer_blender.py`, `DRIVE`):
- **`stateful`:** each frame, take the axis–angle of the upper arm relative to the scapula on the branch (θ·n or (θ − 2π)·n) closest to the previous frame, then apply half of it. This follows the real path past 180° with no flip. It needs runtime memory.
- **`reference` (stateless, chosen):** take the branch closest to a **fixed mid-elevation reference**, the rotation vector at the 120° coupled pose (unique there, 155° < 180°).
  - At rest it gives the identity.
  - Along the whole coupled 0–160° motion it gives **exactly** the stateful result (identical metrics at every angle).
  - So option A needs one constant vector per side, not runtime state.
  - **Limitation:** this is verified on the coupled elevation path and the nine benchmarks only. Motions far from that path, such as large horizontal adduction or extension behind the back, could pick a different branch and need their own check.

**Weight transfer refinements** (each measured; renders inspected):

| Variant | Pairs at 145/160° | Collapse at 160° | Volume at 160° | Stretch at 160° | Visual |
|---|---|---|---|---|---|
| Original 67-joint | 176 / 444 | 42 | −5.0% | 400 | shoulder-top pinch; posterior armpit point |
| Continuous drive, transfer 1.0 | 36 / 48 | 10 | +2.2% (90°: +5.2%) | 830 | overshoot |
| Transfer 0.6, 4 smoothing passes | 2 / 14 | 4 | −1.3% | 668 | **new crease across the front shoulder top** at the zone edge |
| + 4-ring edge taper | 58 / 110 | 4 | −2.7% | 566 | front crease gone; **new lateral-chest crease** at the zone's lower edge (z = 1.30 m) |
| + 8-ring edge taper | 172 / 234 | 16 | −4.3% | 476 | gains lost |
| **+ zone lowered to z > 1.22 m (selected)** | **58 / 110** | **4** | **−2.0%** | 634 | both creases gone |

**Selected configuration across all nine benchmarks** (`claude_w3a/helper_reference_all_benchmarks.json`):

| Benchmark | Worst pairs | Worst collapse | Other changes |
|---|---|---|---|
| Shoulder press | 462 → **124** (the 90° elbow crease at frame 0, K1's domain) | 48 → **4** | volume −5.0…+1.5 → −2.0…+3.0%; stretch 438 → 634 |
| Bent-over row | 156 → 148 | — | stretch 0 → 2 |
| Grip | 150 → 146 | — | — |
| Squat, lunge, walk, trunk rotation, single-leg stance, calf raise | unchanged | unchanged | — |

**What is still wrong with the selected variant** (phone sheets `claude_w3a/helper_reference_{front,rear,side}_sheet.jpg`):
- **Armpit bulge:** a lump of upper-arm skin at the armpit at 145–160° (side view).
- **Posterior armpit web:** smoother than the original's point pinch, but still a sheet.
- **Stretch:** faces stretched more than ×2 rise by about 230 at 160°.

These are retained as failures. The native test `test_known_cost_stretch_is_recorded_not_hidden` keeps the stretch increase visible.

**Native tests:** `scripts/blender_tests/test_shoulder_helper_reference_drive.py`, 4 pass, run in the benchmark workflow.
- the contract is extended only in memory (69 joints);
- the helper is the identity at rest, with no branch jump from 90° to 160° (steps < 10°);
- pairs at 145°/160° halve or better, collapse falls, and volume loss is smaller;
- the stretch increase is asserted, so it stays visible.

**Status for the W3 decision (owner + Lane G):**
- Option A with a **stateless reference drive** is now the best measured shoulder result.
- It needs 69 deforming joints plus a runtime rule (pick the rotation branch nearest a constant per-side reference vector, then apply half of it).
- It does not reach "no worse folds" yet, because of the armpit bulge and the extra stretch, so it is **not adopted**.
- Options B and C remain open.
