# Source shell geometry and actual laptop Blender review

Follow-on to Work's PR34, not a repeat of its 54-file acquisition/topology audit.
Preserved PR32 `555e2a6c`, PR33 `484aa52b`, PR34 initially `c765ff24`, then
reconciled its newer `247020ac` head. Final header CI run38075047099 independently
observed SUCCESS (65tests,54hash-pinned headers). No source islands removed or
canonical assets edited.

Eight flagged male STLs were independently obtained on this laptop from frozen
[BoneHub revision ac8de2b3](https://huggingface.co/datasets/BoneHub/visible-human-3d-models/tree/ac8de2b38f5ae1a0996053ca0639dd6ae43358f1/visible_human_3d_models/CT/Mesh/01_Male).
Each exact SHA256 matched PR34's source pin before private storage. This is the
same Visible Human donor, NOT an independent population sample. Raw bytes and
all review images remain outside Git in `work/private-bonehub-components-20261010`.

## Exact-vertex nondegenerate triangle components

Lengths below are **source units, NOT verified millimetres**. Component grouping
uses exact float32 vertex connectivity; point-connected shells remain one group.
Bounds and mathematical moments are diagnostics, not anatomical or joint centres.

| Source label | Component face counts | Small component extent X/Y/Z | Overused edges |
| --- | --- | --- | --- |
| CALCANEUS_LEFT | 37620 + 196 | 5.574646 / 2.546661 / 2.092415 | 0 |
| INTERMEDIATE_CUNEIFORM_LEFT | 4864 + 48 | 0.196106 / 0.008789 / 0.235916 | 0 |
| TALUS_LEFT | 24772 + 2 | 0.00003052 / 0 / 0.00001526 | 0 |
| HAMATE_RIGHT | 4600 | No second usable-face component | 0 |
| RIB_1_LEFT | 15352 + 2 | 0.00003052 / 0.00002289 / 0 | 0 |
| RIB_1_RIGHT | 17676 | No second usable-face component | 0 |
| RIB_3_LEFT | 28320 + 8 | 0.00003052 / 0.00003815 / 0 | 5, small component only |
| RIB_4_LEFT | 31768 + 64 + 8 + 6 + 6 + 4 + 2 | 64-face shell: 0.189972 / 0.280251 / 0.201904 | 12, distributed 5/3/3/1 across four tiny components |

Main-shell signed algebraic volumes are respectively80337.617137,3829.707494,
43259.376380,3474.871500,9261.037189,10708.379927,17145.358260,20955.320426
in source-unit cubed, NOT accepted physical bone volumes. Small closed shell
volumes: calcaneus11.947015; cuneiform1.191027484e-8; rib4's64-face shell0.001575517.
Zero-volume, open, overused-edge or inconsistent-winding components return null
volume/volume centre. Self-intersection and vertex-manifoldness are NOT certified.
Degenerate triangles excluded from moment analysis are retained in raw rendering.

Calcaneus fragment bounds are X420.833801..426.408447,
Y246.727432..249.274094,Z108.846878..110.939293. Main-shell minimumY253.819168:
their Y bounding intervals are disjoint. This is a geometric observation, not
proof the fragment is unwanted anatomy. Rib4's64-face shell is similarly far
outside the main shell's X range: X437.717224..437.907196 vs272.816193..376.439209.
No fragment deletion or source correction is authorized by these findings.

## Byte-level frame evidence, reconciled with concurrent Work

All eight hash-pinned STL headers explicitly contain
`3D Slicer output. SPACE=LPS`. This laptop independently checked eight files;
concurrent Work PR34 has now independently verified all54header declarations
in successful CI38075047099. Reuse that completed full-source result. Neither
check verifies image registration, length units, exporter options, or
correspondence with our raw NLM CT pixels.
[Official Slicer documentation](https://slicer.readthedocs.io/en/latest/user_guide/data_loading_and_saving.html#specifying-the-coordinate-system-in-model-files)
defines these header tags and distinguishes internal RAS from saved model LPS.
The earlier blanket statement that export coordinate choice was undocumented
is superseded by the actual byte-verified headers, not by a scanner transform.

The upstream mesh README's MRML export snippet alone does not show the final
STL writer settings. BoneHub images derive from aligned/rescaled Visible Human
CT; raw NLM image coordinates cannot be assumed identical. No transform installed.

## Actual Blender and verification

Blender5.2.1 LTS `9e2066aef7ef` imported every raw triangle and each separate
vertex instance with exact float32 coordinates, no welding/smoothing/scaling.
Generated three512x512 source-axis views per file:24PNG hashes independently
verified, eight raw hashes reverified after rendering. No blend file saved.
CALCANEUS_LEFT/source_Z and RIB_4_LEFT/source_Z visually inspected: calcaneus
fragment visible; tiny rib islands cannot be certified by whole-source views.
Views are source-axis diagrams, NOT accepted anatomical orientations.

Tests:18 synthetic/CLI tests PASS; two actual Blender integration tests PASS.
Native missing-feature RED -> GREEN and tiny-camera false-success RED -> GREEN
were observed. Bounded renderer refuses unsupported extents/offsets before any
output, preserving geometry rather than automatically scaling it. Both Windows
and Linux synthetic CI and Ubuntu actual-Blender CI are configured; this new
checkpoint's remote CI was subsequently observed: all three jobs in
[run38075799684](https://github.com/anyangle1409-code/animation-software/actions/runs/38075799684)
SUCCESS on`fc6c639d665aff904559fadd24bc755b639c436f`, including native Blender,
Windows reconstruction and Linux source gates. Clean detached short-path
checkout also51targeted tests PASS (18new+23unchanged reconstruction+10source gate).
Full inherited regression suite remains red; no broad-suite acceptance claimed.

## Next executable action / laptop handoff

1. Preserve verified checkpoint CI and review Ubuntu's actual installed Blender version.
2. Obtain only bounded source image/segmentation metadata needed to test STL
   declared LPS against image transforms and units; verify immutable revision
   and raw header fingerprints. Do not download multi-GB volumes blindly.
3. Review fragment-focused views and registered label masks before interpreting
   fragments. Keep raw source, experiment and canonical layers separate.
4. Independent-cohort VSD data remain license-quarantined; article permissions
   do not authorize noncommercial dataset bytes for product use.

Canonical readiness remains0READY/9PARTIAL/3BLOCKED; Gates6/9 and independent
pelvic landmarks remain open. Source skeleton continues to govern all geometry.
