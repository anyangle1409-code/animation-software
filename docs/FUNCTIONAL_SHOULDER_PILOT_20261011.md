# W1 — first authored shoulder shape/rig pilot, 11 October 2026

**PARTIAL functional prototype, not original human / anatomy / motion acceptance.**
This follows the owner's new PR48 v1.1 decision at
`f9d4ca0f078207a6561bd4f3e1460bdf9d0f7192`, superseding the earlier clinical
registration prerequisite for starting a separate prototype. No shared plan,
frozen candidate, Claude work or Lane G implementation was modified.

## Live input and separation

- Work PR26 `b8fcb6470347044bfd3b749bfbc84a8989573260`: three checks SUCCESS,
  run38101469591. PR48 is documentation-only, no checks reported.
- Prior source PR56 `6791933870953d6857604ded24ba9de27c8b8df0`: six SUCCESS
  checks across38136503170/38136532937; no completed source probes repeated.
- Latest renderer/exercise-interface branches through G4e `a81ecf51` fetched,
  preserved without merging or duplicating them. Claude `540edd4c` preserved.
- c004 scalar/landmark record reused, not rebuilt or changed. Local byte SHA256
  `99500d94e06c66ca489bdaccc0345446f98794946254c5e592d9449696f396c1`
  verified unchanged before/after actual generation. Cross-platform checkout
  newline hashes can differ; actual source digest is in each generated manifest.
- Clinical readiness file and 0 READY /9 PARTIAL /3 BLOCKED remain unchanged.
  Inherited 1097-test suite remains non-green; no cosmetic broad rerun.

## Authored shape vs control rig

Six compact controls: bilateral clavicle, scapula, humerus. **Scapula control
heads are at AC**, not the inherited scapula display-rod head at glenoid; this
is an explicit control-pivot representation change, not an anatomical landmark
relocation. Original SC/AC/GH anchors and humeral segment lengths are retained.

Clavicle is a capped volumetric tube along a new S-shaped centreline, with
separate anterior medial and posterior lateral bows. ±12/7mm bows, 6mm tube
radius and split0.65 are **artist review assumptions**, not measurements.
Fontana's two projected radii do not uniquely define an anatomical 3D curve:
`canonical_clavicle_shape_source_review_v1.json` remains authoritative about
that limitation. No stature ratio or contradicted regression statistic used.

Scapula is a closed coarse4mm-thick authored blade fan around existing c004
relative landmark guides, with separate spine/acromion, glenoid-rim and
coracoid guide regions. Source context is the existing Lee2024 relative
landmark model; global pose and articular surfaces remain provisional. No
source STL/CT geometry is copied. It is visibly faceted and NOT a realistic
finished scapula surface or proof of thorax-conforming placement.

All shape vertices have one declared rigid control weight. Native tests compare
actual evaluated vertices against each control palette. These are bone guides,
**not skin or muscle weights**. Skin must be authored around this developing
skeleton, never used to move its anchors.

## Actual results

7 new mathematical tests PASS (endpoint invariance, opposing bows, bilateral
mirror, bad inputs, closed blade topology); actual Blender5.2.1 native test1
PASS (SC/AC connection, arm length, actual deformed vertices at seven stages,
saved/reopened counts and nonapproval). Missing feature tests failed first.
Independent read-only review: no Critical/Important finding; two Minor input
bugs (degenerate bow-tie fan and huge-integer overflow) reproduced then fixed
with failing/passing regressions. All actual evaluated vertices checked within
3.60e-7m of intended rigid transforms; GH attachment within2.85e-7m. Actual
pilot has no zero-area faces. Converted tube cap vertices are separate from
side seams: visually capped, NOT topologically watertight. General fan-outline
self-intersection/concavity validation is not a clinical surface acceptance.

Initial actual export exposed missing mesh armature parents. Focused native
regression reproduced FAIL; explicit parent preserving world transform fixed
it, regression PASS. Corrected export completed without those warnings.

Private output: `C:/Users/Mark/Documents/Codex/hgpt-functional-shoulder-v1-parented-20261011/`.
20 real Blender800x800 PNGs: front/side/rear/three-quarter/overhead at authored
arm rotations0/45/90/160deg. Warning is rendered into every image. Native
`.blend`, shoulder-only GLB, six-control rest/mapping and seven time samples
are in that folder. Generated-file digests independently recalculated/matched.
Source bytes/native Blend outputs are NOT committed to Git. CI generates
rights-safe authored diagnostic views/GLB/JSON as downloadable artifacts.

Pre-metadata-renaming final-parented local native SHA:
`4b0f92431d7c4ed7bbcd8851ee82066acf5a4288f9f16856087241fc4e80bb3e`;
GLB `162f6bcdc856915e1911d04026df70b852b65d677ef2b54f635c84cf4a8942b8`.
The native scene/GLB are unchanged by renaming the diagnostic angle field;
future regenerated files carry their own manifest digests.

## Movement evidence boundary and visible findings

Latest reviewed-code regeneration is in
`C:/Users/Mark/Documents/Codex/hgpt-functional-shoulder-v1-reviewed-20261011/`.
All22 generated-file hashes independently match the manifest. Native SHA256:
`73b54685eb45e2cc32d80d46f685356bab3dc3a1fef68d5b682bbeb42c5b5754`;
GLB SHA256:
`71b2cc03c9675323420a0dbc8f0b27ca6f207325b04594ade36b00d47b1b6727`.
These are the current handoff bytes, superseding the earlier parented output.

PR68 initial head5d78f642: both platform mathematical checks PASS; native
unit1 PASS on Ubuntu Blender4.0.2, but image generation FAILED(exit134) because
libEGL.so.1 was missing. Follow-up workflow explicitly installs EGL/Mesa and
uses a software-rendered virtual display (existing repository render pattern).
This is an environment repair, not anatomical approval; new exact-head CI
must verify the repaired render/export path before claiming online success.

Uses existing primary evidence ledger
`anatomy/audit/primary_clavicle_motion_u3_source_review_20261010.json`:
Ludewig2009 DOI10.2106/JBJS.G.01483,12 healthy subjects/bone-pin tracking.
Elevation includes clavicle elevation/retraction/axial rotation and scapular
upward rotation/tilt, not GH-only motion. Existing evidence distinguishes
SC, AC, ST, GH and HT reference frames. No universal2:1 motion assumption.
The present diagnostic shows those coupled directions qualitatively, but its
12/10/28deg clavicular and52/16deg scapular response and smoothstep time law
are **authored, unvalidated**. Arm delta from the slightly tilted inherited
rest posture is not a measured HT angle. No loaded exercise/dynamics claim.

Native neutral rear/side and elevated front/rear plus overhead reviewed:
distinct centres, visible broad blades, opposite clavicle bows and moving
shoulder girdle are observable. Neutral/pose blade shape remains crude;
missing thorax prevents checking scapulothoracic conformity/contact. GH head
guide sits alongside coarse rim; no cartilage or clearance acceptance.
Official PMC fulltext request returned browser challenge during this session;
not bypassed. No photographic/video reference comparison completed, so no
real-human movement-validation PASS is claimed.

## Integration and next executable actions

GLB is **SHOULDER GUIDES ONLY**, not the promised full male character. Native
matrices are row-major Z-up; GLB exporter converts to Y-up. Do not hand the
native matrices directly to G4b's column-major GLB-space input. Full GLB joint
order/inverse-bind/source-to-runtime preflight and renderer parity remain
pending. Read Lane G PR59/60/66/67 contracts, consume them without rewriting
their importer. All approval flags remain false. No production model supplied.

Next: exact-head CI and review; add source-aware thorax/sternum guides and
test scapula location/contact in neutral/elevation; replace the crude fan with
a better authored blade; then expand to full-body lean control skeleton and
original male skin/weights (W2), with independently compared movement frames
and shoulder/axilla correctives (W3/W4). Do not wait for all206 clinical bones,
repeat prior CT/source scans, promote c005 or claim W0–W7 complete.
