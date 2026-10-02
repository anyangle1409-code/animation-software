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
    "uses the first-party renderer, validates prompts on the clean fallback, " +
    "loads/plays/scrubs every registered library exercise, and attempts no external HTTP(S) request. " +
    "It does not substitute for final " +
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
  const discardCurrentCandidate = async () => {
    const discard = panel.locator('[data-hgpt-generate-control^="discard-"]').first();
    await discard.click();
    await page.waitForFunction(
      () =>
        document.querySelector(
          '[data-hgpt-panel="generate-first-party"] .review-status',
        ) === null,
      undefined,
      { timeout: 10_000 },
    );
  };
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
  await discardCurrentCandidate();

  // The product-level shorthand requested for normal use must drive the same
  // local deterministic pipeline, not a separate parser or hosted service.
  await panel
    .locator('[data-hgpt-generate-control="prompt"]')
    .fill("exercise: dumbbell shoulder press");
  await panel.locator('[data-hgpt-generate-control="generate"]').click();

  await page.waitForFunction(
    () =>
      document.querySelector(
        '[data-hgpt-panel="generate-first-party"] .review-status strong',
      )?.textContent === "READY FOR REVIEW",
    undefined,
    { timeout: 120_000 },
  );

  const commandGeneration = await page.evaluate(() => {
    const panel = document.querySelector('[data-hgpt-panel="generate-first-party"]');
    if (!(panel instanceof HTMLElement)) {
      throw new Error("Production Generate panel is unavailable for exercise command");
    }
    const cards = Array.from(panel.querySelectorAll(".review-gates article"));
    return {
      status: panel.querySelector(".review-status strong")?.textContent ?? null,
      note: panel.querySelector(".generate-candidate .panel__note")?.textContent ?? "",
      gateCount: cards.length,
      nonPassGates: cards
        .filter((card) => !card.classList.contains("is-pass"))
        .map((card) => card.textContent ?? ""),
      sourceVisible: panel.querySelector(".generate-source") !== null,
    };
  });
  assert.equal(commandGeneration.status, "READY FOR REVIEW");
  assert.match(commandGeneration.note, /Home Gym PT clean scaffold/);
  assert(commandGeneration.gateCount > 0, "Exercise command emitted no validation gates");
  assert.deepEqual(commandGeneration.nonPassGates, []);
  assert.equal(commandGeneration.sourceVisible, true);
  report.checks.productionExerciseCommand = commandGeneration;
  await discardCurrentCandidate();

  // Mobile keyboards commonly emit a smart apostrophe. The built production
  // app must normalise it through the same deterministic prompt path rather
  // than requiring ASCII-only exercise names.
  await panel
    .locator('[data-hgpt-generate-control="prompt"]')
    .fill("exercise: farmer’s walk");
  await panel.locator('[data-hgpt-generate-control="generate"]').click();

  await page.waitForFunction(
    () =>
      document.querySelector(
        '[data-hgpt-panel="generate-first-party"] .review-status strong',
      )?.textContent === "READY FOR REVIEW",
    undefined,
    { timeout: 120_000 },
  );

  const mobilePunctuationGeneration = await page.evaluate(() => {
    const panel = document.querySelector('[data-hgpt-panel="generate-first-party"]');
    if (!(panel instanceof HTMLElement)) {
      throw new Error("Production Generate panel is unavailable for mobile punctuation command");
    }
    const cards = Array.from(panel.querySelectorAll(".review-gates article"));
    return {
      status: panel.querySelector(".review-status strong")?.textContent ?? null,
      note: panel.querySelector(".generate-candidate .panel__note")?.textContent ?? "",
      gateCount: cards.length,
      nonPassGates: cards
        .filter((card) => !card.classList.contains("is-pass"))
        .map((card) => card.textContent ?? ""),
      sourceVisible: panel.querySelector(".generate-source") !== null,
    };
  });
  assert.equal(mobilePunctuationGeneration.status, "READY FOR REVIEW");
  assert.match(mobilePunctuationGeneration.note, /Farmer's Walk/);
  assert.match(mobilePunctuationGeneration.note, /Home Gym PT clean scaffold/);
  assert(mobilePunctuationGeneration.gateCount > 0, "Mobile punctuation command emitted no validation gates");
  assert.deepEqual(mobilePunctuationGeneration.nonPassGates, []);
  assert.equal(mobilePunctuationGeneration.sourceVisible, true);
  report.checks.productionMobilePunctuationCommand = mobilePunctuationGeneration;
  await discardCurrentCandidate();

  // Exercise-command integration must also cover the cable equipment path:
  // local parsing, first-party validation, generated source and UI equipment
  // reporting all have to agree in the built production bundle.
  await panel
    .locator('[data-hgpt-generate-control="prompt"]')
    .fill("exercise: cable triceps pushdown");
  await panel.locator('[data-hgpt-generate-control="generate"]').click();

  await page.waitForFunction(
    () =>
      document.querySelector(
        '[data-hgpt-panel="generate-first-party"] .review-status strong',
      )?.textContent === "READY FOR REVIEW",
    undefined,
    { timeout: 120_000 },
  );

  const cableGeneration = await page.evaluate(() => {
    const panel = document.querySelector('[data-hgpt-panel="generate-first-party"]');
    if (!(panel instanceof HTMLElement)) {
      throw new Error("Production Generate panel is unavailable for cable command");
    }
    const cards = Array.from(panel.querySelectorAll(".review-gates article"));
    const specValues = Array.from(panel.querySelectorAll(".spec-list dd"))
      .map((item) => item.textContent ?? "")
      .filter(Boolean);
    return {
      status: panel.querySelector(".review-status strong")?.textContent ?? null,
      note: panel.querySelector(".generate-candidate .panel__note")?.textContent ?? "",
      gateCount: cards.length,
      nonPassGates: cards
        .filter((card) => !card.classList.contains("is-pass"))
        .map((card) => card.textContent ?? ""),
      specValues,
      approveVisible:
        panel.querySelector('[data-hgpt-generate-control^="approve-"]') !== null,
      sourceVisible: panel.querySelector(".generate-source") !== null,
    };
  });
  assert.equal(cableGeneration.status, "READY FOR REVIEW");
  assert.match(cableGeneration.note, /Home Gym PT clean scaffold/);
  assert(cableGeneration.gateCount > 0, "Cable command emitted no validation gates");
  assert.deepEqual(cableGeneration.nonPassGates, []);
  assert(
    cableGeneration.specValues.includes("Cable station"),
    `Cable generation did not report cable equipment: ${JSON.stringify(cableGeneration.specValues)}`,
  );
  assert.equal(cableGeneration.approveVisible, true);
  assert.equal(cableGeneration.sourceVisible, true);
  report.checks.productionCableExerciseCommand = cableGeneration;
  await discardCurrentCandidate();

  // Unsupported biomechanics must be rejected locally and explained instead
  // of being guessed, silently approximated, or sent to a hosted AI service.
  await panel
    .locator('[data-hgpt-generate-control="prompt"]')
    .fill("Create a goblet squat.");
  await panel.locator('[data-hgpt-generate-control="generate"]').click();

  await page.waitForFunction(
    () =>
      document.querySelector(
        '[data-hgpt-panel="generate-first-party"] .review-status strong',
      )?.textContent === "NEEDS A DECISION",
    undefined,
    { timeout: 30_000 },
  );

  const rejection = await page.evaluate(() => {
    const panel = document.querySelector('[data-hgpt-panel="generate-first-party"]');
    if (!(panel instanceof HTMLElement)) {
      throw new Error("Production Generate panel is unavailable after rejection");
    }
    const issues = Array.from(panel.querySelectorAll(".generate-issues li"))
      .map((item) => item.textContent ?? "")
      .filter(Boolean);
    return {
      status: panel.querySelector(".review-status strong")?.textContent ?? null,
      issues,
      approveVisible:
        panel.querySelector('[data-hgpt-generate-control^="approve-"]') !== null,
      previewVisible:
        panel.querySelector('[data-hgpt-generate-control^="preview-"]') !== null,
      sourceVisible: panel.querySelector(".generate-source") !== null,
    };
  });
  assert.equal(rejection.status, "NEEDS A DECISION");
  assert(rejection.issues.length > 0, "Blocked prompt emitted no local explanation");
  assert(
    rejection.issues.some((issue) => /goblet|bodyweight|not certified/i.test(issue)),
    `Blocked prompt explanation was not specific: ${JSON.stringify(rejection.issues)}`,
  );
  assert.equal(rejection.approveVisible, false);
  assert.equal(rejection.previewVisible, false);
  assert.equal(rejection.sourceVisible, false);
  report.checks.productionUnsupportedPrompt = rejection;

  const canvas = page.locator('[data-hgpt-scene-host="first-party"] canvas');
  await canvas.screenshot({ path: path.join(OUT, "generated-squat.png") });

  // Supplement the source-level all-library regression suite with production-
  // bundle evidence that every registered exercise exposed in the toolbar can
  // actually be loaded, played and scrubbed through the first-party Studio UI.
  // This is deliberately interaction-level evidence only: it does not claim
  // that a headless browser replaces final desktop/iPhone visual acceptance.
  await discardCurrentCandidate();
  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();
  const exercisePanel = page.locator('[data-hgpt-panel="exercise-first-party"]');
  await exercisePanel.waitFor({ state: "visible", timeout: 20_000 });

  const toolbar = page.locator('[data-hgpt-toolbar="first-party"]');
  const exerciseSelect = toolbar.locator("select").first();
  const libraryOptions = await exerciseSelect.locator("option").evaluateAll((options) =>
    options
      .map((option) => ({
        value: option.value,
        label: option.textContent ?? "",
      }))
      .filter((option) => !option.label.startsWith("Candidate:")),
  );
  assert(libraryOptions.length > 0, "Production toolbar exposed no library exercises");
  assert.equal(
    new Set(libraryOptions.map((option) => option.value)).size,
    libraryOptions.length,
    "Production toolbar exposed duplicate library exercise ids",
  );

  const timeline = page.locator('[data-hgpt-timeline="first-party"]');
  await timeline.waitFor({ state: "visible", timeout: 20_000 });
  const timeReadout = timeline.locator(".timeline__time").first();
  const track = timeline.locator(".timeline__track");
  const libraryPlayback = [];

  for (const option of libraryOptions) {
    await exerciseSelect.selectOption(option.value);
    await page.waitForFunction(
      ({ expectedId, expectedName }) => {
        const select = document.querySelector(
          '[data-hgpt-toolbar="first-party"] select',
        );
        const title = document.querySelector(
          '[data-hgpt-panel="exercise-first-party"] h2',
        );
        return (
          select instanceof HTMLSelectElement &&
          select.value === expectedId &&
          title?.textContent === expectedName
        );
      },
      { expectedId: option.value, expectedName: option.label },
      { timeout: 10_000 },
    );

    const initialTime = await timeReadout.textContent();
    assert.match(
      initialTime ?? "",
      /^0\.00s \/ \d+(?:\.\d+)?s$/,
      `${option.value}: loading the exercise did not reset the timeline`,
    );

    const frameBefore = await canvas.evaluate((element) =>
      Number(element.dataset.hgptRendererFrame ?? "0"),
    );

    await timeline.getByRole("button", { name: "Play", exact: true }).click();
    await page.waitForFunction(
      () => {
        const readout = document.querySelector(
          '[data-hgpt-timeline="first-party"] .timeline__time',
        )?.textContent;
        return readout ? Number.parseFloat(readout) > 0.01 : false;
      },
      undefined,
      { timeout: 5_000 },
    );
    const advancedTime = await timeReadout.textContent();
    await timeline.getByRole("button", { name: "Pause", exact: true }).click();

    const scrubTime = await track.evaluate((element) => {
      const bounds = element.getBoundingClientRect();
      element.dispatchEvent(
        new PointerEvent("pointerdown", {
          bubbles: true,
          pointerId: 1,
          buttons: 1,
          clientX: bounds.left + bounds.width * 0.37,
          clientY: bounds.top + bounds.height * 0.5,
        }),
      );
      return element
        .closest('[data-hgpt-timeline="first-party"]')
        ?.querySelector(".timeline__time")
        ?.textContent ?? "";
    });
    const scrubSeconds = Number.parseFloat(scrubTime);
    assert(
      Number.isFinite(scrubSeconds) && scrubSeconds > 0,
      `${option.value}: midpoint scrub did not move the timeline`,
    );

    await page.waitForFunction(
      ({ before }) => {
        const element = document.querySelector(
          '[data-hgpt-scene-host="first-party"] canvas',
        );
        return (
          element instanceof HTMLCanvasElement &&
          Number(element.dataset.hgptRendererFrame ?? "0") > before &&
          Number(element.dataset.hgptRendererDrawCount ?? "0") > 0
        );
      },
      { before: frameBefore },
      { timeout: 5_000 },
    );

    const scene = await canvas.evaluate((element) => ({
      frame: Number(element.dataset.hgptRendererFrame ?? "0"),
      drawCount: Number(element.dataset.hgptRendererDrawCount ?? "0"),
      sceneChildren: Number(element.dataset.hgptSceneChildren ?? "0"),
    }));
    assert(scene.sceneChildren > 0, `${option.value}: rendered scene became empty`);

    libraryPlayback.push({
      id: option.value,
      name: option.label,
      advancedTime,
      scrubTime,
      ...scene,
    });
  }

  report.checks.productionLibraryExercisePlayback = {
    exerciseCount: libraryPlayback.length,
    exercises: libraryPlayback,
  };

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
