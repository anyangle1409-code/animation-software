# W1 authored costal blade curvature — provisional

Separate `codex/functional-scapula-bowl-20261011`, parentPR71
eaa6850c9a4091c24edf9a95bebf10438e839e1d all4CI SUCCESS. PR48owner decision
f9d4ca0f preserved. No LaneG, source records, accepted anatomy or old assets edited.

## Reference and explicit assumption

[University of Utah Digital Dissector, scapula anterior view](https://anatomy.med.utah.edu/diganat/anatomy_tutorials/digital_dissector/index.php?add=/scapula&lab=29&menu=29+Scapula&selectsize=Small&textsize=Small)
describes a shallow concave costal/subscapular fossa. This is a qualitative
shape reference, not a registered specimen, depth measurement or contact model.
Only the textual shape description informed this project-authored guide;
no institutional images/scans redistributed or used as output geometry.

New shape: four radial rings/one centre per surface, shallow parabolic
posterior recession8mm, surface spacing4mm along a fixed posterior-oriented
reference normal from the first3outline points. This is NOT uniform4mm
perpendicular thickness measured at every curved face; steep retained outline
sectors have much smaller local perpendicular spacing.
8mm is an artist hypothesis, NOT a source measurement. Retained13border
midplanes, SC/AC/GH, rest matrices, other16pilot meshes and existing pose
response; joint centres are not moved to fit the blade or future skin.
No new clavicle/scapula placement or fitted glenoid/epicondylar axes claimed.

## Executed evidence

4new pure tests: missing-feature FAIL then PASS. Posterior recession/border
identity, Xmirror without anterior inversion, opposing edge uses/closed
topology and invalid/ambiguous input refusal. Inherited10pure tests PASS.
2new native Blender tests: missing-feature FAIL then PASS; source/rest/other
mesh identity, all106vertices per blade rigidly following scapula palette at
0/90/160. Repeated rebuild exposed numbered Blender object IDs; exact lookup
reproducer confirmed `.001` naming; lookup now tolerates this, no geometry
or tolerance relaxation. Inherited3reach +2thorax native tests PASS.
No unchanged1097test suite or CT/proximity/old motion audit repeated.

Actual Blender5.2.1 nine new800px front/side/rear at0/90/160, private:
`C:/Users/Mark/Documents/Codex/hgpt-functional-scapula-bowl-v1-20261011/`.
Native SHA256d35f0048db0a876fc8a3a576e4ca44602b6f4836e3c843a6a9ea7bd39f8101f6.
All10generated hashes independently checked against manifest. Source record
SHA99500d94e06c66ca489bdaccc0345446f98794946254c5e592d9449696f396c1 unchanged.
Neutral side and160rear images actually inspected. Radial curvature visible,
not proof of anatomical realism; gross blade placement, upper-rib paths and
sternum tilt/length remain provisional/defective. No human skin/muscle yet.
Independent code review and exact-head CI required before final checkpoint.

## Open gates / next task

No clinical anatomy, collision/contact, breathing, fitted human motion,
full-body deformation or production approval. Research0READY/9PARTIAL/3BLOCKED
unchanged. Next consequential geometry: source-informed thorax dimensions,
blade placement/local anatomical axes and original full-body mesh around the
skeleton; no repeated nine unchanged renders. No newGLB; preservedPR68GLB
and PR71native matrices remain separate provisional integration data.
