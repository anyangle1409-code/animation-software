# R46 continuation implementation plan

Goal: continue the unfinished R45 fit from its last accepted state without changing geometry policy or acceptance limits.

R45 run39115485844 produced native evidence and was rejected by the unchanged owner-junction test. No model was saved. The fit hit its1800-second execution limit after five accepted steps; it did not converge. Junction offsets at the three failing stations were2.814/2.399/1.874mm left and2.750/2.442/1.875mm right, versus unchanged minima20/12/6mm. All83 native surface responses and13 original benchmarks passed. Motion excess0.445976mm and crease excess1.797725deg stayed within their original0.5mm/2deg limits.

R46 changes execution budget and initial state only: resume the retained R45 delta, fit for at most9000seconds, allow180minutes total so validation/rendering can finish. The fitter, skin-distance field, LP backend and inherited candidate tests are byte-identical after candidate-name substitution. Existing R37/R38/R41/R42/R43/R44 tests are untouched. A longer run is an experiment, not evidence that the requested shape is feasible.

- [x] Download and verify R45 artifact SHA2564fa00d6fe12dc0a107d83f7b33aca9053e388611972bdd0d122b464900e2d0d1.
- [x] Read all failed profile measurements and pre-save outcomes; inspect matching native still and press-video frame.
- [x] Prepare separately named R46 scripts, own preservation/domain/field/LP tests and workflow. Eight control tests pass against retained R45 fixtures; this does not validate R46 geometry.
- [x] Pin initial NPZ SHA256fa9720bc900e6e646a197d578381eaaac7ed95561e2f9330cdae76226c1b09c1.
- [x] Local continuation accepted another0.391440mm step after211.9seconds with unchanged hard fitting gates. Predicted first-station offsets improved2.814→3.077mm left and2.750→3.013mm right; still below20mm and not a native model validation.
- [ ] Push only new R46 source and this handoff update with a normal expected-head branch update.
- [ ] Run native83-pose checks, all13 benchmarks, original guard and fixed profile tests; save a candidate only if every applicable gate passes.
- [ ] Produce R45/R46 matching-angle comparisons, R42-target/R46 comparisons and press videos even if rejected; retain failed checks and automatically commit evidence to the authorized branch.

Frozen: canonical skeleton, V-series, Basis, weights, topology, HGPT_SHOULDER and all non-S7 keys; original arm/elbow source coordinates,166-degree endpoint and anchors. Editable material mask and45mm displacement limit unchanged. No reference photos. No merge or force push.

If continuation stalls or fails acceptance, report it as a rejected study. Do not weaken tests or expand the editable region without the owner's required discussion and concrete before/after evidence.
