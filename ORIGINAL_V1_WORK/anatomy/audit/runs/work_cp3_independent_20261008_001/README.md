# Independent Blender 5.2.1 LTS rehearsal

Fresh empty-scene builds use a003 data and an exactly mirrored bone-copy fixture. This is NOT a new canonical audit revision and does not correct a003 anatomy. No old or production asset is modified.

Both builds retain 206 bones and 427 markers, and the fresh-process round-trip comparator passes. Endpoint error is below 6e-8 m; marker-centre error below 2e-7 m; marker-frame component error below 5.3e-7. Maximum roll error is 0.024 degrees; the exactly mirrored fixture's roll difference is 0.027 degrees. CP2 still rejects the known zero-disc-gap anatomy.

135 isolated implementation tests pass on the new builder output using a rehearsal-only copy of the a003 fit record bound to its new SHA256. Of 43 mirror pairs, 41 Blender comparisons pass and two have different source amplitudes and use the existing solver-only coverage. This is command/JCS/centre/continuity integrity, not anatomical contact/follower or whole-body acceptance. Gate 9 is not closed.

Raw capture JSON, input fixtures, both rehearsal .blend files, movement reports and raw samples are gzip archives. The manifest provides compressed and uncompressed hashes; decompress them to inspect/recompute. The animated test .blend can be regenerated from retained input .blend and movement record using run_isolated_tests_blender.py; its hash is stored in the report. Immutable output-path guards apply.

Reproduction: decompress the archives, run cp3_roundtrip_compare.py with the appropriate record/capture, or use the retained builder/capture commands in their script help. For movement, run run_isolated_tests_blender.py with the retained a003 rehearsal .blend and movement_record.json and NEW output paths. No evidence or anatomy gate is promoted by this run.
