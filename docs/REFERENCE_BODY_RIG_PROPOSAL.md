# Reference body rig — measured proposal

Investigation for `docs/REFERENCE_BODY_RIG_REVIEW.md`. **Nothing implemented,
nothing promoted, nothing merged.** No asset was written. Measured through the
locked registration already used for the surface fit — same sole-to-crown span,
same pelvis midline, orthographic, arms 10° from vertical and legs 2° adducted.
The photograph was not re-scaled by shoulder width or arm length.

## The finding that decides the shape of the proposal

Comparing the imported character against **both** the reference and the
canonical rig the animation is authored on (`src/rig/humanoid.ts`) splits the
problem cleanly in two:

| Proportion, % of figure height | canonical rig | imported character | reference (est.) |
|---|---|---|---|
| shoulder lateral offset | 9.71 | 9.68 | 10.64 |
| upper arm length | 17.14 | 16.98 | ~17.2 |
| **forearm length** | **14.86** | **10.93** | **~14.7** |

- **The forearm is a defect.** The character disagrees with the canonical rig
  *and* the reference *and* standard anthropometry (elbow-to-wrist ≈ 0.146H), by
  the same ~4% of body height. Correcting it moves the character toward all
  three at once. This is not chasing a photograph; it is bringing the imported
  asset into agreement with the rig its animation is authored on.
- **The shoulder width is a style choice.** The character and the canonical rig
  agree to within 0.03% of height. Only the reference is wider. Widening the
  character therefore moves it *away* from the canonical rig unless the
  canonical rig is widened too — which is an animation-authoring change, not an
  asset fix.

These two should be decided separately. They are separable: the forearm change
is local to one bone pair, the shoulder change is a translation of the whole arm
chain.

## Proposal, per side

| Change | % of height | model units | 1.75 m studio |
|---|---|---|---|
| Lateral shift of the whole arm chain | 1.83 | 37.0 mm | 32.1 mm |
| Forearm lengthening (elbow→wrist) | 3.92 | 79.2 mm | 68.7 mm |
| Upper arm | 0.17 | — | no change proposed |

The forearm target is the canonical rig's own 14.86% of height, not a number
read off the photograph. The lateral shift is the value that makes the shoulder
span match, computed against the candidate's own deltoid radius rather than the
2.41% axis mismatch — the candidate's deltoid is thicker than the reference's,
so shifting by the full axis difference would overshoot the span.

### Before → proposed joint centres

Bind pose, model units, left side; the right mirrors exactly.

| Bone | before (x, y, z) | proposed (x, y, z) |
|---|---|---|
| `DEF-upper_arm.L` | 0.195, 1.585, −0.027 | 0.232, 1.585, −0.027 |
| `DEF-forearm.L` | 0.435, 1.340, −0.022 | 0.472, 1.340, −0.022 |
| `DEF-hand.L` | 0.601, 1.234, 0.077 | 0.698, 1.196, 0.112 |

The wrist moves outward with the chain and then along the existing forearm
direction by the lengthening, so the forearm's orientation is unchanged and only
its length differs. The twist helpers (`DEF-upper_arm.*.001`,
`DEF-forearm.*.001`) and the finger chain translate with their parents.

## Projected result

| Measure | reference | candidate now | projected | residual |
|---|---|---|---|---|
| shoulder span | 31.34% | 27.68% | **31.34%** | 0.00 |
| shoulder line | 53.3° | 60.5° | **55.5°** | 2.1° |
| neutral wrist height | 49.3% | 54.68% | **51.07%** | 1.77% |

**Shoulder slope reaches the reference within about 2° with no further yoke
sculpting** — which was the question. The angle is currently too steep because
the run is too short, not because the line is wrong: the drop stays at 14.88% of
height and the run grows from 8.41% to 10.24%. Note the absolute angles depend
on exactly where the deltoid tip is sampled (a slightly different tip window
gives reference 50.7° and candidate 56.8°); the *gap* is 6–7° on either
definition, and the projected residual is ~2° on either.

The 1.77% of height still left at the wrist is deliberate. Closing it would mean
lengthening the forearm past the canonical rig's own proportion, which trades a
defensible target for a photograph-matching one.

## Would the joints still sit plausibly inside the surface?

**No — the surface has to move with them**, which is the main structural
consequence. `07_joints_current_vs_proposed.png` shows it: the proposed shoulder
lands at the outer edge of the current deltoid rather than inside its mass, and
the proposed wrist lands inside the current *hand* mesh, near the fingers. The
current deltoid's outer radius is about 4.6% of height (≈93 mm); a 37 mm shift
leaves the joint inside that mass but well off-centre, and rotating about it
would swing the arm eccentrically.

So the arm-chain vertices must translate with their bones and the forearm's must
be stretched along its axis, and the inverse bind matrices must be recomputed
from the new bind pose. Weights and topology need not change.

## Downstream effects

The retarget path preserves the source skeleton and writes orientations onto it,
so a longer source forearm does not change any code — it changes where the hand
*lands* in every pose. Everything anchored to the hand moves with it.

| Area | Expected effect |
|---|---|
| Curl bottom / mid / peak | Hands start ~69 mm lower and ~32 mm wider. The documented ~6 mm dumbbell/thigh overlap at curl bottom changes and must be re-measured; it may resolve or worsen. |
| Shoulder press bottom / overhead | Rack and lockout heights rise by the forearm extension; overhead dumbbell separation widens by 64 mm across. |
| Push-up top / bottom | Hand contacts move outward and the torso sits higher off the floor at the same elbow angle. The floor lock needs recalibration. The documented push-up hand-placement issue (shoulder 218 mm ahead of the hand) is directly affected and should be re-measured after, not before. |
| Pull-up bottom / top | Grip width on the bar widens by 64 mm; hang height and the top position change. Bar contact locks need recalibration. |
| Deepest squat | Arms swing forward for counterbalance; reach changes but there is no contact, so this is a whole-character regression check rather than a recalibration. |
| Dumbbell attachment, grip centre | Grip closure at 85% is unaffected (it is finger rotation, not bone length), but the attachment offset from the wrist is calibrated against the current hand position and should be re-verified. |
| Left/right symmetry | The edit mirrors exactly by construction; needs the usual paired-vertex check. |
| Absolute retarget path | No code change; the mapping is by bone name and none are added or removed. Needs re-running because the bind data changes. |
| Export/runtime agreement | Node-side measurement and the viewport must be re-checked to agree after the bind change, as they were for the surface fit. |
| Hand/wrist weight repair (v5 → v6) | Its handover rings sit exactly where the forearm is stretched. The shard and facet checks must be re-run; this is the most likely place for a regression. |

### Files and data that would change

- **The imported character GLB only**: node translations for the arm chain, the
  skin's inverse bind matrices, and `POSITION`/`NORMAL` for arm-weighted
  vertices. No `JOINTS_0`/`WEIGHTS_0` change.
- `src/rig/humanoid.ts` — **only if** the shoulder widening is accepted and the
  canonical rig is to stay in agreement with the character. Not needed for the
  forearm change.
- `src/constraints/locks.ts`, `points.ts`, `rules.ts` — contact and equipment
  anchors, if their calibration is absolute rather than derived.
- `src/exercises/gripProfiles.ts` and the exercise definitions — only if grip
  widths are stored as absolute offsets.
- Tests that assert on geometry rather than behaviour:
  `src/constraints/contactDiagnostics.test.ts`, `src/equipment/grip.test.ts`,
  `src/equipment/gripDiagnostics.test.ts`,
  `src/equipment/twoHandAttachment.test.ts`,
  `src/exercises/bicepCurlTechnique.test.ts`,
  `src/exercises/gripProfiles.test.ts`, `src/editor/gripReview.test.ts`,
  `src/character/imported.test.ts`,
  `src/retargeting/movementCertification.test.ts`.

## Risks

1. **The forearm change is a 36% length increase on that bone.** It is
   justified by three independent references agreeing, but it is not a small
   edit, and every hand contact in the app is downstream of it.
2. **Recalibrating contacts is where exercise intent could drift.** The
   temptation will be to nudge a contact until a pose looks right; that is
   rewriting movement to hide proportions. Contacts should be re-derived from
   the same rules, not hand-placed.
3. **The hand/wrist weight repair sits in the stretched region** and could
   regress.
4. **Widening the shoulder splits the character from the canonical rig** unless
   both change. A divergence is survivable — retargeting is by orientation — but
   it means the authored pose and the rendered pose disagree about where the
   shoulder is, which will surface in contact-heavy exercises.
5. The reference's shoulder-joint *height* is not visible in a front photograph.
   It is estimated here by carrying across the candidate's own
   separation-point-to-joint offset, the single assumption in the table. It
   affects the upper-arm comparison, not the forearm or the span.

## Adapt the current surface, or regenerate from v7?

**Both, in parts.** The refmatch surface splits cleanly along the same line as
the proposal:

- **Keep the torso terms.** Hip, waist, ribcage/lat and yoke are independent of
  the arm rig and were measured against trunk landmarks that do not move. They
  are the part of the surface fit that clearly worked.
- **Re-derive the arm terms.** The deltoid −5 mm and forearm +7 mm radial terms
  were set from radii measured against the *current* attachment position. After
  the shift those measurements have to be retaken, and the arm vertices must in
  any case translate and stretch with their bones — a different operation from a
  radial term.

So: apply the rig change to v7, translate and stretch the arm surface with it,
re-apply the torso terms unchanged, and re-derive only the limb terms. Not a
full regeneration, and not an adaptation of the current candidate either.

## Recommendation

Take the forearm correction and hold the shoulder widening for a separate
decision. The forearm is a measurable defect against the project's own canonical
rig; the shoulder width is a preference about which physique the character
should have, and accepting it implies a canonical-rig change too. Splitting them
also keeps the downstream revalidation tractable: the forearm change alone
already touches every hand contact in the app.
