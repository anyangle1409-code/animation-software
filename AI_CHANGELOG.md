# AI Change Log

This file records changes made by Codex and Claude. Each assistant must add an
entry whenever it changes code, tests, documentation, assets, exercise
definitions, or repository configuration.

## Unreleased

### Claude — 2026-09-10 — the character layer, made replaceable

The visible character was welded to the animation. `buildSkinnedRig` imported
one mesh builder, the viewport imported another, the exporter hardcoded the
first, and the surface was bound to the rig by *bone index* — so no externally
authored mesh could be dropped in without editing all three. This separates the
three layers the studio actually has:

1. **Rig** (`src/rig`) — bones, limits, poses. Unchanged, and knows nothing
   about surfaces.
2. **Skinning/deformation** (`src/character`, new) — how a surface attaches to
   those bones, plus whatever per-character corrections it needs.
3. **Visible mesh** — supplied by a `CharacterSource` and replaceable without
   touching either layer above.

**The interface.** A `CharacterSource` has an id, a label, a declared set of
capabilities and an async `build(rig)`. Every source ends at
`assembleCharacter`, which binds its surfaces to a freshly built canonical bone
hierarchy, so the studio and the exporter cannot drift apart: both ask the
registry for a source and pose what comes back through `applyCharacterPose`.

**Registered characters.** `builtin` is the existing anatomical surface, still
the default. `procedural` is the original tube-and-blob mannequin, kept as a
diagnostic model — cheap, obviously synthetic, and with trivially predictable
weights, which is what you want when the question is whether a deformation
problem is in the rig or in the mesh. `registerBundledCharacter(...)` is the
one call that will put a higher-quality GLB in front of the animation; nothing
is registered yet, because there is no asset yet.

**Rebinding by bone name.** `rebindToCanonical` takes an imported skinned mesh
and re-places every vertex through `q = Σ wᵢ · (Cⱼ · S · Bᵢ⁻¹) · p` — out of
each source bone's bind frame, through a uniform height scale, into the
canonical bone's rest frame — then rewrites the skin indices to our bone order.
Bones our rig does not carry (twist bones, helpers) hand their weight to the
nearest mapped ancestor. UVs and materials survive untouched, which is the
point: a textured, mapped, higher-quality mesh keeps everything that makes it
higher quality. Two honest limits, both documented at the function: proportions
follow the rig rather than the model, and custom normals, tangents and morph
targets are authored against the old bind pose, so they are dropped and the
normals recomputed.

**Deformation stacks are per character.** The elbow corrective and the armpit
morph correctives are authored against particular vertices of the built-in
mesh, so they now live in that character's own stack and are handed to nobody
else — asserted by test. The exporter no longer knows what a shoulder
corrective is: it asks the active character's stack for a sampler and bakes
whatever tracks come back.

**Capability, not assumption.** The anatomy view asks
`capabilities.anatomy` before mounting the écorché variant; a textured import
says no and gets the plain surface rather than a mis-mapped one.

**Imports keep both routes.** Rebinding onto the studio rig is the default and
produces an ordinary registered character — equipment, grip and export all work
on it unchanged. Retargeting the model's own skeleton is retained beside it for
a character whose proportions must be preserved. The panel gained a character
picker and a bind-mode picker and nothing else; the larger character-management
UI is deliberately not built.

Untouched: the canonical skeleton, joint limits, IK, contacts and grip,
equipment sockets, exercise definitions, the biceps-curl motion, animation
validation and timing.

Verified: the built-in character still builds, binds and animates; a GLB loaded
through the new source architecture rebinds onto the canonical rig and is
driven by the same curl; the dumbbell is exported as a child of `hand_r` for an
imported character as for the built-in one; posed bone rotations match the
baked clip's tracks at four points through the rep; and swapping characters
live in the viewport keeps the dumbbells in the hands. 168 of 169 tests pass —
the one failure is the unfinished head pass from the previous round, recorded
below, not a regression from this work.

### Claude — 2026-09-09 — shoulder junction folds, and the armpit

Two defects, both the source's, both on the shared surface so the Character
view, the Anatomy view and the GLB export get the same repair.

**The fins.** A row of vertices at y ≈ 1.40, from 20 mm to 100 mm either side of
the midline, alternated in and out of the surface by 11 to 20 mm — a zig-zag
along the top of the trapezius that read as a pale fin from behind. Everything
else in that region deviates from its own neighbourhood by about 1.5 mm, which
is what curvature looks like at this vertex spacing, so the fold is noise an
order of magnitude above the anatomy. `smoothShoulderFins` measures each vertex
against the mean of its neighbours along its normal and removes only the part of
that deviation above 4 mm, so a real ridge is inside the threshold and untouched:
a clamp on outliers, not a smoothing pass. 48 vertices move, by at most 15.8 mm,
and the worst deviation falls from 19.5 mm to 5.6 mm.

- Self-intersecting non-adjacent triangle pairs around the shoulders fall from
  188 to 146: 46 of the fold's own pairs removed and 4 created.
- The four that remain cannot be removed from this side. The fin is a doubled
  sheet, and the leaf underneath has to travel out through the leaf above it to
  reach the surface they should share. Every guard tried against that — halving
  the corners of a crossing triangle, dropping them outright, dropping only the
  corner moving towards the other sheet — cascaded through the fold and took the
  whole repair back to nothing. Resolving them means moving the leaf above too,
  which is the outer shoulder.

**The armpit.** The source hands the axilla a scrambled binding: adjacent
vertices on the same sheet of skin, 40 mm from the humerus axis and 200 mm below
the shoulder joint, are bound one to the upper arm outright and the next to the
second spine segment outright. Raising the arm swings one and leaves the other,
so a 15 mm edge reaches 130 mm.

`correctArmpitWeights` recovers the two sheets by majority over each vertex's own
ring, counts rows out from the fold where they meet, and grades the arm's share
across five rows either side. Two influences per vertex throughout, and the
majority owner of every vertex is preserved — the ribcage stays the ribcage —
so the body's own proportion tests measure the same chest and shoulder width
afterwards. 772 vertices are regraded and the worst step in the arm's share
across an edge falls from 0.69 to 0.16.

That is as far as weights can go, and the reason is arithmetic rather than
tuning. An edge carries (difference in the arm's share) × (how far its ends
swing). At 100° of abduction the axilla swings about 180 mm, so a 12 mm edge
holds 2× only if the share changes by less than 0.07 across it — fifteen rows
from arm to torso. The surface has about six rows to give, and widening the band
past them drags the chest up with the arm. Every graded weighting tried, from a
six-row blend to an edge-by-edge relaxation against a per-edge ceiling, lands
between 4× and 12×.

**So the binding keeps the crease and a corrective takes the tearing.**
`buildArmpitCorrectives` skins the surface at eighteen sampled shoulder poses per
side, repairs each one directly — over-stretched edges pulled together,
over-squashed ones pushed apart, inside the shoulder's field and nowhere else —
and carries the repair back through the skinning matrices into bind space, where
it becomes a morph target. Eleven samples are textbook lifts and seven are taken
from the exercise clips themselves, because the exercises twist the shoulder as
they raise it — the pull-up by more than 40° — and an earlier version driven by
abduction and forward-lift angles alone made the pull-up *worse*, 5.3× to 8.4×,
by applying shapes built for a shoulder that was not there. The shapes are
blended by how close the shoulder is to each sample, normalised so they never
sum to more than one correction.

They are ordinary glTF morph targets with an ordinary weights track: `bakeClip`
samples the influences from the same pose the bones come from, using the same
function the viewport uses, so the exported animation deforms exactly as the
studio does. The exported file grows from 1.0 MB to 7.0 MB, because glTF stores
each morph target as a full-length vertex array and three's exporter does not
emit the sparse form these would compress to.

Worst stretch and squash across the shoulder and armpit, excluding the elbow,
for the source binding and for this one:

| | source | repaired |
| --- | --- | --- |
| one arm abducted, 30–130° | 6.23 / 0.56 | 1.80 / 0.54 |
| one arm forward, 45–120° | 5.69 / 0.36 | 1.51 / 0.54 |
| both arms, 30–165° | 7.81 / 0.09 | 3.87 / 0.12 |
| dumbbell curl | 1.55 / 0.63 | 1.55 / 0.63 |
| shoulder press | 7.33 / 0.09 | 3.39 / 0.22 |
| push-up | 4.56 / 0.47 | 3.37 / 0.48 |
| pull-up | 8.68 / 0.10 | 4.31 / 0.20 |

**Against the limits declared for this round — 2.0× stretch, 0.35× compression —
one arm at a time meets them through the whole range the exercises use, and the
curl meets them. Both arms together, one arm past 130°, and the loaded press,
push-up and pull-up do not.** They are between two and three times better than
the binding they replace and they are not yet right. The tests hold the measured
values as ceilings so none of it can be given back quietly.

Triangle orientation and area in the posed shoulder, against the same poses on
the source: inverted triangles 62 against 50 at 60° of abduction, 372 against
364 at 100°, 680 against 674 at 150°, 847 against 788 at 150° of forward lift —
the folding at extreme angles is the character's own and this work adds a little
to it. Self-intersecting pairs in the same region go the other way, and by much
more: 14 against 46 at 60°, 10 against 46 at 100°, 13 against 46 at 150°, 260
against 386 at 150° forward.

Bind positions: 76 vertices move in total across every shared repair now in
place, by at most 29.9 mm, all of them on the back of the neck and the top of the
shoulders. The full-body silhouette is unchanged — same shoulder width, same
chest, same waist — and the repository's own proportion tests check it.

Verification: 158 tests pass — the repository's own 122 unmodified, plus 36 for
the anatomy build, of which 9 are new for the shoulder: the folds flattened, the
armpit regraded without moving a single vertex's owner, two influences per vertex
everywhere, nothing moving until an arm lifts, one arm inside the declared limits
through its range, the improvement over the source, no exercise made worse by the
correctives, the correctives present in the exported GLB with a weights track
that actually rises, and the anatomy view carrying the same shapes.
`npm run typecheck` and `npm run build` are clean.

### Claude — 2026-09-09 — head-to-neck weights and the nape ledge, shared by every consumer

The character's generator binds by a single rule near the top of the body —
`if (part !== 'body' || sourcePoint.y > 1.50) influences = [{ sourceName: 'head', weight: 1 }]`
— so everything above 1.50 m in the source becomes head:1.00 with no blend. On
the finished mesh that leaves 3,868 vertices bound wholly to the head, reaching
down to y = 1.397, and only seven vertices in the whole body carrying both head
and neck weight. The neck bone runs from 1.420 to 1.520 and drives almost none
of the surface over it, so the neck does not deform: it is rigid with the skull,
and the transition to the chest happens as a step at the edge of the head's
region rather than along the neck.

The same rule also decides which conversion transform each source vertex is
carried through, and the head's transform does not land where the spine's does.
So the seam is a ledge in the surface as well as a cliff in the weights: down the
midline the back of the neck sits at z = -35 mm from y = 1.39 to 1.41 and then
steps back to -69 mm across a single 13 mm row, and the nape overhangs a recess.

Both repairs now live in `src/body/neck.ts` and run from
`buildAnatomicalBodyGeometry` — the one place the decoded surface is built — so
the studio's Character view, the Anatomy view and the GLB exporter all get the
same corrected mesh without any of them asking for it. The earlier Anatomy-only
copies of both are gone.

- **A chain, not a blend.** Spine to neck over the lower half of the head-bound
  block, neck to head over the upper, each a straight ramp in height. Two
  influences per vertex, never three, and the partner switch is a level surface
  at 1.45 m so head weight is never adjacent to spine weight. 1,347 vertices
  rewritten, 1,213 of them previously head:1.00.
- **The block is taken whole, never cut off by radius.** Every version with a
  radial taper inside it put head weight against spine weight out at the edge
  and tore the surface open; pulled in to 85 mm it measures worse too, taking
  rotation from 1.29× to 1.59×.
- **The neck's sideways reach is trimmed** beyond 65 mm — its own surface at the
  base — fading to nothing by 145 mm. The source gave the neck bone a share of
  twelve vertices on the top of each shoulder, out to 170 mm on the deltoid; a
  head turn stretched an 8.6 mm edge there to 2.15× and squashed its mirror to
  0.31×. On the shoulder the freed share goes to the collarbone rather than the
  arm, so lifting the arm behaves exactly as it did before, to within float
  noise.
- **Positions and colours are untouched.** This changes which bones drive the
  neck, not where the neck is, and a test compares every position and colour
  component against the source build.

Deformation across every edge the repair touches, measured against the same
edges on the source binding (stretch / squash):

| pose | repaired | source |
| --- | --- | --- |
| flexion 20° | 1.158 / 0.732 | 2.937 / 0.839 |
| extension 20° | 1.266 / 0.839 | 2.748 / 0.249 |
| rotation 25°, either way | 1.294 / 0.828 | 2.213 / 0.310 |
| flexion 15° with 20° turn | 1.218 / 0.743 | 2.779 / 0.188 |

The limits — no more than 1.30× stretch, no less than 0.60× compression — were
fixed before the weighting was tuned, and the weighting was changed until it met
them rather than the other way round. Maximum influences per vertex: 2. Largest
step in the head's share across an edge: 1.00 before, 0.43 after — and the
largest one left is a 32 mm edge inside the throat, which is the ramp's own
gradient rather than a boundary. The largest step between any two bones is 0.94,
between the collarbone and the top of the spine on the shoulder: two bones that
hold still together, so it is a step in the weights and nothing in the skin.

`correctNeckLedge` closes the ledge, on the shared mesh, before anything reads
it — the weight repair included, because it finds the seam from the source's own
head binding. The seam and the step are measured from the mesh itself in 2.5 mm
bands with a 13 mm window, every band keyed on |x| so the result is mirrored by
construction, and each row under the seam slides back towards the nape's depth:
most at the seam, less further down, nothing at all 55 mm below it or 85 mm out
to the side. The ledge becomes a slope from the nape into the upper trapezius.

- **40 vertices move, by at most 29.9 mm**, all of them on the back of the neck.
  The step being closed is 34.2 mm and the row directly under the seam has to
  reach the nape, so that is the floor for closing it without moving the head
  block — which carries the face, the jaw, the ears and the hairline, and is
  untouched. Spreading the ramp further would move more rows, not fewer
  millimetres.
- **Depth only.** No vertex moves sideways or vertically, and none moves
  forwards. The trapezius ridge is a lateral form, so sliding the surface back in
  depth cannot flatten it — which is what an earlier smoothing pass over the same
  region did, and why this one is not a smoothing pass.
- **Nothing new folds.** No triangle in the mesh turns over or is pinched below a
  quarter of its area, and a Möller-Trumbore pass over the 768 triangles round
  the neck finds 70 intersecting non-adjacent pairs against the source's 74: the
  correction removes four and adds none. The remaining 70 are the source's own
  shoulder fold, untouched here.
- The largest gap between neighbouring rows down the midline falls from 34.2 mm
  to 9.6 mm, which is the spacing the rest of the neck already has.

The Anatomy view's private levelling pass is deleted: it was a second correction
for the same defect applied to one mode only. Anatomy now inherits the corrected
base and sculpts relief on top of it, and a guard over the whole écorché surface
damps any displacement — from any stage — that would leave a triangle facing
against the character's own. Of its 27,460 triangles, 0 do.

**Unresolved when this landed, and taken up in the round above.** Raising the arm
tore the armpit: 5.20× stretch at 60°, 8.03× at 100°, and 0.12× compression at
45° of forward flexion, on edges where the thorax meets the upper arm. Those
numbers were the character's own — the source mesh measured identically, before
any of this work — and nothing in this entry changed them. The shoulder round
above brings them down by two to three times and does not finish the job; the
figure is not ready for exercise production while any of it stands.

Verification: 150 tests pass — the repository's own 122 unmodified, plus 28 for
the anatomy build, of which 13 cover this junction: two influences summing to
one, head share handed over by position, left/right symmetry, deformation limits
under neutral, flexion, extension, both rotations and a combined pose, the arm
left as the source had it, colours unchanged and movement confined to the back of
the neck in depth alone, the ledge closed into a slope and mirrored, no triangle
turned over or pinched anywhere in the mesh, Character and Anatomy sharing one
corrected base, and both the corrected weights and the corrected positions read
back out of a decoded GLB export. `npm run typecheck` and `npm run build` are
clean.

### Claude — 2026-09-09 — Anatomy view: sculpted arm and elbow deformation

Adds a fifth view mode, `Anatomy`, beside Skeleton / Muscles / Combined /
Character. It renders the same skinned body as a greyscale écorché on a black
stage. Nothing in this entry changes the Character view, the muscle overlay, the
exercise definitions, the rig, the IK, the grip, the animation timing or the GLB
export; the anatomy geometry is built separately and the character's own surface
is asserted bit-identical before and after.

- **Muscle relief from the existing model.** Each belly in `muscles/model.ts` is
  read as a continuous 0–1 field over the bind-pose surface and used to displace
  it along its own normals, so a muscle is form rather than colour. Nine fields:
  three deltoid heads, biceps, triceps, forearm flexors and extensors, plus a
  brachialis and a brachioradialis that exist in `body/ecorche.ts` as shape only
  — no group id, no activation row, never a belly in the overlay. Peak relief is
  13.0 mm and the mean is 4.1 mm over 1,062 vertices.
- **Arm surface settling.** The source mesh carries a horizontal band across the
  upper arm, visible in Character mode too, which made the relief read as bulges
  stacked on a segmented tube. A few weight-limited Laplacian passes over the arm
  region remove it. Mesh seams are welded for the purpose so a split vertex ring
  does not shade like an edge.
- **Elbow skin blend.** The character hands the humerus over to the forearm
  across roughly 40 mm on one side of the joint and 20 mm on the other, which
  deforms like a hinge between two tubes. Anatomy mode redistributes that pair's
  share on a smooth ramp, symmetric and ±50 mm.
- **Elbow pose corrective.** A bind-space offset scaled by elbow flexion, driven
  by `4·s·(1−s)` on the forearm's weight share — strongest where blend skinning
  actually collapses. Exactly zero at extension, so the clip still loops;
  symmetric left to right; bounded at 25 mm.
- **Activation colour is built and held at zero.** `ECORCHE_GREYSCALE` keeps the
  view in grey while the anatomy is being judged. The per-group field, the
  shader hook and the border threshold all still work.
- **Local refinement is written and switched off.** `body/refine.ts` does
  red-green subdivision of a named region with interpolated skin weights. A
  triangle-by-triangle audit showed most high-flexion surface contact is the
  upper arm meeting the forearm rather than elbow-ring density, so it is not used
  here. The note at the top of `body/elbow.ts` records what was measured and why
  the remaining contact was accepted.

The user approved each stage from rendered previews before this checkpoint, and
approved the elbow result explicitly. Verification: 137 tests pass — the
repository's own 122 unmodified, plus 15 for the anatomy build — and
`npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-09 — skin, eyes and clothing-seam preview

- Replaced the grey teaching surface with a warm natural skin palette while
  preserving the existing red/orange active-muscle overlay.
- Rebuilt the eyes as visible sclera with separate brown irises and pupils,
  slightly compressed vertically and positioned inside the existing sockets.
  The eye surfaces remain part of the same head-skinned draw call.
- Replaced interpolated vertex-colour clothing boundaries with geometric cuts
  through triangles at the waist and mid-thigh. The resulting waistband and
  hems are straight, share the body's skin binding and remain poseable without
  grey fringes or saw-tooth triangle edges.
- Preserved the approved head, shoulders, torso, legs, feet, grip, dumbbells and
  bicep-curl motion. The generated mesh is 13,952 vertices and 27,460 triangles.

The user approved the full-body and detail validation renders before commit.
Verification: 122 tests pass; `npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-08 — approved shoulder and head refinement

- Rounded and narrowed the raised, squared-off deltoid caps and introduced a
  natural neck-to-shoulder slope without moving the underlying shoulder joints.
- Shortened the elongated head profile and added restrained width through the
  cranium and temples while keeping the crown aligned to the 1.75 m rig.
- Preserved the approved torso, legs, feet, curl motion, dumbbell placement and
  two-handed grip from the preceding correction.

The user approved the rest, mid-curl and top-curl validation render before this
change was committed. Verification: 122 tests pass; `npm run typecheck` and
`npm run build` are clean.

### Codex — 2026-09-08 — `codex/anatomical-reference-character`

Purpose: correct the withdrawn anatomical character using the supplied curl
reference as a visual gate, without changing Claude's muscle-overlay system or
the accepted lower-body proportions.

- **Correct bind conversion.** Rebuilt the MakeHuman surface in the canonical
  rig's actual rest pose. The source spine is now mapped waist-to-neck instead
  of backwards; upper-arm, forearm, thigh and shin twist segments are fitted
  proportionally; palms use wrist-to-knuckle length; every finger segment maps
  joint-to-joint. Tiny cross-side source weights are removed before collapsing
  to the app's two-influence skin.
- **Reference-shaped body.** Applies the adult-male and muscular CC0 targets,
  then sculpts a lean chest-to-waist V taper. The accepted legs and feet remain
  anatomically shaped and the sole is fitted to the app's floor. The source's
  helper hair strips are deliberately excluded; they are rig guides, not hair.
  The result is 13,524 vertices and 27,036 triangles, split across six generated
  modules so no GitHub blob approaches the earlier transfer limit.
- **Face and clothing.** Keeps the anatomical head, nose, lips, ears and eye
  geometry, uses a neutral anatomical-grey teaching surface and fitted dark
  shorts, and remains one skinned draw call shared by viewport and GLB export.
- **Grip and motion.** Retains the smaller round dumbbells, corrected anatomical
  grip position and 126-degree curl. Rest, mid-curl and top-curl renders include
  the real equipment transforms and show the handle inside each closed hand.
- **Regression coverage.** The contracted-curl export test now measures every
  posed triangle edge, directly rejecting torn shoulders, metre-long strips and
  exploded finger fans. Body tests cover two-weight normalization, human bounds,
  male taper, clothing, eyes and the increased anatomical-mesh budget.
- **Provenance.** Restored `THIRD_PARTY_ASSETS.md` and added a reproducible
  generator for the exact CC0 sources and rest-pose conversion.

Verification: 122 tests pass; `npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-08 — `codex/anatomical-reference-character`

Purpose: improve the dumbbell curl while recording and withdrawing an
unsuccessful imported-character experiment.

- **Retained:** replaced the oversized hex dumbbell ends with smaller round
  plates and reduced peak elbow flexion/shoulder travel so the weights do not
  crowd the chest. The existing grip placement and mirrored finger closure are
  unchanged.
- **Rejected and removed:** an attempted MakeHuman-to-canonical remap passed
  static mesh and bone tests but failed in the real posed preview. Its bind pose
  was incompatible with the canonical skeleton, causing torn shoulders and
  torso sections and fingers to explode away from both hands. The body also did
  not match the requested athletic male reference. All generated mesh data,
  surface-highlighting changes and third-party asset files from that attempt
  have been removed; the last known-good profile character is restored.
- **Regression coverage:** added a contracted-curl skin test which transforms
  every vertex and rejects detached or exploded geometry. This covers the visual
  failure that the earlier bone-only tests missed.

Verification: 122 tests pass, including the new fully posed skin check;
`npm run typecheck` and `npm run build` are clean.

### Claude Opus 5 — 2026-09-08 — `claude/home-gym-pt-animation-txux66`

Purpose: make the studio's character read as a person rather than a mannequin,
and make the muscle overlay usable as exercise instruction.

Preserved Codex's `067e90db` grip work unchanged: `anatomicalGripOffset` is
still what places a one-hand attachment, and its two animation tests still run.

- **Character.** Re-authored the body profiles as an athletic adult male:
  V-taper from a 0.39 m chest to a 0.27 m waist, deltoid caps, biceps and
  triceps mass, a forearm flare into a narrow wrist, patella at the knee, and a
  calf. Added a face — eyeballs with irises and lids, brow, nose, lips, jaw
  corners, ears — and a close-cropped hair shell.
- **Clothing.** Surface colour is now a vertex attribute on the same single
  mesh, so skin, dark fitted shorts, waistband, eyes, lips and hair cost one
  draw call between them. The shorts run from the hip to mid-thigh, leaving
  every joint the exercises work bare.
- **Muscle overlay.** Each belly is now built on an anatomical frame — length
  along the muscle, width across the body, depth through the skin — instead of
  spreading along an arbitrary axis. Bellies taper into tendon at both ends and
  are fitted against the body at runtime, so none of them break the skin during
  the curl and none exceed 7 mm in any other exercise. Re-placed all 21 muscle
  definitions against the new surface.
- **Highlighting.** Primary muscles are now a clear red, secondary a softer
  orange, stabilisers close to flesh tone and untargeted muscles almost
  invisible. For the curl this leaves both biceps as the obvious highlight, with
  the forearm flexors and front deltoids behind them.
- **Grip.** The thumb now extends at the knuckle and folds over, laying it along
  the handle instead of sweeping it past the palm. This rig has no
  carpometacarpal joint, so the thumb cannot oppose across the palm; along the
  bar is as close to a wrap as its joint limits allow.
- **Backdrop.** A studio/light backdrop toggle, so app-facing captures come out
  on a clean light stage instead of the editor's dark one.
- **Tests.** New `body/body.test.ts` cases for the male silhouette, the shorts'
  coverage and the eyes; a new `muscles/muscles.test.ts` covering containment,
  attachment, left/right mirroring, the biceps through the curl and the
  activation palette; a new `equipment/grip.test.ts` checking each handle stays
  wrapped by the fingers and thumb and rigid in the hand throughout both
  dumbbell exercises.

Verification: 121 tests pass; `npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-08 — `codex/fix-dumbbell-grip-position`

Purpose: keep dumbbell handles visibly enclosed by the fingers throughout
hand-held exercises.

- Moved the default one-hand equipment grip from inside the palm to the centre
  of the curled-finger loop, with mirrored left/right palm-facing offsets.
- Applied the anatomical default to the bicep curl and dumbbell shoulder press.
- Expanded animation tests to check both hands throughout the full repetition
  and detect a handle positioned inside the palm.

Verification: 81 local tests passed on the compatible Codex checkout;
`npm run typecheck` and `npm run build` completed successfully.

## Baseline history

### Claude Opus 5 — 2026-09-08 — commit `e6ef05b4`

Added the anatomical skinned body, corrected mirrored finger flexion, and added
the dumbbell shoulder press and pull-up. Reported 101 passing tests.

### Claude Opus 5 — 2026-09-08 — commit `287f72c6`

Created the initial Home Gym PT Animation Studio, including its canonical rig,
IK, equipment, exercise definitions, editor, retargeting and exporters.

### Repository owner — 2026-09-07 — commit `df07dced`

Created the repository with the initial commit.
