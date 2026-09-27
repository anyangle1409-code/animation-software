# Offline standalone acceptance

The final operational Home Gym PT product must work with network access disabled.

## Test setup

Run the production build/package exactly as a user would receive it.

Then disable external network connectivity for the test environment.

Do not rely on:
- dev server fallback behaviour;
- npm/node_modules at runtime;
- CDN resources;
- hosted APIs;
- cloud AI;
- remote model downloads.

## Required PASS

### Startup
- app opens;
- no uncaught startup error;
- no external network request is attempted;
- production character loads from packaged first-party assets.

### Character
- `HomeGymPT_Male_ORIGINAL_v1` loads;
- dressed/required production variant loads;
- canonical v4 rig binds correctly;
- no V8/MakeHuman/legacy fallback is invoked.

### Exercises
- every library exercise loads;
- playback works;
- timeline/scrubbing works;
- cameras/inspection controls work;
- equipment renders/animates;
- contacts/IK/validation run.

### Prompt generation
- prompt parsing works locally;
- certified-family generation works;
- validation/correction loop works;
- unsupported prompts are rejected/explained locally;
- no hosted language model/API is contacted.

### Import/export
If included in the release:
- local user GLB import works through the first-party codec;
- export works through the first-party codec;
- no third-party loader/exporter is present.

### Mobile/interaction
- touch orbit/zoom works;
- play/pause/scrub works;
- camera presets work;
- selection/gizmo behaviour intended for release works.

### Release evidence
Require:
- `npm run audit:standalone` source/provenance gates PASS;
- production-output audit PASS;
- runtime network audit PASS;
- final character runtime audit PASS;
- release asset allowlist PASS;
- full test suite PASS;
- offline manual/automated acceptance PASS.

## Network observation

Where browser tooling is available, record all network requests during the test.

Allowed:
- same-package/local static resources required by the product.

Forbidden:
- external host;
- analytics/telemetry service;
- font CDN;
- hosted model;
- AI endpoint;
- remote image/model/audio;
- package CDN.

The expected external-host request count is **zero**.

## Definition

Passing this checklist means the operational product is self-contained with
respect to third-party runtime code/assets/services.

External development tools used to create/test it are outside this boundary and
are not required for operation.
