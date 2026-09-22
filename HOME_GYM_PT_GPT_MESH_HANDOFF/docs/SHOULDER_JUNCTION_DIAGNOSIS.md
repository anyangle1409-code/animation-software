# Shoulder-to-upper-arm junction — diagnosis

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `8e674f7` · **Shoulder-fix commit:** `eca99bb`
**One candidate correction was tested and rejected on its own measurements. Nothing retained,
nothing promoted, working tree clean.**

The reported symptom: in the side Bottom view the upper arm still appears to originate from the
anterior face of the shoulder rather than hanging from underneath the acromion/deltoid cap.

**Answer: it is the mesh/skin sitting around an otherwise-correct joint.** The joint centre, the
clavicle endpoint and the upper-arm rest orientation are all ruled out by measurement, and the
decisive evidence is an invariance test rather than an opinion.

## Conventions

`+z` is front, the character's left arm is at `+x`, all figures mm, world space, posed at Bottom on
`CORNER_FINAL_SHORTS`. One correction to an earlier note: `boneByName.get('clavicle_l')` returns the
bone's **origin**, which is the sternoclavicular end at `x = 15.9` — near the midline. The acromion
is the clavicle's **tail**, and canonically that is exactly where `upperarm_l.head` sits.

## The canonical chain, measured

| | Value |
|---|---|
| Clavicle origin (SC joint) | `(15.9, 1407.6, 28.4)` |
| Upper-arm joint centre | `(214.9, 1412.1, -21.9)` |
| Elbow | `(205.3, 1115.6, -5.2)` |
| Humerus sagittal tilt | 3.22° |
| Canonical `clavicle_l.tail` | `(-0.17, 1.44, -0.035)` |
| Canonical `upperarm_l.head` | `(-0.17, 1.44, -0.035)` — **identical** |

The rig places the glenohumeral centre exactly *at* the acromion, with no inferior offset, where
anatomically the humeral head centre sits 20–25 mm below it. That looked like the answer. It is not,
and the reason is the next section.

## The invariance test — the decisive result

Two things sit above the joint, and they behave completely differently:

| Measured at Bottom | Joint at y 1412.1 | Joint at y 1390.5 | Change |
|---|---:|---:|---:|
| **Deltoid apex above the joint** (arm-owned, weight ≥ 0.7) | **7.8 mm** | **7.8 mm** | **0.0 mm** |
| Acromion / trapezius apex above the joint (clavicle-owned) | 64.0 mm | 80.5 mm | +16.5 mm |
| Joint z | −21.9 | −22.6 | −0.7 mm |
| Humerus tilt | 3.22° | 3.24° | +0.02° |

Moving the joint **21.6 mm** vertically changed the deltoid's relationship to it by **exactly
nothing**. The deltoid is arm-owned, so it translates rigidly with the arm root: every joint move
carries its own cap with it. **No joint-position lever can change how the arm sits inside its own
deltoid.**

Only 7.8 mm of arm-owned mass sits above the joint centre. A deltoid should rise 25–35 mm above it,
wrapping over the humeral head to the acromion. So the humerus begins essentially at the top of its
own mass — which is what "originates from the shoulder rather than hanging underneath the cap"
looks like.

And the mass that *is* above it sits forward: the deltoid apex is at `z = +4.8` against a joint at
`z = −21.9`, so the top of the arm is **26.7 mm anterior of the bone**. In side view the arm's upper
surface leads, the bone descends behind it, and the junction reads as anterior.

## Ruling out the other three causes

- **Upper-arm root / joint centre position** — ruled out as the *relationship*. Its absolute position
  is adjustable, but the invariance test shows the deltoid follows it one-for-one. The joint's own
  placement is also now good: z −21.9, girdle at +19.6 mm, tilt 3.22°.
- **Clavicle endpoint** — it is the only lever that moves the posed joint at all (≈1.08 mm of joint
  per mm of tail), but it moves the acromion *and* the deltoid with it. Confirmed by the test above.
- **Upper-arm rest orientation** — ruled out by construction. `upperarm_l` head and tail share the
  same z, so the rest humerus is vertical, and the measured tilt (3.22°) comes from the authored 3°
  of curl flexion. Rotating it swings the arm; it cannot add mass above the joint.
- **Mesh/skin around an otherwise-correct joint** — **this is the cause.** Both defining numbers
  (7.8 mm of mass above the joint, apex 26.7 mm anterior of it) are properties of the geometry and
  its skin weights, and both are provably invariant to every rig lever available.

There is also a hard architectural limit behind this, established earlier and unchanged: the posed
arm root is placed from the canonical clavicle's frame at the imported clavicle→shoulder distance,
so neither the asset's rest pose nor `upperarm_l.head` reaches it. Verified again here —
moving canonical `upperarm_l.head` down 25 mm left the posed joint at `(214.9, 1412.1, -21.9)`,
**unchanged to the tenth of a millimetre**.

## The candidate correction, tested and rejected

Clavicle tail `y 1.440 → 1.420`, chosen because it moves the joint vertically while leaving z, tilt,
hand position and clearance alone. It is the only rig-side candidate that could plausibly have
helped.

**Joint movement:** 21.6 mm down, 0.7 mm back, 0.9 mm medial. Tilt +0.02°.

**Mesh movement, measured separately** by diffing posed vertices between the two rig states:

| | |
|---|---|
| Vertices moved | 3,650 of 10,839 |
| Mean movement | 16.98 mm |
| Worst movement | 22.07 mm |
| Arm-owned vertices (255) | mean **20.73 mm**, worst 22.07 mm |

The arm-owned mesh moved 20.73 mm for a 21.6 mm joint move — one-for-one, which is the same
invariance stated numerically. The junction did not change shape; the arm translated.

Guards held throughout (clearance +8.3 mm body, no technique violations, tilt and hand z static), so
it was not rejected for breaking anything. It was rejected because **it does not fix the reported
defect** — and in the render it reads worse, dropping the arm away from the trapezius and exposing a
larger gap above the shoulder.

**Not retained.** `src/rig/humanoid.ts` is unchanged; the working tree is clean.

## What would actually fix it

A geometry/skin change, which is exactly the scope of the separate high-detail mesh candidate in
`HOME_GYM_PT_GPT_MESH_HANDOFF/`. Two concrete targets for it:

1. **Deltoid mass above the joint: 7.8 mm → 25–35 mm.** The cap should wrap over the humeral head
   and reach the acromion, not start at the joint's own height.
2. **Deltoid apex z: +4.8 → at or behind the joint's −21.9.** The top of the arm should sit over the
   bone, not 26.7 mm in front of it.

Both are measurable with `scratchpad/repair/sagittal.test.mts` (included in the handoff as
`harnesses/`), so a new mesh can be checked against them directly rather than by eye.

Worth adding to the handoff's constraints: this must not be "fixed" by moving the joint, because the
joint move is invisible at the junction and costs the girdle alignment that was just corrected.

## Measurement caveat, stated because it shaped the work

Three selection methods for the arm surface were tried before one held up. An x-slab and a
sleeve-radius selection both reached the lat and ribcage behind the arm, reporting implausible arm
depths of 115–148 mm and a midline biased backwards — which would have produced exactly the
"bone ahead of the mass" conclusion the test was looking for, for the wrong reason. The figures
above therefore use skin ownership (`upper_arm*` weight ≥ 0.7), which is well defined at the
arm/torso junction where geometry is not, plus apex measurements that need no slab at all. The
invariance result is independent of all of this: it compares the same measure against itself across
two rig states.

## Status

Diagnosed, candidate tested and rejected on measurement, nothing retained. Accepted geometry, rig,
curl and assets untouched.

**Not promoted. Not merged.**
