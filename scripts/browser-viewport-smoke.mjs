#!/usr/bin/env node
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const BASE_URL = process.env.HGPT_BROWSER_URL || "http://127.0.0.1:5174";
const URL = BASE_URL + (BASE_URL.includes("?") ? "&" : "?") + "sceneHost=r3f";
const OUT = path.resolve("reports/browser-smoke");
fs.mkdirSync(OUT, { recursive: true });

const report = {
  generatedAt: new Date().toISOString(),
  url: URL,
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
    args: [
      "--use-angle=swiftshader",
      "--enable-webgl",
      "--ignore-gpu-blocklist",
    ],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });

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
  await page.waitForSelector(".toolbar__title", { state: "visible", timeout: 20_000 });
  assert.equal(await page.locator(".toolbar__title").textContent(), "Home Gym PT");

  const canvas = page.locator(".studio__viewport canvas");
  await canvas.waitFor({ state: "visible", timeout: 20_000 });
  await page.waitForTimeout(750);

  const initialBox = await canvas.boundingBox();
  assert(initialBox && initialBox.width > 300 && initialBox.height > 300, "3D canvas has invalid desktop dimensions");

  const webgl = await page.evaluate(() => {
    const element = document.querySelector(".studio__viewport canvas");
    if (!(element instanceof HTMLCanvasElement)) return { exists: false };
    const gl = element.getContext("webgl2");
    return gl
      ? {
          exists: true,
          width: gl.drawingBufferWidth,
          height: gl.drawingBufferHeight,
          version: gl.getParameter(gl.VERSION),
          renderer: gl.getParameter(gl.RENDERER),
          error: gl.getError(),
          touchAction: element.style.touchAction,
        }
      : { exists: false };
  });
  assert.equal(webgl.exists, true, "WebGL2 context was not available");
  assert(webgl.width > 0 && webgl.height > 0, "WebGL drawing buffer is empty");
  assert.equal(webgl.error, 0, "WebGL reported an error after initial render");
  assert.equal(webgl.touchAction, "none", "Canvas touch action is not disabled by the orbit input adapter");
  report.checks.webgl = webgl;

  const cameraSelect = page.locator("label.field").filter({ hasText: "Camera" }).locator("select").first();
  await cameraSelect.selectOption("front");
  await page.waitForTimeout(750);
  const front = await canvas.screenshot({ path: path.join(OUT, "desktop-front.png") });
  const frontHash = hash(front);

  await cameraSelect.selectOption("left");
  await page.waitForTimeout(750);
  const left = await canvas.screenshot({ path: path.join(OUT, "desktop-left.png") });
  const leftHash = hash(left);
  assert.notEqual(frontHash, leftHash, "Front and left camera renders were byte-identical");
  report.checks.cameraPresetRenderChanged = { frontHash, leftHash };

  const beforeOrbit = await canvas.screenshot({ path: path.join(OUT, "desktop-before-orbit.png") });
  const box = await canvas.boundingBox();
  assert(box, "Canvas disappeared before orbit test");
  const startX = box.x + box.width * 0.55;
  const startY = box.y + box.height * 0.5;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  await page.mouse.move(startX + Math.min(140, box.width * 0.2), startY + 45, { steps: 12 });
  await page.mouse.up();
  await page.waitForTimeout(550);
  const afterOrbit = await canvas.screenshot({ path: path.join(OUT, "desktop-after-orbit.png") });
  const beforeOrbitHash = hash(beforeOrbit);
  const afterOrbitHash = hash(afterOrbit);
  assert.notEqual(beforeOrbitHash, afterOrbitHash, "Primary-pointer orbit did not visibly change the canvas");
  report.checks.mouseOrbitRenderChanged = { beforeOrbitHash, afterOrbitHash };

  const beforeWheel = hash(await canvas.screenshot());
  await page.mouse.move(startX, startY);
  await page.mouse.wheel(0, -420);
  await page.waitForTimeout(550);
  const afterWheel = hash(await canvas.screenshot({ path: path.join(OUT, "desktop-after-wheel.png") }));
  assert.notEqual(beforeWheel, afterWheel, "Wheel zoom did not visibly change the canvas");
  report.checks.wheelZoomRenderChanged = { beforeWheel, afterWheel };

  const backdropSelect = page.locator("label.field").filter({ hasText: "Backdrop" }).locator("select").first();
  const beforeBackdrop = hash(await canvas.screenshot());
  await backdropSelect.selectOption("void");
  await page.waitForTimeout(450);
  const afterBackdrop = hash(await canvas.screenshot({ path: path.join(OUT, "desktop-void.png") }));
  assert.notEqual(beforeBackdrop, afterBackdrop, "Backdrop change did not visibly change the canvas");
  await backdropSelect.selectOption("studio");
  report.checks.backdropRenderChanged = { beforeBackdrop, afterBackdrop };

  const viewMode = page.getByRole("group", { name: "View mode" });

  // BoneGroups consumer evidence: exercise the real live Skeleton view under
  // R3F, then prove its rendered pose changes while playback advances.
  await viewMode.getByRole("button", { name: "Skeleton", exact: true }).click();
  await page.waitForTimeout(450);
  const skeletonBeforeBuffer = await canvas.screenshot({
    path: path.join(OUT, "desktop-skeleton-before-play.png"),
  });
  const skeletonBeforeHash = hash(skeletonBeforeBuffer);

  const timeReadout = page.locator(".timeline__time").first();
  const timeBefore = await timeReadout.textContent();
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await page.waitForTimeout(650);
  const timeAfter = await timeReadout.textContent();
  const skeletonAfterBuffer = await canvas.screenshot({
    path: path.join(OUT, "desktop-skeleton-after-play.png"),
  });
  const skeletonAfterHash = hash(skeletonAfterBuffer);
  assert.notEqual(timeBefore, timeAfter, "Playback time did not advance");
  assert.notEqual(
    skeletonBeforeHash,
    skeletonAfterHash,
    "Skeleton/BoneGroups render did not visibly change while playback advanced",
  );
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  report.checks.playbackAdvanced = { before: timeBefore, after: timeAfter };
  report.checks.skeletonBoneGroupsRenderChanged = {
    beforeHash: skeletonBeforeHash,
    afterHash: skeletonAfterHash,
  };

  // FirstPartyTransformGizmo live render evidence. Select a real canonical bone
  // through the editor store, then clear it. This verifies the gizmo subtree is
  // mounted and visually active without pretending to replace the physical
  // drag/touch acceptance gate.
  const selectedBone = await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().selectBone("forearm_l");
    return useStudio.getState().selection.bone;
  });
  assert.equal(selectedBone, "forearm_l", "Could not select forearm_l for gizmo evidence");
  await page.waitForTimeout(300);
  const gizmoSelectedHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-gizmo-selected.png") }),
  );
  const clearedBone = await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().selectBone(null);
    return useStudio.getState().selection.bone;
  });
  assert.equal(clearedBone, null, "Could not clear bone selection after gizmo evidence");
  await page.waitForTimeout(300);
  const gizmoClearedHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-gizmo-cleared.png") }),
  );
  assert.notEqual(
    gizmoSelectedHash,
    gizmoClearedHash,
    "Selecting a bone did not visibly change the live gizmo/skeleton render",
  );
  report.checks.transformGizmoSelectionRenderChanged = {
    selectedBone,
    selectedHash: gizmoSelectedHash,
    clearedHash: gizmoClearedHash,
  };

  await viewMode.getByRole("button", { name: "Character", exact: true }).click();
  await page.waitForTimeout(450);
  const characterViewHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-character-after-skeleton.png") }),
  );
  assert.notEqual(
    characterViewHash,
    skeletonAfterHash,
    "Character and Skeleton views were byte-identical",
  );
  report.checks.viewModeRenderChanged = {
    skeletonHash: skeletonAfterHash,
    characterHash: characterViewHash,
  };

  // CharacterFigure and MuscleView consumer evidence. Use a bodyweight
  // exercise so equipment cannot account for the pixel difference, and sample
  // authored Start/Peak keyframes rather than relying on wall-clock playback.
  const exerciseSelect = page.locator("label.field").filter({ hasText: "Exercise" }).locator("select").first();
  await exerciseSelect.selectOption("air_squat");
  await page.waitForTimeout(450);

  const startKey = page.locator(".timeline__key.marker-start").first();
  const peakKey = page.locator(".timeline__key.marker-peak").first();
  assert((await startKey.count()) > 0, "No authored Start keyframe is available for consumer evidence");
  assert((await peakKey.count()) > 0, "No authored Peak keyframe is available for consumer evidence");

  await viewMode.getByRole("button", { name: "Character", exact: true }).click();
  await startKey.click();
  await page.waitForTimeout(350);
  const characterStartTime = await timeReadout.textContent();
  const characterStartHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-character-start.png") }),
  );
  await peakKey.click();
  await page.waitForTimeout(350);
  const characterPeakTime = await timeReadout.textContent();
  const characterPeakHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-character-peak.png") }),
  );
  assert.notEqual(characterStartTime, characterPeakTime, "Character Start and Peak resolved to the same time");
  assert.notEqual(
    characterStartHash,
    characterPeakHash,
    "CharacterFigure render was byte-identical at authored Start and Peak poses",
  );
  report.checks.characterFigureRenderAcrossAuthoredPoses = {
    exercise: "air_squat",
    startTime: characterStartTime,
    peakTime: characterPeakTime,
    startHash: characterStartHash,
    peakHash: characterPeakHash,
  };

  await viewMode.getByRole("button", { name: "Muscles", exact: true }).click();
  await startKey.click();
  await page.waitForTimeout(350);
  const musclesStartTime = await timeReadout.textContent();
  const musclesStartHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-muscles-start.png") }),
  );
  assert.notEqual(
    musclesStartHash,
    characterStartHash,
    "Muscles and Character Start views were byte-identical",
  );
  await peakKey.click();
  await page.waitForTimeout(350);
  const musclesPeakTime = await timeReadout.textContent();
  const musclesPeakHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-muscles-peak.png") }),
  );
  assert.notEqual(musclesStartTime, musclesPeakTime, "Muscles Start and Peak resolved to the same time");
  assert.notEqual(
    musclesStartHash,
    musclesPeakHash,
    "MuscleView render was byte-identical at authored Start and Peak poses",
  );
  report.checks.muscleViewRenderAcrossAuthoredPoses = {
    exercise: "air_squat",
    startTime: musclesStartTime,
    peakTime: musclesPeakTime,
    startHash: musclesStartHash,
    peakHash: musclesPeakHash,
  };

  await viewMode.getByRole("button", { name: "Character", exact: true }).click();
  await page.waitForTimeout(250);

  // EquipmentView consumer evidence. Keep the scene paused and toggle only
  // showEquipment so the pixel difference is attributable to that subtree.
  await exerciseSelect.selectOption("dumbbell_bicep_curl");
  await page.waitForTimeout(350);
  await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    const state = useStudio.getState();
    if (!state.showEquipment) state.toggle("showEquipment");
    state.pause();
  });
  await page.waitForTimeout(250);
  const equipmentVisibleHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-equipment-visible.png") }),
  );
  const equipmentHidden = await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().toggle("showEquipment");
    return useStudio.getState().showEquipment;
  });
  assert.equal(equipmentHidden, false, "Equipment visibility toggle did not hide equipment");
  await page.waitForTimeout(250);
  const equipmentHiddenHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-equipment-hidden.png") }),
  );
  assert.notEqual(
    equipmentVisibleHash,
    equipmentHiddenHash,
    "EquipmentView visibility toggle did not visibly change the rendered canvas",
  );
  const equipmentRestored = await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().toggle("showEquipment");
    return useStudio.getState().showEquipment;
  });
  assert.equal(equipmentRestored, true, "Equipment visibility was not restored after evidence capture");
  report.checks.equipmentViewVisibilityRenderChanged = {
    visibleHash: equipmentVisibleHash,
    hiddenHash: equipmentHiddenHash,
  };

  // IKHandles consumer evidence. Contact locks and editable IK are distinct:
  // create one temporary IK goal through the same store API the editor uses,
  // then toggle only showIkHandles.
  await exerciseSelect.selectOption("pull_up");
  await page.waitForTimeout(350);
  const ikEvidence = await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    const state = useStudio.getState();
    state.pause();
    state.setTime(0);
    if (!state.showIkHandles) state.toggle("showIkHandles");
    const start = state.document.clip.keyframes[0];
    const wasEnabled = Boolean(start?.ik.arm_l?.enabled);
    if (!wasEnabled) state.toggleIK("arm_l");
    const refreshed = useStudio.getState().document.clip.keyframes[0];
    return {
      time: refreshed.time,
      wasEnabled,
      enabled: Boolean(refreshed.ik.arm_l?.enabled),
      activeGoals: Object.entries(refreshed.ik)
        .filter(([, goal]) => goal?.enabled)
        .map(([chain]) => chain),
    };
  });
  assert(ikEvidence?.enabled, "Temporary arm_l IK goal was not enabled through the editor store");
  await page.waitForTimeout(350);
  const ikVisibleHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-ik-handles-visible.png") }),
  );
  const ikHidden = await page.evaluate(async () => {
    const { useStudio } = await import("/src/editor/store.ts");
    useStudio.getState().toggle("showIkHandles");
    return useStudio.getState().showIkHandles;
  });
  assert.equal(ikHidden, false, "IK handle visibility toggle did not hide handles");
  await page.waitForTimeout(250);
  const ikHiddenHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-ik-handles-hidden.png") }),
  );
  assert.notEqual(
    ikVisibleHash,
    ikHiddenHash,
    "IKHandles visibility toggle did not visibly change the rendered canvas",
  );
  const ikRestored = await page.evaluate(async (wasEnabled) => {
    const { useStudio } = await import("/src/editor/store.ts");
    const state = useStudio.getState();
    state.toggle("showIkHandles");
    if (!wasEnabled) state.toggleIK("arm_l");
    const refreshed = useStudio.getState();
    return {
      showIkHandles: refreshed.showIkHandles,
      ikEnabled: Boolean(refreshed.document.clip.keyframes[0]?.ik.arm_l?.enabled),
    };
  }, ikEvidence.wasEnabled);
  assert.equal(ikRestored.showIkHandles, true, "IK handle visibility was not restored after evidence capture");
  assert.equal(
    ikRestored.ikEnabled,
    ikEvidence.wasEnabled,
    "Temporary IK goal was not restored to its original enabled state",
  );
  report.checks.ikHandlesVisibilityRenderChanged = {
    time: ikEvidence.time,
    activeGoals: ikEvidence.activeGoals,
    visibleHash: ikVisibleHash,
    hiddenHash: ikHiddenHash,
  };

  await page.setViewportSize({ width: 780, height: 900 });
  await page.waitForTimeout(450);
  const resizedBox = await canvas.boundingBox();
  assert(resizedBox && resizedBox.width > 300 && resizedBox.height > 300, "Canvas became invalid after responsive resize");
  await canvas.screenshot({ path: path.join(OUT, "responsive-780x900.png") });
  report.checks.responsiveResize = resizedBox;

  // Real-WebGL evidence for the project-owned ThreeSceneHost. This is an
  // isolated second canvas, not a production host switch.
  const probeSetup = await page.evaluate(async () => {
    const container = document.createElement("div");
    container.dataset.hgptThreeHostContainer = "true";
    container.style.position = "fixed";
    container.style.right = "8px";
    container.style.bottom = "8px";
    container.style.width = "320px";
    container.style.height = "220px";
    container.style.zIndex = "9999";
    document.body.appendChild(container);
    const { mountBrowserThreeHostProbe } = await import("/scripts/browser-three-host-probe.js");
    const probe = mountBrowserThreeHostProbe(container);
    window.__hgptThreeHostProbe = probe;
    return {
      cssWidth: container.getBoundingClientRect().width,
      cssHeight: container.getBoundingClientRect().height,
    };
  });
  const probeCanvas = page.locator('canvas[data-hgpt-three-host-probe="true"]');
  await probeCanvas.waitFor({ state: "visible", timeout: 10_000 });
  await page.waitForTimeout(250);
  const probeStateBefore = await page.evaluate(() => window.__hgptThreeHostProbe?.getState());
  const probeBefore = hash(
    await probeCanvas.screenshot({ path: path.join(OUT, "first-party-host-before.png") }),
  );
  await page.waitForTimeout(500);
  const probeStateAfter = await page.evaluate(() => window.__hgptThreeHostProbe?.getState());
  const probeAfter = hash(
    await probeCanvas.screenshot({ path: path.join(OUT, "first-party-host-after.png") }),
  );
  assert.notEqual(
    probeBefore,
    probeAfter,
    "First-party ThreeSceneHost real-WebGL frame loop did not visibly advance",
  );
  assert(
    probeStateBefore && probeStateAfter,
    "First-party ThreeSceneHost did not expose renderer-neutral frame-driver state",
  );
  assert.notEqual(
    probeStateBefore.playbackTime,
    probeStateAfter.playbackTime,
    "Renderer-neutral playback time did not advance under the first-party host",
  );
  assert.notDeepEqual(
    probeStateBefore.forearmMatrix,
    probeStateAfter.forearmMatrix,
    "Real bicep-curl forearm pose did not advance under the first-party host",
  );

  const probeResize = await page.evaluate(async () => {
    const container = document.querySelector('[data-hgpt-three-host-container="true"]');
    const canvas = document.querySelector('canvas[data-hgpt-three-host-probe="true"]');
    if (!(container instanceof HTMLElement) || !(canvas instanceof HTMLCanvasElement)) {
      throw new Error("ThreeSceneHost probe DOM is missing");
    }
    const before = { width: canvas.width, height: canvas.height };
    container.style.width = "410px";
    container.style.height = "260px";
    await new Promise((resolve) => setTimeout(resolve, 350));
    return {
      before,
      after: { width: canvas.width, height: canvas.height },
      css: container.getBoundingClientRect().toJSON(),
    };
  });
  assert.notDeepEqual(
    probeResize.before,
    probeResize.after,
    "First-party ThreeSceneHost drawing buffer did not resize with its container",
  );
  report.checks.firstPartyThreeSceneHostRealWebgl = {
    initialCss: probeSetup,
    frameBeforeHash: probeBefore,
    frameAfterHash: probeAfter,
    frameDriverBefore: probeStateBefore,
    frameDriverAfter: probeStateAfter,
    resize: probeResize,
  };
  await page.evaluate(() => {
    window.__hgptThreeHostProbe?.dispose();
    delete window.__hgptThreeHostProbe;
    document.querySelector('[data-hgpt-three-host-container="true"]')?.remove();
  });

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
  fs.writeFileSync(path.join(OUT, "browser-smoke.json"), JSON.stringify(report, null, 2) + "\n");
}
