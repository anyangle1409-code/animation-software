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
];

const supportingHistory = [
  "docs/WORK_FIRST_PARTY_HANDOFF.md",
  "docs/STANDALONE_PROGRESS.md",
];

const exists = (p) => fs.existsSync(path.join(ROOT, p));
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

for (const p of required) {
  if (!exists(p)) failures.push(`missing required authority file: ${p}`);
}

for (const p of forbiddenPaths) {
  if (exists(p)) failures.push(`forbidden legacy/reference bundle reintroduced: ${p}`);
}

for (const p of supportingHistory) {
  if (!exists(p)) {
    failures.push(`missing supporting history file: ${p}`);
    continue;
  }
  if (!read(p).includes("AUTHORITY NOTICE — SUPPORTING HISTORY ONLY")) {
    failures.push(`supporting history lacks non-authoritative banner: ${p}`);
  }
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
  forbiddenPathsAbsent: forbiddenPaths.filter((p) => !exists(p)),
  supportingHistoryMarkedNonAuthoritative: supportingHistory.filter(
    (p) => exists(p) && read(p).includes("AUTHORITY NOTICE — SUPPORTING HISTORY ONLY"),
  ),
  failures,
};

console.log(JSON.stringify(result, null, 2));
if (failures.length) process.exit(1);
