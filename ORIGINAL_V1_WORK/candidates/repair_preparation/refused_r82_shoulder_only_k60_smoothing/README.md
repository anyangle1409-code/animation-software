# r82 (REFUSED experiment, preserved, not a retained candidate)

What: r68 + shoulder-region-only weight smoothing (k=60, 700 vertices, declared before the edit) + refitted corrective (corr_v21, mask declared and committed before the solve). Blend SHA-256 46a50d8dcbf66a403351e08a9a84001dac4ab02f71d4dd9add6eb1067790747a.

Result (metrics-only, 15 poses, P3): 0 development failures, shoulder self-intersections press_top 0, press_top_rhythm 0, pull-ups 0, squat 80 (r81: 16/12/0/0/82). BUT strict regressions versus P3B1 are 17 (r81: 12): arm/torso minimum edge ratios fall further (pull-up arm 0.673 vs 0.865, press_top arm 0.601 vs 0.78, press_bottom torso 0.503 vs 0.698) and arm/shoulder stretch maxima rise above the P3B1 tolerance. It trades the shoulder-top intersections for more compression and stretch, so it is refused. r81 stays the retained experimental continuation.

Lesson: the weight-only probe numbers (arm min 0.798) did not survive the corrective refit; the corrective, not the smoothing zone, is where the arm/torso compression comes from. The next lever is the corrective's compression floor, or an owner disposition of the remaining r81 regressions.