# G5e — owner-only original body review, no external hosting

Added a zero-third-party-dependency Node HTTP server: `node scripts/serve_original_review_local.mjs` serves `http://127.0.0.1:4175/` **on the same laptop only**. It serves the single owner-local neutral-view HTML page and flat first-party `.mjs` module files from `src/viewer`. It never serves `.glb`, `.blend` or private downloaded assets, accepts no uploads or POST methods, and explicitly binds to loopback rather than the public network. The browser's file picker supplies the original GLB locally; it is SHA verified before any GPU draw.

For an iPhone, `127.0.0.1` means the **phone itself**, not the laptop. This server does **not** make the laptop page accessible to a phone, provide a live public link or supply an iPhone model file. Browser tests remain needed, especially with the latest strict CSP and module dependency imports. Access beyond loopback would require a separately reviewed private transport/deployment plan and consent.

CI exercises local HTTP responses and rejects non-GET/HEAD operations, model extension serving and unusual routes. The target remains a review-only page: no production/biomechanical claims, no Work foot geometry or PT App edits.
