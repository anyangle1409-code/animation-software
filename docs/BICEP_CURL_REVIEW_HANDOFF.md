# Home Gym PT — Bicep Curl Review Handoff

**Prepared:** 2026-09-14  
**Working branch:** `chatgpt/absolute-retarget-imports`  
**Current retained head before this handoff update:** `b2a7db71adea054383d22282e3660a04e78d9a62`  
**Do not merge yet.**

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

Latest full validation after the grip-review pass: **285 passed, 1 optional real-character diagnostic skipped, across 35 test files.** TypeScript and production build both pass. Existing notes only: Vite >500 kB chunk advisory and the already-known npm audit report of 2 moderate vulnerabilities.

## Character assets

### Proven baseline — keep safe

`HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` version 5  
SHA-256: `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`

This remains the proven asset and has **not** been overwritten.

### Historical review-only outer-elbow asset

`HomeGymPT_Male_HAND_REPAIR_OUTER_ELBOW_CANDIDATE.glb`  
SHA-256: `8e8df9e8adcf43e0e6473bf98efadb05a31075031f9124787429ec2aedca99e4`

Its mesh/skeleton/BIN payload are the same as v5; metadata enabled the measured directional outer-elbow smoothing. The software now exposes the same bounded outer-smoothing candidate through the live character-level corrective control, so **re-importing this GLB is no longer necessary for ordinary 0–100% A/B review**. Keep it only as historical/reproducible evidence. Do not overwrite v5 with it.

The directional outer pass remains capped at **8 mm** additional bind-space displacement, is zero at extension, and stays separate from the retained radial elbow-volume corrective.

## Next visual review order

1. Load the proven v5 character with **Dumbbell Bicep Curl**. Keep authored grip closure at **85%** initially.
2. In Review, judge the whole rep once at normal speed: relaxed shoulders, still torso, natural elbow path, neutral wrist and rigid dumbbells.
3. Use the default forearm Movement Review / **Focus review joint** and inspect the live elbow through the rep. Do not change motion based only on the old three-frame offline preview; the current numeric motion diagnostics are clean.
4. Set the playhead to **Peak (2.00s)**. In Correctives, keep the exact same frame/camera and tap **0 / 25 / 50 / 75 / 100%**. Judge outer elbow contour, flattening, pinching and whether the bend reads like flesh around a joint rather than a hinge.
5. If needed, run **Compare 0–100%** to see strain at each candidate's worst P99 frame. Use strain as supporting evidence only; do not let it choose the visual winner automatically.
6. Keep a non-zero permanent outer corrective only if it is clearly more human at peak **and** remains natural through bottom/mid/return. The authored baseline remains the fallback.
7. In Grip, compare **85 / 80 / 75 / 70 / 65%** on the same frame, then use the direct **Bottom / Mid lift / Peak / Mid lower / Return** buttons. Judge all four fingers around the handle, thumb opposition, palm loading, dumbbell centring/rigidity and left/right symmetry.
8. Also inspect shoulder-press start before permanently lowering global closure; the same hand model must still work outside the curl.
9. If one global closure cannot solve thumb/pinky overlap without making another digit too open, move to **per-digit closure trims** on the real imported character. Do not translate the whole dumbbell as the first fix and do not revive direct source-Rigify finger rotations.
10. Only after elbow silhouette **and** grip are visually accepted should the curl be treated as the template for scaling to more exercises.

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

The shared `AI_CHANGELOG.md` contains the detailed implementation reasoning and validation history. Claude should read **both** that changelog and this handoff before making the next curl change.
