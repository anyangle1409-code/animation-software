# W8 fixed-pose corrective isolation — 24 October 2026

Status: software tests PASS; new native cloud execution PENDING. No model repair or anatomical acceptance.

## Purpose and decision

The verified W8 native archive shows abnormal local edge ratios, stored S7/K1 key geometry and actual S7 activity. The earlier probe omitted K1 channels. Association between an active key and an edge change cannot isolate its contribution. Next dependency: observe actual K1 values and compare the same endpoints at the same skeletal pose with controlled key muting.

Chosen approach: extend the existing pinned r57/W8 probe in memory, retaining its source SHA256, frozen native tessellation and nine press samples. This reuses the native pose exactly. Static key-ratio multiplication would misrepresent key combinations and the modifier stack; an edited .blend candidate is unnecessary for a diagnostic.

## Measurement contract

- Source W8 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`, frozen driver/benchmark source `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.
- Four previously ranked W8 edges only: [15645,53019], [17185,44317], [29237,71026], [32352,71428]. These IDs and suffixes are not reviewed anatomical landmarks or sides; no equivalent V14/R120 correspondence is inferred.
- At each existing press sample, record observed coordinates and actual key values including K1 elbow channels. Temporarily mute S7 alone, K1 alone, and all non-Basis keys, in separate conditions reset from original mute flags.
- Evaluate all conditions with the unchanged pose. Compare edge lengths against benchmark rest V0 in the benchmark's common coordinate space. Report native geometric length ratios, never tissue strain or safe limits.
- Preserve pre-existing muted keys; do not change key values, rig transforms, mesh coordinates, weights or source files. Restore mute flags in `finally`, refresh dependency graph, require identical full skeletal pose signature and key values, unchanged topology and restored endpoint coordinates within 1e-8 m. That tolerance is a numerical reproducibility check, not a biological threshold.
- All-keys-muted retains authored helper motion, constraints, weights and modifiers. It is NOT independently certified skeletal skinning or physiological truth. Conditional changes are not additive causal percentages; unchanged sampled edges do not prove keys have no effect elsewhere.
- No corrected candidate is saved. Failure prevents a successful native report. Source hash and rest signature remain guarded by the existing probe. Publish enriched pose JSON and a phone-readable Markdown table in the existing pose artifact.

## Tests and evidence

K1 omission regression observed FAIL (empty extracted list), then PASS after adding the existing named prefix. Eleven new isolation tests cover fixed-pose measurements, restoration on exceptions, preserved values/pre-existing mutes, changed topology, nonfinite coordinates, missing endpoints, degenerate rest edges, altered skeletal pose, failed coordinate restoration, operator/save guard and phone report status. Missing-module and missing-renderer failures observed before implementation. Full Python diagnostic suite: **226/226 PASS** in isolated cloud workspace; actual Blender execution pending the new workflow. Native results must be downloaded, hashed and read before any claim they passed.

## Anatomical dependencies remain blocked

ISB Part II (Wu et al. 2005, DOI 10.1016/j.jbiomech.2004.05.042; https://pubmed.ncbi.nlm.nih.gov/15844264/) concerns standardized motion coordinates, not automatic rig-axis identity. Seth et al. 2019 (https://pmc.ncbi.nlm.nih.gov/articles/PMC6856649/) models independent scapular movement and validates muscle path behavior; neither justifies treating arbitrary Blender helpers as anatomical joints. Existing foundation-first roadmap and permanent muscle IDs remain authoritative. No new attachments, clinical ROM clamps or highlighting.

The 46 landmarks remain unbound; 0/19 native generic human movement scenarios approved. Shoulder/squat/grip, archive identity and real contact/skin acceptance remain open.
