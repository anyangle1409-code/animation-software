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
