# ORIGINAL_v1 foot: ball breadth stage and posed sweep (Claude, 13 Oct 2026)

**Status: review candidates, not accepted.** This is mesh-only work. The a003 source and the frozen skeleton are untouched, and C3 still awaits owner sign-off.

## F4: ball breadth (mesh-only)

**Evidence.** ANSUR II male horizontal foot breadth at 1.82 m is **104.1 ± 4.7 mm** (OLS on stature, n = 4,082). The a003, C2 and C3 feet measure **94.6 mm** across the metatarsal heads, within ±15 mm of the ball line and below 40 mm height. The metatarsal-head stations are unchanged; only the soft tissue around them widens.

**Change.** `scripts/build_original_foot_breadth_candidate_blender.py`:
- Per 2 mm slice, x is scaled about the slice centre.
- The weight is 1 within ±15 mm of the ball line, fading to 0 at ±45 mm, so the heel and toes are untouched.
- Height fades from 30 mm to 70 mm, so the dorsum is untouched.
- The scale is solved as **×1.100** (at most 4.8 mm per side).
- Mirrored to the other foot; y and z never change.

**Checks (both PASS).** Topology, groups and weights unchanged; only foot-region x moved; symmetry 0; all foot bone stations still inside the skin; ball breadth 104.1 mm.

| Candidate | Parent | File (SHA-256) |
|---|---|---|
| C2W | C2 (a003 skeleton, 309.2 mm) | `breadth/HGPT_ORIGINAL_V1_FOOT_C2W_CLAUDE.blend` (`2e9f1145…`) |
| C3W | C3 (skeleton candidate, 279.9 mm) | `breadth/HGPT_ORIGINAL_V1_FOOT_C3W_CLAUDE.blend` (`ed6c940b…`) |

**Heel: not changed (open question).** ANSUR heel breadth at 1.82 m is 73.7 ± 5.3 mm. On this mesh the answer depends on where the heel is measured:
- 82.6 mm across the heel–midfoot transition at the ankle line;
- 58.2 mm (a003/C2) or 60.7 mm (C3) across the heel proper, 20 mm or more behind the ankle-joint centre.

The ANSUR landmark (widest heel, behind the malleoli) cannot be placed unambiguously, so the heel zone is opt-in (`--heel`) and was not used.

**Still open in F4:** lesser-toe girth (the toes stay thin), and nails (no nail geometry exists).

## F6: posed deformation sweep

`scripts/verify_original_foot_posed_sweep_blender.py` runs forward kinematics with the leg fixed. It has no ground contact or IK and makes no gait claim. Both sides are posed about local X:
- `foot_*` at −30, −15, +10 and +20°;
- `toe_*` at −50 (toe-off dorsiflexion), −30 and +30°.

Results over the foot faces:

| Model | Collapse (< 0.1) | Stretch (> 2) | Self-intersecting pairs | Min area ratio (worst pose) |
|---|---|---|---|---|
| a003 | 0 at every pose | 0 | 0 | 0.450 (foot −30) |
| C2W | 0 | 0 | 0 | 0.450 (foot −30) |
| C3W | 0 | 0 | 0 | 0.450 (foot −30); toe +30: 0.530 (a003 0.690) |

Full table: `breadth/foot_posed_sweep.json`.

**Visible.** Toe-off bends all five toes as one block at the runtime toe line. Individual MTP/IP motion needs the 95-control toe rig (Work PR105), which may not replace the 67-joint app rig. That is blocked on an owner and Lane G decision (ledger F5). C3 keeps its small dorsal dip in front of the ankle.

## Phone review sheets

All sheets are in `ORIGINAL_V1_WORK/anatomy/candidates/claude_foot_20261013/breadth/`:
- `sheets_c2w/` and `sheets_c3w/`: neutral, a003 above and the candidate below;
- `sheets_*_toeoff/`: toe −50°.
