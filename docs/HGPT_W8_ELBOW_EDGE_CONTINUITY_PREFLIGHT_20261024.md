# W8 fixed-rest elbow-region mesh-edge continuity — cloud-only read-only preflight
**24 October 2026. Experimental diagnostic; anatomical validation NOT_GRANTED.**

## Purpose and source provenance

The previous [W8 elbow PCA report](HGPT_W8_ELBOW_PCA_REPRODUCIBLE_AUDIT_20261023.md) found a pronounced distal/mid upper-arm **covariance spread-product proxy**, including in rest space. That statistic cannot establish whether a *connected mesh* locally compresses or stretches during a press. This new test examines unique edges in fixed rest-space skin bands; it is an **additional local surface continuity descriptor**, not a muscle, anatomical cross-section, tissue strain, or injury threshold.

- Source model: preserved reconstructed W8 SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`.
- Pose geometry: immutable native diagnostic run [39937882229](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229), artifact `12495910312`. Its ZIP digest is pinned in `track_rest_hotspots.py` for direct ZIP use. The cloud job downloads the exact artifact ID into a directory and checks model identity, preserved-source declarations, rest topology, labels and per-frame counts; **an extracted directory is not independently ZIP-digest-verified by this script**.
- Rest axes: [run 40029398965](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965), W8 artifact `12534047239`, pinned `rig_rest_axes_metadata.json` member SHA256 `01ef8a7cf4eab8ea8eb29d2fcb2f5cd310ce8a936062624b06868a2e38b7b677`. Its historical five-job workflow failed a separate docstring/static test; its three model inspections and rest comparison passed. Prior ZIP/member SHA verification is recorded in the [execution ledger](PHONE_CLOUD_EXECUTION_LEDGER_20261023.md).
- Only W8 saved shoulder-press samples **0, 6 and 8** are inspected. There is **no isolated elbow curl, radius/ulna pronation, or return-to-neutral trial** in this input.

## Algorithm and interpretation

1. Reuse the previously pinned `upperarm_l/r` rest head/tail controls and the existing rest-space middle (0.55) and distal (0.95) narrow bands. Suffixes `l/r` are **authoring labels, not independently certified anatomical sides**; the authored tail is not a certified elbow centre.
2. Freeze skin vertex IDs from the **same rest geometry** for all sampled poses. Extract unique triangle edges only where both endpoints lie within a given band. Reject empty, duplicate, degenerate or out-of-range edge records.
3. For each fixed edge `(i,j)`, calculate `||pose[j]-pose[i]|| / ||rest[j]-rest[i]||`. This is dimensionless and invariant to whole-body rigid translation/rotation. Record minimum, 5th percentile, median, 95th percentile and maximum; also record 95th percentile of the **paired absolute ratio change from pose sample 0**.
4. Reject changed rest vertices, triangle topology, dominant labels, source hashes, missing saved frames or changed diagnostic counts. Never set a pass/fail human strain threshold from these distributions.

**Limitations:** A ratio above 1 is longer than that edge in the saved rest mesh, not a measured anatomical strain; a ratio below 1 is shorter, not necessarily unsafe compression. This method cannot detect all triangle inversions, intersections, shoulder axilla defects, deep muscle overlap or actual anatomical joint centres. Because the original press itself fails whole-body deformation gates, this report is for triage only. It does not diagnose why a ratio changed.

## Reproduction and validation state

The isolated source file is `scripts/cloud_body_analysis/elbow_edge_continuity.py`; ten synthetic unit tests are in `scripts/cloud_body_analysis/tests/test_elbow_edge_continuity.py`. A local synthetic run passed **10/10** using dependency stubs for imports; **this is not a native-data integration result**. The cloud workflow now invokes the script after the existing W8 PCA audit and uploads `w8_elbow_edge_continuity.json` and `.md` in its normal native localization artifact. The full CI and real W8 numerical output must be checked before claiming success.

Reproduce from exact extracted original artifacts:

```bash
python -m unittest discover -s scripts/cloud_body_analysis/tests -p test_elbow_edge_continuity.py -v
python scripts/cloud_body_analysis/elbow_edge_continuity.py \
  --w8 /path/to/extracted/W8 \
  --rig /path/to/extracted/rig-W8/W8/rig_rest_axes_metadata.json \
  --out /tmp/w8-elbow-edge-continuity
```

## ISB segment calibration and future general motion tests

**Shoulder complex:** ISB [Part II](https://pubmed.ncbi.nlm.nih.gov/15844264/) requires separately defensible thorax, clavicle, scapula and humerus landmarks and segment frames before a local helper rotation may be called glenohumeral or scapulothoracic motion. Inspect independently reviewed 3D anatomical sides and thorax IJ/PX/C7/T8, scapular TS/AI/AA, clavicle SC/AC and humeral landmarks. Do not prescribe a fixed scapulohumeral rhythm: the [2025 systematic review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/) describes substantial variability.

**Elbow and forearm:** Distinguish humeral epicondyles and the proximal/distal **radius and ulna** axes, and inspect true joint centres before using flexion/pronation labels. A single `forearm_tw0` group or authored bone tail cannot certify pronation. Test neutral → reviewed intermediate flexion/supination/pronation → neutral on both sides only after frames are calibrated; compare local edge ratios, skin self-contact, silhouette, elbow crease and proximal/distal radius/ulna paths.

**Hip, knee, ankle and foot:** ISB [Part I](https://pubmed.ncbi.nlm.nih.gov/11934426/) and [multisegment foot standards](https://www.isbweb.org/activities/standards) require distinct pelvis/femur/tibia/hindfoot/forefoot coordinates and actual ground contact. Squat trajectories need pelvis/hip/knee/ankle coupling, patella tracking and foot/toe contact checks, not independent Euler-angle clipping. CDC [adult ROM population means](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html) are **descriptive group statistics**, never model-specific hard limits.

**Gates unchanged:** 46 unbound landmark requirements; 0/19 generic human movement tests executed/approved; native shoulder press/squat/grip acceptance failed/blocked. No skeletal, skin, muscle attachment, original `.blend`, PT-App, production, or Claude-owned changes. Permanent muscle IDs retained; muscle highlighting remains deferred.


## Independent local archived-data replay (same session; not CI)

After the initial staging, the two historical ZIP artifacts were downloaded again and independently SHA256-checked:

| Archived artifact | Downloaded ZIP SHA256 | Result |
|---|---|---|
| W8 native saved pose `12495910312` | `3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e` | Matches pinned digest |
| W8 rest rig `12534047239` | `adaba1780dcde12b589f590bc6de7ae2227485471f9ff0817a56dff888188267` | Matches published digest |
| W8 `rig_rest_axes_metadata.json` member | `01ef8a7cf4eab8ea8eb29d2fcb2f5cd310ce8a936062624b06868a2e38b7b677` | Matches pinned member SHA256 |

The locally staged edge diagnostic was executed against the **actual hash-verified ZIP and rig member** using faithful local copies of its two existing helper modules. It completed with four descriptive regions. This is a **local real-evidence replay**, not yet an Actions execution of the committed branch; local synthetic tests remained 10/10.

| Authored suffix | Rest band | Unique edges | Press 0 p95 | Press 6 p95 | Press 8 p95 |
|---|---|---:|---:|---:|---:|
| l | middle | 901 | 1.2954 | 1.7229 | 1.5885 |
| l | distal | 488 | 1.4136 | 1.1902 | 1.1374 |
| r | middle | 897 | 1.2954 | 1.7066 | 1.5834 |
| r | distal | 486 | 1.4177 | 1.1956 | 1.1389 |

The 95th percentile is a **ratio of saved pose edge length to saved rest edge length**, not a physical muscle strain or safe upper limit. The mid-band p95 increases at sample 6 relative to sample 0 while distal p95 decreases; this is a reproducible **geometric observation only**. No causal inference about elbow taper, skin weights, shoulder cap, muscle overlap or anatomical correctness is justified. Local output JSON SHA256 was `0eda56b171af4195dd50bddd9f745d647e441544bedbe4f9f16d28a47c8107ca`; do not treat it as a GitHub Actions artifact hash.

**Still pending:** Verify the workflow's newly committed exact source/test versions, job conclusion, real artifact members and artifact ZIP digest. No native anatomy, movement or skin approval.


## 24 October — cloud confirmation and deterministic edge review extension

The previously pending [seven-job run 40056461299](https://github.com/anyangle1409-code/animation-software/actions/runs/40056461299) completed **SUCCESS** for all seven jobs at implementation commit `d17739c0129aa0053032b3c543ce515d572720b6`. The native-localization log records **178/178 tests PASS**, and explicitly ran the saved-W8 edge audit (`W8_ELBOW_LOCAL_EDGE_RATIOS_DESCRIPTIVE_ANATOMY_NOT_APPROVED regions 4`). The native ZIP [artifact 12546225033](https://github.com/anyangle1409-code/animation-software/actions/runs/40056461299/artifacts/12546225033) was independently downloaded and its ZIP SHA256 **matched** GitHub's published digest `a03eeb67fe487cd79181552a08fb8c0b164d4b777a571e81b45545fc0b641cd0`. Embedded `w8_elbow_edge_continuity.json` SHA256 `0eda56b171af4195dd50bddd9f745d647e441544bedbe4f9f16d28a47c8107ca` also matched the earlier local replay. This confirms report reproduction, **not** anatomical correctness.

The actual saved W8 sample **0** has distal-band minimum pose/rest edge ratios of **0.167612** (suffix l) and **0.163126** (suffix r), whereas sample **6** minima are **0.837984** and **0.848307**. The same distal bands have sample-0 fifth percentiles **0.440318/0.439205** and sample-6 fifth percentiles **0.924156/0.924663**. These distributions suggest a useful **starting-pose-specific skin investigation**: the starting shoulder-press configuration is already far from the saved rest mesh at some distal edges, and a later pose may be less compressed in this one geometric metric. The metric does not diagnose bad skinning, tissue compression, correct technique, or actual elbow landmarks by itself.

A **subsequent** isolated read-only code extension ranks the five shortest and longest pose/rest mesh edges at samples 0/6/8, and the five edges with greatest absolute change relative to sample 0 at samples 6/8, for each existing fixed rest band. Every row preserves original mesh vertex ID pair, rest-space midpoint in metres and all three saved pose ratios. Stable numeric vertex IDs are reproducible *investigation handles*, **not** accepted anatomical landmark IDs, muscle origins, attachment patches or approved repair locations. Ranking is deterministic with vertex-ID tie breaks; no arbitrary biological threshold is introduced. Four additional synthetic tests cover identity, tie ordering, invalid inputs and rest translation.

**New extension status:** commits `fe4651643849116c97ba55428a6858ee77a96b75` and `ae75f4ed5c0ef2d97bcbadd5bd77f2e563672acb` are staged on the isolated branch. Their full Actions execution and new JSON member hash are **not verified at the time of writing**. The previously verified artifact predates the ranking extension. Inspect the next successful native-localization ZIP before treating new rankings as observed evidence.

**Research interpretation remains unchanged:** ISB upper-limb joint-coordinate conventions require independent humerus/radius/ulna and side/landmark calibration ([ISB Part II](https://pubmed.ncbi.nlm.nih.gov/15844264/)). Fixed rest skin edge IDs do not establish joint centres, segment axes or soft-tissue mechanical strain. Do not turn descriptive [CDC clinical ROM means](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html) into hard limits. Shoulder/scapula/clavicle, elbow/pronation and hip/knee/ankle general-motion validation remains blocked; 46 anatomical landmarks unbound and 0/19 generic tests accepted. No original model or production file changed.


### First source-pinned ranked-edge report (code-only workflow run; synthetic extension tests pending)

The native-localization job in [run 40060666110](https://github.com/anyangle1409-code/animation-software/actions/runs/40060666110), at code commit `fe4651643849116c97ba55428a6858ee77a96b75`, completed **SUCCESS** and emitted the new ranking. Its [native artifact 12546669848](https://github.com/anyangle1409-code/animation-software/actions/runs/40060666110/artifacts/12546669848) was independently downloaded: ZIP SHA256 **MATCH** `257e6de31cc14e2b1b7d3aee1ddd520061cb00f33aa3c98f15929e1576701738`; embedded `w8_elbow_edge_continuity.json` SHA256 `5fb76a15d8bcee051b7b1e2f3696c5cb692e247ca9268cd694aadf3217412df9`. This **does not** certify the entire run or the subsequently added four tests. The later full-test run `40060680693` must be checked separately.

| Authored suffix / rest band | Ranking and saved sample | Fixed rest mesh vertex IDs | Rest midpoint (body-local m) | Pose/rest ratio |
|---|---|---|---|---:|
| l / distal | Shortest at sample 0 | 15645, 53019 | −0.234720, −0.025484, 1.193890 | 0.167612 |
| r / distal | Shortest at sample 0 | 17185, 44317 | +0.234709, −0.025419, 1.193933 | 0.163126 |
| l / middle | Longest at sample 6 | 29237, 71026 | −0.159497, +0.010991, 1.313827 | 2.673372 |
| r / middle | Longest at sample 6 | 32352, 71428 | +0.159445, +0.010973, 1.313840 | 2.648593 |

The ranked JSON includes the **top five** for each category/region and all three ratios per edge, so the same mesh edges can be located and followed later. The roughly mirrored coordinates and similar values across authored suffixes are **observations**, not proof of anatomical L/R, normal morphology or causality. Mesh-edge vertex IDs and rest midpoints must not be promoted to humeral epicondyles, radius/ulna landmarks, muscle origins or proposed geometry corrections. Sample 0 and 6 are **shoulder-press poses**, not a controlled isolated elbow movement. Do not change acceptance gates or the preserved model.


### Final cloud validation of ranking extension

The earlier pending state is superseded: [run40060680693](https://github.com/anyangle1409-code/animation-software/actions/runs/40060680693) at `ae75f4ed5c0ef2d97bcbadd5bd77f2e563672acb` finished **SUCCESS in all seven jobs**. Native-localization logs show the four new ranked-hotspot tests individually **PASS**, the full suite **182/182 PASS**, and the actual W8 pinned saved-geometry report generated. [Artifact12547635497](https://github.com/anyangle1409-code/animation-software/actions/runs/40060680693/artifacts/12547635497) was independently downloaded: ZIP SHA256 `820cd02e9cae17289e360e488e32c60e40cce7060a397e6bc4ee1cac7b6941fe` **MATCH** GitHub; embedded `w8_elbow_edge_continuity.json` SHA256 `5fb76a15d8bcee051b7b1e2f3696c5cb692e247ca9268cd694aadf3217412df9` **MATCH** the preceding code-only artifact. All eight final-run ZIP digests were independently verified; see the [execution ledger](PHONE_CLOUD_EXECUTION_LEDGER_20261023.md).

**This confirms deterministic report generation and pinned-source integrity, not anatomical joint calibration, correct skinning, safe ROM or any fixed deformation.** The next *separate* evidence gate is a read-only native Blender inspection of the identified fixed mesh edges, local skin weights, active corrective channels and true segment landmarks during both starting and overhead poses, without editing the model. Later isolated elbow flexion/pronation and whole-body lower-limb tests still require independently verified anatomical axes. Muscle highlighting remains deferred.
