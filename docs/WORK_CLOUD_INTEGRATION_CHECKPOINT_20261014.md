# Work cloud integration — 14 October 2026

Independent software lane from PR103 `94e066b9`. No Claude branches, frozen
models, production clips or geometry changed. Reviewed PR48/26, software
PR101–103, PT PR2–6 and Claude PR111–113 plus master-execution checkpoint.

## Export milestone

Blender 5.2.1 on the actual unchanged a003 source reproduces an **importer
display aid**, not a GLB leak: the serialized GLB contains one body mesh;
default import creates Icosphere (42 vertices), while
`disable_bone_shape=True` imports one body and one rig. Do not delete geometry
by name or suppress rig controls in the exporter. Claude's round-trip script
ran unchanged apart from printing serialized inventory: five poses PASS,
max 0.0007 mm, 67 joints, 17,946 vertices, 35,888 triangles, six zero morphs.

The existing candidate receipt now rejects orphan, missing or shared mesh
payloads as well as extra mesh nodes. 14 receipt tests PASS; the orphan test
failed before the guard. Actual native provenance regression PASS. Full
studio baseline: 201 files / 1,125 tests PASS, 62 skipped. No movement approval.

## Next queue

Opt-in versioned provisional rig extension (helpers, individual toes,
knee/elbow morphs); bounded morph-before-skin and pose compatibility;
reuse existing intent/parser/playback; app preflight; controlled native GPU
experiments; dependency audit. Keep all production gates closed.

The environment exposes no usage meter or reset-resume control. Resume from
this independent branch after fetching its live HEAD and rechecking PR26.
