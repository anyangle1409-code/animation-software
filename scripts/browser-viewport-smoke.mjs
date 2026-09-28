#!/usr/bin/env node
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const URL = process.env.HGPT_BROWSER_URL || "http://127.0.0.1:5174";
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
      const response = await fetch(URL, { redirect: "manual" });
      if (response.ok) return;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await delay(250);
  }
  throw new Error(`Vite server did not become ready at ${URL}: ${lastError?.message ?? "unknown error"}`);
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

  // BoneGroups consumer evidence: exercise the real live Skeleton view under
  // R3F, then prove its rendered pose changes while playback advances.
  await page.getByRole("button", { name: "Skeleton", exact: true }).click();
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

  await page.getByRole("button", { name: "Character", exact: true }).click();
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

  // CharacterFigure consumer evidence: the clean procedural character must be
  // visibly posed by the live per-frame path while playback advances.
  const characterBeforeHash = characterViewHash;
  const characterTimeBefore = await timeReadout.textContent();
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await page.waitForTimeout(650);
  const characterTimeAfter = await timeReadout.textContent();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  const characterAfterHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-character-after-play.png") }),
  );
  assert.notEqual(characterTimeBefore, characterTimeAfter, "Playback time did not advance in Character view");
  assert.notEqual(
    characterBeforeHash,
    characterAfterHash,
    "CharacterFigure render did not visibly change while playback advanced",
  );
  report.checks.characterFigureRenderAdvanced = {
    beforeTime: characterTimeBefore,
    afterTime: characterTimeAfter,
    beforeHash: characterBeforeHash,
    afterHash: characterAfterHash,
  };

  // MuscleView consumer evidence: switch to the live muscles mode and require
  // both a distinct rendered view and visible per-frame change.
  await page.getByRole("button", { name: "Muscles", exact: true }).click();
  await page.waitForTimeout(450);
  const musclesBeforeHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-muscles-before-play.png") }),
  );
  assert.notEqual(
    musclesBeforeHash,
    characterAfterHash,
    "Muscles and Character views were byte-identical",
  );
  const musclesTimeBefore = await timeReadout.textContent();
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await page.waitForTimeout(650);
  const musclesTimeAfter = await timeReadout.textContent();
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  const musclesAfterHash = hash(
    await canvas.screenshot({ path: path.join(OUT, "desktop-muscles-after-play.png") }),
  );
  assert.notEqual(musclesTimeBefore, musclesTimeAfter, "Playback time did not advance in Muscles view");
  assert.notEqual(
    musclesBeforeHash,
    musclesAfterHash,
    "MuscleView render did not visibly change while playback advanced",
  );
  report.checks.muscleViewRenderAdvanced = {
    beforeTime: musclesTimeBefore,
    afterTime: musclesTimeAfter,
    beforeHash: musclesBeforeHash,
    afterHash: musclesAfterHash,
  };

  await page.getByRole("button", { name: "Character", exact: true }).click();
  await page.waitForTimeout(250);

  await page.setViewportSize({ width: 780, height: 900 });
  await page.waitForTimeout(450);
  const resizedBox = await canvas.boundingBox();
  assert(resizedBox && resizedBox.width > 300 && resizedBox.height > 300, "Canvas became invalid after responsive resize");
  await canvas.screenshot({ path: path.join(OUT, "responsive-780x900.png") });
  report.checks.responsiveResize = resizedBox;

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
