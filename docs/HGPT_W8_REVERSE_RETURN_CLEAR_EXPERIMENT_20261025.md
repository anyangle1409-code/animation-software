# W8 reverse press and explicit-clear experiment — 2026-10-25

## Question and boundaries

This read-only diagnostic asks two narrow engineering questions on the immutable W8 reconstruction:

1. Does replaying the pinned r57 shoulder-press samples from `t=1` back to `t=0` reproduce the evaluated geometry captured at the corresponding forward samples?
2. After that replay, does explicitly resetting the pose and zeroing every non-Basis shape key reproduce the benchmark's original evaluated reference?

Neither result is an anatomical neutral, a physiological return trajectory, an ISB validation, a model repair or exercise approval. The reverse path reuses the same authored parameterization and driver calls; it cannot establish realistic return timing, hysteresis, balance or tissue mechanics.

## Method

- Source: W8 reconstruction, pinned SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`.
- Code dependency: frozen r57 commit `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.
- The existing forward benchmark captures copies of evaluated vertices at samples `0..8` after the actual driver call.
- The probe preserves the already-reported post-forward residual, then invokes the pinned `pose_press` and actual `drive` functions at samples `8..0` and compares each evaluated mesh with its corresponding forward capture.
- In a separate final experiment, it calls the pinned skeletal reset, sets every non-Basis key to zero, updates Blender, and compares the frozen evaluated mesh and skeletal signature with the benchmark reference.
- Every evaluation uses the existing frozen-topology guard. No `.blend` is saved.

## Interpretation gates

- `MEASURED_REVERSE_REPLAY_NOT_PHYSIOLOGICAL_RETURN` reports only deterministic geometric retracing at the nine authored samples.
- `EXPLICIT_IN_MEMORY_CLEAR_EXPERIMENT_NOT_MODEL_REPAIR` reports only the consequence of a temporary reset-plus-zero operation.
- Any residual is retained as measured evidence rather than causing the artifact-producing job to hide the result.
- Population range-of-motion averages are not used as hard limits.
- Muscle attachment/highlighting, source geometry, skeletons, weights, drivers and corrective keys remain unchanged.

## Verified native result

Commit `401faa2fda53c5dbfde511dc87af480604271594` ran as GitHub Actions run `40203540066`: SUCCESS 7/7.

- All nine reverse samples reproduced the matching forward evaluated mesh exactly: zero vertices moved above 1 nm, zero maximum displacement and zero RMS displacement at every sample.
- The explicit in-memory skeletal reset plus zeroing all non-Basis keys restored the 219,974-vertex evaluated reference exactly, with no active non-Basis keys and an identical skeletal pose signature.
- The unchanged forward-only postcondition still fails: 102,253 vertices moved, maximum displacement 0.06231378350054487 m, RMS 0.012929646292009458 m, and 14 terminal keys remain active despite exact skeletal reset.
- Pose artifact `12603071682` was independently downloaded, CRC checked and rehashed as `5521331f7cfd224eb2e41f1eef71bf61ffdff62f8efd5f3a783025e2c797d1dc`. It contains 71 members, 66 PNGs and no `.blend`.

The result establishes deterministic reversibility of this authored nine-sample state function and shows the cause of the prior endpoint mismatch can be cleared in disposable runtime state. It does not establish physiological return, tissue hysteresis, anatomical neutral or a source repair.
