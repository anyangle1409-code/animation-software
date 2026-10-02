#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.cwd();

/**
 * Final-release checks only.
 *
 * Do not call run-standalone-audit.mjs here. That aggregate is deliberately a
 * pre-promotion safety gate and requires ORIGINAL v1 to remain blocked. A true
 * release must instead prove approved promotion plus the active runtime cutover.
 */
export const RELEASE_CHECKS = Object.freeze([
  { id: "runtime_dependency_creep", script: "scripts/check-runtime-dependency-creep.mjs", args: [] },
  { id: "release_readiness", script: "scripts/check-first-party-release-readiness.mjs", args: [] },
  { id: "canonical_v4_runtime_coupling", script: "scripts/audit-canonical-v4-runtime-coupling.mjs", args: [] },
  { id: "original_v1_runtime_cutover", script: "scripts/audit-original-v1-runtime-cutover.mjs", args: [] },
  { id: "original_v1_promotion", script: "scripts/audit-original-v1-promotion.mjs", args: [] },
  { id: "final_character_runtime", script: "scripts/audit-final-character-runtime.mjs", args: [] },
  { id: "external_runtime_resources", script: "scripts/audit-external-runtime-resources.mjs", args: [] },
  { id: "runtime_network", script: "scripts/audit-runtime-network.mjs", args: [] },
  { id: "production_output", script: "scripts/audit-production-output.mjs", args: ["dist"] },
  { id: "release_components", script: "scripts/audit-first-party-release-components.mjs", args: [] },
  { id: "release_allowlist", script: "scripts/audit-release-allowlist.mjs", args: ["dist"] },
]);

export function runFirstPartyReleaseAudit(root = ROOT, checks = RELEASE_CHECKS) {
  const results = [];
  for (const { id, script, args = [] } of checks) {
    const proc = spawnSync(process.execPath, [script, ...args], {
      cwd: root,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    });
    results.push({
      id,
      script,
      args,
      pass: proc.status === 0,
      status: proc.status,
      stdout: (proc.stdout || "").slice(-12000),
      stderr: (proc.stderr || "").slice(-6000),
    });
  }

  return {
    generatedAt: new Date().toISOString(),
    pass: results.every(result => result.pass),
    checks: results.map(({ id, script, args, pass, status }) => ({
      id,
      script,
      args,
      pass,
      status,
    })),
    note:
      "Final automated release gate. It is intentionally expected to fail before ORIGINAL v1 approval/activation and exact release allowlisting. Production-package offline browser acceptance and physical desktop/iPhone evidence remain additional required gates.",
    details: results,
  };
}

function main() {
  const audit = runFirstPartyReleaseAudit(ROOT);
  const { details, ...result } = audit;

  fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
  fs.writeFileSync(
    path.join(ROOT, "reports", "first_party_release_audit.json"),
    JSON.stringify({ result, details }, null, 2) + "\n",
  );
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.pass ? 0 : 1);
}

const invoked =
  process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
