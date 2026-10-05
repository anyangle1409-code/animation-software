# r96 axilla edge localization

This read-only diagnostic compares the frozen r95 weights-only surface with the declared r96 topology-only intermediate. Corrective shape keys are disabled.

The same small anterior/lower axilla edge families dominate all four elevated-arm stress poses in both candidates. In `press_top`, the worst left-side edges are:

| Edge | Rest midpoint (m) | r96 ratio |
| --- | --- | ---: |
| `6-6290` | `(-0.156811, -0.048577, 1.391671)` | 3.294347 |
| `922-6290` | `(-0.153881, -0.048312, 1.385712)` | 3.271660 |
| `890-6231` | `(-0.149426, -0.045893, 1.371759)` | 3.018340 |
| `6-4507` | `(-0.162040, -0.044907, 1.395944)` | 2.656018 |
| `859-6105` | `(-0.157383, -0.003839, 1.344671)` | 2.619404 |

The initial r96 ring did not change the first four ratios because it sits above or crosses the wrong cells. It also introduced a new sharp pair at edge `4505-13465` (press-top cosine 0.162245, drop 0.835740) where the ring split the surface without resolving the lower strain source.

This evidence narrows the next topology hypothesis to three circumferential support rows passing through the exact lower/middle strain cells represented by seed edges `859-6105`, `890-6231`, and `922-6290`. It does not authorize an edit by itself; the exact edge sets and invariants must be committed in a separate pre-edit declaration.

Files:

- `r95_weights_only_edge_localization.json`
- `r96_topology_only_edge_localization.json`
