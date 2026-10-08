# Primary limb endpoint review — 2026-10-08

Original de Leva (1996) tables visually inspected. Table 4 confirms upper arm 281.7 mm, forearm 268.9 mm and thigh 422.2 mm at the source male stature 1741 mm. Corrected shank KJC–AJC to 440.3 mm; 434.0 mm belongs to KJC–lateral malleolus. These are estimated longitudinal cohort spans, not selected bone lengths.

Five limb tests, five owner-policy/source-fix tests and seven source-identity tests pass. Target-data and atlas structural validators pass; freeze_ready remains false. Full discovery: 805 tests, the same five failures and four errors as the preceding checkpoint. No new remaining failures. The transient owner-policy check failed because the replacement blocker capitalized its required phrase; the lowercase phrase was restored without changing policy or weakening the test. The initial 434.0 mm regression failure is retained in before_fix.txt.

Radius and ulna numerical targets remain blocked by endpoint-compatible articular/surface geometry and independent stature context. Forearm shortness is strongly supported under the stated proxy assumptions; it does not select whole-bone length or wrist centre. Thigh remains contested, not established short. All production and a003 assets are unchanged.

Primary PDF is linked and hashed in source_access_and_endpoint_review.json; copyrighted full text is not redistributed. Next action: map radius/ulna landmarks and contacts independently; retain provisional conversions and separate wrist definitions.
