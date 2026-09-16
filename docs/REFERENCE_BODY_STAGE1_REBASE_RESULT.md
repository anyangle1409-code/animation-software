# Stage 1 — upper-arm neutral rebase: retained

Executing `docs/REFERENCE_BODY_STAGE1_REBASE_TEST.md`. The +4.3° neutral rebase
**passes every acceptance criterion and is retained**. Nothing promoted or
merged; Stage 2 has not started.

The asset is unchanged — this is a motion change only. Candidate remains
`HomeGymPT_Male_STAGE1_CANDIDATE.glb`
(`c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`).

## What changed

`src/exercises/definitions/bicepCurl.ts`, two poses, one channel:

| | before | after |
|---|---|---|
| `startPose.upperarm_l/r.x` | 0° | **4.3°** |
| `peakPose.upperarm_l/r.x` | 4° | **8.3°** |

Both moved by the same +4.3°, which is what makes it a rebase of the neutral
rather than a reshaping of the curve. Abduction (`z`) untouched at ∓3° and ∓4°.

## 1. Relative-motion preservation — exact

Sampling the accepted clip and the rebased clip every 0.05 s across the full
5.5 s rep, for both `upperarm_l` and `upperarm_r`:

**Worst deviation from +4.3°: 0.000000°.**

| t | accepted | rebased | Δ | relative to own baseline |
|---|---|---|---|---|
| 0.0 s | 0.0000° | 4.3000° | 4.3000° | 0.0000° |
| 0.5 s | 0.0000° | 4.3000° | 4.3000° | 0.0000° |
| 1.0 s | 0.0000° | 4.3000° | 4.3000° | 0.0000° |
| 1.5 s | 1.5867° | 5.8867° | 4.3000° | 1.5867° |
| 2.0 s | 4.0000° | 8.3000° | 4.3000° | 4.0000° |
| 3.3 s | 4.0000° | 8.3000° | 4.3000° | 4.0000° |
| 5.0 s | 0.0000° | 4.3000° | 4.3000° | 0.0000° |
| 5.5 s | 0.0000° | 4.3000° | 4.3000° | 0.0000° |

The relative column reproduces the accepted curve exactly: quiet while the elbow
leads, the delayed drift beginning by 1.5 s, the full 4° for the squeeze, and a
clean return to neutral. Timing and easing are untouched because neither was
edited.

## 2. The behavioural test, generalised not weakened

`src/animation/animation.test.ts > "lets the elbow lead while the upper arm
stays quiet early in the curl"` now measures against the curl's own start-pose
neutral instead of a hard-coded zero. It proves the same behaviour and one thing
more:

- elbow flexion at 1.0 s still > 50°;
- upper-arm drift from baseline at 1.0 s is 0 to six decimals, **both sides**;
- at 1.5 s the drift has begun and is still below the full 4°;
- at 3.3 s the drift is 4° to six decimals;
- **new:** at 5.5 s the drift is back to 0 to six decimals on both sides, so the
  loop is asserted to close on the neutral it started from.

Every tolerance is as tight as before. The only thing that changed is what zero
is measured from.

## 3. Clearance — re-measured on the retained curve

| Frame | clearance L / R | vertices inside | region |
|---|---|---|---|
| **Bottom** | **+1.74 / +1.82 mm** | 0 / 0 | upper thigh |
| Mid lift | +214.91 / +214.98 mm | 0 / 0 | upper thigh |
| Peak | +201.17 / +201.17 mm | 0 / 0 | pectoral |
| Mid lower | +240.36 / +240.44 mm | 0 / 0 | upper thigh |
| **Return** | **+1.74 / +1.82 mm** | 0 / 0 | upper thigh |

The Bottom figure survived the full-curve rebase unchanged, as it must — the
start pose is the same. Every other frame improved: Mid lift +40 mm, Peak
+12 mm, Mid lower +40 mm against the accepted curve. No new hip, pelvis, groin
or other body contact appeared anywhere. Bilateral mismatch ≤ 0.09 mm.

## 4. Technique and invariants

`validateClip` over the complete loop, 83 frames: **zero violations, loop
closed**, covering `elbow_not_inward_l/r`, `elbow_under_shoulder_l/r` and
`shoulder_quiet_l/r`. The late absolute value is 8.3°, inside the shoulder-quiet
envelope of [−5°, +10°] — verified by the rule passing, not assumed.

Unchanged: forearm 14.86%, shoulder bind chain, abduction 3°, elbow flexion
6° → 126° (asserted separately and still passing), 5.5 s timing and phase
structure, supination, clavicle, grip closure 85%, elbow corrective 0%,
`handleGripOffsets`, dumbbell rigidity, topology, skin weights and the Stage 1
forearm bind correction.

## 5. Visual

`12_upperarm_rebase.png` — side view, matched camera, accepted above and rebased
below, at Bottom, Mid lift, Peak and Return. Bottom and Return are
indistinguishable. Mid lift and Peak show the elbow a little further forward,
consistent with 8.3° against 4°, and it still reads as a strict dumbbell curl:
no forward reach, no shoulder swing, no drift during the elbow-led opening, and
a natural elbow silhouette throughout.

## 6. No regression elsewhere

| check | result |
|---|---|
| whole-body strain, five exercises | identical, except the curl's P99 improving 1.4806 → 1.4759 |
| hand/wrist handover rings | max aspect 27.756327, p99 5.870764 — unchanged |
| shoulder press, four frames | 299–466 mm clear, zero inside, exactly symmetric |
| renderer vs exporter grip transform | 0.0000 mm at t = 0, 2, 4 s, both sides |
| typecheck / build | clean |
| suite | 292 passed, 1 skipped, 1 failed — the pre-existing `strainReview` timeout |

No threshold was weakened.

## Stage 1 sign-off

| # | criterion | status |
|---|---|---|
| 1 | forearm at corrected canonical proportion | met |
| 2 | shoulder chain untouched | met |
| 3 | one character-aware grip rule across viewer/exporter/solver/diagnostics | **partial** — one definition, renderer and exporter agree to 0.0000 mm; the solver stays in canonical space because the pipeline resolves equipment before the character is posed |
| 4 | handle inside the fist | met |
| 5 | Bottom/Return penetration cleared | **met** |
| 6 | Mid lift, Peak, Mid lower clear | met |
| 7 | accepted curl mechanics otherwise unchanged | met |
| 8 | grip closure 85%, elbow corrective 0% | met |
| 9 | shoulder press and shared paths | met |
| 10 | hand/wrist repair no worse | met |
| 11 | strain/diagnostic acceptable | met |
| 12 | typecheck, build, focused tests; only the known timeout | met |
| 13 | Stage 2 not started | met |

Twelve of thirteen. Criterion 3 is the one carried-over partial, and
`docs/REFERENCE_BODY_STAGE1_CONTACT_DIAGNOSTIC.md` explicitly accepted it —
"the solver remains in canonical space because equipment is resolved before the
character pose is applied; do not restructure that pipeline unless this
diagnostic proves an actual error caused by it". No such error was found.

**I have not declared Stage 1 frozen**, because the instruction is to freeze only
when every criterion passes and criterion 3 is partial by your own earlier
allowance rather than by full satisfaction. That is your call to confirm.

**Stage 2 has not started.** The push-up remains deferred.
