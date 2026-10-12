# G5c — first-party ORIGINAL_v1 owner-local review page

An independent static HTML entry point was added at `src/viewer/originalFullBodyOwnerLocalReview.html`, using existing owner-local authenticated neutral-render controller from G4u/G4v. It has a manually selected private .glb input, five fixed cameras, a responsive canvas, accessible status text, and page-exit cleanup. iOS form controls retain 16px font size and user pinch zoom. No CDN, third-party library, auto file fetch, model embedding or upload.

**To run later:** serve the existing repository's `src/viewer` directory as static files on the owner's trusted local environment over localhost HTTPS/HTTP; open the page in a WebGL2 browser and choose the exact private review-only GLB from that same device. Do not commit or publish the private file. File URL/import restrictions vary across browsers, so a static local server is preferable.

The page has not been deployed. Automated tests only verify HTML wiring and previously tested controller rejection of forged/wrong GLB source; they do not prove a private original full-body GPU render nor iPhone compatibility. The model's feet, anatomy, natural exercises and production admission remain unapproved.
