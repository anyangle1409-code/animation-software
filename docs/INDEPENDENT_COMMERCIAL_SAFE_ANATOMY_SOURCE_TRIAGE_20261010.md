# Independent external anatomical source candidates — cohort + rights triage (2026-10-10)

## Purpose / boundary

Home Gym PT's **CP1 / Phase 6 canonical anatomical source closure remains BLOCKED** in the ribs, carpus and tarsus. Verified BoneHub Visible Human male source STLs (PRs #32–34) provide useful labelled bone surfaces but represent *the same one NLM male donor* as the CT investigation. The current Work laptop session is already examining their raw meshes, fragments, segmentation layers and coordinate registration. **Do not duplicate that activity.**

This independent, metadata-only review looks for ***different human subjects*** to cross-check morphology/kinematics and makes conservative distinctions between a dataset's rights, a public scientific article's licence and a separately licensed segmentation *model*. No images, STL or NIfTI patient data were downloaded, no numerical bone targets selected and no software dependency was installed.

Machine-readable record: \`ORIGINAL_V1_WORK/anatomy/independent_source_rights_cohort_candidates_20261010.json\`. Test gate: \`scripts/anatomy_fit/audit_independent_source_rights.py\`.

## Priority 1 — rib shape cohort that is genuinely different from the Visible Human donor

**TotalSegmentator original hospital CT dataset**: [Wasserthal et al., Zenodo 6802614](https://zenodo.org/records/6802614), [TotalSegmentator project](https://github.com/wasserth/TotalSegmentator), [dataset CC BY information](https://huggingface.co/datasets/huggingface/CADS-dataset/blob/main/0037_totalsegmentator/README_0037_totalsegmentator.md).

- Published version: **1,204 CT exams, 104 anatomical labels (59 bones)**, sampled from clinical practice. Latest software README describes different later released CT counts; **do not casually replace the original cohort count with 1,228** or double-count versions.
- Separately labelled left/right ribs, vertebral levels, scapulae and clavicles provide a promising *independent donor collection* for intersubject rib shapes and thorax modelling, subject to case-by-case QA.
- Dataset and a third-party mirror [MedOtter/totalsegmentator-ribs](https://huggingface.co/datasets/MedOtter/totalsegmentator-ribs) advertise **CC BY 4.0**, but *verify the particular source record and each file's terms* before any commercial derivative. The main repository code is Apache 2.0: **software licence is not CT-data licence**.
- The clinical dataset includes pathological and incomplete acquisitions, variable CT fields of view and no guarantee of standing posture. Ribs may be damaged or truncated. Gender, stature, age and protocol must be evaluated for any 182 cm male target. There is no guarantee all individuals show 24 labelled ribs.
- **The MedOtter mirror is a pointer/repackaging of the TotalSegmentator subjects**, *not an additional independent cohort* and not a warrant to use the entire 37 GB mirror on a laptop.
- **Crucial licence distinction:** TotalSegmentator base \`total\` task is publicly usable under the project's stated terms, but its **\`appendicular_bones\` model/task is separately licensed for commercial use**. It must NOT be used as free commercial carpal or tarsal segmentation software merely because the base CT dataset is CC BY. [Official project subtask list](https://github.com/wasserth/TotalSegmentator#subtasks).

**Immediate low-resource next move:** metadata-only cohort and licence verification; identify one *source-authorized* CT subset with complete bilateral ribs and no visible fractures, then isolate independent geometry-derived shape statistics using documented acquisition frame. Avoid committing patient scans, masks or raw 3D medical assets to Git. This would target the **ribs BLOCKED** evidence gap. It is not, by itself, evidence of costal cartilage, rib tubercle contacts or functional thorax motion.

## Priority 2 — independent dynamic subtalar joint transforms with a clinical caveat

**University of Utah, Ankle Arthrodesis Compensation dataset**: [Repository catalogue](https://hive.utah.edu/catalog?f%5Bkeyword_sim%5D%5B%5D=Tibiotalar+Arthrodesis&locale=en); DOI [10.7278/S5d-1nqg-0fqd](https://doi.org/10.7278/S5d-1nqg-0fqd); source study DOI [10.2106/JBJS.19.01132](https://doi.org/10.2106/JBJS.19.01132).

- University of Utah catalog explicitly lists **CC BY** (commercial reuse with attribution), separate bone surface files, CT images and measured rigid-body transforms for subtalar kinematics.
- Offers more directly functional joint-transform information than a neutral-pose static CT mesh. May be useful as a supplementary motion-mechanics and contact check.
- **NOT a normative healthy ankle cohort.** Cases are people following ankle fusion (tibiotalar arthrodesis). An untreated contralateral limb labelled \`NonAD\` is not automatically a healthy, uncompensated control limb. Exclude it from normal adult subtalar ROM/shape targets without a suitable design and comparator.
- License of catalogue should be checked against downloadable component files/participant release terms before copying data into a commercial derivative. No such raw data was acquired in this evidence check.

**Immediate low-resource next move:** source documentation only; determine the kinematic transform convention, participant movement task and which comparisons are clinically valid. Research-grade extreme/pathology case validation possible; not a shortcut to a canonical ankle centre or normal loading mechanics.

## Priority 3 — separate low-limb specimen bone silhouettes, limited tarsal resolution

[UltraBones100k dataset](https://huggingface.co/datasets/luohwu/UltraBones100k) publishes **14 CT/ultrasound specimens** with an advertised CC BY 4.0 licence and preoperative CT bone segmentations (tibia, fibula and a \`foot.stl\`). Verify original source terms and specimen case descriptions. It appears useful for gross lower-leg to foot shape evidence but the supplied \`foot.stl\` may be a **merged surface** and is *not demonstrably seven labelled tarsal contact surfaces*. Do not infer 14 independent healthy adults, male stature distribution or true subtalar motion from a file count.

## Important quarantined source — individual foot bone cohort with non-commercial rights

BoneHub VSD [\`vsd-feet-seg\`](https://huggingface.co/datasets/BoneHub/vsd-feet-seg) / [\`vsd-lower-extremities-seg\`](https://huggingface.co/datasets/BoneHub/vsd-lower-extremities-seg), Fischer et al. 2023 DOI [10.1038/s41597-023-02669-z](https://doi.org/10.1038/s41597-023-02669-z) offers **30 independent cadaver cases (16 male)**, but underlying raw dataset rights are **CC BY-NC-SA 4.0**. It is also the *same 30 source donors* in both the full lower-extremity and foot-only subsets. **No raw data, copied source meshes, or proprietary commercial derived shape targets are authorized here.** The published article may have different rights from the patient CT data.

Review rights with source owners before any downstream use. Do not silently substitute model output from a non-commercial dataset or commercially gated segmentation model.

## Specific Work integration / CP1 next steps

1. **Work continues existing laptop source registration**: exact-source STLs/NRRD/CT, fragment provenance and independent Blender review, without altering accepted anatomy.
2. **This branch handles external population evidence and rights**: TotalSegmentator *base* rib cohort provenance and completeness/metadata-only screening; Utah ankle clinical mechanics for supplementary uncertainty tests; disallow VSD NC and separately licensed \`appendicular_bones\` for production until rights confirmed.
3. Later, using truly independent usable subjects, compare full curved rib centreline shapes and sternum/rib-level relations against the single Visible Human donor's curvature, with source-specific measurement endpoint definitions.
4. Independently cross-check natural human foot morphology and contact corridors with unrestricted high-quality sources; one fused \`foot.stl\` is not seven articular centres.
5. **Never treat multiple mirrors, repeated segmentations or two sides of one donor as independent subjects.** Never infer canonical 182 cm proportions from an unqualified clinical collection.

**Hard stop:** This report does not make CP1 pass, alter c005, mark ribs/carpus/tarsus ready, approve mesh import into the app, or modify r95. The canonical readiness ledger remains **0 READY / 9 PARTIAL / 3 BLOCKED**. Treat all candidate sources as *metadata opportunities* until legal, imaging, population and anatomical validation gates pass.
