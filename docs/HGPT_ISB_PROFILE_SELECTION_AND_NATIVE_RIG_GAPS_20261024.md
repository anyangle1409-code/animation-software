# ISB profile selection and native rig gaps — 24 October 2026

**Research/dependency clarification only. No anatomical frame binding or model change.**

## Standards checked directly

The primary [ISB 2005 paper](https://media.isbweb.org/images/documents/standards/Wu%20et%20al%20J%20Biomech%2038%20%282005%29%20981%E2%80%93992.pdf), DOI 10.1016/j.jbiomech.2004.05.042, makes distinctions that must survive implementation:

- Sections 3.3.3–3.3.4 define elbow-study ulna/radius frames in specified elbow/forearm calibration positions. Section 4.3 explicitly uses different radius/ulna definitions for wrist studies. A frame profile therefore needs both the standard section and calibration pose; a bone name is insufficient.
- Sections 3.4.1–3.4.2 describe forearm/humerus and ulna/humerus motion using Z–X–Y ordering. Section 3.4.3 describes radius/ulna motion using X–Z–Y ordering. The clinical labels and moving/fixed axes cannot be replaced by a generic unsigned rotation magnitude.
- Section 3.4 notes anatomical rotation axes do not necessarily coincide with segment coordinate axes. The wrist section also explicitly handles left/right sign conventions. Do not mirror suffixes and assume the same anatomical convention.

These points refine the existing unbound landmark checklist; they do not authorize reconstructing anatomical axes from arbitrary rig heads/tails.

The primary [ISB 2021 foot recommendations](https://media.isbweb.org/images/documents/standards/leardinietal2021.pdf), DOI 10.1016/j.jbiomech.2021.110581, recommend reproducible protocols suited to the scientific task rather than one universal foot model. They distinguish segment motion in a global frame, relative joint motion and projected angles, and require explicit anatomical axes/planes. Their scope is skin-marker measurement; animation-rig design is an engineering application, not directly certified by that paper.

## Verified native evidence, not anatomical inference

Source: independently hashed latest W8 artifact12551788540, run40072736803, `W8/rig_rest_axes_metadata.json`; member SHA256 `01ef8a7cf4eab8ea8eb29d2fcb2f5cd310ce8a936062624b06868a2e38b7b677`. V14/R120 contain identical 77 bone metadata rows. All report ISB calibration false.

| Recorded authored chain | What is actually available | Unresolved before human-motion acceptance |
|---|---|---|
| spine_03 → clavicle → scapula → upperarm | Named hierarchy for each suffix | Anatomical thorax/SC/AC/GH landmarks, independent side identity, trajectory and coordination |
| upperarm → forearm → hand; forearm_tw0/tw1 parented to forearm | Two twist helpers plus forearm segment | No separately named radius/ulna bones; no independently reviewed radius/ulna frame binding or relative-motion evidence |
| pelvis → thigh → shin → foot → toe | One foot and one toe control per suffix | No separately named hindfoot/midfoot/forefoot or patella controls; reviewed segment observability, joint centres, plantar contacts and arch/toe trajectories unresolved |

Absence of separately named controls is not proof of absent visible motion or a mandate to add bones. Helpers, constraints and skin may approximate movement; their behavior must be measured before choosing a replacement. Conversely, names alone cannot demonstrate actual independent anatomical segments. No current bone receives an anatomical muscle attachment because of this table.

## Engineering contract for a future reviewed binding

Each future frame binding must carry: permanent semantic segment ID; model/source SHA; selected standard and section/profile; calibration pose; landmark IDs and independently reviewed positions; anatomical side evidence; frame origin and ordered axes; units/handedness; parent/child relationship; rotation sequence and positive-motion convention; neutral offset; reviewer/evidence record. Separate profiles may reference the same reviewed landmarks without sharing a coordinate definition.

Before acceptance, test landmark perturbation/degeneracy, side/sign round trips, global rigid-motion invariance, singular configurations, reference→movement→reference trajectories, and native skin/contact evidence. Show both the measured transform and the derived named angle. A numerical SO(3) pass never fills missing profile fields. Do not import clinical ROM means as stops or attach muscles to twist-helper centroids.

This is a future implementation contract, not a new approved JSON binding. The existing 46 records remain null/unbound; 0/19 generic motions approved. Hip/knee/ankle frame selection still needs its own precise primary-standard review, not extrapolation from the upper limb. Existing press/squat/grip failures remain.
