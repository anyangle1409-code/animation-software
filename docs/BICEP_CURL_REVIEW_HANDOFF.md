# Home Gym PT — Bicep Curl Review Handoff

**Prepared:** 2026-09-14  
**Working branch:** `chatgpt/absolute-retarget-imports`  
**Do not merge yet.**

## Retained curl state

The bicep curl remains the validation template. Its accepted motion still uses a 5.5-second repetition, 6° → 126° elbow flexion, 72° → 80° supination, relaxed 5° clavicle depression, and only a small 0° → 4° late upper-arm drift. The elbow leads the concentric; the upper arm waits until 55% of the lift and uses minimum-jerk easing. On the eccentric the elbow opens first and the upper arm waits 20% before settling.

The Studio now also has:

- **Grip closure** live tuning in the Exercise panel. Default remains 85%; changing it regenerates through the real production pipeline and is undoable.
- **Focus selected** camera mode. Select an elbow, hand or other joint, choose `Focus selected`, and the camera follows that joint during playback. Switch to `Free orbit` to keep the close-up and inspect manually.
- Stricter curl technique guardrails that catch shrugging shoulders, excessive upper-arm takeover, loss of supination, sideways wrist deviation, torso swing, elbow drift and the pre-existing wrist/stance/symmetry faults.

Latest full validation after the guardrail pass: **207 passed, 1 optional real-character diagnostic skipped, across 20 test files.** TypeScript and production build pass. The only build note is the existing >500 kB Vite chunk advisory.

## Character candidates

### Proven baseline — keep safe

`HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` version 5  
SHA-256: `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`

This remains the proven candidate and has **not** been overwritten.

### Review-only outer-elbow candidate

`HomeGymPT_Male_HAND_REPAIR_OUTER_ELBOW_CANDIDATE.glb`  
SHA-256: `8e8df9e8adcf43e0e6473bf98efadb05a31075031f9124787429ec2aedca99e4`

Its mesh, skeleton and binary payload are the same as v5. Only metadata adds `elbowCorrective.outerSmooth: 1.0`. It activates with measured elbow flexion, is zero at extension, follows the source surface curvature and caps extra bind-space displacement at 8 mm.

Offline measurements improve modestly, but the visual difference is deliberately subtle. **Do not promote it without the live A/B review.**

## Tomorrow's review order

1. Load v5 with Dumbbell Bicep Curl and leave Grip closure at **85%**.
2. Use three-quarter/full view once to judge the whole rep: shoulders relaxed, torso still, elbows natural, no wrist flick.
3. Select the left or right forearm/elbow area and choose **Focus selected**.
4. Scrub/play bottom, mid-concentric, peak hold, mid-eccentric and return to bottom.
5. Re-import the OUTER_ELBOW candidate and repeat the same elbow close-up.
6. Keep `outerSmooth` only if the outer elbow contour is clearly more human in motion and does not look flattened or over-smoothed.
7. For grip, return to v5 or the accepted elbow candidate and compare **85 / 80 / 75 / 70 / 65%** closure. Check curl bottom/mid/top and shoulder-press start.
8. Choose a lower permanent closure only if all four fingers still enclose the handle securely, the thumb remains opposed, the palm looks loaded, the dumbbell stays centred, and left/right remain symmetric.
9. If global closure cannot fix the remaining thumb/pinky overlap, the next step is **per-digit grip shaping** on the real imported character—not moving the whole dumbbell and not direct source-bone approximations.

## Grip collision baseline

At the authored 85% closure, saved production-path evidence gives 103 surface vertices per hand inside the 15 mm-radius dumbbell handle:

- palm/hand: 30, max penetration 14.57 mm
- thumb: 28, max 13.18 mm
- pinky: 25, max 12.53 mm
- ring: 9, max 8.90 mm
- index: 8, max 6.91 mm
- middle: 3, max 3.62 mm

The concentration on palm/thumb/pinky is why translating the whole dumbbell is not the preferred first fix.

## Rejected experiments — do not revive blindly

- Amplifying the existing radial elbow morph — adds bulk without fixing the angular silhouette.
- Local elbow subdivision — denser topology but worse local compression and insufficient visual benefit.
- Broad shoulder-weight smoothing — previously worsened strain.
- Direct source-Rigify finger rotations as a proxy for lower grip closure — does not reproduce the preserved absolute-retarget production pose closely enough.
- Blind whole-dumbbell translation to fix grip penetration.

## Useful retained commits

- `e2ebca5` — live grip closure tuning.
- `9126b7b` — selected-joint focus camera.
- `d2b3a24` — bicep-curl realism guardrails.

The shared `AI_CHANGELOG.md` contains the detailed reasoning and measurements from the earlier elbow, retarget, hand and timing work.
