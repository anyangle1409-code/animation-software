#!/usr/bin/env node
import { execFileSync } from "node:child_process";

const EXPECTED_BRANCH = "work/standalone-first-party-audit-20260927";
const TARGETS = [
  "chatgpt/absolute-retarget-imports",
  "claude/home-gym-pt-animation-txux66",
  "codex/anatomical-reference-character",
  "codex/fix-dumbbell-grip-position",
  "work/self-sufficient-engine-integration-20260925",
];

const apply = process.argv.includes("--apply");

function git(args, options = {}) {
  return execFileSync("git", args, {
    encoding: "utf8",
    stdio: options.stdio ?? ["ignore", "pipe", "pipe"],
  }).trim();
}

function succeeds(args) {
  try {
    execFileSync("git", args, { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

const branch = git(["branch", "--show-current"]);
if (branch !== EXPECTED_BRANCH) {
  console.error(`REFUSE: checked out branch is "${branch}", expected "${EXPECTED_BRANCH}".`);
  process.exit(2);
}

git(["fetch", "origin", "--prune"], { stdio: "inherit" });

const safe = [];
for (const target of TARGETS) {
  const remoteRef = `refs/remotes/origin/${target}`;
  if (!succeeds(["show-ref", "--verify", "--quiet", remoteRef])) {
    console.log(`SKIP: origin/${target} is already absent.`);
    continue;
  }

  if (!succeeds(["merge-base", "--is-ancestor", `origin/${target}`, "HEAD"])) {
    console.error(`REFUSE: origin/${target} is no longer fully contained in HEAD.`);
    process.exit(3);
  }

  safe.push(target);
  console.log(`SAFE: ${target} is fully contained in HEAD.`);
}

if (!apply) {
  console.log("\nDRY RUN ONLY. Re-run with --apply to delete the SAFE remote branches.");
  process.exit(0);
}

for (const target of safe) {
  console.log(`Deleting origin/${target}...`);
  git(["push", "origin", "--delete", target], { stdio: "inherit" });
}

console.log("\nContained historical branch cleanup complete.");
