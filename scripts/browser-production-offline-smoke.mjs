#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { chromium } from "playwright";

const BASE_URL = process.env.HGPT_BROWSER_URL || "http://127.0.0.1:4174";
const BASE_ORIGIN = new URL(BASE_URL).origin;
const OUT = path.resolve("reports/browser-smoke/production-offline");
fs.mkdirSync(OUT, { recursive: true });

const report = {
  generatedAt: new Date().toISOString(),
  url: BASE_URL,
  productionBuild: true,
  status: "FAIL",
  supplementaryOnly: true,
  physicalDeviceGateClosed: false,
  finalOfflineGateClosed: false,
  note:
    "Automated production-dist evidence. It proves the built app runs locally, " +
    "uses the first-party renderer, validates a prompt on the clean fallback, " +
    "and attempts no external HTTP(S) request. It does not substitute for final " +
    "ORIGINAL-v1 packaging or real desktop/iPhone offline acceptance.",
  checks: {},
  consoleErrors: [],
  pageErrors: [],
  failedCriticalRequests: [],
  externalRequests: [],
};

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
  throw new Error(
    `Production preview did not become ready at ${BASE_URL}: ${lastError?.message ?? "unknown error"}`,
  );
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
  page.on("request", (request) => {
    const target = new URL(request.url());
    if (
      (target.protocol === "http:" || target.protocol === "https:") &&
      target.origin !== BASE_ORIGIN
    ) {
      report.externalRequests.push({
        url: request.url(),
        resourceType: request.resourceType(),
      });
    }
  });
  page.on("requestfailed", (request) => {
    if (["document", "script", "stylesheet"].includes(request.resourceType())) {
      report.failedCriticalRequests.push({
        url: request.url(),
        resourceType: request.resourceType(),
        error: request.failure()?.errorText ?? "request failed",
      });
    }
  });

  await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 30_000 });
  await page.waitForSelector('[data-hgpt-editor-shell="first-party"]', {
    state: "visible",
    timeout: 20_000,
  });
  await page.waitForSelector('[data-hgpt-scene-host="first-party"] canvas', {
    state: "visible",
    timeout: 20_000,
  });

  assert.equal(await page.locator(".toolbar__title").textContent(), "Home Gym PT");
  await page.waitForFunction(() => {
    const canvas = document.querySelector(
      '[data-hgpt-scene-host="first-party"] canvas',
    );
    return (
      canvas instanceof HTMLCanvasElement &&
      canvas.dataset.hgptRendererBackend === "home-gym-pt-webgl2" &&
      Number(canvas.dataset.hgptRendererFrame ?? "0") > 0 &&
      Number(canvas.dataset.hgptRendererDrawCount ?? "0") > 0
    );
  });

  const startup = await page.evaluate(() => {
    const canvas = document.querySelector(
      '[data-hgpt-scene-host="first-party"] canvas',
    );
    if (!(canvas instanceof HTMLCanvasElement)) {
      throw new Error("Production first-party canvas is unavailable");
    }
    return {
      rendererBackend: canvas.dataset.hgptRendererBackend ?? "",
      rendererFrame: Number(canvas.dataset.hgptRendererFrame ?? "0"),
      rendererDrawCount: Number(canvas.dataset.hgptRendererDrawCount ?? "0"),
      sceneChildren: Number(canvas.dataset.hgptSceneChildren ?? "0"),
      sceneNames: canvas.dataset.hgptSceneNames ?? "",
    };
  });
  assert.equal(startup.rendererBackend, "home-gym-pt-webgl2");
  assert(startup.rendererFrame > 0);
  assert(startup.rendererDrawCount > 0);
  assert(startup.sceneChildren > 0);
  assert(startup.sceneNames.length > 0);
  report.checks.productionStartup = startup;

  const rightTabs = page.locator(".studio__side--right .tabs").first();
  await rightTabs.getByRole("button", { name: "Generate", exact: true }).click();
  const panel = page.locator('[data-hgpt-panel="generate-first-party"]');
  await panel.waitFor({ state: "visible", timeout: 20_000 });
  await panel
    .locator('[data-hgpt-generate-control="prompt"]')
    .fill("Create a bodyweight squat with a slow tempo.");
  await panel.locator('[data-hgpt-generate-control="generate"]').click();

  await page.waitForFunction(
    () =>
      document.querySelector(
        '[data-hgpt-panel="generate-first-party"] .review-status strong',
      )?.textContent === "READY FOR REVIEW",
    undefined,
    { timeout: 120_000 },
  );

  const generation = await page.evaluate(() => {
    const panel = document.querySelector('[data-hgpt-panel="generate-first-party"]');
    if (!(panel instanceof HTMLElement)) {
      throw new Error("Production Generate panel is unavailable");
    }
    const cards = Array.from(panel.querySelectorAll(".review-gates article"));
    return {
      status: panel.querySelector(".review-status strong")?.textContent ?? null,
      note: panel.querySelector(".generate-candidate .panel__note")?.textContent ?? "",
      gateCount: cards.length,
      nonPassGates: cards
        .filter((card) => !card.classList.contains("is-pass"))
        .map((card) => card.textContent ?? ""),
      approveVisible:
        panel.querySelector('[data-hgpt-generate-control^="approve-"]') !== null,
      sourceVisible: panel.querySelector(".generate-source") !== null,
    };
  });
  assert.equal(generation.status, "READY FOR REVIEW");
  assert.match(generation.note, /Home Gym PT clean scaffold/);
  assert(generation.gateCount > 0, "Generated candidate emitted no validation gates");
  assert.deepEqual(generation.nonPassGates, []);
  assert.equal(generation.approveVisible, true);
  assert.equal(generation.sourceVisible, true);
  report.checks.productionPromptGeneration = generation;

  const canvas = page.locator('[data-hgpt-scene-host="first-party"] canvas');
  await canvas.screenshot({ path: path.join(OUT, "generated-squat.png") });

  assert.equal(report.pageErrors.length, 0, `Page errors: ${report.pageErrors.join(" | ")}`);
  assert.equal(
    report.failedCriticalRequests.length,
    0,
    `Critical request failures: ${JSON.stringify(report.failedCriticalRequests)}`,
  );
  assert.equal(
    report.externalRequests.length,
    0,
    `External browser requests: ${JSON.stringify(report.externalRequests)}`,
  );
  assert.equal(report.consoleErrors.length, 0, `Console errors: ${report.consoleErrors.join(" | ")}`);

  report.status = "PASS";
} catch (error) {
  report.failure = error instanceof Error ? error.stack ?? error.message : String(error);
  throw error;
} finally {
  if (browser) await browser.close();
  fs.writeFileSync(
    path.join(OUT, "browser-smoke-production.json"),
    JSON.stringify(report, null, 2) + "\n",
  );
}
