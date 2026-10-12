# G5d owner review page default-deny browser policy

12 October 2026. The owner-only ORIGINAL_v1 page now defines meta Content Security Policy with default-deny network and form submissions, loads only same-origin first-party script modules, and explicitly denies connect-src. Existing inline CSS remains permitted for local styling. Inline boot logic moved to a same-origin ES module for CSP compatibility. No private GLB included or transmitted.

Important: a CSP meta tag cannot enforce frame-ancestors; avoid making anti-framing claims. Depending on browser support, separate HTTP response headers may be needed for comprehensive protection. CSP is defence in depth: review of imported modules and trusted local hosting are still required. The policy intentionally blocks remote asset loading, including any future remote model source. Automated tests inspect wiring and deny directives; no physical iPhone browser test performed.

Work owns original skeleton/feet/mesh, and no production PT App files were changed.
