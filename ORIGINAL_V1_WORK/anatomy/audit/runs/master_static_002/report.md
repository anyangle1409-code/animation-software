# Anatomical Blender measurements

Overall: **UNVERIFIED**. Character accepted: **No**.

This report checks recorded geometry and measures supplied samples. It does not approve anatomical placement or movement.

| Check | Status | Detail |
|---|---|---|
| provenance | PASS | Atlas hashes match; saved source identified. This does not prove fitted geometry. |
| units | PASS | Explicit conversion matches the scene unit scale; character physical scale still needs independent confirmation. |
| identity | PASS | Unique stable anatomical names; untagged helper controls excluded. |
| bone_coverage | PASS | {"represented": 206, "expected": 206, "missing": []} |
| geometry_integrity | PASS | Finite nonzero segments, proper unsheared axes, existing parents and no cycles. |
| bilateral_lengths | UNVERIFIED | Differences measured; no universal symmetry tolerance or fit inferred. |
| landmark_integrity | PASS | Only supplied landmark IDs/coordinates checked; anatomical placement unverified. |
| joint_marker_coverage | PASS | {"measured": 427, "expected": 427, "missing": []} |
| distinct_centres | UNVERIFIED | No exact collision detected in supplied pairs; source-fitted separations still unverified. |
| trajectory_integrity | UNVERIFIED | No invalid provided time sequence; absent/short tracks do not establish motion. |
| sample_integrity | PASS | Provided transforms structurally valid; omitted pose data is not evidence. |
| test_execution | UNVERIFIED | {"sampled_test_ids": [], "missing_context_samples": [], "note": "Labels are not proof of complete sides, stages, planes or reversal. Inspect local test evidence."} |
| anatomical_placement | UNVERIFIED | Requires character landmarks/contact surfaces and reviewed fitting evidence. Bone names/matrices are insufficient. |
| joint_operation | UNVERIFIED | Requires sourced relative contact/axis/coupling tests in Blender; raw principal rotations are not clinical JCS angles. |

## Bilateral segment measurements

| Segment | Left (m) | Right (m) | Relative difference | Status |
|---|---|---|---|---|
| parietal | 0.0169953 | 0.0169953 | 0 | UNVERIFIED |
| temporal | 0.0364005 | 0.0364005 | 0 | UNVERIFIED |
| zygomatic | 0.0222896 | 0.0222896 | 0 | UNVERIFIED |
| malleus | 0.00600004 | 0.00600004 | 0 | UNVERIFIED |
| incus | 0.005 | 0.005 | 0 | UNVERIFIED |
| stapes | 0.003 | 0.003 | 0 | UNVERIFIED |
| nasal | 0.0207123 | 0.0207123 | 0 | UNVERIFIED |
| lacrimal | 0.0116619 | 0.0116619 | 0 | UNVERIFIED |
| maxilla | 0.0359583 | 0.0359583 | 0 | UNVERIFIED |
| palatine | 0.0158114 | 0.0158114 | 0 | UNVERIFIED |
| inferior_nasal_concha | 0.0250799 | 0.0250799 | 0 | UNVERIFIED |
| rib_01 | 0.0802367 | 0.0802258 | 0.00013522 | UNVERIFIED |
| rib_02 | 0.124242 | 0.12424 | 1.67159e-05 | UNVERIFIED |
| rib_03 | 0.169658 | 0.169656 | 1.15098e-05 | UNVERIFIED |
| clavicle | 0.22286 | 0.22286 | 0 | UNVERIFIED |
| scapula | 0.211715 | 0.211715 | 0 | UNVERIFIED |
| humerus | 0.282496 | 0.282496 | 0 | UNVERIFIED |
| ulna | 0.257399 | 0.257399 | 0 | UNVERIFIED |
| radius | 0.257417 | 0.257417 | 0 | UNVERIFIED |
| scaphoid | 0.011 | 0.011 | 0 | UNVERIFIED |
| trapezium | 0.011 | 0.011 | 0 | UNVERIFIED |
| metacarpal_1 | 0.048 | 0.048 | 0 | UNVERIFIED |
| thumb_proximal_phalanx | 0.031 | 0.031 | 0 | UNVERIFIED |
| thumb_distal_phalanx | 0.02294 | 0.02294 | 0 | UNVERIFIED |
| trapezoid | 0.011 | 0.011 | 0 | UNVERIFIED |
| metacarpal_2 | 0.0584074 | 0.0584074 | 0 | UNVERIFIED |
| digit2_proximal_phalanx | 0.0449998 | 0.0449998 | 0 | UNVERIFIED |
| digit2_middle_phalanx | 0.027 | 0.027 | 0 | UNVERIFIED |
| digit2_distal_phalanx | 0.0189 | 0.0189 | 0 | UNVERIFIED |
| lunate | 0.011 | 0.011 | 0 | UNVERIFIED |
| triquetrum | 0.011 | 0.011 | 0 | UNVERIFIED |
| pisiform | 0.007 | 0.007 | 0 | UNVERIFIED |
| hamate | 0.011 | 0.011 | 0 | UNVERIFIED |
| metacarpal_4 | 0.0515874 | 0.0515874 | 0 | UNVERIFIED |
| digit4_proximal_phalanx | 0.046 | 0.046 | 0 | UNVERIFIED |
| digit4_middle_phalanx | 0.0280001 | 0.0280001 | 0 | UNVERIFIED |
| digit4_distal_phalanx | 0.0201601 | 0.0201601 | 0 | UNVERIFIED |
| metacarpal_5 | 0.0532016 | 0.0532016 | 0 | UNVERIFIED |
| digit5_proximal_phalanx | 0.036 | 0.036 | 0 | UNVERIFIED |
| digit5_middle_phalanx | 0.022 | 0.022 | 0 | UNVERIFIED |
| digit5_distal_phalanx | 0.0167201 | 0.0167201 | 0 | UNVERIFIED |
| capitate | 0.015 | 0.015 | 0 | UNVERIFIED |
| metacarpal_3 | 0.0539843 | 0.0539843 | 0 | UNVERIFIED |
| digit3_proximal_phalanx | 0.049 | 0.049 | 0 | UNVERIFIED |
| digit3_middle_phalanx | 0.03 | 0.03 | 0 | UNVERIFIED |
| digit3_distal_phalanx | 0.021 | 0.021 | 0 | UNVERIFIED |
| rib_04 | 0.20015 | 0.200148 | 9.71973e-06 | UNVERIFIED |
| rib_05 | 0.216712 | 0.216708 | 1.78946e-05 | UNVERIFIED |
| rib_06 | 0.221094 | 0.22109 | 1.86047e-05 | UNVERIFIED |
| rib_07 | 0.218136 | 0.218131 | 2.07682e-05 | UNVERIFIED |
| rib_08 | 0.208953 | 0.208948 | 2.35023e-05 | UNVERIFIED |
| rib_09 | 0.203606 | 0.2036 | 2.65785e-05 | UNVERIFIED |
| rib_10 | 0.200115 | 0.20011 | 2.88752e-05 | UNVERIFIED |
| rib_11 | 0.102504 | 0.102509 | 4.58044e-05 | UNVERIFIED |
| rib_12 | 0.0985278 | 0.0985321 | 4.3813e-05 | UNVERIFIED |
| hip_bone | 0.17119 | 0.17119 | 0 | UNVERIFIED |
| femur | 0.412882 | 0.412882 | 0 | UNVERIFIED |
| patella | 0.044 | 0.044 | 0 | UNVERIFIED |
| tibia | 0.439144 | 0.439144 | 0 | UNVERIFIED |
| fibula | 0.40043 | 0.40043 | 0 | UNVERIFIED |
| talus | 0.0469655 | 0.0469655 | 0 | UNVERIFIED |
| calcaneus | 0.0193393 | 0.0193393 | 0 | UNVERIFIED |
| cuboid | 0.0516876 | 0.0516876 | 0 | UNVERIFIED |
| metatarsal_4 | 0.0783237 | 0.0783237 | 0 | UNVERIFIED |
| toe4_proximal_phalanx | 0.0282295 | 0.0282295 | 0 | UNVERIFIED |
| toe4_middle_phalanx | 0.0152439 | 0.0152439 | 0 | UNVERIFIED |
| toe4_distal_phalanx | 0.00898556 | 0.00898556 | 1.32664e-08 | UNVERIFIED |
| metatarsal_5 | 0.0783237 | 0.0783237 | 0 | UNVERIFIED |
| toe5_proximal_phalanx | 0.0268129 | 0.026786 | 0.00100421 | UNVERIFIED |
| toe5_middle_phalanx | 0.014479 | 0.0144644 | 0.0010042 | UNVERIFIED |
| toe5_distal_phalanx | 0.00833393 | 0.00832156 | 0.00148512 | UNVERIFIED |
| navicular | 0.016 | 0.016 | 0 | UNVERIFIED |
| medial_cuneiform | 0.0580041 | 0.0580041 | 0 | UNVERIFIED |
| metatarsal_1 | 0.0725646 | 0.0725646 | 0 | UNVERIFIED |
| hallux_proximal_phalanx | 0.0458718 | 0.0458616 | 0.000222289 | UNVERIFIED |
| hallux_distal_phalanx | 0.0292175 | 0.0292101 | 0.000252919 | UNVERIFIED |
| intermediate_cuneiform | 0.0496573 | 0.0496573 | 0 | UNVERIFIED |
| metatarsal_2 | 0.0863864 | 0.0863864 | 0 | UNVERIFIED |
| toe2_proximal_phalanx | 0.0361511 | 0.0361464 | 0.00013015 | UNVERIFIED |
| toe2_middle_phalanx | 0.0195216 | 0.019519 | 0.000130149 | UNVERIFIED |
| toe2_distal_phalanx | 0.0126295 | 0.0126273 | 0.00017045 | UNVERIFIED |
| lateral_cuneiform | 0.053785 | 0.053785 | 0 | UNVERIFIED |
| metatarsal_3 | 0.0806274 | 0.0806274 | 0 | UNVERIFIED |
| toe3_proximal_phalanx | 0.0326862 | 0.0326901 | 0.000120121 | UNVERIFIED |
| toe3_middle_phalanx | 0.0176505 | 0.0176527 | 0.000120128 | UNVERIFIED |
| toe3_distal_phalanx | 0.0110356 | 0.0110375 | 0.000163596 | UNVERIFIED |
