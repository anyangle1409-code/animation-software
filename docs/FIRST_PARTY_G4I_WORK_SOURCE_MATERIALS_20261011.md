# G4i — strict first-party ORIGINAL Work material + absent-UV diagnostics

**11 October 2026, Chat Lane G. Based on actual Work #68 GLB audit [G4g #73](https://github.com/anyangle1409-code/animation-software/pull/73) and verified identity-group importer [G4h #74](https://github.com/anyangle1409-code/animation-software/pull/74).**

## Actual source finding

Work's legitimate 18-mesh glTF 2.0 Blender shoulder pilot (CI run 38153765790, artifact 11706909894, exact GLB SHA `fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f`) describes **six source materials, doubleSided:true and nonmetallic roughness=0.4**. Some wholly untextured scapula blades have no TEXCOORD_0 attribute. Our earlier preview importer accepted only doubleSided=false, roughness exactly 1 and assumed every part had UV0 whenever enabled. These are **software acceptance limitations**, not a reason to reposition shoulder joints, override the source material or regenerate the original shape.

## Implemented

The `allowProvisionalPilot:true`-ONLY path expands the strict source *metadata intake* as follows:

- Accept true/false `doubleSided` source setting, record `sourceDoubleSided` on each original part.
- Accept original finite bounded 0..1 nonmetallic `roughnessFactor` while rejecting nonzero metallic factors, NaN/infinite, blending/transmission and unsupported material fields. Preserve `sourceRoughness`; do not relabel it as already-rendered physically based material.
- Permit `TEXCOORD_0` to be **absent** on untextured pilot materials, return `sourceUV0:null` rather than fabricating coordinates; textured source still strictly requires its real authored UV0 and dedicated original PNG-validated path.
- All actual binary primitive indices, source positions, normals, joint names, four influences, source inverse bind matrices and original bone hierarchy still pass unchanged old strict primitive validation in a separately prepared validation copy.
- The standard non-pilot importer remains **strictly unchanged**: still refuses double-sided and nonmatte source material, and no general relaxation of ordinary GLB dimensions, scene, URL or rights guard is allowed.

**Important:** this only stores the actual material's metadata and original glTF source factors so a later native renderer can choose correct sidedness/lighting; native physically based BRDF and specular roughness shading have NOT been implemented. A missing untextured UV must be handled explicitly in a future GPU screen program; the current source UV-texture shader does not accept null source UV.

## Tests

Targeted Node tests use 18-mesh synthetic valid glTF with Work-like 0.4 roughness, double-sided surfaces and zero source UV and verify the full skin/position parser still accepts it, SHA source bytes remain unchanged, metadata is faithfully preserved, invalid range/alpha/extensions fail and old standard validator remains strict. A pinned CI job re-downloads **actual** Work model artifact #68, reruns `scripts/audit-original-work-shoulder-pilot.mjs` and saves only JSON issue/status report. Do not redistribute Work model itself.

**Do not call Work's six-joint shoulder pilot a finished human model**: Work #72 costal curvature remains provisional, model is not full-body, authored motion is not clinically validated, no accepted soft-tissue weights/deformation, equipment contact, rights review or production release. Clinical readiness 0 READY / 9 PARTIAL / 3 BLOCKED remains independently open.

**Next:** if actual GLB now passes full source G4f validation, record source SHA/binds and 18 parts and move to real native 18-draw scene/rig basis parity; if not, use current CI exact first-party failure to fix one genuine requirement at a time, preserving original anatomical data.
