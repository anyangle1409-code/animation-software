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

## Verification state

Pure-Python behavior tests were observed RED before implementation and GREEN afterward. Native Blender results and artifact hashes remain pending until a new GitHub Actions run completes and its archive is independently checked.
