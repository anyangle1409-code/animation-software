# Grid, Orbit and Transform physical parity handoff

## Why this gate is still open

The first-party runtime cutover is complete: React/ReactDOM, R3F/Drei and Three
are removed from the live source/package graph, and the automated Chromium
WebGL smoke passes without them.

This physical gate remains open for a different reason: no recorded real
desktop + iPhone Safari human visual/input review has yet closed the subjective
and touch-interaction requirements below. Unit tests and headless Chromium are
strong engineering evidence, but they do not prove iPhone touch cancellation,
human grid/gizmo appearance, or physical-device interaction quality.

Package removal is **not** waiting on this gate anymore. This gate now controls
physical parity/release evidence only; removed packages must not be restored to
make a physical check pass.

## Automated Chromium evidence

A supplementary GitHub Actions workflow now runs the real Vite app in headless Chromium with WebGL/SwiftShader and stores screenshots plus `reports/browser-smoke/browser-smoke.json`. It verifies module execution, a live WebGL2 drawing buffer, camera-preset render changes, primary-pointer Orbit, wheel zoom, backdrop changes, playback advance and responsive resize without console/page/critical module-request errors.

This is useful engineering evidence, but it **does not close this physical gate**. It is not iPhone Safari and it does not certify subjective grid appearance, gizmo correctness, touch cancellation or human visual parity. Use the physical checks below for those items.

## Laptop entry and evidence

On `work/standalone-first-party-audit-20260927`, from the repository root:

```bat
npm ci
npm run dev -- --host 0.0.0.0
```

Use the Vite URL printed by the terminal in a compatible desktop browser. For iPhone, open the same app via the laptop's local network IP and printed port on the same network; use Safari. This is local development access, not a finished-product remote runtime dependency. Do not use an image of the app or a blank HTML shell as evidence. Record branch/HEAD, browser and OS versions, screen size, date, and screenshots or a short recording of each check. Keep those review files outside the release allowlist.

## Desktop checks

1. Confirm Home Gym PT editor text, the 3D canvas, character/skeleton, reference grid and no error overlay or console errors. Exercise and Camera selectors should function.
2. In Studio backdrop, inspect minor 0.25 m and major 1 m grid lines at front, side and three-quarter camera presets. Change Backdrop to Void, then back to Studio. Check the floor/grid visibility and colour against the selected backdrop; check at close and distant zoom.
3. On the canvas, primary mouse drag rotates the camera smoothly without moving the selected model. Wheel zoom stays within the 0.6–12 m envelope. Change Camera presets and use Focus after selecting a bone; verify Orbit continues from the new target without a jump.
4. In Skeleton view, select a visible bone. Drag each visible rotation-axis ring in turn and verify only the chosen bone edit is applied within its anatomical limit. Undo and Redo must restore the pose. Orbit must remain suspended during a gizmo drag, then resume after release/cancel.
5. In the Equipment tab, select a static equipment item and verify translate/rotate and socket edit paths where available. In IK & locks, drag target and pole handles. Check that the selected axis and stored edit agree, and Undo/Redo work. Do not change exercise biomechanics to make a control appear correct.
6. Resize the browser and check canvas aspect, picking, gizmo size and camera target. Pause and scrub Bottom/Mid/Peak/Return while checking that grips, equipment and floor contacts do not lag a frame behind the character.

## iPhone Safari checks

1. Load the executing app and confirm a visible 3D scene; record any layout clipping or browser console error available through desktop Safari inspection.
2. One finger on canvas rotates; two fingers pinch zooms and remains within the same 0.6–12 m range. Switch camera presets, scrub and repeat. Neither gesture should scroll the page while touching the canvas.
3. Select and drag a visible gizmo axis. One finger should edit the selected object, not orbit simultaneously. Release and repeat Orbit; verify touch cancellation does not leave dragging stuck.
4. Rotate the phone and repeat canvas touch, selection, pinch and gizmo interactions after resize.

## Decision record

For each Grid, desktop Orbit, iPhone Orbit, bone Transform,
equipment/socket Transform, and IK target/pole Transform, record
**PASS/FAIL/NOT TESTED** plus the screenshot/recording path and a one-line
observation. A failed or untested item keeps the physical release gate open.

If all pass, rerun focused controls tests, typecheck/build,
`npm run audit:standalone`, and the applicable release/offline gates. Runtime
package removal is already complete; this evidence must not reintroduce React,
R3F/Drei, Three or another runtime framework.
