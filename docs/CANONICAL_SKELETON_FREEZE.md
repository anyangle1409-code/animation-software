# Canonical skeleton — STRUCTURALLY FROZEN

**Skeleton id:** `hgpt_canonical_v3` · **Bones:** 63 · **Frozen at:** the commit that introduced this file, on `chatgpt/absolute-retarget-imports` (parent `c2372c1`).

The hierarchy and rest geometry below are what final skin weights are painted against and what every exported file names. `src/rig/frozen.test.ts` holds them exactly — every bone, its parent, and its rest head and tail to the micrometre — so any structural change fails the suite.

## What is frozen, and what is not

| Frozen | Not frozen |
|---|---|
| Which bones exist (63) | Joint limits — tunable without touching a weight |
| Each bone's parent | Motion: scapular rhythm, palm cupping and thumb opposition are all **off** in exercise motion, and turning them on changes no bone |
| Rest head and tail of every bone | Retargeting and deformation helpers on imported characters (twist bones, correctives) |
| `SKELETON_ID = hgpt_canonical_v3` | Skin weights (the next pass) |

Changing anything in the left column needs a new skeleton id, a migration for exported files, a re-check of every weight, and an update here.

## Hierarchy

Left side shown; the right side mirrors it bone for bone.

```
root
└─ pelvis
   ├─ spine_01 ─ spine_02 ─ spine_03
   │                        ├─ neck ─ head
   │                        └─ clavicle_l
   │                           └─ scapula_l                      (acromioclavicular joint)
   │                              └─ upperarm_l ─ forearm_l ─ hand_l
   │                                                           ├─ thumb_01_l ─ thumb_02_l ─ thumb_03_l
   │                                                           ├─ metacarpal_index_l  ─ index_01_l  ─ index_02_l  ─ index_03_l
   │                                                           ├─ metacarpal_middle_l ─ middle_01_l ─ middle_02_l ─ middle_03_l
   │                                                           ├─ metacarpal_ring_l   ─ ring_01_l   ─ ring_02_l   ─ ring_03_l
   │                                                           └─ metacarpal_pinky_l  ─ pinky_01_l  ─ pinky_02_l  ─ pinky_03_l
   └─ thigh_l ─ shin_l ─ foot_l ─ toe_l
```

7 centre bones + 28 per side = 63.

- **Scapula** (v2): head at the clavicle's tail, tail at the inferior angle 2 cm under the production character's back skin. Structural; no rhythm.
- **Metacarpals** (v3): one per finger, from the carpometacarpal joint to the knuckle. The knuckle (the finger's existing head) fixes the tail. Adult male metacarpal lengths (68/65/57/53 mm, scaled to this 187 mm hand) fix the base, and bases converge to half the knuckle spread (a 31 mm carpal row).
- **Thumb:** `thumb_01` *is* the thumb metacarpal; its head is the CMC joint. It has three axes; there is no separate CMC bone (see below).
- **No canonical twist bones.** Upper-arm, forearm, thigh and shin twist stay character deformation helpers. The forearm helper keeps its locked 50% share (`FOREARM_TWIST_SHARE`).

## Measured ranges (left side; the right mirrors)

**Thumb base (`thumb_01`)**

| axis | range | meaning |
|---|---|---|
| x | −85..20 | −: flexion across the palm · +: extension |
| y | −20..20 | −: pronation (opposition twist) · +: supination |
| z | −25..60 | +: palmar abduction · −: retroposition |

With the thumb metacarpal at least 30° out of the palm plane, the thumb pad meets each fingertip pad (gap ≤ 0.09 mm, pads face to face at 153–173°). These poses are all within the limits, held in `src/rig/palm.test.ts`:

| finger | x | y | z |
|---|---|---|---|
| index | −30 | −3.9 | 24.7 |
| middle | −45.7 | −0.4 | 26.8 |
| ring | −61.6 | −4.6 | 27.8 |
| pinky | −71.6 | −5.3 | 24.9 (pinky metacarpal spread 8°, turned 5°) |

The sweep looks large because this thumb rests 44° out from the index in the palm plane.

The old ±14 (x) and −25..60 (z) ranges sit inside the new ones, so no existing pose moves.

**Metacarpals**

| | spread (x) | turn (y, + towards thumb) | flexion (z, + palmward) |
|---|---|---|---|
| index | ±3 | ±3 | −3..3 |
| middle | ±3 | ±3 | −3..3 |
| ring | ±5 | ±10 | −5..15 |
| pinky | ±8 | ±15 | −5..30 |

Power grip asked for no cupping. In the dumbbell grip the little finger already lies 18.3 mm from the bar's centre line, against the grip test's 38 mm allowance, and cupping only lifts it away. Opposition is what needs the palm, and only the ring and little fingers'.

## Why 63 and not 65

A dedicated thumb CMC bone was required only if `thumb_01` could not represent opposition. It can:

- The production character's `DEF-thumb.01` is the thumb metacarpal: 45 mm long, with the proximal phalanx as its child, and its axis runs exactly onto it. So the CMC joint is that bone's head, which is `thumb_01`'s.
- Three axes at that one pivot already span every orientation, so a second bone at the same point adds nothing.
- Measured opposition succeeds within anatomical ranges.

## Why the production palm bones were not the source

The production character does carry `DEF-palm.01–04`, but they cannot be measured from:

- **Placement:** every one sits 207–213 mm from its own knuckle and 99–146 mm behind the wrist.
- **Direction:** each points 16–37° off the wrist-to-knuckle line, and is rolled about 84° from the hand's frame.
- **Weights:** they carry no skin weight at all.

The export kept the joints and lost their placement.

- **Deriving the metacarpals instead:** they were derived from the canonical wrist and knuckles plus anatomical proportions. On the production hand, every derived metacarpal line lies inside the skin along its whole length, 1.9–15 mm from it.
- **Retargeting:** `plausiblePalms` refuses these joints. A metacarpal's base must lie within its hand: no further from the knuckle than the wrist, and within 30° of the wrist-to-knuckle line. So the production fingers still hang from the hand.
- **Other characters:** correctly placed palm bones are guessed by name — canonical, Unreal `index_metacarpal_l`, Rigify `DEF-palm.01.L` — and driven relative to the hand.

## Equivalence at freeze (against v2, `c2372c1`)

| | values | worst difference |
|---|---|---|
| canonical frames, 7 exercises × 61 frames | 452,620 | 5.6e-16 |
| production character bones + grips | 381,024 | 1.3e-15 |
| production character posed vertices | 1,365,714 | 1.3e-15 m |
| procedural mannequin posed vertices | 1,464,960 | 1.3e-15 m |
| contacts, technique results | all | identical |
| export tracks | 35,608 | only `index/middle/ring/pinky_01` changed; metacarpal rest × new = old to float32 precision |

## Open items that do not block the freeze

- **The production palm bones need re-exporting** with their placement if palm cupping is ever to show on the production mesh. Until then the character has no palm skin to move, and the fingers follow the hand.
- **Mirrored characters: hand roll.** For a mirrored character (the production character is one), the retargeter places the hand's knuckle fan about 5.5° off the mirrored rig, against 0.5° for a same-side character. This was measured identically on the 55-bone rig with no palm bones, so it predates this pass. It belongs to hand retargeting, not the skeleton. It should be looked at before the grip weights are judged.
- **The mannequin's own hand disagrees with the canonical knuckles.** Its index knuckle sits 2.8 mm outside its surface, and the derived pinky base sits 12–15 mm outside it at every convergence tried. The mannequin carries no metacarpal weights, and the final weights target the production character, whose hand contains every line.
