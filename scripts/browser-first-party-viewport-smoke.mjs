#!/usr/bin/env node
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const BASE_URL = process.env.HGPT_BROWSER_URL || "http://127.0.0.1:5174";
const URL = BASE_URL;
const OUT = path.resolve("reports/browser-smoke/first-party-host");
fs.mkdirSync(OUT, { recursive: true });

const report = {
  generatedAt: new Date().toISOString(),
  url: URL,
  sceneHost: "first-party",
  status: "FAIL",
  supplementaryOnly: true,
  physicalDeviceGateClosed: false,
  checks: {},
  consoleErrors: [],
  pageErrors: [],
  failedCriticalRequests: [],
};

const hash = (buffer) => crypto.createHash("sha256").update(buffer).digest("hex");
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForServer() {
  let lastError;
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try {
      const response = await fetch(BASE_URL, { redirect: "manual" });
      if (response.ok) return;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await delay(250);
  }
  throw new Error(`Vite server did not become ready at ${BASE_URL}: ${lastError?.message ?? "unknown error"}`);
}

let browser;
try {
  await waitForServer();
  browser = await chromium.launch({
    headless: true,
    args: ["--use-angle=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"],
  });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });

  page.on("console", (message) => {
    if (message.type() === "error") report.consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => report.pageErrors.push(error.message));
  page.on("requestfailed", (request) => {
    if (["document", "script", "stylesheet"].includes(request.resourceType())) {
      report.failedCriticalRequests.push({
        url: request.url(),
        resourceType: request.resourceType(),
        error: request.failure()?.errorText ?? "request failed",
      });
    }
  });

  await page.goto(URL, { waitUntil: "domcontentloaded", timeout: 30_000 });
  await page.waitForSelector('[data-hgpt-scene-host="first-party"]', {
    state: "visible",
    timeout: 20_000,
  });
  await page.waitForSelector(".toolbar__title", { state: "visible", timeout: 20_000 });

  assert.equal(await page.locator(".toolbar__title").textContent(), "Home Gym PT");

  const leftTabs = page.locator(".studio__side--left .tabs").first();
  const rightTabs = page.locator(".studio__side--right .tabs").first();
  const equipmentTab = leftTabs.getByRole("button", { name: "Equipment", exact: true });
  const reviewTab = rightTabs.getByRole("button", { name: "Review", exact: true });
  await equipmentTab.click();
  await reviewTab.click();
  assert((await equipmentTab.getAttribute("class"))?.includes("is-active"), "Left editor tab did not activate");
  assert((await reviewTab.getAttribute("class"))?.includes("is-active"), "Right editor tab did not activate");

  const panelToggle = page.locator(".studio__panel-toggle").first();
  assert.equal(await panelToggle.textContent(), "Hide panels");
  await panelToggle.click();
  assert((await page.locator(".studio").first().getAttribute("class"))?.includes("studio--focus"), "Panel hide did not enter focus mode");
  assert.equal(await panelToggle.textContent(), "Show panels");
  await panelToggle.click();
  assert(!(await page.locator(".studio").first().getAttribute("class"))?.includes("studio--focus"), "Panel show did not leave focus mode");
  assert.equal(await panelToggle.textContent(), "Hide panels");

  await leftTabs.getByRole("button", { name: "Joint", exact: true }).click();
  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();
  report.checks.editorShell = {
    leftTab: "joint",
    rightTab: "exercise",
    panelsOpen: true,
  };

  const firstPartyShellDom = await page.evaluate(async () => {
    const [{ createStudioAppShellDom }, { studioLayoutStore }] = await Promise.all([
      import("/src/editor/appShellDom.ts"),
      import("/src/editor/layoutState.ts"),
    ]);

    studioLayoutStore.setState({
      leftTab: "joint",
      rightTab: "exercise",
      panelsOpen: true,
    });

    const shell = createStudioAppShellDom(document, studioLayoutStore);
    shell.element.dataset.hgptEditorShellProbe = "first-party";
    shell.element.style.position = "fixed";
    shell.element.style.left = "-10000px";
    shell.element.style.top = "0";
    shell.element.style.width = "900px";
    shell.element.style.height = "700px";
    document.body.append(shell.element);

    const leftLabels = Object.values(shell.controls.leftTabs).map((button) => button.textContent);
    const rightLabels = Object.values(shell.controls.rightTabs).map((button) => button.textContent);
    const slotNames = Object.values(shell.slots).map(
      (slot) => slot.dataset.hgptEditorSlot ?? "",
    );

    shell.controls.leftTabs.equipment.click();
    shell.controls.rightTabs.review.click();
    shell.controls.panelToggle.click();

    const state = studioLayoutStore.getState();
    const result = {
      leftLabels,
      rightLabels,
      slotNames,
      leftTab: state.leftTab,
      rightTab: state.rightTab,
      panelsOpen: state.panelsOpen,
      equipmentActive: shell.controls.leftTabs.equipment.classList.contains("is-active"),
      jointInactive: !shell.controls.leftTabs.joint.classList.contains("is-active"),
      reviewActive: shell.controls.rightTabs.review.classList.contains("is-active"),
      focusClass: shell.element.classList.contains("studio--focus"),
      panelToggleText: shell.controls.panelToggle.textContent,
    };

    shell.dispose();
    shell.element.remove();
    studioLayoutStore.setState({
      leftTab: "joint",
      rightTab: "exercise",
      panelsOpen: true,
    });
    return result;
  });

  assert.deepEqual(
    firstPartyShellDom.leftLabels,
    ["Joint", "Grip", "IK & locks", "Contacts", "Equipment", "Character"],
    "First-party editor shell left-tab labels drifted from the React reference",
  );
  assert.deepEqual(
    firstPartyShellDom.rightLabels,
    ["Generate", "Exercise", "Muscles", "Technique", "Correctives", "Compare", "Review", "Export"],
    "First-party editor shell right-tab labels drifted from the React reference",
  );
  assert.deepEqual(
    firstPartyShellDom.slotNames,
    ["toolbar", "left-panel", "viewport", "right-panel", "timeline"],
    "First-party editor shell slot contract is incomplete",
  );
  assert.equal(firstPartyShellDom.leftTab, "equipment");
  assert.equal(firstPartyShellDom.rightTab, "review");
  assert.equal(firstPartyShellDom.panelsOpen, false);
  assert.equal(firstPartyShellDom.equipmentActive, true);
  assert.equal(firstPartyShellDom.jointInactive, true);
  assert.equal(firstPartyShellDom.reviewActive, true);
  assert.equal(firstPartyShellDom.focusClass, true);
  assert.equal(firstPartyShellDom.panelToggleText, "Show panels");
  report.checks.firstPartyEditorShellDom = firstPartyShellDom;

  const canvas = page.locator('[data-hgpt-scene-host="first-party"] canvas').first();
  await canvas.waitFor({ state: "visible", timeout: 20_000 });
  await page.waitForTimeout(900);

  const initialBox = await canvas.boundingBox();
  assert(initialBox && initialBox.width > 300 && initialBox.height > 300, "First-party canvas has invalid dimensions");

  const webgl = await page.evaluate(() => {
    const element = document.querySelector('[data-hgpt-scene-host="first-party"] canvas');
    if (!(element instanceof HTMLCanvasElement)) return { exists: false };
    const gl = element.getContext("webgl2");
    return gl
      ? {
          exists: true,
          width: gl.drawingBufferWidth,
          height: gl.drawingBufferHeight,
          error: gl.getError(),
          touchAction: element.style.touchAction,
        }
      : { exists: false };
  });
  assert.equal(webgl.exists, true, "First-party host has no WebGL2 context");
  assert(webgl.width > 0 && webgl.height > 0, "First-party drawing buffer is empty");
  assert.equal(webgl.error, 0, "First-party WebGL reported an error");
  assert.equal(webgl.touchAction, "none", "First-party orbit input did not disable default touch action");
  report.checks.webgl = webgl;

  const hostDiagnostic = async () =>
    page.evaluate(() => {
      const canvas = document.querySelector('[data-hgpt-scene-host="first-party"] canvas');
      if (!(canvas instanceof HTMLCanvasElement)) return null;
      return {
        frameCount: Number(canvas.dataset.hgptFrameCount ?? 0),
        sceneChildren: Number(canvas.dataset.hgptSceneChildren ?? 0),
        cameraPosition: canvas.dataset.hgptCameraPosition ?? null,
        cameraQuaternion: canvas.dataset.hgptCameraQuaternion ?? null,
        rendererFrame: Number(canvas.dataset.hgptRendererFrame ?? 0),
        sceneNames: canvas.dataset.hgptSceneNames ?? "",
      };
    });

  const initialDiagnostic = await hostDiagnostic();
  assert(initialDiagnostic && initialDiagnostic.frameCount > 3, "First-party frame loop did not advance");
  assert(initialDiagnostic.rendererFrame > 2, "First-party renderer did not continuously draw");
  assert(initialDiagnostic.sceneChildren > 0, "First-party scene content did not mount");
  for (const expected of ["hgpt-studio-stage", "hgpt-skeleton-view", "hgpt-muscle-view"]) {
    assert(
      initialDiagnostic.sceneNames.includes(expected),
      `First-party scene is missing ${expected}: ${initialDiagnostic.sceneNames}`,
    );
  }
  report.checks.initialHostDiagnostic = initialDiagnostic;

  const cameraSelect = page.locator("label.field").filter({ hasText: "Camera" }).locator("select").first();
  await cameraSelect.selectOption("front");
  await page.waitForTimeout(600);
  const frontDiagnostic = await hostDiagnostic();
  const frontHash = hash(await canvas.screenshot({ path: path.join(OUT, "front.png") }));
  await cameraSelect.selectOption("left");
  await page.waitForTimeout(600);
  const leftDiagnostic = await hostDiagnostic();
  const leftHash = hash(await canvas.screenshot({ path: path.join(OUT, "left.png") }));
  assert(
    frontDiagnostic && leftDiagnostic,
    "First-party host camera diagnostics were unavailable",
  );
  assert.notEqual(
    frontDiagnostic.cameraPosition,
    leftDiagnostic.cameraPosition,
    "First-party camera position did not change between presets",
  );
  assert.notEqual(
    frontDiagnostic.cameraQuaternion,
    leftDiagnostic.cameraQuaternion,
    "First-party camera orientation did not change between presets",
  );
  assert(
    leftDiagnostic.rendererFrame > frontDiagnostic.rendererFrame,
    "First-party renderer frame counter did not advance between camera presets",
  );
  assert.notEqual(
    frontHash,
    leftHash,
    `First-party camera presets did not change the render; front=${JSON.stringify(frontDiagnostic)} left=${JSON.stringify(leftDiagnostic)}`,
  );
  report.checks.cameraPresetRenderChanged = {
    frontHash,
    leftHash,
    frontDiagnostic,
    leftDiagnostic,
  };

  const box = await canvas.boundingBox();
  assert(box, "First-party canvas disappeared before orbit test");
  const startX = box.x + box.width * 0.55;
  const startY = box.y + box.height * 0.5;
  const orbitBefore = hash(await canvas.screenshot());
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + Math.min(140, box.width * 0.2), startY + 45, { steps: 12 });
  await page.mouse.up();
  await page.waitForTimeout(500);
  const orbitAfter = hash(await canvas.screenshot({ path: path.join(OUT, "after-orbit.png") }));
  assert.notEqual(orbitBefore, orbitAfter, "First-party mouse orbit did not change the render");
  report.checks.mouseOrbitRenderChanged = { orbitBefore, orbitAfter };

  const wheelBefore = hash(await canvas.screenshot());
  await page.mouse.wheel(0, -420);
  await page.waitForTimeout(500);
  const wheelAfter = hash(await canvas.screenshot({ path: path.join(OUT, "after-wheel.png") }));
  assert.notEqual(wheelBefore, wheelAfter, "First-party wheel zoom did not change the render");
  report.checks.wheelZoomRenderChanged = { wheelBefore, wheelAfter };

  const backdropSelect = page.locator("label.field").filter({ hasText: "Backdrop" }).locator("select").first();
  const backdropBefore = hash(await canvas.screenshot());
  await backdropSelect.selectOption("void");
  await page.waitForTimeout(400);
  const backdropAfter = hash(await canvas.screenshot({ path: path.join(OUT, "void.png") }));
  assert.notEqual(backdropBefore, backdropAfter, "First-party backdrop did not change the render");
  await backdropSelect.selectOption("studio");
  report.checks.backdropRenderChanged = { backdropBefore, backdropAfter };

  const viewMode = page.getByRole("group", { name: "View mode" });
  const timeReadout = page.locator(".timeline__time").first();

  await viewMode.getByRole("button", { name: "Skeleton", exact: true }).click();
  await page.waitForTimeout(350);
  const skeletonBefore = hash(await canvas.screenshot({ path: path.join(OUT, "skeleton-before.png") }));
  const timeBefore = await timeReadout.textContent();
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await page.waitForTimeout(650);
  const timeAfter = await timeReadout.textContent();
  const skeletonAfter = hash(await canvas.screenshot({ path: path.join(OUT, "skeleton-after.png") }));
  assert.notEqual(timeBefore, timeAfter, "First-party playback time did not advance");
  assert.notEqual(skeletonBefore, skeletonAfter, "First-party skeleton render did not advance");
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  report.checks.skeletonPlayback = { timeBefore, timeAfter, skeletonBefore, skeletonAfter };

  const selectedBone = await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().selectBone("forearm_l");
    return useStudio.getState().selection.bone;
  });
  assert.equal(selectedBone, "forearm_l");
  await page.waitForTimeout(250);
  const gizmoSelected = hash(await canvas.screenshot({ path: path.join(OUT, "gizmo-selected.png") }));
  await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().selectBone(null);
  });
  await page.waitForTimeout(250);
  const gizmoCleared = hash(await canvas.screenshot({ path: path.join(OUT, "gizmo-cleared.png") }));
  assert.notEqual(gizmoSelected, gizmoCleared, "First-party gizmo selection did not change the render");
  report.checks.transformGizmoSelectionRenderChanged = { gizmoSelected, gizmoCleared };

  const exerciseSelect = page.locator("label.field").filter({ hasText: "Exercise" }).locator("select").first();
  await exerciseSelect.selectOption("air_squat");
  await page.waitForTimeout(350);
  const startKey = page.locator(".timeline__key.marker-start").first();
  const peakKey = page.locator(".timeline__key.marker-peak").first();

  await viewMode.getByRole("button", { name: "Character", exact: true }).click();
  await startKey.click();
  await page.waitForTimeout(300);
  const characterStart = hash(await canvas.screenshot({ path: path.join(OUT, "character-start.png") }));
  await peakKey.click();
  await page.waitForTimeout(300);
  const characterPeak = hash(await canvas.screenshot({ path: path.join(OUT, "character-peak.png") }));
  assert.notEqual(characterStart, characterPeak, "First-party character did not change across authored poses");

  await viewMode.getByRole("button", { name: "Muscles", exact: true }).click();
  await startKey.click();
  await page.waitForTimeout(300);
  const musclesStart = hash(await canvas.screenshot({ path: path.join(OUT, "muscles-start.png") }));
  await peakKey.click();
  await page.waitForTimeout(300);
  const musclesPeak = hash(await canvas.screenshot({ path: path.join(OUT, "muscles-peak.png") }));
  assert.notEqual(musclesStart, musclesPeak, "First-party muscles did not change across authored poses");
  assert.notEqual(musclesStart, characterStart, "First-party muscles and character renders were identical");
  report.checks.authoredPoseRendering = {
    characterStart,
    characterPeak,
    musclesStart,
    musclesPeak,
  };

  await viewMode.getByRole("button", { name: "Character", exact: true }).click();
  await exerciseSelect.selectOption("dumbbell_bicep_curl");
  await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    const state = useStudio.getState();
    state.pause();
    if (!state.showEquipment) state.toggle("showEquipment");
  });
  await page.waitForTimeout(300);
  const equipmentVisible = hash(await canvas.screenshot({ path: path.join(OUT, "equipment-visible.png") }));
  await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().toggle("showEquipment");
  });
  await page.waitForTimeout(250);
  const equipmentHidden = hash(await canvas.screenshot({ path: path.join(OUT, "equipment-hidden.png") }));
  assert.notEqual(equipmentVisible, equipmentHidden, "First-party equipment visibility did not change the render");
  await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    if (!useStudio.getState().showEquipment) useStudio.getState().toggle("showEquipment");
  });
  report.checks.equipmentVisibility = { equipmentVisible, equipmentHidden };

  await exerciseSelect.selectOption("pull_up");
  await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    const state = useStudio.getState();
    state.pause();
    state.setTime(0);
    if (!state.showIkHandles) state.toggle("showIkHandles");
    if (!state.document.clip.keyframes[0]?.ik.arm_l?.enabled) state.toggleIK("arm_l");
  });
  await page.waitForTimeout(300);
  const ikVisible = hash(await canvas.screenshot({ path: path.join(OUT, "ik-visible.png") }));
  await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().toggle("showIkHandles");
  });
  await page.waitForTimeout(250);
  const ikHidden = hash(await canvas.screenshot({ path: path.join(OUT, "ik-hidden.png") }));
  assert.notEqual(ikVisible, ikHidden, "First-party IK handles did not change the render");
  report.checks.ikHandleVisibility = { ikVisible, ikHidden };

  await page.setViewportSize({ width: 780, height: 900 });
  await page.waitForTimeout(450);
  const resized = await canvas.boundingBox();
  assert(resized && resized.width > 300 && resized.height > 300, "First-party canvas became invalid after resize");
  report.checks.responsiveResize = resized;

  assert.equal(report.pageErrors.length, 0, `Page errors: ${report.pageErrors.join(" | ")}`);
  assert.equal(
    report.failedCriticalRequests.length,
    0,
    `Critical request failures: ${JSON.stringify(report.failedCriticalRequests)}`,
  );
  assert.equal(report.consoleErrors.length, 0, `Console errors: ${report.consoleErrors.join(" | ")}`);

  report.status = "PASS";
} catch (error) {
  report.failure = error instanceof Error ? error.stack ?? error.message : String(error);
  throw error;
} finally {
  if (browser) await browser.close();
  fs.writeFileSync(
    path.join(OUT, "browser-smoke-first-party.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
}
