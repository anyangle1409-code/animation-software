# W1D triangle-interior source witnesses — candidate only

Input Work `b8fcb6470347044bfd3b749bfbc84a8989573260`; separate branch
`codex/source-surface-triangle-witness-20261011`. Shared plan PR48 read at
`517596207b12ed3693b62c9d4521f23bbd8e3067`, without merging.

New stdlib `scripts/anatomy_fit/source_triangle_witness.py` projects one point
onto a closed nondegenerate triangle, including its interior. It is NOT a full
mesh-mesh minimum, signed penetration, cartilage gap, joint centre or physical
registration. All acceptance flags stay false; no source repairs or scaling.

Ruling: bounded reversible design proceeds under explicit owner autonomous
authorization, without routine design approval. Keep real source LEFT-only;
synthetic mirrored tests are not bilateral patient evidence. Cost: right check
remains open. No anatomical or renderer assets changed.

## Actual existing source and Blender evidence

Reused two private original STLs, no downloads, source revision
`ac8de2b38f5ae1a0996053ca0639dd6ae43358f1`, same Visible Human male donor.
All valid face islands retained. Degenerate faces excluded from BVH query only;
all original triangles remain in native scene. LPS header is not accepted
laterality, units or image registration.

| Source label | Original SHA256 | Raw / usable faces |
| --- | --- | --- |
| TALUS_LEFT | b79dcb8037223d2652e300cb42124c9d4e16dfedcc49ff36b4d44ed3fc24602e | 24812 / 24774 |
| CALCANEUS_LEFT | 5e160f34aff9c2bfb1e3b6546add17a083ec4f6bb4be0f29392e714d44132eb9 | 37816 / 37816 |

Blender5.2.1 factory/2threads: 12391talus vertices against calcaneus triangles,
18912calcaneus vertices against talus triangles. Native BVH nearest-face proposals
independently projected by double-precision implementation. Maximum coordinate
error0.0000300204983, distance error0.0000344127564; numerical tolerance0.0001
**source units**, NOT mm. Verifies each proposed triangle projection, not an
independent global nearest-triangle search. 3365/2734 witnesses strictly interior.

Directional minimum witnesses0.3077868659540219/0.3091393150716292 source units
improve earlier rounded0.382vertex-only upper bound. Still upper bounds: positive
witnesses do NOT exclude between-face intersection or prove normal joint spaces.
All raw vertices saved/reopened exactly; source hashes rechecked after execution.
Actual768x768native render viewed: two coloured source shells, retained calcaneus
fragment. One oblique view cannot certify articular contact/anatomy. Probe14.329s.

Private folder: `work/private-bonehub-components-20261010/source-triangle-witness-20261011`, outside Git.

- Report SHA256 `ec235cea59101ab3055c15cb2ddb157874f21c64e3b70e3c14fd0934e555d528`.
- Scene SHA256 `c0e9916ee44c295552fe4d51a4cef1f4ffb711f369f0cb2c6047e8f77ab71bb8`.
- ViewedPNG SHA256 `d7f4cee70d290fbfe8d4e87dc91f511c33e6502413f5c5158c8e2de38f5c8da3`.

## Verification and limits

Interior test observed FAIL missing feature then PASS. Initial setup error was
replaced by explicit feature assertion and RED rerun. One rotated fixture had
wrong hand-derived expected nearest edge: localY/Z(1,2) projects to(.5,1.5) on
y+z=2. Corrected fixture, not algorithm or tolerance. 10mathematical tests PASS;
18unchanged shell/CLI tests PASS. Actual native independent synthetic BVH test
PASS both signed-X mathematical frames, NOT bilateral anatomy. Windows/Linux
mathematical and native Ubuntu Blender CI configured; remote result pending.

Fresh readiness recount0READY/9PARTIAL/3BLOCKED, unchanged. Historical full1097
suite remains red20failures/41errors/1skip; no unnecessary rerun or full-green
claim. c005/source frame/physical units/contact/production gates unaccepted.

Latest exact heads PR26/44/45/41/42/43/46 CI all reportedSUCCESS; PR48 has no
checks, not a CI success claim. Other lane branches and frozen assets preserved.

Next: pinned right talus/calcaneus and wrist witnesses only if bytes available or
bounded acquisition justified. Do not redo left pair or44vertex scans. Exact
mesh-mesh/intersection tests and anatomical articular patches remain separate.
Standing-source probe: [Sebaaly publisher](https://link.springer.com/article/10.1007/s00586-020-06670-7)
preview/subscription only, no original tables read; PubMed429. No retry unchanged
denial or abstract arch means substituted for per-level vertebral angles.

## Independent code review and fix pass

Read-only reviewer independently ran10+18Python tests and native1PASS, but found
two Important edge cases outside those fixtures: nonzero subnormal squared area
could place the witness off-plane; squaring1e-200distance could return zero.
Both reproductions added and observedFAIL before minimal fixes: refuse subnormal
squared area; use stable hypot for candidate ordering and distance. Final12new+
18unchanged tests and actual native1PASS. No Minor or Critical findings.
Reviewer did not judge private artifacts/remote CI/anatomical truth/physical
registration/full clearance/inherited full suite; those are respectively exact
local evidence or explicitly open gates, not assumed approvals. No full rerun.

## Bilateral filename pairs completed; no anatomical approval

Only6missing private laptop STLs acquired (3839704bytes total), exact frozen
revision LFS SHA/size verified; left scaphoid also matched historical pin. No
completed54/30surface acquisition or44vertex scan rerun. Source SHA/face counts,
directions, numeric-only results and four private scene/report/image hashes in
`docs/SOURCE_TRIANGLE_BILATERAL_CANDIDATES_20261011.json`; raw vertices absent.

Four nominal pairs now executed in native Blender: left/right talus-calcaneus
and scaphoid-lunate. All69707source vertex queries checked against independently
projected target triangle proposals. Retained all valid islands, original raw
source triangles/vertices saved/reopened exactly; four actual previews viewed.
Not independently accepted anatomical laterality, contact or original mesh rights.

Right foot30984queries/7.047s, directional witnesses0.5860309822/0.5843044781;
left wrist3684queries/2.300s,0.8742576687/0.8747750457;
right wrist3736queries/2.347s,0.9030651755/0.8839689544. Allsource units only.
Earlier vertex-only bounds rounded0.590/0.875/0.910 respectively. Neither small
improvements nor side differences imply accepted joint clearance or pathology.

Initial wrist probes FAILED0.0001numeric tolerance before output creation:
native float32 globalZaround1100 produced0.000100771939 coordinate discrepancy.
Diagnostic evidence isolated large-offset rounding, not anatomy. Query-index-only
subtraction of one existing target source vertex and double-precision restoration
reduced maxima below0.00000250distance/0.00000196coordinate, same tolerance.
No saved vertices changed, rescale or source-to-HGPT transform installed. Local
rebasing used for wrist indices only; completed foot probes not repeated.

Code2b471fa8ec95cba2de3475e5d940921f7b1b55dd ALL3CIchecksSUCCESS,
[run38133931890](https://github.com/anyangle1409-code/animation-software/actions/runs/38133931890).
Metadata-only follow-up must have its newest exact-head CI checked separately.
Draft PR50, no main merge. Readiness0READY/9PARTIAL/3BLOCKED unchanged.

Next: preserve/reuse completed four scenes and projections, confirm latest CI,
then a bounded true triangle/triangle intersection or global-distance prerequisite
with fail-closed numerical tests, or W1A physical registration evidence. Independent
articular patch/landmark/qualified review and accepted units remain required.
