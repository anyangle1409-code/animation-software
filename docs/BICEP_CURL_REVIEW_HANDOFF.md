# Home Gym PT — Bicep Curl Review Handoff

**Prepared:** 2026-09-14  
**Working branch:** `chatgpt/absolute-retarget-imports`  
**Audited retained production head:** `4e34c043a04b81585aaae54e826b994cade0c6eb`  
**Audit scope:** documentation and branch hygiene only; no Studio or motion change.  
**Do not merge yet.**

## Review status — 2026-09-15

Three of the four questions this handoff opened are now closed.

**Curl motion — visually accepted. Do not reopen.** All 166 clip frames were measured on
the imported v5 through the production path, and the rep was watched at 1× and 0.25×. Worst
hand-path jerk 0.595 mm; dumbbell position jerk 0.879 mm; dumbbell rotation jerk 0.187°;
elbow jerk 0.164° at a maximum 3.14°/frame (94.2°/s, matching the retained profile); wrist
0.004°/frame. Clavicle world-Y travel 0.00 mm, so there is no shoulder hike. Mirrored hand
mismatch 0.00 mm. The handle sits 101.83 mm from the hand bone with 0.000 mm variation
through the rep, so the dumbbells are rigid and contact is never lost.

**Elbow corrective — stays at 0%.** The bounded directional outer pass is visually inert at
Peak: 402 of 1,369,000 pixels change between 0% and 100%, silhouette contour moves ≤ 1 px,
and strain is unchanged (P99 55.7% at all five settings). The 72 vertices per side move
7.77 mm in bind space but only 4.65 mm posed, of which 0.55–0.75 mm mean is perpendicular to
any candidate camera.

**Global grip closure — stays at 85%.** The relationship runs opposite to this document's
earlier assumption: 85% gives reach use 93% "Within envelope", and *lowering* closure
*raises* reach use (80% → 98%, 75% → 104% "Review fit", 70% → 110%, 65% → 116%). At 65% the
fingers visibly detach from the handle at Bottom.

Do **not** infer per-digit closure direction from `digitReachUse` alone. It is a geometric
distance relative to the allowed reach envelope; a lower percentage does not mean a looser
finger and a higher one does not mean a tighter finger. The saved collision evidence shows
substantial pinky penetration at the authored grip, which points the other way.

### Promoted 2026-09-15

**The baseline character is now `HomeGymPT_Male_BASELINE_v6.glb`**, SHA-256
`46180b5741216f823e4f1e0030a06d65fff0f10bd1d7b132e4c36a0814a410ed` — the approved
hand/wrist handover weight repair, byte-identical to the candidate that was reviewed. The
studio ships it dressed, as `HomeGymPT_Male_BASELINE_v6_SHORTS.glb`
(`0761fb048510a80ce4aa8835f05a0007697086dcc60cd46a1ddb6e8ccc47b0d6`), with the bare body
registered alongside it so deformation can still be reviewed on skin. Proven v5 is retained
untouched as the fallback and still hashes to `dfb0fea6…`.

### Promoted 2026-09-16 — baseline v7

**The baseline character is now `HomeGymPT_Male_BASELINE_v7.glb`**, SHA-256
`54222af34402281351b60d8bc2fb66f7e3fdf77d2c03eb869b5581d03adb16c4` — baseline v6 plus the
approved shoulder-slope candidate B, geometry bit-identical to `SHOULDER_B.glb`. The studio
ships it dressed, as `HomeGymPT_Male_BASELINE_v7_SHORTS.glb`
(`a5bec8fac0ce014d2ce96bcdb7b4cb846cfc65ee92ef5364f08ca0f7a2976f66`), carrying the approved
front-crotch garment F3. Promotion chain: proven v5 → v6 (hand/wrist weights) → v7 (shoulder
slope B), garment F3. v6, v6 dressed and v5 are all retained untouched at the hashes above,
and the skeleton, inverse binds, weights, topology, UVs and vertex colours are unchanged
throughout, so the curl motion, the 0% elbow corrective, the 85% grip closure, retargeting
and the exercise definitions are all untouched by this promotion.

Neither promotion reopened the curl motion, the elbow corrective or global grip closure.

### What is still open
1. **Palm loading and thumb opposition** at 85% closure. The underside review shows the
   weight hanging in the finger hooks with a visible palm gap, and weak thumb opposition.
   The weight repair leaves both unchanged, deliberately. This is a separate visual
   decision, to be taken after the deformation fix is accepted.
2. **Dumbbell/thigh overlap at the curl bottom.** A true 3D intersection, not screen-space
   occlusion: closest approach −5.86 mm (left) and −5.81 mm (right), with three thigh
   vertices inside a plate on each side. Documented, not fixed — every sanctioned lever
   costs more than the 6 mm it buys, and whole-dumbbell translation remains rejected.
3. **Push-up wrist extension.** *(Future exercise-definition fix — deliberately not part
   of the character promotion.)* Re-measured anatomically on 2026-09-15: the earlier
   115.4°/102.6° pair were quaternion magnitudes, not wrist angles. The **pull-up is fine**
   — almost all of its figure is forearm pronation (79–101°, normal for an overhand grip),
   true angulation never exceeds 53°, and no change is needed. The **push-up is real**:
   102.7° of wrist extension at the top of the rep and 74.8° at the bottom, against a
   typical human limit of 70–80°, because the shoulder sits 218 mm ahead of the hand and
   the forearm leans 25° off vertical instead of standing up. Fixing it means moving the
   hand contact forward roughly 20 cm, which is an exercise-definition change and has
   **not** been made. See `AI_CHANGELOG.md`.
4. **A −15 mm deep-squat reading** at the front of the pelvis where the shorts panel meets
   the body. Measured, not visible in any capture, and unexplained rather than dismissed —
   see `docs/SHORTS_CANDIDATE_REVIEW.md`.

## CLAUDE — START HERE TOMORROW

1. Read `AI_CHANGELOG.md` and this handoff before changing anything.
2. Checkout `chatgpt/absolute-retarget-imports`. The character is now **baseline v7**, registered automatically from `public/characters/` — `HomeGymPT_Male_BASELINE_v7.glb` for deformation review, `HomeGymPT_Male_BASELINE_v7_SHORTS.glb` as the shipped default. Baseline v6, v6 dressed and proven v5 (`dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`) are the retained fallbacks; use them for A/B, not as the working character.
3. Do **not** rewrite the curl motion. Its measured movement is mechanically clean, and it is now visually accepted as well.
4. The elbow corrective stays at **0%** and global grip closure stays at **85%**. Both comparisons are complete; do not rerun them as new work.
5. Do not revive rejected subdivision, broad shoulder smoothing, whole-dumbbell translation, destructive rebind, or direct Rigify-finger experiments.
6. Make a permanent change only after a live same-frame visual comparison. Record the chosen document identity, character identity and deformation revision with the approval.

The remaining visual work is the four open items listed above.

## Final branch hygiene audit

At audited production head `4e34c043a04b81585aaae54e826b994cade0c6eb`, the tracked tree contains no `.github` workflow, temporary Python helper, scratch output or unfinished experiment artifact. Files named `*Diagnostics.ts` and their tests are retained production review controls with validation coverage; they are not temporary files. This final audit adds documentation only, so the latest validated code state remains **287 passed, 1 optional real-character diagnostic skipped, across 36 test files**, with TypeScript and production build passing. No workflow was rerun for this documentation-only change.

## Retained curl state

The bicep curl remains the validation template. Its accepted motion still uses a 5.5-second repetition, 6° → 126° elbow flexion, 72° → 80° supination, relaxed 5° clavicle depression, and only a small 0° → 4° late upper-arm drift. The elbow leads the concentric; the upper arm waits until 55% of the lift and uses minimum-jerk easing. On the eccentric the elbow opens first and the upper arm waits 20% before settling.

A fresh production-path motion report on the retained curl found:

- elbow maximum angular speed: **94.2°/s** on flexion/extension
- elbow maximum angular acceleration: **147.8°/s²**, at the transition into the peak hold
- largest keyframe velocity discontinuity: only **2.47°/s**
- resolved left/right mirror mismatch: **0° max / 0° RMS**
- elbow drift relative to the shoulder: **21.55 mm max**, at the contracted position
- elbow return error: **0 mm**
- concentric elbow excursion: **120.266°**; meaningful elbow motion begins around 15% of the segment
- concentric upper-arm contribution: **4.123°**; meaningful support motion begins around 65% of the segment, about **1.0 s after** elbow onset
- eccentric upper-arm support begins around 36.7% of the return segment, about **0.433 s after** elbow onset
- clavicle motion during the rep: **0°**

These measurements do **not** support another speculative curl-motion change. The shoulders are not being actively hiked, bilateral motion is exact, the transition is smooth, and the elbow drift is the intentionally small late upper-arm contribution. Remaining visual concerns should therefore be treated first as **peak-elbow surface/silhouette** and **hand/dumbbell contact** issues.

## Studio review tools now available

- **Consolidated Movement Review** in Review: selected-joint speed, acceleration, keyframe continuity, bilateral mismatch and spatial drift are shown together with direct jump/focus actions. Dumbbell Bicep Curl defaults to `forearm_l` when no joint is selected.
- **Focus selected** camera follows the selected elbow/hand/joint during playback.
- **Joint transition continuity** localises velocity discontinuities at authored phase boundaries.
- **Resolved bilateral motion symmetry** compares final sampled motion using the rig's real mirror transform, not raw Euler-value guesses.
- **Spatial joint path** measures joint movement relative to its anatomical parent; selecting a forearm directly measures elbow wander relative to the shoulder while removing root translation.
- **Grip closure** remains live, undoable and production-path generated. Authored default is still **85%**.
- **Fine grip review presets:** **65 / 70 / 75 / 80 / 85%** without changing playhead, wrist or dumbbell placement.
- **Curl grip review frames:** Bottom 0.00s / Mid lift 1.00s / Peak 2.00s / Mid lower 4.00s / Return 5.00s.
- **Per-digit grip trims** remain available for thumb/index/middle/ring/pinky if global closure cannot solve a local overlap.
- **Grip worst-point review** can jump to each digit's worst measured frame through the whole rep.
- **Corrective tuning** is character-level and export-aware. The active viewport and GLB export sampler share the same value.
- **Same-frame corrective presets:** **0 / 25 / 50 / 75 / 100%**; these change only corrective strength and deliberately leave the playhead on the exact same frame.
- **Corrective strain sweep:** on-demand 0/25/50/75/100% whole-rep P99/max scan. It restores the pre-scan tuning/pose and can jump to each candidate's worst P99 frame.
- **Correctives on / Raw skinning** remains a viewport-only A/B and does not alter the clip/source mesh/export. Production visual sign-off is disabled in Raw skinning, and any permanent export-aware corrective change increments the character deformation revision so an older sign-off cannot remain valid.

Latest full validation after the deformation-aware visual-review pass: **287 passed, 1 optional real-character diagnostic skipped, across 36 test files.** TypeScript and production build both pass. Existing notes only: Vite >500 kB chunk advisory and the already-known npm audit report of 2 moderate vulnerabilities.

## Character assets

### Proven baseline — keep safe

`HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` version 5  
SHA-256: `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`

This remains the proven asset and has **not** been overwritten.

### Hand/wrist weight repair candidate — awaiting approval

`HomeGymPT_Male_HAND_WRIST_WEIGHT_CANDIDATE.glb`  
SHA-256: `46180b5741216f823e4f1e0030a06d65fff0f10bd1d7b132e4c36a0814a410ed`

Skin weights only, at the `DEF-hand.*` ↔ `DEF-f_{index,middle,ring,pinky}.01.*` rings and
the `DEF-forearm.*.001` ↔ `DEF-hand.*` ring, both sides. Topology, bind geometry, skeleton,
inverse binds, UVs, colours and the other joint/weight sets are byte-identical to v5. Full
diagnosis, cap selection and before/after measurements are in
`docs/CHARACTER_CANDIDATE_REPAIR.md`. Not promoted; v5 remains the proven asset and the
fallback.

### Historical review-only outer-elbow asset

`HomeGymPT_Male_HAND_REPAIR_OUTER_ELBOW_CANDIDATE.glb`  
SHA-256: `8e8df9e8adcf43e0e6473bf98efadb05a31075031f9124787429ec2aedca99e4`

Its mesh/skeleton/BIN payload are the same as v5; metadata enabled the measured directional outer-elbow smoothing. The software now exposes the same bounded outer-smoothing candidate through the live character-level corrective control, so **re-importing this GLB is no longer necessary for ordinary 0–100% A/B review**. Keep it only as historical/reproducible evidence. Do not overwrite v5 with it.

The directional outer pass remains capped at **8 mm** additional bind-space displacement, is zero at extension, and stays separate from the retained radial elbow-volume corrective.

## Next visual review order

Steps 1–3 below are complete: the curl motion is visually accepted, the elbow corrective is
settled at 0% and global closure at 85%. What follows is the remaining order.

1. ~~Judge the whole rep at normal speed.~~ Done; accepted.
2. ~~Compare elbow corrective 0 / 25 / 50 / 75 / 100% at Peak.~~ Done; 0% retained.
3. ~~Compare grip closure 85 / 80 / 75 / 70 / 65%.~~ Done; 85% retained.
4. ~~Review the hand/wrist weight repair candidate against proven v5.~~ Done; approved and
   promoted as baseline v6. The shorts layer was approved and promoted with it.
5. Decide **palm loading and thumb opposition** separately, on
   the underside view at Bottom and Peak. Per-digit trims are the tool for that, not global
   closure, and not `digitReachUse` percentages on their own.
6. Leave the ~6 mm dumbbell/thigh overlap documented. Do not translate the whole dumbbell,
   change stance or change the curl motion to fix it.
7. Only once hand deformation **and** grip contact are visually accepted should the curl be
   treated as the template for scaling to more exercises.

## Grip collision baseline

At authored 85% closure, saved production-path evidence against the strict 15 mm-radius / 120 mm handle cylinder gives 103 surface vertices per hand inside the handle:

- palm/hand: 30, mean penetration 6.45 mm, max 14.57 mm
- thumb: 28, mean 6.26 mm, max 13.18 mm
- pinky: 25, mean 5.66 mm, max 12.53 mm
- ring: 9, mean 3.88 mm, max 8.90 mm
- index: 8, mean 3.90 mm, max 6.91 mm
- middle: 3, mean 1.66 mm, max 3.62 mm

The concentration on palm/thumb/pinky is why whole-dumbbell translation remains a poor first fix. Collision count alone is **not** sufficient reason to lower closure; secure visual wrap still wins.

## Rejected experiments — do not revive blindly

- Amplifying the existing radial elbow morph — adds bulk without fixing the angular silhouette.
- Simple/local/outer-only elbow subdivision — denser topology but insufficient visual benefit and/or worse local compression.
- Broad shoulder-weight smoothing — worsened strain.
- Raised-arm-only shoulder/axilla radial corrective — too little visible gain and more compression.
- Wrist relative morph prototype — outward puff with no useful strain improvement.
- Deep-squat heavier hip smoothing / forward hip morph — no useful visible/measured gain.
- Direct source-Rigify finger rotations as a proxy for lower grip closure — does not reproduce the preserved absolute-retarget production pose closely enough.
- Blind whole-dumbbell translation to fix grip penetration.
- Destructive rebind of the imported character. Preserve-source-skeleton absolute anatomical retargeting remains mandatory.

## Useful retained commits

- `e2ebca5` — live grip closure tuning.
- `9126b7b` — selected-joint focus camera.
- `d2b3a24` — bicep-curl realism guardrails.
- `8cd8bd1` — export-aware elbow corrective tuning.
- `42a2136` — corrective candidate sweep.
- `ba55b08` — joint transition continuity diagnostics.
- `50e4188` — resolved bilateral motion diagnostics.
- `7445ef4` — spatial joint-path diagnostics.
- `9451538` — consolidated movement review diagnostics.
- `f6c1ce9` — same-frame corrective presets.
- `b2a7db7` — fine grip review controls and curl review frames.
- `1edbd65` — visual sign-off bound to production deformation state.

The shared `AI_CHANGELOG.md` contains the detailed implementation reasoning and validation history. Claude should read **both** that changelog and this handoff before making the next curl change.
