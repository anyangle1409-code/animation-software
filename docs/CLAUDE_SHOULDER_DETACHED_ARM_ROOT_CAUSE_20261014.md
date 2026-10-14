# Why the overhead arm looks detached from the shoulder (Claude, 14 Oct 2026)

**Owner question:** "It almost looks like the arm isn't connected to the shoulders. Why are we getting this deformation?"

**Short answer:** the scapula in the coupled motion rotates the wrong way. It is driven about the runtime bone's arbitrary
local axes, not the anatomical scapula frame. Overhead, the arm therefore has to turn about 160° relative to the shoulder
blade, and no skin blend between two frames that far apart can hold together. The deltoid skin stays on the trunk as a
"shelf" and the arm leaves from underneath it.

Two further defects add to it:
- the scapula's skin weights reach too far down the back and side;
- the arm's pivot sits 53 mm above the anatomical shoulder joint.

All measurements are on the unchanged a003 runtime rig. Everything here is diagnostic; nothing is changed or approved.

Evidence (phone sheets):
- `ORIGINAL_V1_WORK/anatomy/audit/claude_shoulder_rootcause_20261014/shoulder_rootcause_sheet.jpg`
- `.../shoulder_collapse_map_sheet.jpg`

Scripts: `scripts/diagnostics/shoulder_rootcause_*.py` and `scripts/original_v1_scapula_isb_drive.py`.

## Findings

### 1. Scapular upward rotation has the wrong sense (primary cause)

`build_functional_original_coupled_motion_blender.apply_coupled_pose` (PR110 lineage) sets
`scapula.matrix_basis = _rotation(x=posterior_tilt, y=±internal_rotation, z=±upward_rotation)`, an Euler rotation in the
**bone's** local frame. The `scapula_r` bone runs infero-medially. Its local axes in world are:

| Axis | Direction | Meaning |
|---|---|---|
| X | (0.88, 0.41, −0.23) | mostly lateral |
| Y | along the bone | — |
| Z | (−0.23, 0.80, 0.55) | mostly **posterior**; the axis used for "upward rotation" |

Measured with each component applied alone:
- **+30° "upward rotation" on `_r`:** the glenoid (upper-arm head) moves **21 mm down**, and the inferior end moves **36 mm toward the spine**. That is anatomical **downward** rotation.
- **+30° "posterior tilt":** moves the glenoid 36 mm down and 32 mm forward.
- **Through the coupled press:** the runtime scapula's lower end rises 121 mm and moves 58 mm toward the spine.

The arm itself is aimed in world space, so it reaches the right direction regardless. The blade turning the wrong way means
the arm's rotation **relative to the scapula** becomes roughly elevation **plus** scapular rotation:

| HT elevation | Scapula vs thorax | Arm vs scapula, today | Arm vs scapula, anatomical-frame drive |
|---|---|---|---|
| 45° | 10° | 54° | 41° |
| 90° | 29° | 116° | 85° |
| 120° | 41° | 155° | 116° |
| 160° | 48° | 162° | 152° |

The 160° value still includes the authored humeral external rotation, about 10°.

### 2. Two-bone skin blending fails near 180°

The deltoid cap is only **48 % upper-arm** weighted; the other 52 % is clavicle and scapula. Upper-arm skin 6–12 cm below
the joint is still 33 % torso-bound.

With the two influences about 160° apart:
- the blended skinning matrix becomes nearly singular (σmin 0.004; 133 skin vertices below 0.3);
- the skin collapses into the shelf and tear (collapse map sheet).

**Dual-quaternion skinning** (Blender "Preserve Volume") was tested as a check and makes it far worse: the skin tears and
balloons, with pairs 444 → 662. Near 180° the quaternion blend flips hemispheres. So the fix has to reduce the relative
rotation, not change the blending method.

W3A, S1 and R1–R3 were patches over this symptom. They cut the near-singular vertices from 133 to 18 but could not remove
the shelf.

### 3. Scapula weights reach too far

With the scapula rotating correctly (inferior angle swinging laterally), the back and side skin weighted to it flares
outward: volume +6.2 % and a large lateral bulge. In a real body the blade glides under that skin.

**Diagnostic fix:** taper the scapula's weight from full at 10 cm from the AC joint to zero at 18 cm, handing the remainder
to the thorax (`spine_03`/`spine_02`). This removes the flare.

### 4. The arm pivot is too high

The runtime `upperarm` head (the arm's pivot) is at z = 1515 mm. The anatomical glenohumeral (GH) centre landmark is at
z = 1462 mm, so the pivot is **53 mm high**. The pivot sits only 21 mm under the top skin, 42 mm under the lateral skin.

- **In-memory test:** lowering the pivot 15–25 mm cuts stretch at 160° from 400 to 290–326, but volume loss rises slightly (−5.0 → −5.6 %). It is secondary to finding 1.
- **This is a frozen canonical-bone question:** it needs an owner decision and was not changed.

## Measured at 160° (collapse / stretch > 2 / pairs / volume)

| Configuration | Collapse | Stretch | Pairs | Volume |
|---|---|---|---|---|
| a003 today | 42 | 400 | 444 | −5.0 % |
| Anatomical-frame (ISB) scapula drive | 60 | 684 | 158 | +6.2 % |
| ISB drive + scapula weight taper (10–18 cm) | 60 | 430 | 160 | −0.3 % |
| (R3, the current review candidate) | 4 | 542 | 106 | −2.0 % |

**Visually**, ISB drive + taper is the first configuration where the arm reads as attached from the front and rear, and the
back stays smooth. What remains:
- a posterior-axillary skin curl, visible from the side;
- 60 collapsed faces, concentrated in that curl.

R3's numbers look better only because W3A/S1 were tuned to the wrong drive. They hide the shelf rather than remove its
cause.

## What this means and next steps

1. **The coupled-motion scapula drive needs the anatomical-frame fix.** Upstream, this is a motion-layer change for Work/Lane
   G: posted on PR #26. `scripts/original_v1_scapula_isb_drive.py` is a review-only wrapper. It builds the ISB frame from
   the model's own landmarks (AA, TS, AI), applies ISB order (internal rotation, upward rotation, posterior tilt) about the
   AC joint with geometrically checked signs, and re-aims the arm. It is bilaterally exact (mirror error 0.0 mm).
2. **Rebuild the shoulder correction on the corrected drive:** a scapula weight taper, then re-solve the W3A helper and S1
   relax (or drop them if no longer needed), aiming at the posterior-axillary curl. This becomes the next review
   candidate (R4).
3. **The arm pivot height** (53 mm above GH) needs an owner decision on the canonical upper-arm bone.
