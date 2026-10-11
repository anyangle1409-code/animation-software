# Female CT bounded intensity diagnostic — not anatomical segmentation

Courtesy of the U.S. National Library of Medicine.

Completed private source-only experiment on existing verified sources1817..1826.
No production code, male acquisition guard, canonical skeleton or source bytes changed.
Ruling: reuse unchanged generic `component_sizes`/`make_surface` helpers from
the pinned private source archive; do not fabricate a female input to the strict
male3mm extraction interface. Full512x512XY,10consecutive1mm source planes,
fixed illustrative HU>=500, no anatomical seed or largest-component selection.
Cost/limit: intensity boundaries are not named bones and the10mm slab is cut.

## Exact verification

- Existing generic surface suite:10tests PASS,0.229s.
- Every10raw/PNG/header pin checked; HUaddend-1024, normal+1, sameXYcorners,
  measured1mm descendingS=-854..-863 verified before output.
- 2621440mask pixels checked against independent PIL PNG decode and stored
  value>=1524:0differences. Signed arithmetic avoids unsignedHUwrap.
- 18410selected voxels;100six-neighbour intensity components, all retained.
  Largest counts8186,7269,627,541,412,278,263,260,131,90 are NOT bone labels.
- 26949vertices/27466quads. Independent six-neighbour exposure count27466;
  coordinate bounds checked. Source slabs touch1392voxels at superior cut,
  1654at inferior cut. Whole anatomical coverage is explicitly not established.
- Extraction1.703s; existing helper SHA256
  `b4f96f83fa3221d60852088a03fb266fe13e42a94c25de0dd1c9334ae60ca54a`.
- Actual Blender5.2.1LTS factory-startup,2threads: native3D scene/render then
  saved/reopened; all26949vertices and27466quad bindings checked against OBJ,
  maximum coordinate rounding difference0mm. No armatures/skeleton changes.
  Native job9.509s. One768x768oblique render actually viewed: two larger thin
  curved intensity-shell clusters plus smaller separate islands. Qualitative
  display only, not accepted anatomical identity/manifold/contour validation.

Coordinates are scannerRASmm under **unverified outer-edge pixel-origin assumption**.
Blender unit display is0.001m/mm; source mesh coordinates are unchanged. No
scanner-to-HGPT registration or pixel-centre convention is accepted. Face-only
voxel boundaries can have nonmanifold edge/corner contacts; no smoothing/repair.
Seven pelvic landmarks remain0/7; readiness0READY/9PARTIAL/3BLOCKED unchanged.
Intensity mask performed; anatomically labelled segmentation NOT performed.
Full regression remains non-green; targeted checks/CI do not cure C003 failures.

## Private outputs and exact pins

Directory outsideGit:
`C:/Users/Mark/Documents/Codex/hgpt-private-female-ct-candidate-1700-1900-20261011/bounded-intensity-1817-1826/`

| Artifact | SHA256 |
| --- | --- |
| safe_diagnostic_report.json | a994ccd727456a22e9f1fc9d0fc0fca6d403605510aa5a164ea1bbdf2f26871f |
| private_intensity_mask.npz | 9cf7b50e53b44ecee87b8704f250692e32959030ac9ac7f10cf8e54fc263d7f2 |
| unfiltered_intensity_boundary.obj | 1034bc4fda196f1250d9d5148121eac71a79f6db379a7813ac9347c762c93d4a |
| private_intensity_components.blend | 8642368a64e8fa2f53d361468087ff9195486d612662b057335ce7711ac7fc52 |
| native_oblique_diagnostic.png | 8f52599f35fc08f16d97557f54221df2626c0ca4c215e17404e548d78e07ef8c |
| safe_native_report.json | c850b5d9bfeea9871d90ecee9bccccbf34dbdf869bffe794f032e9fb6165d8e4 |

Existing201source report pin:
`a4796ab1fdfa186a41300b1e02842a24cf352ca118a9037e2020e5183d7b9cfb`.
Private orchestration scripts retained under
`C:/Users/Mark/Documents/Codex/hgpt-private-hip-plate-678c8c03/`:
`female_bounded_intensity_diagnostic.py`, `female_bounded_native_diagnostic.py`.
Generators intentionally refuse existing output locations; do not rerun over files.

## Checkpoint and next executable task

PR26headfb55493de85d444475f71bd58ce5e6b34ba7cd09 all3CIchecks PASS,
run38100119831. Three linked worktrees clean before this metadata checkpoint;
other live branches preserved. Battery22% observed; no power settings changed.

Next: extend intensity-only mask/count diagnostics across existing201arrays with
bounded memory/time, independently check mask arithmetic/source grid and record
end-plane/XY contacts. Preserve all components; do not infer anatomy from rank.
Claude can open the privateBlend and inspect source1817..1826intensity components,
not edit the source skeleton or accept landmarks. Qualified independent anatomical
review and full-coverage evidence remain separate required gates.
