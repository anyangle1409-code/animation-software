# r88 (REFUSED; three metrics-only probes, no candidate built; r87 retained)

Declaration: DECLARATION.md (committed before any solve). Probes: abduction corrective re-solved from the weights-only dump with all r83 arguments plus `--region-floor` (an absolute minimum edge ratio per region in every pose): A `arm:0.765`, B `torso:0.684`, C both. Each solution was applied to the weights-only intermediate and screened with the 15-pose metrics-only test (`abd_probe.ps1`). The squat items in the comparison against P3B1 are expected (the probes carry no flexion keys); everything else is the real signal.

| probe | press_top arm min (need 0.76) | pullup_top torso min (need 0.673) | new regressions versus r83 / r87 |
|---|---|---|---|
| r87 (reference) | 0.745 | 0.669 | - |
| A arm floor | cleared | still 0.669 | pull-up arm minimum 0.857 -> 0.82 (pullup_bar, pullup_hang; below P3B1 0.865 minus 0.02), pull-up arm max +0.13, press_top_rhythm torso min 0.524 -> 0.459 |
| B torso floor | 0.748 (not cleared) | cleared | pull-up arm minimum 0.857 -> 0.835 (pullup_bar, pullup_hang) |
| C both | cleared | cleared | pull-up arm min 0.832, pull-up arm max +0.125, pull-up volume deviation 0.0126 -> 0.0214, pullup shoulder min 0.46 -> 0.439, press_top SI 32 -> 50, press_top_rhythm SI 28 -> 34 |

Every probe buys one of the two targets at the price of two or more new strict regressions (pull-up arm minimum in two poses), so none is strictly preferable to r87. Measured cause: the weights alone give a pull-up arm minimum of 0.826 and the corrective is what lifts it to 0.857, while the same corrective is what compresses press_top arm edges (stretched 1.294 by the weights, compressed to 0.745). One displacement field serves both poses; the press_top arm and pull-up arm minima trade against each other on the corrective's frontier. Stop condition applied; no further floors tuned.