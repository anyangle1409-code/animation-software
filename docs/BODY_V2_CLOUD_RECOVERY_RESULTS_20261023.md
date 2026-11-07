# Cloud Body v2 recovery results

Run: https://github.com/anyangle1409-code/animation-software/actions/runs/39918805189
Commit: `6e4823e50ce8081fc5ec3a722d88dfa4e03ca1bb`

Reconstruction/archive checks: FAIL / INCOMPLETE.
All 13 × 9 movement paths executed for all four inputs: False.
Zero collapse/stretch/intersection quality gate across all inputs: False.
Application and pinned test suites: FAIL / INCOMPLETE; exit codes {'vitest': '0', 'typecheck': '0', 'scripts': '1', 'scripts_tests': '1', 'scripts_blender_tests': '1', 'muscles': '0', 'guards': '0'}.
Anatomical and visual approval: NOT GRANTED. R120 remains EXPERIMENTAL.

| Model | Path | SHA256 |
|---|---|---|
| W8 | W8/body_v2.blend | 2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c |
| V14 | V14/body_v2_legs.blend | 5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91 |
| R120 | R120/body_v2_rebuilt.blend | fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb |

See RECOVERY_RESULT.json, verify/, native/, tests/, native/V14/muscle/ and logs/ for exact failures and discrepancies.
Missing reports or renders are never a pass. Raw failure counts across different mesh topologies are diagnostic, not a like-for-like improvement claim.
W8 screenshot source identity and unsaved R52/R57 increments remain unresolved.
PT_MODEL_VERSION 1.0 preserved. No production replacement, merge or deployment.
