# W1/W2 original full-body bridge — provisional

Separate `codex/functional-original-fullbody-bridge-20261011`, stacked on
PR72 `f29fb92542430279e822ba4d2baa7d19ae406a67`. The PR48 owner decision at
`f9d4ca0f` and all later Lane G software work remain preserved. This checkpoint
does not alter the source Blender file, the accepted-state ledgers, or any Chat
parser/renderer contract.

## What was actually connected

The existing project-authored male body is now guarded as an explicit evidence
bridge rather than being implied by unrelated shoulder-only renders:

- `HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE`: 17,946 vertices;
- `HGPT_CANONICAL_V4_ORIGINAL`: 67-bone runtime armature and the body's existing
  Armature modifier target;
- `HGPT_ANATOMICAL_MASTER`: separate 206-bone source armature present at rest;
- 16 bilateral major-bone diagnostic mappings, including explicit many-to-one
  radius/ulna→forearm and tibia/fibula→shin collapses.

The mapping follows the already recorded F-SIDE-001 convention: anatomical left
is +X and binds runtime `*_r`; anatomical right binds runtime `*_l`. Independent
review caught and corrected the initial name-matched reversal before this branch
was accepted. The nine unchanged images did not depend on this mapping and were
not rerendered.

That mapping is an inventory/communication aid only. The 206-bone armature does
not drive the body. It is not a registered retarget, inverse-bind mapping, or
anatomical acceptance result.

The old r95/a003 scene predates the point-domain `hgpt_region` attribute expected
by the current pose-definition loader. The evidence builder adds an all-torso
placeholder attribute in memory only so the existing pose constructors load;
it does not execute region metrics and never saves the source `.blend`.

## New executed evidence

Four pure contract tests passed after missing-feature failures: orthogonal
front/side/rear views, bilateral inventory guard, wrong-body/runtime refusal,
and pose-bounds full-body camera framing including non-finite/overflow refusal. Four
native Blender 5.2.1 tests passed against the actual r95/a003 scene, checking
all three named objects, exact 206/67-bone counts, 17,946 vertices, the enabled
Armature modifier target, anatomical rest state, and negative disabled/wrong-
target/additional-anatomical-driver/non-rest cases.

Nine new 900px images were rendered from actual Blender 5.2.1 at neutral,
press-top and pull-up-top, each front/side/rear. The first attempt exposed a
torso-only crop; bounds-derived framing then produced complete head-to-foot and
raised-hand views. Neutral front and press-top rear were visually inspected.
The original body deforms under the existing runtime pose constructors; the
proxy thorax, sternum, broad scapula markers, long-bone shafts and joint-centre
markers remain project-generated diagnostics.

Private evidence directory:
`C:/Users/Mark/Documents/Codex/hgpt-functional-original-fullbody-v1-20261012/`.
Manifest SHA-256:
`d9cec2eea95d0c4a04e3f8557644b64733b419816968f4ff2ec87159477a3785`.
All ten manifest-listed evidence hashes were independently recomputed with zero
mismatches. Source blend SHA-256 remains
`670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56`.
No private output or new native/source bytes are added to Git.

## Defects exposed, not approvals

The views confirm a usable original-body/runtime bridge, but also show why it is
not an anatomy or deformation milestone: scapula proxies are broad ellipsoids;
the thorax cage is a torso-derived wire guide rather than ribs; it stays a rigid
spine child while the shoulder markers move; and no surface-contact solver keeps
the blades on a measured rib surface. Existing shoulder/axilla skin response is
visible but has not been compared with qualified real-human motion.

The rest-fit rays are diagnostic only. Proximal upper-arm and thigh samples hit
remote surfaces (up to 0.4998 m and 0.2633 m), so those values cannot be treated
as local tissue thickness or accepted centring. There is no breathing, muscle
sliding, collision/contact, anatomical-axis registration, clinical motion,
skin-weight, deformation-quality, GLB, or production approval here.

## Exact next action

Replace the proxy thorax/scapula markers with the newer separate authored thorax,
S-curved clavicles and costal blade shapes while preserving this original body
and its runtime deformation. Define an explicit 206→67 retarget/attachment
contract (including non-bijective limbs), then compare blade-on-thorax placement
and coupled 0/90/160 movement against qualified anatomical and real-human
references. Only after that should broad movement deformation and Chat GLB/
inverse-bind packaging advance. Do not repeat these nine unchanged views.
