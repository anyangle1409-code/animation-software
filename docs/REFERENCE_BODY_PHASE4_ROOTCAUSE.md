# Phase 4 — root cause found: the forearm twist helpers distribute nothing

Executing the Phase 4 root-cause authorization. Stage 2 locked and Phase 3
passed, both untouched. **Phase 4 does not pass**; Phase 5 not started. Nothing
promoted or merged. Suite green: 298 passed, 1 skipped, 0 failed.

## 1. Trustworthy silhouette evidence

The previous render filtered vertices by skin weight and drew only triangles
whose three corners survived, which tore the mesh into shards. The replacement
(`scratchpad/repair/p4view.test.mts`) filters **nothing**: every triangle of
every mesh is rasterised and the camera is simply zoomed onto the forearm, so
what the image shows is the actual skinned surface. 19,304 triangles, matched
fixed cameras, side and three-quarter views, a joint-centre overlay and a drawn
floor line for the palm contact.

`scratchpad/repair/shots/P4_base_{Top,Bottom}_{side,threequarter}[_skeleton].png`

It shows both problems plainly:

- the wrist bent to very near a right angle, which is the 92.1° extension;
- the forearm between elbow and wrist reading as a **narrow, flattened, faceted
  strap** while the upper arm beside it holds full rounded volume.

## 2. Placement tested before weights, as instructed

Swept the push-up floor contact through the accepted twist/swing decomposition —
the same measurement, not a reimplementation — so the numbers are comparable:

| hand z | true wrist extension |
|---|---|
| 1.12 | 115.66° |
| 1.18 | 107.05° |
| **1.24 (previous)** | **92.10°** |
| 1.30 | 80.32° |
| 1.34 | 73.89° |
| 1.36 | 70.99° |
| 1.42 | 63.59° |

Extension falls monotonically as the hands move forward. The 70–75° band wants
z ≈ 1.334–1.36 — a +95 to +120 mm move, **not** the historical ~200 mm estimate,
which the measurement does not support.

### A structural conflict, quantified

The band cannot be reached. The push-up's own `forearm_vertical_l/r` rule caps
the elbow-to-wrist z offset at 60 mm at the bottom:

| hand z | elbow-wrist dz | rule |
|---|---|---|
| 1.240 | 8.7 mm | passes |
| 1.270 | 36.8 mm | passes |
| **1.295** | **≈59.5 mm** | **passes** |
| 1.300 | 64.3 mm | violates |
| 1.340 | 99.1 mm | violates |

With a flat planted palm, wrist extension **is** the forearm's angle from the
floor, so "forearm near vertical at the bottom" and "wrist under 75°" are
geometrically incompatible. The best extension available inside the authored
technique is **81.18°** at z = 1.295.

**Retained: z = 1.295.** Extension 92.10° → **81.18°**, pronation 77.33°,
deviation −16.96°, every push-up technique rule clean, palm planted, both sides
identical. It is a real improvement and fully rule-compliant, but it is short of
the authorised band, and closing the remaining 6° needs a decision on which of
the two requirements yields. Worth noting for that decision: 14.62° of the
measured angle is the hand-to-forearm offset present in the bind pose itself, so
81.18° of axis angle is about 66° of actual joint rotation from its own rest —
comfortably inside human range.

## 3. Placement did not fix the forearm, so twist was diagnosed next

Re-rendered at z = 1.295: the forearm is **still a flattened strap**. So
placement is not the root cause of the deformation, and per the decision the next
step was pronation/twist distribution — not weights.

Measuring each bone's twist about its own long axis, bind pose against posed:

| bone | Top | Bottom |
|---|---|---|
| upper_armL | 53.7° | 69.8° |
| upper_armL001 | **53.7°** | **69.8°** |
| forearmL | 31.7° | 9.1° |
| forearmL001 | **31.7°** | **9.1°** |
| handL | 57.7° | 57.7° |

**The twist helpers carry exactly their parent's twist, to the decimal.** They
distribute nothing. A Rigify deform forearm is two bones precisely so the
pronation is shared and the surface winds gradually from elbow to wrist; here
`DEF-forearmL001` contributes zero gradient, and the whole 48.6° step from the
forearm to the hand (9.1° → 57.7° at the bottom) lands in the single wrist joint.

That is exactly what produces a flattened, creased strap: no winding along the
radius and ulna, all of it in one place.

## The root cause

Not skin weights. Not hand placement. Not the Stage 1 forearm lengthening, and
not the v5→v6 wrist repair region.

The retargeting drives `DEF-forearm.L` and leaves `DEF-forearm.L.001` riding its
parent rigidly — which is the documented behaviour for connected helper bones,
and correct for most of them, but wrong for a twist helper, whose entire purpose
is to carry a share of its parent's axial rotation. The same pattern shows on
the upper arm, where `DEF-upper_armL001` also duplicates its parent exactly.

The fix is therefore to distribute axial twist along helper chains in the driver
— give a twist helper a fraction (conventionally half) of its parent's
pronation. That is a source-level fix at the demonstrated defect and needs no
reweighting, which is the outcome the decision's ordering was designed to reach.

## Why I stopped here

That change lives in the retargeting layer and therefore affects every exercise
and both locked stages, so it needs its own validation pass rather than being
appended to this one. It is also the first change in this phase that would touch
shared machinery rather than one exercise's data.

Phase 4 acceptance is not met: wrist extension is improved but outside the
authorised band because of the rule conflict above, and the forearm silhouette is
unchanged pending the twist fix. Stage 1 grip/curl and Stage 2 are unaffected —
the retained placement change touches only the push-up's floor contact.
