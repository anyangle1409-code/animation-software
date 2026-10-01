# ORIGINAL v1 future production promotion workflow

Prepared; production_approved remains FALSE. No current candidate can pass.
Phase 12 requires explicit final owner acceptance, all phase exit records and
candidate-bound provenance, first-party, development/production deformation,
anatomy, topology, clothing, grip/contact, real runtime animation, automated QA
and standalone/release evidence. A completed optimisation or a numerical score
has no promotion authority. Routine review snapshots remain non-blocking.

## Prepare the final packet later

Prepare its shape with `python scripts/verify_original_v1_production_promotion.py
--template --json-out <new template.json>` (one line). This writes INCOMPLETE
packet/report templates for the current candidate. It does not run gates, accept
the model, export assets or change status. Missing values stay missing. Preserve
the template as preparation; create actual reports only after running the tests.

Packet JSON schema 1 contains final `candidate_sha256`, exact
`target_runtime_commit`, `gates` keyed by the names in
`scripts/verify_original_v1_production_promotion.py`, `owner_acceptance` as a
report reference, and exactly two `assets` with unique bare/dressed role and distinct repository-relative path,
SHA-256 and source candidate SHA. Never use the old R2 candidate GLBs as final
r29/r30 assets. A report reference is `{ "path": "relative/evidence.json",
"sha256": "exact content digest" }`; boolean PASS claims are refused.

Each gate report includes gate_id, candidate_sha256, status PASS, explicit checks
with unique string id/passed true and nonempty `evidence` path/hash references,
executed command, source_git_commit, ISO evidence_timestamp with timezone and
underlying source_evidence path/hash references. Each check's evidence must be
included in source_evidence. Duplicate check IDs or source references are refused.
Every gate includes `assets` identifying the exact same two final exports as the
packet, including role, path, content SHA and source candidate SHA. Changed export
bytes invalidate prior evidence even if the Blend candidate SHA stays unchanged.
Runtime/release reports also bind the exact
target_runtime_commit. Required check IDs are listed in the verifier; do not
silently remove them. Reports must wrap actual executed audit evidence, not
fabricated success. Human anatomy/contact classifications record their limits.

Final owner record includes decision OWNER ACCEPTED, actor owner, exact candidate
SHA, decision_source, ISO timestamp with timezone and the exact final `assets`
inventory. It must record the owner's actual explicit
message/decision. Pending routine reviews or agent-generated labels never count.
This verifier cannot authenticate the owner's identity; the repository operating
contract requires truthful recording of the source.

This verifies explicit evidence contracts, file integrity and the numerical
gates it recomputes. It cannot establish that arbitrary referenced text proves
anatomy, smooth motion or first-party ownership. Domain tools/reviewers must
execute and record those checks with their limits; placeholders are never proof.

## Validate without mutation

Run `python scripts/verify_original_v1_production_promotion.py <packet.json>
--json-out <new receipt.json>` (on one line). It checks references/hashes, gate
identity, explicit check coverage, phase dependencies, owner acceptance, assets,
recomputes development/production deformation and refuses unresolved strict R2
regressions. It never flips production flags or edits a release allowlist.

On refusal, preserve issues and repair only the failed gate. On all gates
satisfied, perform a separate controlled owner-authorised asset-only integration
on the standalone branch; never merge this branch's older runtime/framework code.
Repeat final release and first-party audits on the exact resulting commit, bind
the receipt/assets/approval decision to that commit and then record production
freeze. If source bytes or integration commit change, previous approval evidence
must be revalidated. No automatic optimisation/comparison/review script may invoke
this release step or change production approval.
