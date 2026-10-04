# r92 dent-limit probes (screening, metrics-only; weights-only intermediate + abduction keys, no flexion keys, no wrist patch)

| | r91 | dent limit 0.025 m | dent limit 0.040 m |
|---|---|---|---|
| deepest chest dent, press_top | 6.95 cm | 3.22 cm | 4.61 cm |
| torso vertices dented > 2 cm (left), press_top | 53 | 24 | 40 |
| volume change caused by the corrective, press_top | -1.50 % | -0.37 % | -0.98 % |
| press_top volume ratio / p99 | 0.9945 / 1.849 | 1.0058 / 1.836 | 0.9996 / 1.835 |
| development failures | 0 | 0 | 0 |
| new strict P3B1 regressions beyond the known squat/push-up items of the probe copy | - | none (press_top arm 0.758, pullup_top torso 0.668: both already open) | 3 more (pull-up arm minimum 0.818 / 0.818 / 0.805) |

Costs versus r91 at 0.025 (all still inside P3B1 tolerance): press_top_rhythm self-intersections 28 -> 36 (P3B1 54), press_top_rhythm arm min 0.728 -> 0.701, torso min 0.524 -> 0.477, pull-up torso min 0.611 -> 0.561, pull-up volume deviation 0.0126 -> 0.0241 (P3B1 0.116).
Visual (review_images/r92_dent_limit_probe): the chest bowl is gone at 0.025 (pectoral with a defined lower edge); the shoulder-top knobs and the lateral/back wing bulges are unchanged (not targeted).