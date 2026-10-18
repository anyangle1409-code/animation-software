# R48 failed before the first accepted step

Run39159707625, source b4b55eeb8943eee4b7f5b4fa4f3624f4690c6f6d,
failed at20:05:31UTC (21:05 Europe/London) on18October2026.

No R48 model was saved. No R48 native renders or video exist. No accepted
deformation increment or fitting history was produced. The overall outline
the owner approved remains R47's; its surface and motion repair is unresolved.

Preparation3/3 and silhouette-derivative1/1 tests passed. The fitter reached
its25minute limit (exit124) while refining the first proposed step. Its log
records5079,6330 and10507 linear constraints and1251,4177 and4661 newly
requested cone cuts. The fallback correctly refused to invent an accepted
state and raised “R48 fitter produced no accepted state; inspect fit.log”.

Full native83-response checks, all13 benchmarks, motion/posterior checks,
marked-normal/actual-outline tests, historical contour/front tests, unchanged
R47 scope tests and protected in-memory model identity checks did not run.
Their R48 outcomes are unknown, not passing. Actual outline error for an
accepted R48 result is unavailable; linearized slack is not that measurement.

The artifact contains only source data, the unchanged zero starting increment,
fit log/exit and the four successful preliminary test records. There is no
fit_status.json, native_final.json, benchmarks.json, solved.npz, model,
rendered comparison or video. No test assertion or limit was altered.

Artifact12148394071 (`original-v1-r48-review`),62915594bytes,
SHA256 b47cf9984492d46b5facd2829383413b3f23d5de2a4bb1c0ca7ba4a7fb269194.
The archive was downloaded and its full hash verified after failure.

The R48 completion notification is disabled after reporting this result.
The R46 notification remains disabled. Further geometry requires a separate
candidate. Investigate the first-solve bottleneck before another cloud run.
