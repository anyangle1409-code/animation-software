# ORIGINAL_v1 neutral toe-pad trial — 13 October 2026

## Phone review

- [Before/after neutral side comparison](https://chatgpt.com/api/library/files/libfile_db9b704ecf848191b67bd8b1bbf48382/download)
- [Before side](https://chatgpt.com/api/library/files/libfile_a32670db9338819198283f93ef83a0a8/download)
- [Trial side](https://chatgpt.com/api/library/files/libfile_114a28be77688191b82900b34423be27/download)
- [Before three-quarter](https://chatgpt.com/api/library/files/libfile_c9f6e4f6e688819182db757146ac08fb/download)
- [Trial three-quarter](https://chatgpt.com/api/library/files/libfile_b00226533f2081918098424ca0868178/download)
- [Before top](https://chatgpt.com/api/library/files/libfile_f02e3394eac88191820f95e79973bb6b/download)
- [Trial top](https://chatgpt.com/api/library/files/libfile_1c5aefaec4b8819198f1c27e293cade6/download)
- [Separate complete native trial](https://chatgpt.com/api/library/files/libfile_b9ccfb0096988191bcffd63ffe3620e8/download)
- [Native measurements and export hashes](https://chatgpt.com/api/library/files/libfile_9d7210e760a881919b131d580e7be5e0/download)
- [Reopen, motion and mesh checks](https://chatgpt.com/api/library/files/libfile_30e3327f90808191a873a4a88cd99810/download)

These are actual Blender 5.2.1 renders. For visibility, each image displays a left-foot surface extract below 160 mm. The open ankle collar is the disclosed display crop; the saved candidate retains the complete original body. No mannequin, V-series asset or generated illustration is used. Side cameras are identical; the comparison marks the reference floor. No toe rotation is applied.

## Scope and measured result

This is a reversible **plantar-contact experiment**, not an accepted foot-shape correction. The owner-rejected elongated/tubular silhouette, abrupt toe roots and shared toe articulation remain open.

902 vertices receive downward-only displacement of at most 10.0618 mm. A vertical ray locates the original lower skin surface; a bounded expansion below a 22 mm dorsal anchor brings a narrow central pad toward the floor. Digit positions come from existing source reference endpoints. The 22 mm anchor, 25 mm blend, widths and terminal taper are **artist trial constraints**, not authoritative anatomical dimensions.

The first broad-underside experiment produced visibly flat/blocky toes and was rejected during this run. The final narrower trial uses rounded lateral and terminal falloff. It remains stylised and needs a more comprehensive authored foot reconstruction.

| Native invariant/result | Outcome |
|---|---|
| Source body | 17,946 vertices; unchanged topology |
| Both foot lengths | 309.156645 mm, unchanged |
| Both foot widths | 96.716918 mm, unchanged |
| Ankle/heel/height and mesh XY | Unchanged |
| Weights and both skeleton rest/world matrices | Unchanged on native reopen |
| All ten distal digit samples, identity pose | Each contains a point within 0.001 mm of reference floor; not a contact-patch proof |
| Original 56 toe endpoint vertical skin brackets | 56/56 retained; no previously bracketed station lost |
| Bilateral Z difference | Maximum 0.000119 mm |
| Return to identity after 12 free-control samples | Zero residual |
| Triangle orientation reversal vs source | Zero |
| Triangle area ratio range | 0.439–3.174; appreciable local stretching/compression remains |
| Existing corrective relative deltas | Preserved within 0.0002 mm; posed quality NOT validated |

The new aggregate distal region uses forward station >245 mm, giving original minimum 8.293 mm and trial minimum 0.0 mm. This differs from the earlier digit-specific 8.5–9.3 mm sample definition; it is not a contradictory measurement or a claim that every toe-tip vertex touches the floor.

## Motion limitations

Native reopen runs bilateral shared toe −15/0/+15 degrees and foot −10/0/+10 degrees. All evaluated coordinates remain finite and the body returns to identity. These are unloaded/free-control diagnostics, not physiological or planted-stance verification.

The trial starts from original weights, **not** the separate PR84 724-vertex weights candidate. Toe-lift −15 still has approximately 0.946 mm proximal forefoot penetration. Toe flexion +15 crosses the fixed floor by approximately 18.35 mm; foot +10 by approximately 43.47 mm. No contact solver or individual digit rig was installed. Do not combine candidates or replace production without new independent checks.

The source toe stations remain low-confidence surface-derived controls. Vertical ray bracketing tests only skin geometry at those points; it does not validate bone volumes, MTP/IP centres, cartilage, toe dimensions, gait or skin thickness. The 280 mm shortening gate remains blocked by the existing reference-envelope/endpoint-semantics conflict.

## Provenance and preservation

- Input branch: `codex/original-foot-proportions-candidate-20261012`.
- Input full commit: `27e2dbf4424b878d8312cf346624e495720bba0a`.
- Source: `ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend`.
- Source SHA-256: `670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56`.
- Final candidate: `HomeGymPT_ORIGINAL_v1_NEUTRAL_TOE_PAD_TRIAL.blend`.
- Candidate SHA-256: `6ee29cec4dfd4b2de867f8dbcce4364203bc5f40182deeea72e60e01683438e2`.
- Runtime: `HGPT_CANONICAL_V4_ORIGINAL`, 67 joints; source anatomical reference: 206 controls.
- Review branch: `codex/original-neutral-toe-pad-trial-20261013`, separate from PR84 and all Chat Lane G branches.

Live PR48, PR26, PR81/comment6120513138 and PR84 were checked before work. Coordination comments show later Chat renderer/app work through PR103; none was duplicated or changed. The exact original source hash was checked before and after native execution. All ten final artifacts were saved persistently. No production asset was overwritten and nothing was merged.

Five new focused tests were observed failing before the bounded geometry helper was implemented, then passing. Ten inherited foot-gate/weight tests also passed; four actual native full-body bridge tests passed on the saved trial. Native source/candidate reopen, skeletal/weight/corrective/XY invariance, symmetry and the twelve motion diagnostics executed separately. Independent review found no critical defect and identified missing structural comparisons and overly broad pad-contact wording. Added exact native reopen comparisons for polygon topology, vertex-group identities, both skeleton heads/tails/lengths/parents, body transform/parent and modifier identities/settings; reran these successfully. Clarified contact as minimum-point evidence rather than a complete loaded contact patch. Full inherited suite was deliberately not rerun under the shared no-repeat rule.

## Restart

Keep this candidate review-only and owner acceptance false. Next consequential work is source-compatible MTP/IP endpoint authority and a credible full foot/toe shape reconstruction, preserving the approved source skeleton. Continue independent shoulder SC/AC/GH frame authority and runtime/skin refit while foot shortening remains blocked. Do not mistake control origins or this successful neutral contact experiment for anatomical acceptance. The prior recurring task remains paused; this is an owner-requested active-session continuation, not an unattended restart promise.

Ruling: perform the narrow reversible plantar trial under the owner's existing autonomous candidate authorization, without forcing foot shortening. Cost if the artist constraints are unsuitable: discard the separate trial; production and source remain untouched.

All gates for owner shape, anatomy, physiological/loaded contact and production remain **NOT ACCEPTED**.
