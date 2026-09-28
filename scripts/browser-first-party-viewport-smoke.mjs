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
    if (!(root instanceof HTMLElement) || !(shell instanceof HTMLElement) || !(bridge instanceof HTMLElement)) {
      return { exists: false };
    }
    return {
      exists: true,
      shellParentIsRoot: shell.parentElement === root,
      bridgeParentIsRoot: bridge.parentElement === root,
      bridgeOutsideShell: !shell.contains(bridge),
      bridgeChildCount: bridge.childElementCount,
      slotCount: shell.querySelectorAll("[data-hgpt-editor-slot]").length,
      viewportSlotClass:
        shell.querySelector('[data-hgpt-editor-slot="viewport"]')?.classList.contains("studio__viewport-slot") ?? false,
    };
  });
  assert.equal(liveEditorShell.exists, true, "First-party editor shell is not live");
  assert.equal(liveEditorShell.shellParentIsRoot, true, "First-party editor shell is not mounted directly under #root");
  assert.equal(liveEditorShell.bridgeParentIsRoot, true, "Temporary React child bridge is not mounted under #root");
  assert.equal(liveEditorShell.bridgeOutsideShell, true, "React bridge unexpectedly owns the first-party shell");
  assert.equal(liveEditorShell.bridgeChildCount, 0, "React bridge should contain only portal ownership, not editor DOM");
  assert.equal(liveEditorShell.slotCount, 5, "First-party editor shell live slot count drifted");
  assert.equal(liveEditorShell.viewportSlotClass, true, "First-party viewport slot lost its layout boundary");
  report.checks.liveEditorShellOwnership = liveEditorShell;

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

  const contactsTab = leftTabs.getByRole("button", { name: "Contacts", exact: true });
  await contactsTab.click();
  const contactPanelParity = await page.evaluate(async () => {
    const [{ createContactPanelDom }, { studioStore }] = await Promise.all([
      import("/src/editor/panels/contactPanelDom.ts"),
      import("/src/editor/storeCore.ts"),
    ]);
    const snapshot = (panel) => ({
      heading: panel.querySelector("h2")?.textContent ?? null,
      note: panel.querySelector(".panel__note")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
      empty: panel.querySelector(".panel__empty")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
      cards: Array.from(panel.querySelectorAll(".contact-card")).map((card) => ({
        className: card.getAttribute("class"),
        head: card.querySelector(".contact-card__head")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
        checked: card.querySelector('input[type="checkbox"]')?.checked ?? null,
        status: card.querySelector(".contact-card__head strong")?.textContent ?? null,
        metrics: Array.from(card.querySelectorAll(".contact-metrics > *")).map(
          (element) => element.textContent?.replace(/\s+/g, " ").trim() ?? null,
        ),
      })),
      hint: panel.querySelector(".panel__hint")?.textContent?.replace(/\s+/g, " ").trim() ?? null,
    });

    const reactPanel = document.querySelector('[data-hgpt-editor-slot="left-panel"] .contact-panel');
    if (!(reactPanel instanceof HTMLElement)) throw new Error("React Contact panel reference is unavailable");
    const react = snapshot(reactPanel);

    const firstParty = createContactPanelDom(document, studioStore);
    firstParty.element.style.position = "fixed";
    firstParty.element.style.left = "-10000px";
    firstParty.element.style.top = "0";
    document.body.append(firstParty.element);
    const candidate = snapshot(firstParty.element);
    firstParty.dispose();
    firstParty.element.remove();
    return { react, candidate };
  });
  assert.deepEqual(
    contactPanelParity.candidate,
    contactPanelParity.react,
    "First-party Contact panel drifted from the React reference",
  );
  report.checks.firstPartyContactPanel = contactPanelParity.candidate;
  await leftTabs.getByRole("button", { name: "Joint", exact: true }).click();
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
