# Target-selection gate mutations — 2026-10-08

Three adversarial test groups exposed malformed-measurement crashes, accepted nonboolean gate flags, and unsupported/missing grades passing a synthetic freeze gate. The pre-fix failure log is retained. The synthetic unblocked fixture exists only in tests; it is not evidence-backed anatomical target data and is never written to target selection.

The validator now requires a literal boolean freeze flag. Frozen evidence leaves must explicitly be A/B or underscore-qualified A/B labels; C/D, unknown labels, empty maps/lists and missing grades reject. Shoulder comparisons occur only after finite positive numeric validation. This is a limited data gate, not proof of complete coordinates or an independent clinical review.

129 relevant tests pass. Full Python discovery ran 740 tests with five failures/four errors, exactly the same named legacy production/recovery failures as the retained earlier 685-test checkpoint; names are in verification.json and traces in full_python_suite.txt. Full-project green is not claimed. Production control decisions were not changed to conceal fixture mismatches. Target-selection, atlas and carpal-axis validators pass their limited scopes; freeze_ready=false. No new Blender geometry is necessary for this pure gate change; the preceding hyoid bpy check remains reproducible.

```bash
python -m unittest scripts.test_canonical_target_selection_validator
python -m unittest discover -s scripts -p 'test_canonical*.py'
python scripts/validate_canonical_target_selection.py
```

Essential shoulder evidence blocker remains: the primary Li2012 PMID22340551 abstract omits the bilateral-distance value and exact endpoints. Its PubMed-linked Ovid full-text route returns HTTP402. Need the primary table/figure or independent compatible landmarks before solving SC centres. All other essential regional coordinate/contact dependencies remain explicitly open in canonical_freeze_readiness_v1.json. Historical preflight evidence remains unchanged.
