# r96 anatomical fold weight screening

Status: **rejected at the numerical gate**. These are probe-only artifacts; none is production-approved.

The declared experiment transferred a bounded fraction of `spine_02`/`spine_03` weight on 82 mirrored axillary vertex pairs. Anterior points received upper-arm and clavicle influence; posterior points received upper-arm and scapula influence. Corrective shape keys remained disabled throughout evaluation.

| Probe | Transfer | Failed checks | Regressions | Improvements | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| `fold_f015` | 15% | 10 (baseline 2) | 19 | 5 | Reject |
| `fold_f030` | 30% | 11 (baseline 2) | 26 | 3 | Reject |
| `fold_f045` | 45% | 12 (baseline 2) | 38 | 1 | Reject |

Even the mildest probe increased failed checks by eight. It raised press-top torso stretch from 3.545 to 5.781, lowered the press-top shoulder minimum edge ratio from 0.123 to 0.101, and introduced failures in pull-up and squat poses. Stronger transfers worsened the same pattern monotonically, reaching 144 press-top self-intersecting face pairs and 11.470 torso maximum stretch at 45%.

This falsifies the broad "make the axillary patch follow the arm more" hypothesis. The patch is already dense, and moving trunk-dominant surface weight toward the arm over-couples it across the shoulder/torso boundary. The next probe must first localize the exact fold-driving edges and vertices, then alter a substantially narrower foundation scope. No corrective fit is authorized by this result.

Evidence files:

- `fold_f015_comparison_vs_topology_control.json`
- `fold_f030_comparison_vs_topology_control.json`
- `fold_f045_comparison_vs_topology_control.json`
