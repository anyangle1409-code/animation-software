# Skeleton-first construction contract

Owner-authorized autonomous Stage 2 implementation. This is isolated engineering tooling, not a canonical candidate.

The existing mesh-fit builder remains unchanged. A new pure-Python module accepts explicit bone endpoints, joint centres and proper frames in metres in the HGPT world basis (+X anatomical left, +Y posterior, +Z superior). It never imports the mesh-fit builder, measures skin or silently substitutes anatomical coordinates. A replay adapter strips legacy records to their explicit skeletal data and labels the result historical replay only. Replay proves reproduction, not independent anatomical validity.

Validate inventory, topology, finite coordinates, nonzero lengths, joint frames, and side binding using the existing CP2 preflight. Add explicit endpoint-defined length and joint attachment constraints; mismatches fail clearly. Check provided axes without deriving missing axes from surface features. Missing independent evidence and missing required constraints remain UNVERIFIED. A 1.82 m adult male is the current target; female profiles may be represented separately but have no fabricated targets or automatic male scaling.

Skin clearance callbacks receive copied immutable coordinate tuples; diagnostics cannot access or mutate the construction record. Nonfinite clearance fails. Any negative clearance is reported as a mesh adaptation issue. Canonical output/promotion is disabled in this module regardless of numerical results. Neither an evidence-status field nor replay can change freeze readiness.

Verification: synthetic fixtures must be clearly identified as tests; actual a003 and c004 replay round trips must preserve exact coordinates, parents and markers. Mutation tests exercise malformed coordinates/frames, bad proportions, detached endpoints, missing source evidence, hostile clearance, output aliasing and premature promotion. Actual anatomy acceptance still requires CP1/CP2/CP3 evidence gates and visual review.
