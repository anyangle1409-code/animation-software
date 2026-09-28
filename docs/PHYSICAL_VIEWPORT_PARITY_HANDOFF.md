# Grid, Orbit and Transform physical parity handoff

## Why this gate is still open

The source now has zero `@react-three/drei` imports. Project-owned Grid, Orbit and Transform controls are mounted in `Viewport.tsx`, but no compatible browser/device visual-input review has been recorded. The previous in-app localhost browser loaded HTML without executing the Vite module. Pure unit tests and the isolated fake-renderer host do not close this gate. Keep Drei installed until the actual app passes the checks below; keep R3F, React/ReactDOM and Three as separate later gates.

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

For each Grid, desktop Orbit, iPhone Orbit, bone Transform, equipment/socket Transform, and IK target/pole Transform, record **PASS/FAIL/NOT TESTED** plus the screenshot/recording path and a one-line observation. A failed or untested item keeps the physical gate open. If all pass, rerun focused controls tests, typecheck/build and `npm run audit:standalone` before proposing Drei package removal. Do not interpret this one gate as approval to remove R3F, React/ReactDOM or Three.
