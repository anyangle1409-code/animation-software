# W3 option A — shoulder-top helper deformer: in-memory feasibility data (Claude, 14 Oct 2026)

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
