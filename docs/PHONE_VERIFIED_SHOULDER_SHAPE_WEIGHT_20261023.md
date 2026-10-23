# Home Gym PT — verified static shoulder weights and corrective shape keys

**2026-10-23. READ ONLY; anatomical / model approval NOT_GRANTED.** GitHub-hosted [run 40022355554](https://github.com/anyangle1409-code/animation-software/actions/runs/40022355554) successfully completed all 5 jobs, including W8, V14, R120 Blender 5.2 inventory, cross-model comparison, and native movement diagnostics. No `.blend` file was modified.

## Native output provenance

The exact 3 report ZIP archives were downloaded and independently SHA256 checked against GitHub:

| Model | Artifact | Verified ZIP SHA256 | Source model SHA256 (unchanged) |
|---|---|---|---|
| W8 | [12530324894](https://github.com/anyangle1409-code/animation-software/actions/runs/40022355554/artifacts/12530324894) | `cf0cfaaad42f50b56263008efaea3ae0a85f0c6177c15e2f13b66411c1375954` | `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c` |
| V14 | [12530663993](https://github.com/anyangle1409-code/animation-software/actions/runs/40022355554/artifacts/12530663993) | `1c3442a761852919ce927c9d10fc11d2d558b1dd2b2c8fa483b9d9ce87e9a712` | `5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91` |
| R120 | [12530559107](https://github.com/anyangle1409-code/animation-software/actions/runs/40022355554/artifacts/12530559107) | `840b3080361cbd525ea8f0c057ae03d812a06cbbd1a3f96550c56e8a272fb2aa` | `fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb` |

Each ZIP includes `shoulder_shape_weight_rois.json`, `inventory.json`, `integrity_checks.json` and `rest_anatomy_inventory.json`. All source-sha / structural integrity guards passed; mesh keys, weights, bones and original production assets were not edited.

## Specific 5cm rest-cube findings

Cells below are defined using **body-object-local coordinates**, seeded from 75%-shoulder-press triangle-flag hotspots; they are not certified anatomical landmarks. Each cell averages total weight **1.00000** (R120 low cells 0.99999), so there is no evidence of gross missing weight normalization inside these cells. Weight *distribution* is not thereby proven anatomically correct.

| Cell | W8 vertices | V14 vertices | R120 vertices | W8 dominant mean influences |
|---|---:|---:|---:|---|
| upper +X (0.125,0.175,1.475)m | 400 | 400 | 409 | spine_03 .32166, scapula_r .28031, clavicle_r .23744, neck .12283, shoulder_cap_r .03777 |
| upper −X (−0.125,0.175,1.475)m | 400 | 400 | 406 | spine_03 .32166, scapula_l .28031, clavicle_l .23744, neck .12283, shoulder_cap_l .03777 |
| lower +X (0.125,0.175,1.425)m | 319 | 316 | 464 | spine_03 .56809, scapula_r .16433, clavicle_r .15466, neck .05534, shoulder_cap_r .03715 |
| lower −X (−0.125,0.175,1.425)m | 319 | 316 | 455 | spine_03 .56809, scapula_l .16433, clavicle_l .15466, neck .05534, shoulder_cap_l .03715 |

The as-loaded W8 stored corrective-key displacements from Basis in those 5cm cubes include:
- upper +X: `HGPT_S7_DELT_r_166` mean **17.135 mm**, `HGPT_S5_BAKE_r_172` mean 16.3293 mm.
- upper −X: `HGPT_S7_DELT_l_166` mean **18.3023 mm**, `HGPT_S5_BAKE_l_172` mean 16.3290 mm.
- lower +X: `HGPT_S7_DELT_r_166` mean **26.1028 mm**; `HGPT_S7_DELT_r_145` 24.7866 mm.
- lower −X: `HGPT_S7_DELT_l_166` mean **26.6527 mm**; `HGPT_S7_DELT_l_145` 24.2718 mm.

The saved `key.value` for these highlighted S7/S5 keys was **0.0**. This is their as-loaded state and **not** proof that they remain zero during exercise poses.

W8/V14 upper-back sample counts and leading mean group weights agree at this precision. R120 has more vertices in some cells because topology differs; cell counts across models cannot serve as a model-quality ranking.

## Activation-rule clue and next verification gate

The pinned source at `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`, `scripts/original_v1_review_candidate_drives.py`, defines `drive_s1()` family activations from measured humerothoracic elevation:
- `HGPT_S1_SHOULDER_`, `HGPT_S2_FOLD_`: nominal start 90°
- `HGPT_S3_SHAPE_`: 20°; `HGPT_S4_SCULPT_` and `HGPT_S5_BAKE_`: 60°
- `HGPT_S6_RELAX_`: 120°; `HGPT_S7_DELT_`: **130°**.
- Each family can override its start with `hgpt_sN_angles_start` on the rig. Side-specific `hgpt_sN_angles_l/r` lists determine piecewise-linear activation hats. The final key clamps to 1.0 above its last nominal angle.

These defaults alone do **not** establish the per-model saved angles, actual shoulder-press elevation or active shape-key values. A follow-on read-only cloud job should inspect exact rig custom-property angles and compare them with existing key names. Do not adjust thresholds, change bone positions, attach muscles or reduce movement-quality tests without separately validated evidence.

See [rig label consistency](PHONE_BONE_SIDE_CONVENTION_20261023.md) and [shoulder/axilla rest-space hotspot triage](PHONE_SHOULDER_AXILLA_TRIAGE_20261023.md). Anatomical laterality and model fitness remain NOT_GRANTED.

## Authored shoulder-press target angles — not yet measured key activation

Pinned source `scripts/build_original_movement_benchmarks_blender.py` at `025d5f28fa7eba2064fba565b1c9b60119cdd2cb` uses `PRESS = {ht_start:90°, ht_end:160°}`, with `smooth(t)=3t²−2t³` and nine samples at `t=i/8`.

| Saved shoulder-press sample | t | *Target* humerothoracic elevation |
|---|---:|---:|
| 0 | 0 | 90° |
| 6 | 0.75 | 149.0625° |
| 8 | 1 | 160° |

These are **requested pose targets**, not a measured independently certified joint angle or the actual `drive_s1()` input. For a rig with default S7 start (130°), samples 6 and 8 lie within the *nominal* S7 activation band. A rig property `hgpt_s7_angles_start` can override the threshold. The active key values at samples 6/8 still need native read-only measurement.

Pinned shoulder-cap helper source `scripts/original_v1_shoulder_cap_helper.py` separately documents a `hgpt_cap_fraction`, optional `hgpt_cap_fraction_ramp`, and `hgpt_axilla_fraction`. These helper-bone rotations are **separate from shape-key value hats**, so a complete diagnosis must examine both. The historical source notes past shoulder-cap fold problems in the 140–160° range. That history is not a new model-failure proof, but it establishes a specific target for further testing.
