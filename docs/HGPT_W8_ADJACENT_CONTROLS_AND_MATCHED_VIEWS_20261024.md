# W8 adjacent controls and matched native views — 24 October 2026

Status: **241/241 Python diagnostic tests PASS; native cloud execution PENDING.** No repair, anatomical calibration or production approval.

## Question and controlled comparison

The previous verified run40076658568 measured four ranked W8 edges. Muting S5 reduced the selected distal compression at sample0 but increased middle-edge stretching at sample6; muting S7 reduced selected middle-edge stretching. Those selected edges do not establish how neighboring geometry behaves or whether a visible surface improves. This task adds controls without changing any authored model.

Use the same pinned W8 source SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`, frozen r57 commit `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`, nine existing press samples and seven existing conditions. No new joint-angle recipe or clinical ROM limit.

## Adjacent controls

For each ranked seed edge, select every other edge of each frozen native triangle that contains **both** seed endpoints. Exclude all seed edges from controls and deduplicate deterministically. The triangle tessellation remains identical across evaluated conditions. A control edge may belong to more than one seed neighborhood; the JSON records that association. Missing seeds or degenerate/duplicate triangle indices fail closed.

These are topological neighboring edges, not independently identified tissue regions. They are chosen from the rest topology once and reused at all nine poses; the existing frozen-evaluation wrapper rejects topology changes. All selected endpoints participate in the same finite-coordinate, fixed skeletal pose, key-value and restored-coordinate checks. The original four seed rows remain identifiable via `edge_role`; all adjacent rows remain in JSON for independent comparison.

## Matched native Blender views

Save eight temporary evaluated geometry snapshots: samples0/6 × observed, S5-muted, S7-muted, all-non-Basis-muted. The snapshot callback copies evaluated coordinates/frozen triangle indices while the condition is active, without changing keys or rig; callback failures restore original mute flags. No snapshot .blend is written.

A **separate fresh Blender Python process** opens only these NPZ arrays, verifies source SHA/topology/finite coordinates, and constructs a temporary mesh in a new scene. It never opens or saves the original model. Render 24 Cycles CPU images with uniform grey diagnostic material and smooth normals, plus six phone comparison sheets. Cameras and lights are fixed from observed seed-endpoint bounds for each sample, then shared across all four conditions. Axis views are labelled `axis_negY`, `axis_posY`, `axis_posX`; they do not certify anatomical front/back/side or left/right. There is no geometric smoothing modifier, muscle highlighting or corrected source asset.

The output manifest records camera plan, snapshot hashes, evaluated vertex-buffer hashes and individual PNG hashes. Raw NPZ files remain temporary; reports and PNGs are preserved in the existing GitHub pose artifact. These actual Blender renders show the sampled evaluated surface, with diagnostic shading rather than source materials. They cannot establish physiological tissue strain, internal muscle attachments, joint centres or dynamic balance.

## Verification and remaining gates

New synthetic guards cover exact triangle-incidence selection, ordering/winding invariance, missing/duplicate seeds, invalid triangles, exclusion of seed edges, snapshot condition values, restoration after snapshot failure, observed-focus camera bounds, translation invariance, invalid focus and no original-file open/save calls in renderer. Tests were observed failing before implementation. Full existing Python suite241/241 PASS; whitespace check PASS. Actual Blender rendering/native counts and artifact hashes remain unverified until the new workflow completes.

Keep all original sources, weights, rig, production, Claude branches, PT-App, PT_MODEL_VERSION1.0 and permanent muscle IDs unchanged. All46 landmarks remain unbound, 0/19 generic motions approved; no muscle attachments or highlighting. Next gate is read actual adjacent measurements and inspect the matched rendered images before considering individual-key isolation or any separate repair proposal.

## First native execution verified; visual QA requires a lighting revision

Run40077762287 at `13c809807a41873987e74acf27ab99df941fec51` passed all7 jobs. Native probe measured20 edges (4 seeds +16 unique neighboring controls),9 poses and7 conditions. Full baseline deformation metrics and all prior seed ratios match run40076658568 exactly. Restoration max error is0m for all20 endpoints sets across9 samples. Pose archive12553972380 independently SHA256-matched `ad5874a4d627cf3729f879b06004fde6f1474d470ec2181d4d9c6c24368cabe8`; it contains24 actual Blender renders,6 comparison sheets, numerical reports and render manifest.

All six sheets were visually inspected. Views are geometrically matched and populated, but sample6 rear lighting clips highlights and8-sample images are noisy. Those images are not sufficient for final visual judgment. The renderer is revised to AgX/exposure-0.5, lower fixed light/world intensity and32 samples, preserving geometry, cameras, all diagnostics and comparative conditions. Native re-execution/visual QA of this revision remains PENDING.

Adjacent control report: `recovery_20261023/w8_adjacent_control_summary_20261024.json`. At sample0, S5 muting moves all8 distal neighboring ratios closer to rest, while moving all8 middle neighboring ratios farther from rest. At sample6, S7 muting moves3/4 neighboring ratios per middle seed closer to rest and1/4 farther; S5 muting moves all8 middle neighbors farther. A ratio nearer1 is only a geometric comparison, not anatomically correct deformation. This mixed response reinforces the need for localized, reviewed investigation rather than global key disable.

Raw NPZ snapshots will now be preserved as a separate `phone-w8-evaluated-snapshots-RUN_ID` artifact. Initial review treated non-retention as a minor issue; actual lighting QA demonstrated a concrete replay need. Keeping them enables a future isolated cloud re-render without recomputing the probe. This resolves that deferred reproducibility limitation; no standalone replay is claimed for run40077762287's missing raw NPZs.
