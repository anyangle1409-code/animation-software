# Phase 4 — push-up wrist and forearm, re-measured after Stage 2

Measurement and diagnosis only; **no fix applied yet**. Stage 2 is locked and
Phase 3 passed. Nothing promoted or merged, tree green.

## A correction to my own first numbers

I first measured wrist extension as the angle between the forearm's and the
hand's bone axes on the **canonical rig**, and got 51.2° at Top and 43.0° at
Bottom — and concluded the wrist was now anatomically plausible. That was wrong.

The purpose-built diagnostic from an earlier round
(`scratchpad/repair/wrist4.test.mts`) measures the **character's** wrist with a
twist/swing decomposition and accounts for the 14.62° offset between the hand
and forearm axes that exists in the bind pose itself. Against that, the
canonical bone-axis angle is not the anatomical wrist angle at all.

## The real figures, on the locked Stage 2 state

Push-up, `HomeGymPT_Male_STAGE2_CANDIDATE.glb`:

| | value |
|---|---|
| bind-pose offset, hand axis vs forearm axis | 14.62°, both sides |
| peak wrist angulation | **92.98°** |
| extension at that peak | **92.10°** |
| ulnar deviation there | −12.73° |
| pronation there | **72.40°** |
| plain forearm-to-hand angle on screen | 104.48° |
| left/right mismatch | 0.0001° |
| decomposition residual | 0.0000° |

Through the repetition, extension runs 68.5° → 92.1° and pronation 72.4° →
97.9°, with deviation −12.7° to −37.0°.

So the historical ~102.7° / ~95.5° evidence was substantially right, and Stage 2
did not fix it: **extension of 92.1° is past the human limit**, which is about
70–80°, and the rig's own `hand` z limit is 80°. Pronation approaching 98° is
also large, and is the obvious candidate for a corkscrew radius/ulna silhouette.

Other geometry, measured on the same state and internally consistent:

| | Top | Bottom |
|---|---|---|
| shoulder ahead of the hand, ground plane | 173.1 mm | 244.6 mm |
| forearm angle from the floor | 83.7° | 70.9° |
| elbow height | 313.5 mm | 300.7 mm |
| lowest palm vertex | +0.3 mm | 0.0 mm |

The palm is planted at the floor to within a third of a millimetre, and both
sides are identical to the digit. The old ~218 mm shoulder-ahead figure now
reads 173 mm at Top and 245 mm at Bottom, so Stage 2 did move it — the brief was
right that it needed re-measuring rather than reusing.

## Where the diagnosis stands

Two of the eight candidate causes can already be separated:

- **Not the Stage 2 shoulder change.** Extension is 92.1° here and the same
  diagnostic's historical figures were ~102.7°/~95.5° before any of this work,
  so the wrist problem pre-dates Stage 2 and was not created by it.
- **Pose and hand placement are implicated, not innocent.** 92.1° of extension
  with the palm planted and the shoulder 173–245 mm ahead of the hand is a
  geometric consequence of where the hand is put, not of skinning.
- **Twist is a separate axis and is large.** 72–98° of pronation is carried
  independently of extension — the decomposition residual is 0.0000°, so these
  are genuinely separate contributions rather than one being an artefact of the
  other.

What I have not done: attributed the *visible* forearm deformation between those
causes and the skinning ones — the Stage 1 lengthened forearm against existing
weights, the v5→v6 hand/wrist repair region, and the weights themselves. My own
attempt at a forearm silhouette render did not produce a trustworthy image
(vertex-filter and camera problems that I chose not to keep iterating on), so I
have no visual evidence to set beside these numbers yet, and the brief is
explicit that a skinning defect must not be masked by moving the pose, nor the
forearm reweighted if fixing the hand placement removes the deformation cleanly.

Deciding that ordering needs the silhouette evidence, so **Phase 4 is not
complete and no fix has been applied**. Phase 5 is not started, since it depends
on Phase 4 passing.
