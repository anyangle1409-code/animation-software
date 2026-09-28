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
  await page.waitForSelector('[data-hgpt-editor-shell="first-party"]', {
    state: "visible",
    timeout: 20_000,
  });

  const liveEditorShell = await page.evaluate(() => {
    const root = document.getElementById("root");
    const shell = document.querySelector('[data-hgpt-editor-shell="first-party"]');
    const bridge = document.querySelector('[data-hgpt-react-bridge="editor-children"]');
    if (!(root instanceof HTMLElement) || !(shell instanceof HTMLElement)) {
      return { exists: false };
    }
    return {
      exists: true,
      shellParentIsRoot: shell.parentElement === root,
      rootChildCount: root.childElementCount,
      reactBridgeAbsent: bridge === null,
      slotCount: shell.querySelectorAll("[data-hgpt-editor-slot]").length,
      viewportSlotClass:
        shell.querySelector('[data-hgpt-editor-slot="viewport"]')?.classList.contains("studio__viewport-slot") ?? false,
    };
  });
  assert.equal(liveEditorShell.exists, true, "First-party editor shell is not live");
  assert.equal(liveEditorShell.shellParentIsRoot, true, "First-party editor shell is not mounted directly under #root");
  assert.equal(liveEditorShell.rootChildCount, 1, "#root should own only the first-party editor shell");
  assert.equal(liveEditorShell.reactBridgeAbsent, true, "Temporary React bridge remained after root removal");
  assert.equal(liveEditorShell.slotCount, 5, "First-party editor shell live slot count drifted");
  assert.equal(liveEditorShell.viewportSlotClass, true, "First-party viewport slot lost its layout boundary");
  report.checks.liveEditorShellOwnership = liveEditorShell;

  const keyboardBinding = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    const original = studioStore.getState();
    const restore = { time: original.time, playing: original.playing };
    original.pause();
    const duration = original.document.clip.duration;
    const fps = original.document.clip.fps;
    const start = Math.min(duration * 0.25, Math.max(0, duration - 2 / fps));
    original.setTime(start);
    const before = studioStore.getState().time;
    const event = new KeyboardEvent("keydown", {
      key: "ArrowRight",
      code: "ArrowRight",
      bubbles: true,
      cancelable: true,
    });
    const dispatchResult = window.dispatchEvent(event);
    const after = studioStore.getState();
    const result = {
      prevented: event.defaultPrevented || dispatchResult === false,
      before,
      after: after.time,
      expected: Math.min(duration, before + 1 / fps),
      playing: after.playing,
    };
    after.setTime(restore.time);
    if (restore.playing) after.play();
    else after.pause();
    return result;
  });
  assert.equal(keyboardBinding.prevented, true, "First-party keyboard binding did not consume ArrowRight");
  assert.equal(keyboardBinding.playing, false, "ArrowRight did not preserve pause-before-step behavior");
  assert(
    Math.abs(keyboardBinding.after - keyboardBinding.expected) < 1e-9,
    "First-party keyboard binding did not advance exactly one frame",
  );
  report.checks.firstPartyKeyboardBinding = keyboardBinding;

  const liveToolbarOwnership = await page.evaluate(() => {
    const shell = document.querySelector('[data-hgpt-editor-shell="first-party"]');
    const toolbarSlot = shell?.querySelector('[data-hgpt-editor-slot="toolbar"]');
    const toolbar = document.querySelector('[data-hgpt-toolbar="first-party"]');
    return {
      exists: toolbar instanceof HTMLElement,
      insideToolbarSlot:
        toolbar instanceof HTMLElement &&
        toolbarSlot instanceof HTMLElement &&
        toolbar.parentElement === toolbarSlot,
      toolbarCount: document.querySelectorAll(".toolbar").length,
      firstPartyToolbarCount: document.querySelectorAll('[data-hgpt-toolbar="first-party"]').length,
    };
  });
  assert.equal(liveToolbarOwnership.exists, true, "First-party Toolbar is not live");
  assert.equal(
    liveToolbarOwnership.insideToolbarSlot,
    true,
    "First-party Toolbar is not mounted in the project-owned toolbar slot",
  );
  assert.equal(liveToolbarOwnership.toolbarCount, 1, "Multiple live Toolbars are mounted");
  assert.equal(
    liveToolbarOwnership.firstPartyToolbarCount,
    1,
    "First-party Toolbar live ownership is ambiguous",
  );
  report.checks.liveToolbarOwnership = liveToolbarOwnership;

  const liveTimelineOwnership = await page.evaluate(() => {
    const shell = document.querySelector('[data-hgpt-editor-shell="first-party"]');
    const timelineSlot = shell?.querySelector('[data-hgpt-editor-slot="timeline"]');
    const timeline = document.querySelector('[data-hgpt-timeline="first-party"]');
    return {
      exists: timeline instanceof HTMLElement,
      insideTimelineSlot:
        timeline instanceof HTMLElement &&
        timelineSlot instanceof HTMLElement &&
        timeline.parentElement === timelineSlot,
      timelineCount: document.querySelectorAll(".timeline").length,
      firstPartyTimelineCount: document.querySelectorAll('[data-hgpt-timeline="first-party"]').length,
    };
  });
  assert.equal(liveTimelineOwnership.exists, true, "First-party Timeline is not live");
  assert.equal(
    liveTimelineOwnership.insideTimelineSlot,
    true,
    "First-party Timeline is not mounted in the project-owned timeline slot",
  );
  assert.equal(liveTimelineOwnership.timelineCount, 1, "Multiple live Timelines are mounted");
  assert.equal(
    liveTimelineOwnership.firstPartyTimelineCount,
    1,
    "First-party Timeline live ownership is ambiguous",
  );
  report.checks.liveTimelineOwnership = liveTimelineOwnership;

  await page.waitForFunction(() => {
    const canvas = document.querySelector(
      '[data-hgpt-editor-slot="viewport"] [data-hgpt-scene-host="first-party"] canvas',
    );
    return Number(canvas?.dataset.hgptFrameCount ?? "0") >= 2;
  });
  const liveViewportDom = await page.evaluate(() => {
    const slot = document.querySelector('[data-hgpt-editor-slot="viewport"]');
    const host = slot?.querySelector('[data-hgpt-scene-host="first-party"]');
    const canvas = host?.querySelector("canvas");
    if (!(slot instanceof HTMLElement) || !(host instanceof HTMLElement) || !(canvas instanceof HTMLCanvasElement)) {
      throw new Error("Live first-party viewport DOM is unavailable");
    }
    return {
      insideViewportSlot: host.parentElement === slot,
      hostCount: document.querySelectorAll('[data-hgpt-scene-host="first-party"]').length,
      canvasCount: host.querySelectorAll("canvas").length,
      hostStyle: {
        width: host.style.width,
        height: host.style.height,
        minHeight: host.style.minHeight,
        position: host.style.position,
      },
      canvasStyle: {
        display: canvas.style.display,
        width: canvas.style.width,
        height: canvas.style.height,
      },
      frameCount: Number(canvas.dataset.hgptFrameCount ?? "0"),
      rendererFrame: Number(canvas.dataset.hgptRendererFrame ?? "0"),
      sceneChildren: Number(canvas.dataset.hgptSceneChildren ?? "0"),
      sceneNames: canvas.dataset.hgptSceneNames ?? "",
    };
  });
  assert.equal(liveViewportDom.insideViewportSlot, true, "First-party viewport is outside the viewport slot");
  assert.equal(liveViewportDom.hostCount, 1, "Multiple live first-party viewport hosts are mounted");
  assert.equal(liveViewportDom.canvasCount, 1, "First-party viewport canvas ownership is ambiguous");
  assert.deepEqual(liveViewportDom.hostStyle, {
    width: "100%",
    height: "100%",
    minHeight: "0px",
    position: "relative",
  });
  assert.deepEqual(liveViewportDom.canvasStyle, {
    display: "block",
    width: "100%",
    height: "100%",
  });
  assert(liveViewportDom.frameCount >= 2, "Live first-party viewport frame loop did not advance");
  assert(liveViewportDom.rendererFrame > 0, "Live first-party WebGL renderer did not render");
  assert(liveViewportDom.sceneChildren > 0, "Live first-party viewport scene is empty");
  assert(liveViewportDom.sceneNames.length > 0, "Live first-party viewport emitted no scene names");
  report.checks.liveFirstPartyViewportDom = liveViewportDom;

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

  await rightTabs.getByRole("button", { name: "Export", exact: true }).click();
  await page.locator('[data-hgpt-panel="export-first-party"]').waitFor();
  const liveExportPanel = await page.evaluate(() => {
    const slot = document.querySelector('[data-hgpt-editor-slot="right-panel"]');
    const read = () => document.querySelector('[data-hgpt-panel="export-first-party"]');
    let panel = read();
    if (!(panel instanceof HTMLElement)) throw new Error("First-party Export panel is unavailable");

    const initial = {
      insideRightPanel: panel.parentElement === slot,
      panelCount: slot?.querySelectorAll(".panel").length ?? -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="export-first-party"]').length,
      heading: panel.querySelector("h2")?.textContent ?? null,
      sampleRate: panel.querySelector('[data-hgpt-export-control="sample-rate"]')?.value ?? null,
      includeEquipment:
        panel.querySelector('[data-hgpt-export-control="include-equipment"]')?.checked ?? null,
      actionLabels: Array.from(panel.querySelectorAll("button")).map((button) => button.textContent),
      status: panel.querySelector(".status")?.textContent ?? null,
    };

    const rate = panel.querySelector('[data-hgpt-export-control="sample-rate"]');
    if (!(rate instanceof HTMLSelectElement)) throw new Error("Export sample-rate control unavailable");
    rate.value = "60";
    rate.dispatchEvent(new Event("change", { bubbles: true }));

    panel = read();
    const equipment = panel?.querySelector('[data-hgpt-export-control="include-equipment"]');
    if (!(equipment instanceof HTMLInputElement)) throw new Error("Export equipment toggle unavailable");
    equipment.checked = false;
    equipment.dispatchEvent(new Event("change", { bubbles: true }));

    panel = read();
    return {
      ...initial,
      edited: {
        sampleRate:
          panel?.querySelector('[data-hgpt-export-control="sample-rate"]')?.value ?? null,
        includeEquipment:
          panel?.querySelector('[data-hgpt-export-control="include-equipment"]')?.checked ?? null,
      },
    };
  });
  assert.equal(liveExportPanel.insideRightPanel, true, "Export panel is outside its right slot");
  assert.equal(liveExportPanel.panelCount, 1, "Export tab has multiple live panels");
  assert.equal(liveExportPanel.firstPartyCount, 1, "First-party Export ownership is ambiguous");
  assert.equal(liveExportPanel.heading, "Export");
  assert.equal(liveExportPanel.sampleRate, "30");
  assert.equal(liveExportPanel.includeEquipment, true);
  assert.deepEqual(
    liveExportPanel.actionLabels,
    ["Export bicep_curl.glb", "GLB", "JSON", "Export dumbbell_bicep_curl.json"],
    "Export action labels drifted",
  );
  assert.equal(liveExportPanel.status, null);
  assert.deepEqual(
    liveExportPanel.edited,
    { sampleRate: "60", includeEquipment: false },
    "Export local options did not update",
  );

  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();
  assert.equal(
    await page.locator('[data-hgpt-panel="export-first-party"]').count(),
    0,
    "Export panel remained mounted after tab change",
  );

  await rightTabs.getByRole("button", { name: "Export", exact: true }).click();
  const remountedExport = await page.evaluate(() => {
    const panel = document.querySelector('[data-hgpt-panel="export-first-party"]');
    return {
      sampleRate:
        panel?.querySelector('[data-hgpt-export-control="sample-rate"]')?.value ?? null,
      includeEquipment:
        panel?.querySelector('[data-hgpt-export-control="include-equipment"]')?.checked ?? null,
      status: panel?.querySelector(".status")?.textContent ?? null,
    };
  });
  assert.deepEqual(
    remountedExport,
    { sampleRate: "30", includeEquipment: true, status: null },
    "Export mount-local defaults did not reset on remount",
  );
  report.checks.liveExportPanel = { ...liveExportPanel, remounted: remountedExport };
  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();

  const reviewStateBeforeLive = await page.evaluate(async () => {
    const [{ studioStore }, { characterStore }] = await Promise.all([
      import("/src/editor/storeCore.ts"),
      import("/src/editor/characterStoreCore.ts"),
    ]);
    const studio = studioStore.getState();
    const character = characterStore.getState();
    const before = {
      exerciseId: studio.document.exercise.id,
      selection: studio.selection,
      camera: studio.camera,
      time: studio.time,
      visualReview: studio.visualReview,
      correctivesPreview: character.correctivesPreview,
      sourceStatus: character.sourceStatus,
    };
    studioStore.getState().loadExercise("dumbbell_bicep_curl");
    studioStore.getState().selectBone(null);
    studioStore.getState().clearVisualReview();
    studioStore.getState().setCamera("recommended");
    studioStore.getState().setTime(0);
    characterStore.setState({
      correctivesPreview: true,
      sourceStatus: { kind: "idle" },
    });
    return before;
  });
  await rightTabs.getByRole("button", { name: "Review", exact: true }).click();
  await page.locator('[data-hgpt-panel="review-first-party"]').waitFor();
  const liveReviewPanel = await page.evaluate(async () => {
    const [{ studioStore }, { characterStore }] = await Promise.all([
      import("/src/editor/storeCore.ts"),
      import("/src/editor/characterStoreCore.ts"),
    ]);
    const read = () => {
      const slot = document.querySelector('[data-hgpt-editor-slot="right-panel"]');
      const panel = document.querySelector('[data-hgpt-panel="review-first-party"]');
      if (!(panel instanceof HTMLElement)) throw new Error("First-party Review panel is unavailable");
      return { slot, panel };
    };

    let { slot, panel } = read();
    const initial = {
      insideRightPanel: panel.parentElement === slot,
      panelCount: slot?.querySelectorAll(".panel").length ?? -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="review-first-party"]').length,
      heading: panel.querySelector("h2")?.textContent ?? null,
      status: panel.querySelector(".review-status strong")?.textContent ?? null,
      gateCount: panel.querySelectorAll(".review-gates article").length,
      movementRows: panel.querySelectorAll(".joint-motion-diagnostic .spec-list > *").length,
      signoffText: panel.querySelector('[data-hgpt-review-control="visual-signoff"]')?.textContent ?? null,
      signoffDisabled:
        panel.querySelector('[data-hgpt-review-control="visual-signoff"]')?.disabled ?? null,
    };

    const signoff = panel.querySelector('[data-hgpt-review-control="visual-signoff"]');
    if (!(signoff instanceof HTMLButtonElement)) throw new Error("Review sign-off control unavailable");
    signoff.click();

    ({ panel } = read());
    const signed = {
      status: panel.querySelector(".review-status strong")?.textContent ?? null,
      button: panel.querySelector('[data-hgpt-review-control="visual-signoff"]')?.textContent ?? null,
      active: panel.querySelector('[data-hgpt-review-control="visual-signoff"]')?.classList.contains("is-active") ?? false,
      documentMatches: studioStore.getState().visualReview?.document === studioStore.getState().document,
    };

    const focus = panel.querySelector('[data-hgpt-review-control="focus"]');
    if (!(focus instanceof HTMLButtonElement)) throw new Error("Review focus control unavailable");
    focus.click();
    const focused = {
      bone: studioStore.getState().selection.bone,
      camera: studioStore.getState().camera,
    };

    studioStore.getState().regenerate();
    ({ panel } = read());
    const invalidated = {
      status: panel.querySelector(".review-status strong")?.textContent ?? null,
      button: panel.querySelector('[data-hgpt-review-control="visual-signoff"]')?.textContent ?? null,
    };

    characterStore.getState().setCorrectivesPreview(false);
    ({ panel } = read());
    const rawSkinning = {
      disabled:
        panel.querySelector('[data-hgpt-review-control="visual-signoff"]')?.disabled ?? null,
      note: Array.from(panel.querySelectorAll(".panel__note"))
        .some((item) => item.textContent?.includes("Enable Correctives on")),
    };
    characterStore.getState().setCorrectivesPreview(true);

    return { ...initial, signed, focused, invalidated, rawSkinning };
  });
  assert.equal(liveReviewPanel.insideRightPanel, true, "Review panel is outside its right slot");
  assert.equal(liveReviewPanel.panelCount, 1, "Review tab has multiple live panels");
  assert.equal(liveReviewPanel.firstPartyCount, 1, "First-party Review ownership is ambiguous");
  assert.equal(liveReviewPanel.heading, "Review");
  assert.equal(liveReviewPanel.status, "READY FOR VISUAL REVIEW");
  assert(liveReviewPanel.gateCount > 0, "Review panel rendered no automated gates");
  assert(liveReviewPanel.movementRows > 0, "Review panel rendered no movement diagnostics");
  assert.equal(liveReviewPanel.signoffText, "Mark visual review passed");
  assert.equal(liveReviewPanel.signoffDisabled, false);
  assert.deepEqual(
    liveReviewPanel.signed,
    {
      status: "APPROVED",
      button: "Clear visual sign-off",
      active: true,
      documentMatches: true,
    },
    "Review visual sign-off did not preserve exact document identity semantics",
  );
  assert.deepEqual(
    liveReviewPanel.focused,
    { bone: "forearm_l", camera: "focus" },
    "Review focus locator did not route selection/camera state",
  );
  assert.deepEqual(
    liveReviewPanel.invalidated,
    { status: "READY FOR VISUAL REVIEW", button: "Mark visual review passed" },
    "Review sign-off was not invalidated by a document edit",
  );
  assert.deepEqual(
    liveReviewPanel.rawSkinning,
    { disabled: true, note: true },
    "Review allowed production sign-off while raw skinning was active",
  );
  report.checks.liveReviewPanel = liveReviewPanel;

  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();
  assert.equal(
    await page.locator('[data-hgpt-panel="review-first-party"]').count(),
    0,
    "Review panel remained mounted after tab change",
  );
  await page.evaluate(async (before) => {
    const [{ studioStore }, { characterStore }] = await Promise.all([
      import("/src/editor/storeCore.ts"),
      import("/src/editor/characterStoreCore.ts"),
    ]);
    studioStore.getState().loadExercise(before.exerciseId);
    studioStore.setState({
      selection: before.selection,
      camera: before.camera,
      time: before.time,
      visualReview: before.visualReview,
    });
    characterStore.setState({
      correctivesPreview: before.correctivesPreview,
      sourceStatus: before.sourceStatus,
    });
  }, reviewStateBeforeLive);

  const contactsTab = leftTabs.getByRole("button", { name: "Contacts", exact: true });
  await contactsTab.click();
  const liveContactPanel = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    const slot = document.querySelector('[data-hgpt-editor-slot="left-panel"]');
    const panel = document.querySelector('[data-hgpt-panel="contacts-first-party"]');
    if (!(panel instanceof HTMLElement)) throw new Error("First-party Contact panel is unavailable");

    const before = studioStore.getState();
    const documentBefore = before.document;
    const historyBefore = before.history;
    const firstLock = before.document.clip.locks[0];
    const firstCheckbox = panel.querySelector('input[type="checkbox"]');
    if (!firstLock || !(firstCheckbox instanceof HTMLInputElement)) {
      throw new Error("Contact toggle probe requires at least one live lock");
    }

    firstCheckbox.checked = !firstLock.enabled;
    firstCheckbox.dispatchEvent(new Event("change", { bubbles: true }));
    const after = studioStore.getState();
    const editedLock = after.document.clip.locks.find((lock) => lock.id === firstLock.id);
    const toggleProbe = {
      changed: editedLock?.enabled === !firstLock.enabled,
      historyAdvanced: after.history.past.length === historyBefore.past.length + 1,
    };

    studioStore.setState({ document: documentBefore, history: historyBefore });

    return {
      exists: true,
      insideLeftPanel: slot instanceof HTMLElement && panel.parentElement === slot,
      panelCount: slot instanceof HTMLElement ? slot.querySelectorAll(".panel").length : -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="contacts-first-party"]').length,
      heading: panel.querySelector("h2")?.textContent ?? null,
      note: panel.querySelector(".panel__note")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
      cardCount: panel.querySelectorAll(".contact-card").length,
      firstStatus: panel.querySelector(".contact-card__head strong")?.textContent ?? null,
      toggleProbe,
    };
  });
  assert.equal(liveContactPanel.exists, true, "First-party Contact panel is not live");
  assert.equal(liveContactPanel.insideLeftPanel, true, "Contact panel is outside the left-panel slot");
  assert.equal(liveContactPanel.panelCount, 1, "Contacts tab has multiple live panel surfaces");
  assert.equal(liveContactPanel.firstPartyCount, 1, "First-party Contact ownership is ambiguous");
  assert.equal(liveContactPanel.heading, "Contacts");
  assert(liveContactPanel.note?.includes("Live production-solver inspection"), "Contact live note did not render");
  assert(liveContactPanel.cardCount > 0, "Contact panel rendered no diagnostics");
  assert(liveContactPanel.firstStatus, "Contact panel rendered no diagnostic status");
  assert.deepEqual(
    liveContactPanel.toggleProbe,
    { changed: true, historyAdvanced: true },
    "Contact checkbox did not preserve the existing lock-edit/history behavior",
  );
  report.checks.liveContactPanel = liveContactPanel;
  await leftTabs.getByRole("button", { name: "Joint", exact: true }).click();
  assert.equal(
    await page.locator('[data-hgpt-panel="contacts-first-party"]').count(),
    0,
    "Detached Contact panel remained mounted after left-tab change",
  );
  const liveExercisePanel = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    const slot = document.querySelector('[data-hgpt-editor-slot="right-panel"]');
    const panel = document.querySelector('[data-hgpt-panel="exercise-first-party"]');
    if (!(panel instanceof HTMLElement)) throw new Error("First-party Exercise panel is unavailable");

    const before = studioStore.getState();
    const documentBefore = before.document;
    const historyBefore = before.history;
    const validationBefore = before.validation;
    const originalTempo = before.document.exercise.tempo.eccentric;
    const originalClosure = before.document.exercise.hands.closure;

    const snapshot = {
      exists: true,
      insideRightPanel: slot instanceof HTMLElement && panel.parentElement === slot,
      panelCount: slot instanceof HTMLElement ? slot.querySelectorAll(".panel").length : -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="exercise-first-party"]').length,
      heading: panel.querySelector("h2")?.textContent ?? null,
      tempoCount: panel.querySelectorAll('.tempo-grid input[type="number"]').length,
      muscleCount: panel.querySelectorAll(".muscle-list li").length,
      specCount: panel.querySelectorAll(".spec-list > *").length,
      equipmentCount: panel.querySelectorAll(".plain-list li").length,
      closureLabel: panel.querySelector('input[aria-label="Grip closure"]')?.getAttribute("aria-label") ?? null,
    };

    const tempoInput = panel.querySelector('.tempo-grid input[type="number"]');
    if (!(tempoInput instanceof HTMLInputElement)) throw new Error("Exercise tempo input is unavailable");
    const nextTempo = originalTempo >= 9.9 ? originalTempo - 0.1 : originalTempo + 0.1;
    tempoInput.value = String(nextTempo);
    tempoInput.dispatchEvent(new Event("input", { bubbles: true }));
    const afterTempo = studioStore.getState();
    const tempoProbe = {
      changed: Math.abs(afterTempo.document.exercise.tempo.eccentric - nextTempo) < 1e-9,
      historyAdvanced: afterTempo.history.past.length === historyBefore.past.length + 1,
    };

    const refreshedPanel = document.querySelector('[data-hgpt-panel="exercise-first-party"]');
    const closureInput = refreshedPanel?.querySelector('input[aria-label="Grip closure"]');
    if (!(closureInput instanceof HTMLInputElement)) throw new Error("Exercise grip-closure input is unavailable");
    const nextClosure = originalClosure >= 0.95 ? originalClosure - 0.05 : originalClosure + 0.05;
    closureInput.value = String(nextClosure);
    closureInput.dispatchEvent(new Event("input", { bubbles: true }));
    const afterClosure = studioStore.getState();
    const closureProbe = {
      changed: Math.abs(afterClosure.document.exercise.hands.closure - nextClosure) < 1e-9,
      historyAdvanced: afterClosure.history.past.length === historyBefore.past.length + 2,
    };

    studioStore.setState({
      document: documentBefore,
      history: historyBefore,
      validation: validationBefore,
    });

    return { ...snapshot, tempoProbe, closureProbe };
  });
  assert.equal(liveExercisePanel.exists, true, "First-party Exercise panel is not live");
  assert.equal(liveExercisePanel.insideRightPanel, true, "Exercise panel is outside the right-panel slot");
  assert.equal(liveExercisePanel.panelCount, 1, "Exercise tab has multiple live panel surfaces");
  assert.equal(liveExercisePanel.firstPartyCount, 1, "First-party Exercise ownership is ambiguous");
  assert(liveExercisePanel.heading, "Exercise heading did not render");
  assert.equal(liveExercisePanel.tempoCount, 4, "Exercise panel lost tempo controls");
  assert(liveExercisePanel.muscleCount > 0, "Exercise panel rendered no muscle metadata");
  assert.equal(liveExercisePanel.specCount, 10, "Exercise grip/stance specification rows drifted");
  assert(liveExercisePanel.equipmentCount > 0, "Exercise panel rendered no equipment/bodyweight entry");
  assert.equal(liveExercisePanel.closureLabel, "Grip closure");
  assert.deepEqual(
    liveExercisePanel.tempoProbe,
    { changed: true, historyAdvanced: true },
    "Exercise tempo input did not preserve the existing regeneration/history behavior",
  );
  assert.deepEqual(
    liveExercisePanel.closureProbe,
    { changed: true, historyAdvanced: true },
    "Exercise grip closure did not preserve the existing regeneration/history behavior",
  );
  report.checks.liveExercisePanel = liveExercisePanel;

  await reviewTab.click();
  assert.equal(
    await page.locator('[data-hgpt-panel="exercise-first-party"]').count(),
    0,
    "Detached Exercise panel remained mounted after right-tab change",
  );
  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();
  const ikTab = leftTabs.getByRole("button", { name: "IK & locks", exact: true });
  await ikTab.click();
  const liveIkPanel = await page.evaluate(async () => {
    const [{ studioStore }, { sampleClip }] = await Promise.all([
      import("/src/editor/storeCore.ts"),
      import("/src/animation/clip.ts"),
    ]);

    studioStore.getState().loadExercise("dumbbell_bicep_curl");
    studioStore.getState().setTime(0);
    studioStore.getState().selectHandle(null);

    const before = studioStore.getState();
    const documentBefore = before.document;
    const historyBefore = before.history;
    const selectionBefore = before.selection;
    const showIkHandlesBefore = before.showIkHandles;

    const readPanel = () => {
      const slot = document.querySelector('[data-hgpt-editor-slot="left-panel"]');
      const panel = document.querySelector('[data-hgpt-panel="ik-first-party"]');
      if (!(panel instanceof HTMLElement)) throw new Error("First-party IK panel is unavailable");
      return { slot, panel };
    };

    let { slot, panel } = readPanel();
    const initial = {
      exists: true,
      insideLeftPanel: slot instanceof HTMLElement && panel.parentElement === slot,
      panelCount: slot instanceof HTMLElement ? slot.querySelectorAll(".panel").length : -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="ik-first-party"]').length,
      heading: panel.querySelector("h2")?.textContent ?? null,
      chainCount: panel.querySelectorAll("[data-hgpt-ik-chain]").length,
      activeHandleCount: panel.querySelectorAll("[data-hgpt-ik-handle]").length,
      lockCount: panel.querySelectorAll("[data-hgpt-lock-id]").length,
    };

    const showHandles = panel.querySelector('[data-hgpt-ik-control="show-handles"]');
    if (!(showHandles instanceof HTMLInputElement)) throw new Error("IK viewport visibility checkbox unavailable");
    showHandles.click();
    const visibilityChanged = studioStore.getState().showIkHandles === !showIkHandlesBefore;

    ({ panel } = readPanel());
    const chainInputs = Array.from(panel.querySelectorAll("[data-hgpt-ik-toggle]"))
      .filter((input) => input instanceof HTMLInputElement);
    const chainInput = chainInputs.find((input) => !input.checked) ?? chainInputs[0];
    if (!(chainInput instanceof HTMLInputElement)) throw new Error("IK chain toggle unavailable");
    const chainId = chainInput.dataset.hgptIkToggle;
    if (!chainId) throw new Error("IK chain id missing");
    const enabledBefore = Boolean(sampleClip(studioStore.getState().document.clip, 0).ik[chainId]?.enabled);
    chainInput.click();
    const enabledAfter = Boolean(sampleClip(studioStore.getState().document.clip, 0).ik[chainId]?.enabled);
    const chainToggleProbe = {
      changed: enabledAfter === !enabledBefore,
      historyAdvanced: studioStore.getState().history.past.length === historyBefore.past.length + 1,
    };

    if (!enabledAfter) {
      ({ panel } = readPanel());
      const reenable = panel.querySelector(`[data-hgpt-ik-toggle="${chainId}"]`);
      if (!(reenable instanceof HTMLInputElement)) throw new Error("IK chain re-enable probe unavailable");
      reenable.click();
    }

    ({ panel } = readPanel());
    const target = panel.querySelector(`[data-hgpt-ik-handle="${chainId}-target"]`);
    if (!(target instanceof HTMLButtonElement)) throw new Error("IK target selection probe unavailable after enabling chain");
    target.click();
    const targetSelected =
      studioStore.getState().selection.handle?.chain === chainId &&
      studioStore.getState().selection.handle?.kind === "target";

    studioStore.setState({
      document: documentBefore,
      history: historyBefore,
      selection: selectionBefore,
      showIkHandles: showIkHandlesBefore,
    });

    ({ panel } = readPanel());
    const lockInput = panel.querySelector("[data-hgpt-lock-id]");
    if (!(lockInput instanceof HTMLInputElement)) throw new Error("IK lock checkbox probe unavailable");
    const lockId = lockInput.dataset.hgptLockId;
    if (!lockId) throw new Error("IK lock id missing");
    const lockBefore = studioStore.getState().document.clip.locks.find((lock) => lock.id === lockId);
    if (!lockBefore) throw new Error("IK lock state unavailable");
    lockInput.click();
    const afterLock = studioStore.getState();
    const lockAfter = afterLock.document.clip.locks.find((lock) => lock.id === lockId);
    const lockProbe = {
      changed: lockAfter?.enabled === !lockBefore.enabled,
      historyAdvanced: afterLock.history.past.length === historyBefore.past.length + 1,
    };

    studioStore.setState({
      document: documentBefore,
      history: historyBefore,
      selection: selectionBefore,
      showIkHandles: showIkHandlesBefore,
    });

    return {
      ...initial,
      visibilityChanged,
      targetSelected,
      chainToggleProbe,
      lockProbe,
    };
  });
  assert.equal(liveIkPanel.exists, true, "First-party IK panel is not live");
  assert.equal(liveIkPanel.insideLeftPanel, true, "IK panel is outside the left-panel slot");
  assert.equal(liveIkPanel.panelCount, 1, "IK tab has multiple live panel surfaces");
  assert.equal(liveIkPanel.firstPartyCount, 1, "First-party IK ownership is ambiguous");
  assert.equal(liveIkPanel.heading, "Inverse kinematics");
  assert.equal(liveIkPanel.chainCount, 4, "IK panel lost chain controls");
  assert(liveIkPanel.lockCount > 0, "IK panel rendered no lock controls");
  assert.equal(liveIkPanel.visibilityChanged, true, "IK viewport-handle toggle did not route to the Studio store");
  assert.equal(liveIkPanel.targetSelected, true, "IK target button did not route handle selection");
  assert.deepEqual(
    liveIkPanel.chainToggleProbe,
    { changed: true, historyAdvanced: true },
    "IK chain toggle did not preserve the existing edit/history behavior",
  );
  assert.deepEqual(
    liveIkPanel.lockProbe,
    { changed: true, historyAdvanced: true },
    "IK lock checkbox did not preserve the existing edit/history behavior",
  );
  report.checks.liveIkPanel = liveIkPanel;
  await leftTabs.getByRole("button", { name: "Joint", exact: true }).click();
  assert.equal(
    await page.locator('[data-hgpt-panel="ik-first-party"]').count(),
    0,
    "Detached IK panel remained mounted after left-tab change",
  );
  const equipmentPanelTab = leftTabs.getByRole("button", { name: "Equipment", exact: true });
  await equipmentPanelTab.click();

  const liveEquipmentPanel = await page.evaluate(async () => {
    const [{ studioStore }, { EQUIPMENT_LIBRARY }] = await Promise.all([
      import("/src/editor/storeCore.ts"),
      import("/src/equipment/library.ts"),
    ]);
    const originalExerciseId = studioStore.getState().document.exercise.id;
    const originalSelection = studioStore.getState().selection;

    studioStore.getState().loadExercise("pull_up");
    const initialState = studioStore.getState();
    const staticInstance = initialState.document.exercise.equipment.instances
      .find((item) => item.attachment.mode === "static");
    if (!staticInstance) throw new Error("Live Equipment probe requires static equipment");
    studioStore.getState().selectEquipment(staticInstance.id);

    const readPanel = () => {
      const slot = document.querySelector('[data-hgpt-editor-slot="left-panel"]');
      const panel = document.querySelector('[data-hgpt-panel="equipment-first-party"]');
      if (!(panel instanceof HTMLElement)) throw new Error("First-party Equipment panel is unavailable");
      return { slot, panel };
    };

    let { slot, panel } = readPanel();
    const beforeEdit = studioStore.getState();
    const documentBefore = beforeEdit.document;
    const historyBefore = beforeEdit.history;
    const initial = {
      exists: true,
      insideLeftPanel: slot instanceof HTMLElement && panel.parentElement === slot,
      panelCount: slot instanceof HTMLElement ? slot.querySelectorAll(".panel").length : -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="equipment-first-party"]').length,
      heading: panel.querySelector("h2")?.textContent ?? null,
      equipmentCount: panel.querySelectorAll(".equipment-list > button").length,
      objectFieldCount: panel.querySelectorAll('[data-hgpt-equipment-field^="position-"], [data-hgpt-equipment-field^="rotation-"]').length,
      socketCount: panel.querySelectorAll("[data-hgpt-socket-id]").length,
    };

    const positionX = panel.querySelector('[data-hgpt-equipment-field="position-x"]');
    if (!(positionX instanceof HTMLInputElement)) throw new Error("Equipment object position editor unavailable");
    const originalX = staticInstance.position.x;
    const nextCm = originalX * 100 + 1;
    positionX.value = String(nextCm);
    positionX.dispatchEvent(new Event("input", { bubbles: true }));
    const afterObject = studioStore.getState();
    const editedObject = afterObject.document.exercise.equipment.instances.find(
      (item) => item.id === staticInstance.id,
    );
    const objectProbe = {
      changed: Math.abs((editedObject?.position.x ?? NaN) - nextCm / 100) < 1e-9,
      historyAdvanced: afterObject.history.past.length === historyBefore.past.length + 1,
    };

    studioStore.setState({ document: documentBefore, history: historyBefore });
    studioStore.getState().selectEquipment(staticInstance.id);

    ({ panel } = readPanel());
    const socketButton = panel.querySelector("[data-hgpt-socket-id]");
    if (!(socketButton instanceof HTMLButtonElement)) throw new Error("Equipment socket selection unavailable");
    const socketId = socketButton.dataset.hgptSocketId;
    if (!socketId) throw new Error("Equipment socket id missing");
    socketButton.click();
    const socketSelected = studioStore.getState().selection.socketId === socketId;

    ({ panel } = readPanel());
    const socketPositionX = panel.querySelector('[data-hgpt-equipment-field="socket-position-x"]');
    if (!(socketPositionX instanceof HTMLInputElement)) throw new Error("Equipment socket position editor unavailable");
    const socketBefore = Number(socketPositionX.value);
    socketPositionX.value = String(socketBefore + 1);
    socketPositionX.dispatchEvent(new Event("input", { bubbles: true }));
    const afterSocket = studioStore.getState();
    const socketProbe = {
      historyAdvanced: afterSocket.history.past.length === historyBefore.past.length + 1,
      hasOverride: Boolean(
        afterSocket.document.exercise.equipment.instances
          .find((item) => item.id === staticInstance.id)
          ?.socketOverrides?.[socketId],
      ),
    };

    ({ panel } = readPanel());
    const reset = panel.querySelector('[data-hgpt-socket-reset]');
    if (!(reset instanceof HTMLButtonElement)) throw new Error("Equipment socket reset unavailable");
    reset.click();
    const afterReset = studioStore.getState();
    const resetProbe = {
      historyAdvanced: afterReset.history.past.length === historyBefore.past.length + 2,
      overrideCleared:
        afterReset.document.exercise.equipment.instances
          .find((item) => item.id === staticInstance.id)
          ?.socketOverrides?.[socketId] === undefined,
    };

    studioStore.getState().loadExercise(originalExerciseId);
    studioStore.setState({ selection: originalSelection });

    return {
      ...initial,
      objectProbe,
      socketSelected,
      socketProbe,
      resetProbe,
      definitionSocketCount: EQUIPMENT_LIBRARY[staticInstance.kind].sockets.length,
    };
  });

  assert.equal(liveEquipmentPanel.exists, true, "First-party Equipment panel is not live");
  assert.equal(liveEquipmentPanel.insideLeftPanel, true, "Equipment panel is outside the left-panel slot");
  assert.equal(liveEquipmentPanel.panelCount, 1, "Equipment tab has multiple live panel surfaces");
  assert.equal(liveEquipmentPanel.firstPartyCount, 1, "First-party Equipment ownership is ambiguous");
  assert.equal(liveEquipmentPanel.heading, "Equipment");
  assert(liveEquipmentPanel.equipmentCount > 0, "Equipment panel rendered no equipment instances");
  assert.equal(liveEquipmentPanel.objectFieldCount, 6, "Equipment static object editors drifted");
  assert.equal(
    liveEquipmentPanel.socketCount,
    liveEquipmentPanel.definitionSocketCount,
    "Equipment socket list drifted from the selected definition",
  );
  assert.deepEqual(
    liveEquipmentPanel.objectProbe,
    { changed: true, historyAdvanced: true },
    "Equipment object transform did not preserve existing edit/history behavior",
  );
  assert.equal(liveEquipmentPanel.socketSelected, true, "Equipment socket selection did not route to Studio state");
  assert.deepEqual(
    liveEquipmentPanel.socketProbe,
    { historyAdvanced: true, hasOverride: true },
    "Equipment socket transform did not preserve existing edit/history behavior",
  );
  assert.deepEqual(
    liveEquipmentPanel.resetProbe,
    { historyAdvanced: true, overrideCleared: true },
    "Equipment socket reset did not preserve existing edit/history behavior",
  );
  report.checks.liveEquipmentPanel = liveEquipmentPanel;

  await leftTabs.getByRole("button", { name: "Joint", exact: true }).click();
  assert.equal(
    await page.locator('[data-hgpt-panel="equipment-first-party"]').count(),
    0,
    "Detached Equipment panel remained mounted after left-tab change",
  );

  await leftTabs.getByRole("button", { name: "Character", exact: true }).evaluate((button) => button.click());
  const liveCharacterPanel = await page.evaluate(async () => {
    const { characterStore } = await import("/src/editor/characterStoreCore.ts");
    const slot = document.querySelector('[data-hgpt-editor-slot="left-panel"]');
    const panel = document.querySelector('[data-hgpt-panel="character-first-party"]');
    if (!(panel instanceof HTMLElement)) throw new Error("First-party Character panel is unavailable");
    const bind = panel.querySelector('[data-hgpt-character-control="bind-mode"]');
    const input = panel.querySelector('[data-hgpt-character-control="file"]');
    if (!(bind instanceof HTMLSelectElement) || !(input instanceof HTMLInputElement)) {
      throw new Error("Character bind/import controls are unavailable");
    }
    const before = characterStore.getState().bindMode;
    bind.value = before === "preserve" ? "rebind" : "preserve";
    bind.dispatchEvent(new Event("change", { bubbles: true }));
    const bindRouted = characterStore.getState().bindMode === bind.value;
    characterStore.getState().setBindMode(before);
    return {
      insideLeftPanel: panel.parentElement === slot,
      panelCount: slot?.querySelectorAll(".panel").length ?? -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="character-first-party"]').length,
      heading: panel.querySelector("h2")?.textContent,
      sourceCount: panel.querySelector('[data-hgpt-character-control="source"]')?.querySelectorAll("option").length ?? 0,
      importAccept: input.accept,
      bindRouted,
    };
  });
  assert.equal(liveCharacterPanel.insideLeftPanel, true, "Character panel is outside the left-panel slot");
  assert.equal(liveCharacterPanel.panelCount, 1, "Character tab has multiple live panel surfaces");
  assert.equal(liveCharacterPanel.firstPartyCount, 1, "First-party Character ownership is ambiguous");
  assert.equal(liveCharacterPanel.heading, "Character");
  assert(liveCharacterPanel.sourceCount > 0, "Character source selector is empty");
  assert.equal(liveCharacterPanel.importAccept, ".glb,.gltf,model/gltf-binary");
  assert.equal(liveCharacterPanel.bindRouted, true, "Character bind mode did not route to its store");
  report.checks.liveCharacterPanel = liveCharacterPanel;
  await leftTabs.getByRole("button", { name: "Joint", exact: true }).evaluate((button) => button.click());
  assert.equal(await page.locator('[data-hgpt-panel="character-first-party"]').count(), 0,
    "Detached Character panel remained mounted after left-tab change");

  const liveJointPanel = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    const slot = document.querySelector('[data-hgpt-editor-slot="left-panel"]');
    const panel = document.querySelector('[data-hgpt-panel="joint-first-party"]');
    if (!(panel instanceof HTMLElement)) throw new Error("First-party Joint panel is unavailable");
    const stateBefore = studioStore.getState();
    const documentBefore = stateBefore.document;
    const historyBefore = stateBefore.history;
    const selectionBefore = stateBefore.selection;
    const read = () => document.querySelector('[data-hgpt-panel="joint-first-party"]');
    const bone = panel.querySelector('[data-hgpt-joint-control="bone"]');
    if (!(bone instanceof HTMLSelectElement)) throw new Error("Joint bone selector unavailable");
    bone.value = "forearm_l";
    bone.dispatchEvent(new Event("change", { bubbles: true }));
    const selected = studioStore.getState().selection.bone === "forearm_l";
    const axis = read()?.querySelector('[data-hgpt-joint-control="axis-x-number"]');
    if (!(axis instanceof HTMLInputElement)) throw new Error("Joint axis editor unavailable");
    axis.value = "35";
    axis.dispatchEvent(new Event("change", { bubbles: true }));
    const axisProbe = {
      value: read()?.querySelector('[data-hgpt-joint-control="axis-x-number"]')?.value,
      historyAdvanced: studioStore.getState().history.past.length === historyBefore.past.length + 1,
    };
    const fingerToggle = read()?.querySelector('[data-hgpt-joint-control="fingers"]');
    if (!(fingerToggle instanceof HTMLInputElement)) throw new Error("Joint finger toggle unavailable");
    const optionsBefore = read()?.querySelector('[data-hgpt-joint-control="bone"]')?.options.length ?? 0;
    fingerToggle.click();
    const optionsAfter = read()?.querySelector('[data-hgpt-joint-control="bone"]')?.options.length ?? 0;
    const result = {
      insideLeftPanel: panel.parentElement === slot,
      panelCount: slot?.querySelectorAll(".panel").length ?? -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="joint-first-party"]').length,
      heading: read()?.querySelector("h2")?.textContent,
      selected,
      axisProbe,
      fingersExpanded: optionsAfter > optionsBefore,
      diagnosticCount: read()?.querySelectorAll(".joint-motion-diagnostic .spec-list dt").length ?? 0,
      timingPresent: read()?.querySelector('[data-hgpt-joint-control="custom-timing"]') instanceof HTMLInputElement,
    };
    studioStore.setState({ document: documentBefore, history: historyBefore, selection: selectionBefore });
    return result;
  });
  assert.equal(liveJointPanel.insideLeftPanel, true, "Joint panel is outside the left-panel slot");
  assert.equal(liveJointPanel.panelCount, 1, "Joint tab has multiple live panel surfaces");
  assert.equal(liveJointPanel.firstPartyCount, 1, "First-party Joint ownership is ambiguous");
  assert.equal(liveJointPanel.heading, "Joint");
  assert.equal(liveJointPanel.selected, true, "Joint bone selection did not route to Studio state");
  assert.deepEqual(liveJointPanel.axisProbe, { value: "35", historyAdvanced: true },
    "Joint axis edit did not preserve value/history behavior");
  assert.equal(liveJointPanel.fingersExpanded, true, "Joint finger visibility did not expand bone choices");
  assert(liveJointPanel.diagnosticCount > 0, "Joint motion diagnostics are missing");
  assert.equal(liveJointPanel.timingPresent, true, "Joint segment timing control is missing");
  report.checks.liveJointPanel = liveJointPanel;
  await leftTabs.getByRole("button", { name: "Character", exact: true }).evaluate((button) => button.click());
  assert.equal(await page.locator('[data-hgpt-panel="joint-first-party"]').count(), 0,
    "Detached Joint panel remained mounted after left-tab change");

  await leftTabs.getByRole("button", { name: "Grip", exact: true }).evaluate((button) => button.click());
  const liveGripPanel = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    const slot = document.querySelector('[data-hgpt-editor-slot="left-panel"]');
    const panel = document.querySelector('[data-hgpt-panel="grip-first-party"]');
    if (!(panel instanceof HTMLElement)) throw new Error("First-party Grip panel is unavailable");
    const before = studioStore.getState();
    const read = () => document.querySelector('[data-hgpt-panel="grip-first-party"]');
    studioStore.getState().loadExercise("dumbbell_bicep_curl");
    const closure = read()?.querySelector('[data-hgpt-grip-control="closure"]');
    if (!(closure instanceof HTMLInputElement)) throw new Error("Grip closure editor unavailable");
    closure.value = "0.7";
    closure.dispatchEvent(new Event("change", { bubbles: true }));
    const globalClosure = studioStore.getState().document.exercise.hands.closure;
    const digit = read()?.querySelector('[data-hgpt-grip-control="digit-thumb"]');
    if (!(digit instanceof HTMLInputElement)) throw new Error("Grip digit editor unavailable");
    digit.value = "0.8";
    digit.dispatchEvent(new Event("change", { bubbles: true }));
    const digitClosure = studioStore.getState().document.exercise.hands.digitClosure?.thumb;
    const offset = read()?.querySelector('[data-hgpt-grip-control$="-offset-x"]');
    if (!(offset instanceof HTMLInputElement)) throw new Error("Grip handle offset editor unavailable");
    const offsetId = offset.dataset.hgptGripControl.slice(0, -"-offset-x".length);
    offset.value = "3";
    offset.dispatchEvent(new Event("change", { bubbles: true }));
    const oneHand = studioStore.getState().document.exercise.equipment.instances.find((item) => item.id === offsetId);
    const offsetMetres = oneHand?.attachment.mode === "hand" ? oneHand.attachment.gripOffset?.x : null;
    studioStore.getState().loadExercise("cable_triceps_pushdown");
    const twoHandCount = read()?.querySelectorAll(".grip-fit").length ?? 0;
    const result = {
      insideLeftPanel: panel.parentElement === slot,
      panelCount: slot?.querySelectorAll(".panel").length ?? -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="grip-first-party"]').length,
      heading: read()?.querySelector("h2")?.textContent,
      globalClosure,
      digitClosure,
      offsetMetres,
      twoHandCount,
      widthControl: read()?.querySelector('[data-hgpt-grip-control$="-width"]') instanceof HTMLInputElement,
    };
    studioStore.setState(before);
    return result;
  });
  assert.equal(liveGripPanel.insideLeftPanel, true, "Grip panel is outside the left-panel slot");
  assert.equal(liveGripPanel.panelCount, 1, "Grip tab has multiple live panel surfaces");
  assert.equal(liveGripPanel.firstPartyCount, 1, "First-party Grip ownership is ambiguous");
  assert.equal(liveGripPanel.heading, "Grip");
  assert.equal(liveGripPanel.globalClosure, 0.7, "Grip global closure did not route to Studio state");
  assert.equal(liveGripPanel.digitClosure, 0.8, "Grip digit closure did not route to Studio state");
  assert(Math.abs(liveGripPanel.offsetMetres - 0.003) < 1e-9, "Grip handle offset did not route to Studio state");
  assert(liveGripPanel.twoHandCount > 0, "Grip two-hand fit diagnostics are missing");
  assert.equal(liveGripPanel.widthControl, true, "Grip two-hand width editor is missing");
  report.checks.liveGripPanel = liveGripPanel;
  await leftTabs.getByRole("button", { name: "Character", exact: true }).evaluate((button) => button.click());
  assert.equal(await page.locator('[data-hgpt-panel="grip-first-party"]').count(), 0,
    "Detached Grip panel remained mounted after left-tab change");

  const validationBeforeTechnique = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    return studioStore.getState().validation;
  });
  assert.equal(
    validationBeforeTechnique,
    null,
    "Technique validation ran while the Technique tab was inactive",
  );

  const techniqueTab = rightTabs.getByRole("button", { name: "Technique", exact: true });
  await techniqueTab.click();
  await page.waitForTimeout(260);

  const liveTechniquePanel = await page.evaluate(() => {
    const slot = document.querySelector('[data-hgpt-editor-slot="right-panel"]');
    const panel = document.querySelector('[data-hgpt-panel="technique-first-party"]');
    return {
      exists: panel instanceof HTMLElement,
      insideRightPanel:
        panel instanceof HTMLElement &&
        slot instanceof HTMLElement &&
        panel.parentElement === slot,
      panelCount:
        slot instanceof HTMLElement ? slot.querySelectorAll(".panel").length : -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="technique-first-party"]').length,
      heading: panel?.querySelector("h2")?.textContent ?? null,
      status: panel?.querySelector(".status")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
      ruleCount: panel?.querySelectorAll(".rule-list > li").length ?? 0,
      commonErrorCount: panel?.querySelectorAll(".error-list > li").length ?? 0,
    };
  });

  assert.equal(liveTechniquePanel.exists, true, "First-party Technique panel is not live");
  assert.equal(
    liveTechniquePanel.insideRightPanel,
    true,
    "First-party Technique panel is not mounted in the right-panel slot",
  );
  assert.equal(liveTechniquePanel.panelCount, 1, "Technique tab has multiple live panel surfaces");
  assert.equal(liveTechniquePanel.firstPartyCount, 1, "First-party Technique ownership is ambiguous");
  assert.equal(liveTechniquePanel.heading, "Technique");
  assert(liveTechniquePanel.status, "First-party Technique validation status did not render");
  assert(liveTechniquePanel.ruleCount > 0, "First-party Technique rendered no rules");
  report.checks.liveTechniquePanel = liveTechniquePanel;
  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();
  const inactiveTechniqueValidation = await page.evaluate(async () => {
    const [{ studioStore }, { EXERCISES }] = await Promise.all([
      import("/src/editor/storeCore.ts"),
      import("/src/exercises/library.ts"),
    ]);
    const currentId = studioStore.getState().document.exercise.id;
    const next = EXERCISES.find((exercise) => exercise.id !== currentId);
    if (!next) throw new Error("No alternate exercise for Technique lifecycle probe");
    studioStore.getState().loadExercise(next.id);
    return { currentId, nextId: next.id };
  });
  await page.waitForTimeout(180);
  const validationWhileInactive = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    return studioStore.getState().validation;
  });
  assert.equal(
    validationWhileInactive,
    null,
    "Detached Technique panel continued validating after tab change",
  );
  await page.evaluate(async ({ exerciseId }) => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    studioStore.getState().loadExercise(exerciseId);
  }, { exerciseId: inactiveTechniqueValidation.currentId });

  const musclesTab = rightTabs.getByRole("button", { name: "Muscles", exact: true });
  await musclesTab.click();
  await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    studioStore.getState().pause();
  });

  const liveMusclePanel = await page.evaluate(() => {
    const slot = document.querySelector('[data-hgpt-editor-slot="right-panel"]');
    const panel = document.querySelector('[data-hgpt-panel="muscles-first-party"]');
    const activeOnly = panel?.querySelector('input[type="checkbox"]');
    const region = panel?.querySelector("select");
    return {
      exists: panel instanceof HTMLElement,
      insideRightPanel:
        panel instanceof HTMLElement &&
        slot instanceof HTMLElement &&
        panel.parentElement === slot,
      panelCount:
        slot instanceof HTMLElement ? slot.querySelectorAll(".panel").length : -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="muscles-first-party"]').length,
      heading: panel?.querySelector("h2")?.textContent ?? null,
      diagnosticCount: panel?.querySelectorAll(".muscle-diagnostic").length ?? 0,
      activeOnly: activeOnly instanceof HTMLInputElement ? activeOnly.checked : null,
      region: region instanceof HTMLSelectElement ? region.value : null,
    };
  });
  assert.equal(liveMusclePanel.exists, true, "First-party Muscle panel is not live");
  assert.equal(
    liveMusclePanel.insideRightPanel,
    true,
    "First-party Muscle panel is not mounted in the right-panel slot",
  );
  assert.equal(liveMusclePanel.panelCount, 1, "Muscles tab has multiple live panel surfaces");
  assert.equal(liveMusclePanel.firstPartyCount, 1, "First-party Muscle ownership is ambiguous");
  assert.equal(liveMusclePanel.heading, "Muscle diagnostics");
  assert(liveMusclePanel.diagnosticCount > 0, "First-party Muscle panel rendered no diagnostics");
  assert.equal(liveMusclePanel.activeOnly, false, "Muscle active-only filter did not start at the React default");
  assert.equal(liveMusclePanel.region, "all", "Muscle region filter did not start at the React default");

  const filteredMusclePanel = await page.evaluate(() => {
    const panel = document.querySelector('[data-hgpt-panel="muscles-first-party"]');
    const activeOnly = panel?.querySelector('input[type="checkbox"]');
    const region = panel?.querySelector("select");
    if (!(activeOnly instanceof HTMLInputElement) || !(region instanceof HTMLSelectElement)) {
      throw new Error("Muscle filters are unavailable");
    }
    const initialCount = panel?.querySelectorAll(".muscle-diagnostic").length ?? 0;
    activeOnly.checked = true;
    activeOnly.dispatchEvent(new Event("change", { bubbles: true }));
    const activeCount = panel?.querySelectorAll(".muscle-diagnostic").length ?? 0;
    activeOnly.checked = false;
    activeOnly.dispatchEvent(new Event("change", { bubbles: true }));
    region.value = "arms";
    region.dispatchEvent(new Event("change", { bubbles: true }));
    const armsCount = panel?.querySelectorAll(".muscle-diagnostic").length ?? 0;
    return { initialCount, activeCount, armsCount };
  });
  assert(
    filteredMusclePanel.activeCount < filteredMusclePanel.initialCount,
    "Active-only Muscle filter did not reduce the visible diagnostic set",
  );
  assert(
    filteredMusclePanel.armsCount > 0 &&
      filteredMusclePanel.armsCount < filteredMusclePanel.initialCount,
    "Muscle region filter did not isolate a subset",
  );

  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();
  assert.equal(
    await page.locator('[data-hgpt-panel="muscles-first-party"]').count(),
    0,
    "Detached Muscle panel remained mounted after tab change",
  );
  await musclesTab.click();
  const remountedMuscleFilters = await page.evaluate(() => {
    const panel = document.querySelector('[data-hgpt-panel="muscles-first-party"]');
    const activeOnly = panel?.querySelector('input[type="checkbox"]');
    const region = panel?.querySelector("select");
    return {
      activeOnly: activeOnly instanceof HTMLInputElement ? activeOnly.checked : null,
      region: region instanceof HTMLSelectElement ? region.value : null,
    };
  });
  assert.deepEqual(
    remountedMuscleFilters,
    { activeOnly: false, region: "all" },
    "Muscle panel local filters did not reset on remount",
  );
  report.checks.liveMusclePanel = {
    ...liveMusclePanel,
    ...filteredMusclePanel,
    remountedMuscleFilters,
  };
  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();

  const compareTab = rightTabs.getByRole("button", { name: "Compare", exact: true });
  await compareTab.click();

  const liveComparisonInitial = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    studioStore.getState().clearComparison();
    studioStore.getState().selectBone(null);
    const state = studioStore.getState();
    const panel = document.querySelector('[data-hgpt-panel="compare-first-party"]');
    const slot = document.querySelector('[data-hgpt-editor-slot="right-panel"]');
    return {
      exists: panel instanceof HTMLElement,
      insideRightPanel:
        panel instanceof HTMLElement &&
        slot instanceof HTMLElement &&
        panel.parentElement === slot,
      panelCount: slot instanceof HTMLElement ? slot.querySelectorAll(".panel").length : -1,
      historyPast: state.history.past.length,
      historyFuture: state.history.future.length,
      exerciseId: state.document.exercise.id,
      keyframes: state.document.clip.keyframes.length,
    };
  });
  assert.equal(liveComparisonInitial.exists, true, "First-party Comparison panel is not live");
  assert.equal(liveComparisonInitial.insideRightPanel, true, "Comparison panel is outside the right slot");
  assert.equal(liveComparisonInitial.panelCount, 1, "Compare tab has multiple live panel surfaces");

  await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    studioStore.getState().setTime(0);
  });
  await page.getByRole("button", { name: "Capture A", exact: true }).click();
  await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    const duration = studioStore.getState().document.clip.duration;
    studioStore.getState().setTime(duration * 0.5);
  });
  await page.getByRole("button", { name: "Capture B", exact: true }).click();
  await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    studioStore.getState().selectBone("forearm_l");
  });

  const liveComparisonCaptured = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    const panel = document.querySelector('[data-hgpt-panel="compare-first-party"]');
    const state = studioStore.getState();
    return {
      svgCount: panel?.querySelectorAll(".comparison-card__diagram").length ?? 0,
      lineCounts: Array.from(panel?.querySelectorAll(".comparison-card__diagram") ?? []).map(
        (svg) => svg.querySelectorAll("line").length,
      ),
      delta: panel?.querySelector(".comparison-delta")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
      historyPast: state.history.past.length,
      historyFuture: state.history.future.length,
      exerciseId: state.document.exercise.id,
      keyframes: state.document.clip.keyframes.length,
    };
  });
  assert.equal(liveComparisonCaptured.svgCount, 2, "Comparison did not render both pose diagrams");
  assert(liveComparisonCaptured.lineCounts.every((count) => count > 0), "Comparison pose diagram is empty");
  assert(liveComparisonCaptured.delta?.includes("Forearm (L) angles"), "Comparison joint delta did not render");
  assert.deepEqual(
    {
      historyPast: liveComparisonCaptured.historyPast,
      historyFuture: liveComparisonCaptured.historyFuture,
      exerciseId: liveComparisonCaptured.exerciseId,
      keyframes: liveComparisonCaptured.keyframes,
    },
    {
      historyPast: liveComparisonInitial.historyPast,
      historyFuture: liveComparisonInitial.historyFuture,
      exerciseId: liveComparisonInitial.exerciseId,
      keyframes: liveComparisonInitial.keyframes,
    },
    "Comparison capture changed document/history state",
  );

  await page.getByRole("button", { name: "Clear both", exact: true }).click();
  const comparisonCleared = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    return studioStore.getState().comparison;
  });
  assert.deepEqual(comparisonCleared, { a: null, b: null }, "Comparison clear did not clear both snapshots");
  report.checks.liveComparisonPanel = {
    ...liveComparisonInitial,
    ...liveComparisonCaptured,
  };
  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).click();
  assert.equal(
    await page.locator('[data-hgpt-panel="compare-first-party"]').count(),
    0,
    "Detached Comparison panel remained mounted after tab change",
  );

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

  const correctiveViewBefore = await page.evaluate(async () => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    const before = studioStore.getState().viewMode;
    studioStore.getState().setViewMode("character");
    return before;
  });
  await page.waitForFunction(async () => {
    const { characterStore } = await import("/src/editor/characterStoreCore.ts");
    return Boolean(characterStore.getState().active);
  });
  await rightTabs.getByRole("button", { name: "Correctives", exact: true }).evaluate((button) => button.click());
  await page.locator('[data-hgpt-editor-slot="right-panel"] .corrective-panel').waitFor();
  const liveCorrectives = await page.evaluate(async () => {
    const [{ characterStore }, { studioStore }] = await Promise.all([
      import("/src/editor/characterStoreCore.ts"),
      import("/src/editor/storeCore.ts"),
    ]);
    const slot = document.querySelector('[data-hgpt-editor-slot="right-panel"]');
    const read = () => document.querySelector('[data-hgpt-panel="correctives-first-party"]');
    const panel = read();
    if (!(panel instanceof HTMLElement)) throw new Error("First-party Correctives panel is unavailable");
    const initial = {
      insideRightPanel: panel.parentElement === slot,
      panelCount: slot?.querySelectorAll(".panel").length ?? -1,
      firstPartyCount: document.querySelectorAll('[data-hgpt-panel="correctives-first-party"]').length,
      heading: panel.querySelector("h2")?.textContent,
      scanEnabled: panel.querySelector('[data-hgpt-corrective-control="scan"]')?.disabled === false,
      strainCount: panel.querySelectorAll(".strain-list .strain-card").length,
    };
    const playheadBefore = studioStore.getState().time;
    panel.querySelector('[data-hgpt-corrective-control="scan"]')?.click();
    const scanned = {
      cards: read()?.querySelectorAll(".strain-list .strain-card").length ?? 0,
      timeRestored: studioStore.getState().time === playheadBefore,
      worstPoint: read()?.textContent.includes("Worst P99"),
    };
    read()?.querySelector('[data-hgpt-corrective-control="raw"]')?.click();
    const rawRouted = characterStore.getState().correctivesPreview === false;
    const rawSelected = read()?.querySelector('[data-hgpt-corrective-control="raw"]')?.classList.contains("is-active");
    read()?.querySelector('[data-hgpt-corrective-control="on"]')?.click();
    const restored = characterStore.getState().correctivesPreview === true;
    return { ...initial, scanned, rawRouted, rawSelected, restored };
  });
  assert.equal(liveCorrectives.insideRightPanel, true, "Correctives panel is outside its right slot");
  assert.equal(liveCorrectives.panelCount, 1, "Correctives tab has multiple live panels");
  assert.equal(liveCorrectives.firstPartyCount, 1, "First-party Correctives ownership is ambiguous");
  assert.equal(liveCorrectives.heading, "Correctives");
  assert.equal(liveCorrectives.scanEnabled, true, "Correctives scan is unavailable for an active character");
  assert(liveCorrectives.strainCount > 0, "Correctives live strain diagnostics are empty");
  assert(liveCorrectives.scanned.cards > liveCorrectives.strainCount, "Correctives scan omitted whole-rep results");
  assert.equal(liveCorrectives.scanned.timeRestored, true, "Correctives scan changed the playhead");
  assert.equal(liveCorrectives.scanned.worstPoint, true, "Correctives scan omitted worst-point locators");
  assert.equal(liveCorrectives.rawRouted, true, "Raw skinning preview did not route to character state");
  assert.equal(liveCorrectives.rawSelected, true, "Raw skinning selection did not rerender");
  assert.equal(liveCorrectives.restored, true, "Correctives preview was not restored");
  report.checks.liveCorrectives = liveCorrectives;
  await rightTabs.getByRole("button", { name: "Exercise", exact: true }).evaluate((button) => button.click());
  assert.equal(await page.locator('[data-hgpt-panel="correctives-first-party"]').count(), 0,
    "Correctives panel remained mounted after tab change");
  await page.evaluate(async (previous) => {
    const { studioStore } = await import("/src/editor/storeCore.ts");
    studioStore.getState().setViewMode(previous);
  }, correctiveViewBefore);

  const firstPartyToolbarDom = await page.evaluate(async () => {
    const [{ createStudioToolbarDom }, { studioStore }] = await Promise.all([
      import("/src/editor/toolbarDom.ts"),
      import("/src/editor/storeCore.ts"),
    ]);

    const original = studioStore.getState();
    const originalState = {
      exerciseId: original.document.exercise.id,
      viewMode: original.viewMode,
      backdrop: original.backdrop,
      camera: original.camera,
    };

    const toolbar = createStudioToolbarDom(document, studioStore);
    toolbar.element.style.position = "fixed";
    toolbar.element.style.left = "-10000px";
    toolbar.element.style.top = "0";
    document.body.append(toolbar.element);

    const viewLabels = Object.values(toolbar.controls.viewModes).map(
      (button) => button.textContent,
    );
    const initialExerciseOptions = Array.from(toolbar.controls.exerciseSelect.options).map(
      (option) => option.textContent,
    );
    const initial = {
      title: toolbar.element.querySelector(".toolbar__title")?.textContent ?? null,
      subtitle: toolbar.element.querySelector(".toolbar__subtitle")?.textContent ?? null,
      viewLabels,
      initialExerciseOptionCount: initialExerciseOptions.length,
      undoDisabled: toolbar.controls.undo.disabled,
      redoDisabled: toolbar.controls.redo.disabled,
    };

    toolbar.controls.viewModes.skeleton.click();
    toolbar.controls.backdropSelect.value = "void";
    toolbar.controls.backdropSelect.dispatchEvent(new Event("change", { bubbles: true }));
    toolbar.controls.cameraSelect.value = "front";
    toolbar.controls.cameraSelect.dispatchEvent(new Event("change", { bubbles: true }));
    const cameraAfterDirectSelect = studioStore.getState().camera;
    toolbar.controls.exerciseSelect.value = "air_squat";
    toolbar.controls.exerciseSelect.dispatchEvent(new Event("change", { bubbles: true }));

    const routed = studioStore.getState();
    const routedState = {
      exerciseId: routed.document.exercise.id,
      viewMode: routed.viewMode,
      backdrop: routed.backdrop,
      camera: routed.camera,
    };

    const candidate = {
      ...routed.document.exercise,
      id: "hgpt_toolbar_probe_candidate",
      name: "Toolbar Probe Candidate",
    };
    studioStore.getState().loadDefinition(candidate);
    const candidateLabel = toolbar.controls.exerciseSelect.options[0]?.textContent ?? null;

    toolbar.controls.regenerate.click();
    const undoEnabledAfterRegenerate = !toolbar.controls.undo.disabled;
    toolbar.controls.undo.click();
    const redoEnabledAfterUndo = !toolbar.controls.redo.disabled;

    studioStore.getState().loadExercise(originalState.exerciseId);
    studioStore.getState().setViewMode(originalState.viewMode);
    studioStore.getState().setBackdrop(originalState.backdrop);
    studioStore.getState().setCamera(originalState.camera);

    toolbar.dispose();
    toolbar.element.remove();

    return {
      initial,
      cameraAfterDirectSelect,
      routedState,
      candidateLabel,
      undoEnabledAfterRegenerate,
      redoEnabledAfterUndo,
    };
  });

  assert.equal(firstPartyToolbarDom.initial.title, "Home Gym PT");
  assert.equal(firstPartyToolbarDom.initial.subtitle, "Animation Studio");
  assert.deepEqual(
    firstPartyToolbarDom.initial.viewLabels,
    ["Skeleton", "Muscles", "Combined", "Character", "Anatomy"],
    "First-party Toolbar view-mode labels drifted from the React reference",
  );
  assert.equal(
    firstPartyToolbarDom.initial.initialExerciseOptionCount >= 1,
    true,
    "First-party Toolbar exercise selector is empty",
  );
  assert.equal(
    firstPartyToolbarDom.cameraAfterDirectSelect,
    "front",
    "First-party Toolbar camera selector did not route to the Studio store",
  );
  assert.deepEqual(firstPartyToolbarDom.routedState, {
    exerciseId: "air_squat",
    viewMode: "skeleton",
    backdrop: "void",
    camera: "recommended",
  });
  assert.equal(
    firstPartyToolbarDom.candidateLabel,
    "Candidate: Toolbar Probe Candidate",
    "First-party Toolbar did not expose a generated candidate",
  );
  assert.equal(
    firstPartyToolbarDom.undoEnabledAfterRegenerate,
    true,
    "First-party Toolbar did not enable Undo after Regenerate",
  );
  assert.equal(
    firstPartyToolbarDom.redoEnabledAfterUndo,
    true,
    "First-party Toolbar did not enable Redo after Undo",
  );
  report.checks.firstPartyToolbarDom = firstPartyToolbarDom;

  const firstPartyTimelineDom = await page.evaluate(async () => {
    const [{ createStudioTimelineDom }, { studioStore }] = await Promise.all([
      import("/src/editor/timelineDom.ts"),
      import("/src/editor/storeCore.ts"),
    ]);
    const original = studioStore.getState();
    const originalState = {
      time: original.time, playing: original.playing, loop: original.loop,
      speed: original.speed, loopRange: original.loopRange,
    };
    studioStore.getState().pause();
    studioStore.getState().setTime(0);
    studioStore.getState().setLoop(true);
    studioStore.getState().setSpeed(1);
    studioStore.getState().setLoopRange(null);

    const timeline = createStudioTimelineDom(document, studioStore);
    timeline.element.style.position = "fixed";
    timeline.element.style.left = "-10000px";
    timeline.element.style.top = "0";
    document.body.append(timeline.element);

    const initial = {
      play: timeline.controls.play.textContent,
      phaseCount: timeline.element.querySelectorAll(".timeline__phase").length,
      keyCount: timeline.element.querySelectorAll(".timeline__key").length,
      hasStartMarker: Boolean(timeline.element.querySelector(".timeline__key.marker-start")),
      speed: timeline.controls.speed.value,
      loop: timeline.controls.loop.checked,
    };
    timeline.controls.play.click();
    const playingAfterClick = studioStore.getState().playing;
    studioStore.getState().pause();
    timeline.controls.speed.value = "1.5";
    timeline.controls.speed.dispatchEvent(new Event("change", { bubbles: true }));
    timeline.controls.loop.checked = false;
    timeline.controls.loop.dispatchEvent(new Event("change", { bubbles: true }));
    const duration = studioStore.getState().document.clip.duration;
    studioStore.getState().setTime(duration / 2);
    timeline.controls.setIn.click();
    const routed = studioStore.getState();
    const routedState = {
      playingAfterClick,
      speed: routed.speed,
      loop: routed.loop,
      loopRangeStart: routed.loopRange?.start ?? null,
      playhead: timeline.controls.playhead.style.left,
    };

    studioStore.getState().pause();
    studioStore.getState().setTime(originalState.time);
    studioStore.getState().setLoop(originalState.loop);
    studioStore.getState().setSpeed(originalState.speed);
    studioStore.getState().setLoopRange(originalState.loopRange);
    if (originalState.playing) studioStore.getState().play();
    timeline.dispose();
    timeline.element.remove();
    return { initial, routedState };
  });

  assert.equal(firstPartyTimelineDom.initial.play, "Play");
  assert.equal(firstPartyTimelineDom.initial.speed, "1");
  assert.equal(firstPartyTimelineDom.initial.loop, true);
  assert(firstPartyTimelineDom.initial.phaseCount > 0, "First-party Timeline rendered no phases");
  assert(firstPartyTimelineDom.initial.keyCount >= 2, "First-party Timeline rendered too few keyframes");
  assert.equal(firstPartyTimelineDom.initial.hasStartMarker, true, "First-party Timeline lost the semantic start marker");
  assert.equal(firstPartyTimelineDom.routedState.playingAfterClick, true);
  assert.equal(firstPartyTimelineDom.routedState.speed, 1.5);
  assert.equal(firstPartyTimelineDom.routedState.loop, true);
  assert.equal(firstPartyTimelineDom.routedState.playhead, "50%");
  assert(typeof firstPartyTimelineDom.routedState.loopRangeStart === "number", "First-party Timeline did not route Set In");
  report.checks.firstPartyTimelineDom = firstPartyTimelineDom;

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
