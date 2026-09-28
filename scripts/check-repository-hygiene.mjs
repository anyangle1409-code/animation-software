#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const failures = [];

const required = [
  "docs/CURRENT_HANDOFF.md",
  "docs/PROJECT_AUTHORITY.md",
  "docs/AI_OPERATING_CONTRACT.md",
  "docs/DECISION_LOG.md",
  "docs/BRANCH_HYGIENE.md",
  "FIRST_PARTY_COMPONENT_MANIFEST.json",
];

const forbiddenPaths = [
  "HOME_GYM_PT_GPT_MESH_HANDOFF",
  "review-assets",
  "AI_CHANGELOG.md",
  "docs/WORK_FIRST_PARTY_HANDOFF.md",
  "docs/STANDALONE_PROGRESS.md",
  "docs/STANDALONE_REMOTE_PROGRESS.md",
  "docs/PREPARE_ORIGINAL_V1_CLEAN_ROOM.md",
  "docs/FIRST_PARTY_DREI_REPLACEMENT.md",
  "docs/FIRST_PARTY_FRAME_LOOP_PLAN.md",
];

const exists = (p) => fs.existsSync(path.join(ROOT, p));
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

for (const p of required) {
  if (!exists(p)) failures.push(`missing required authority file: ${p}`);
}

for (const p of forbiddenPaths) {
  if (exists(p)) failures.push(`obsolete/legacy path reintroduced: ${p}`);
}

if (exists("README.md")) {
  const readme = read("README.md");
  for (const link of [
    "docs/CURRENT_HANDOFF.md",
    "docs/PROJECT_AUTHORITY.md",
    "docs/AI_OPERATING_CONTRACT.md",
    "docs/DECISION_LOG.md",
  ]) {
    if (!readme.includes(link)) failures.push(`README does not point to authority file: ${link}`);
  }
} else {
  failures.push("README.md missing");
}

if (exists("docs/CURRENT_HANDOFF.md")) {
  const handoff = read("docs/CURRENT_HANDOFF.md");
  if (!handoff.includes("work/standalone-first-party-audit-20260927")) {
    failures.push("CURRENT_HANDOFF does not identify the active standalone branch");
  }
}

const result = {
  status: failures.length === 0 ? "PASS" : "FAIL",
  requiredAuthorityFiles: required,
  obsoleteAndLegacyPathsAbsent: forbiddenPaths.filter((p) => !exists(p)),
  failures,
};

console.log(JSON.stringify(result, null, 2));
if (failures.length) process.exit(1);
