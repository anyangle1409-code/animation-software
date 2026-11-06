# Home Gym PT standing checkpoints — 2026-11-06

## Fresh-open verification
All three original .blend files opened separately in Blender 5.2.2 LTS (d13f752e3b9c). File hashes matched the dual-character transfer receipt, and the local reference copies were made read-only. No linked Blender libraries were detected. The two female files each have seven packed images, a 50,090-vertex body, and a 69-bone rig with 66 deform bones. Male 07c has a 56,677-vertex body and 81 bones, with 66 deform bones. F11a is the rollback and F12d is the female baseline.

## Female F13a clearance trial
A capped local displacement along the shorts vertex normals targeted the faces identified by the F12d hip-flexion diagnostic. A fresh Blender reopen and mesh fingerprints verified that only the shorts mesh fingerprint differs. The rig rest matrices and the other mesh fingerprints match F12d.

| Structural check | F12d exposed vertices | F13a exposed vertices |
| --- | ---: | ---: |
| Standing | 0 | 0 |
| Hip 45° / knee 60° | 0 | 0 |
| Hip 90° / knee 90° | 12 | 6 |

Standing fabric-to-skin p95 rose from 4.44 to 4.87 mm. The pointed gusset and uneven waistband remain visible. Remaining work includes reshaping the gusset and hems, cleaning up the waistband, closing the remaining coverage gaps, refining the bra cups and strap joins, repairing the thumbs and hand intersections, and refining the ponytail. F13a is an unapproved trial. Female V1 awaits explicit owner approval. Full exercise animation remains paused.

F13a SHA-256: e5d989dbc1526fa0652d7e0fd7341cc3fa1f21af83cab6feaf4202cabd49fbfe. Keep the Blender files and renders private.

## Male 07c appearance requirements
The structural base is approved. The verified proxy has no UV layers, materials, or packed images. Recover the original textured source `HGPT_Meshy_Male_Pro_1.82m_Clean_Unrigged.blend` (expected SHA-256 `b41518437550a6aa57df65c80c05fbc7955053619d94efa83f6587f54efe4e9f`) and record licence provenance. On a separate derivative, transfer or rebuild UVs and bake skin appearance, then fit eyes, hair and clothing. Preserve the standing silhouette, bind pose, weights and corrective shapes, and check for seams and garment clipping in matched front, side, back and three-quarter views. Package textures and get a separate appearance approval.
