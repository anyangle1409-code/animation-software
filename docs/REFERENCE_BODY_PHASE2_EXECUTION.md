# Phase 2 — Stage 2 executed, then reverted on a character-candidate blocker

Executing `docs/REFERENCE_BODY_PHASE2_AUTHORIZATION.md` from `f637f41`. Phase 1
treated as locked and untouched. Nothing promoted or merged. The tree is green:
**298 passed, 1 skipped, 0 failed.**

Both authorised decisions were exercised and nearly all of the work validated.
It is reverted for one reason, in "The blocker" below, and every number needed
to re-apply it is recorded here.

## What was built and validated

### The canonical rig (Decision 2's premise)

`SHOULDER_WIDENING = 0.01924 × RIG_HEIGHT` = 33.67 mm per side, applied to the
clavicle tail and every bone outboard of it, mirroring through the existing
machinery. Nothing scaled: upper-arm and forearm lengths unchanged, the clavicle
simply spans further. Deltoid-to-deltoid went **433 → 500 mm**, against the
reference's 0.2969 of height ≈ 520 mm, so the rig moved decisively toward the
reference rather than past it.

### Shoulder-relative contact rules (Decision 1)

All four exercises validated **clean** — `P2RULE` for curl, press, push-up and
pull-up all reported no violations.

| exercise | re-derivation | why it is not a weakening |
|---|---|---|
| press | `hands.width` 0.96 → 1.027; `hand_width` envelope 0.45–1.05 → 0.517–1.117 | the rule's own label is a shoulder-relative press path |
| pull-up | `hands.width` 0.48 → 0.547; `grip_width` 0.42–0.56 → 0.487–0.627; **rack sockets ±0.24 → ±0.274** | the label states "just wider than the shoulders"; the bar is 1.3 m wide with uprights at ±0.62, so ±0.274 is comfortably on it — no physical conflict |
| pull-up | `HANG.y` −0.055 → −0.0631 | measured, not guessed: the longer clavicle lifts the shoulder 8.1 mm in the hang (1.4205 → 1.4286), which cut shoulder-to-bar to 549 mm against a 560 mm arm and bent the elbow to 22.8°. Dropping the root by the same 8.1 mm restored 11.86°, against 12.06° before Stage 2 |
| push-up | `hands.width` 0.6 → 0.667; `hands_width` 0.48–0.68 → 0.547–0.747; `body_line` tolerance 0.06 → 0.06 + widening | **the sagittal deviation measures 0.0000 at every frame.** The whole 0.0669 is the constant lateral fact that a shoulder is wider than a hip, which was 0.0332 before. Carrying the widening into the tolerance leaves the sagittal margin at 26.8 mm — *exactly* what it was before — so the sag/pike the rule exists to catch is policed identically |

### Procedural anatomy (Decision 2)

- **The baked surface follows the rig.** `buildAnatomicalBodyGeometry` is baked
  against the old bone positions, so without this the arm hung off a shoulder no
  longer under it: upper-arm girth collapsed from 97 mm to 30 mm, since girth is
  read as the arm's width beyond the shoulder head.
- **The transition had to span several edges.** The shift is 33.7 mm and the
  median shoulder edge is 7 mm, so a mask going 0 → 1 across one edge moves its
  ends past each other and inverts it — measured, that took the worst edge to
  5.5% of rest length against a 10% floor. Averaging the weight field made it
  worse and bled the shift into the neck. A graph-distance ramp over **2 hops**,
  held at 1 where the arm owns the surface outright, fixed it: **worst 5.215 and
  tightest 0.1580, both better than the unshifted baseline's 5.308 and 0.1324.**
  So the shift improves shoulder deformation rather than degrading it, and the
  band decays to nothing well before the chest and waist the reference already
  places within tolerance. The torso is not widened and no belly is scaled.
- **Three deltoid origins re-anchored.** They sit a fixed distance from the
  clavicle's *lateral* end, which moved outward, so the along-bone offset carries
  the widening. Without it `deltoid_medial` went back to **lengthening (1.0045)
  in its own abduction** — the exact defect its own source comment records from
  an earlier round.
- **Pectoralis and latissimus insertions** brought from 14 mm to 4 mm lateral of
  the humerus shaft, a 10 mm translation and smaller than the widening, where
  the pectoralis major actually inserts. Their bellies had ridden the humerus
  out while the armpit skin did not follow that far, leaving them 10.0 mm and
  7.5 mm outside the surface in a push-up against a 7 mm allowance.

At that point the suite stood at **297 passed, 1 failed**: `pectoralis_l` 2.9 mm
outside the skin in the shoulder press. Every non-scaling lever was tried and
none closed it — `taper` migrates the violation between poses rather than
reducing it (0.92 → 7.7 mm, 0.84 → 10.3 mm, 0.78 → moves to the squat),
`flatten` has no effect on the probed depth at all, an explicit `outward` moves
it by under 0.3 mm, and widening the skin band does not change the figure by a
single digit because the probe reads the rig-derived profile skin, not the baked
surface. Scaling the belly down would be the remaining option and the decision
forbids it.

## The blocker

The authorisation requires Phase 1's grip and clearance to survive. Measured on
the Stage 2 character candidate, they do not — and the cause is the candidate,
not the re-derivations.

| | Stage 1 candidate | Stage 2 candidate | canonical target |
|---|---|---|---|
| character hand at curl Peak | 0.1909 / 1.2972 / 0.2452 | **0.1549 / 1.0156 / 0.3603** | 0.2050 / 1.3067 / 0.2375 |

On Stage 1 the character's hand tracks the canonical pose to about 10 mm in y
and z. On Stage 2 it sits **281 mm low and 123 mm forward** — the arm hangs
rather than curling. The grip readings follow from that and are meaningless
rather than merely poor: fingers 2.4 mm to 94.1 mm from the handle, palm 32.8 mm
clear, thumb 440 mm away, wrap 100°, and the curl's dumbbell-to-thigh figure
reads +140 mm because the weight is nowhere near the leg.

So `stage2_shoulder.mjs` moves the bind pose in a way the retarget binding does
not survive. The candidate's metadata is intact — both candidates carry
`scene.extras.homeGymPT`, and `gripSolutionId` resolves to `homeGymPTMale` on
both — so this is not lost grip data. The likely culprit is that translating
`DEF-upper_arm.*` rigidly rotates the *clavicle* (its head is at the sternum and
its tail is the moved child), and the change of basis `bindRetarget` computes
once from the bind pose is then inconsistent for that chain. Stage 1's forearm
tool used the same mechanism safely because it translated **along** a bone axis,
leaving every bone's direction unchanged; a lateral translation does not.

That is a real structural finding about the method, not a tuning problem, and
fixing it means reworking how the widening is expressed in the character — most
likely as a clavicle **rotation plus length** change rather than a rigid
translation of its child, so no bone's parent silently changes direction.

## Why it is reverted rather than left in place

The canonical half and all the re-derivations are sound on their own evidence,
but they are only correct *together with* a character candidate that matches.
Shipping the canonical widening against a character whose arm is 28 cm out would
leave the rig and the character disagreeing about where the shoulder is, which
Phase 2's own derivation notes is worse than either alone.

So `src/` is back to the locked Phase 1 state, green at 298 passed / 1 skipped /
0 failed, and Phases 3–5 are not started. Nothing above needs re-deriving: the
values, the reasons and the measurements are all recorded here, and re-applying
them is mechanical once the character candidate is rebuilt by a method that
preserves the retarget binding.

| file | SHA-256 |
|---|---|
| `scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE.glb` (do not use) | `173ef5dfe6c5985306274d4cee75d64e95708fcaac1824c1fb62bf487f509f4d` |
