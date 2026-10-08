# Scapular landmark measurement evidence

Lee ECS, Lawrence RL, Rainbow MJ (2024), *Sexual dimorphism and allometry in human scapula shape*, DOI 10.1111/joa.14124. Replication dataset DOI [10.5683/SP3/PHVS3D](https://doi.org/10.5683/SP3/PHVS3D), released 2024-08-08, CC BY 4.0.

Workbook downloaded from https://borealisdata.ca/api/access/datafile/714668. Published MD5: `c0adeb1dbed8a83e61572640de345a0b`. SHA256: `c8d9bd697014f350e2145d781bcf37162a9e1377a2d3c20b288c10844bb0b976`.

Contains demographic records and 29 XYZ landmarks for 125 subjects. Source R array layout and millimetre labels were checked; stature is in centimetres. Sheet dimension metadata incorrectly says A1: read actual XML cells and join subject IDs. No source mesh was imported. The analysis is our direct OLS of measurements/rigidly aligned coordinates on stature, not a reproduction of the authors' shape PCA.

Recompute: `python scripts/anatomy_fit/scapula_landmark_model.py --height-cm 182.00002908706665`. All-male and asymptomatic/no-full-thickness-tear subsets remain separate. Their sparse relative envelopes do not specify SC, AC or GH centres, thorax pose, cartilage, or a full bone surface.
