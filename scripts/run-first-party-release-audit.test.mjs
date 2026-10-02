import assert from "node:assert/strict";
import test from "node:test";
import {
  RELEASE_CHECKS,
  runFirstPartyReleaseAudit,
} from "./run-first-party-release-audit.mjs";

test("final release audit uses final-mode gates rather than the blocked standalone aggregate", () => {
  const ids = RELEASE_CHECKS.map(check => check.id);

  assert.equal(ids.includes("standalone_source"), false);
  assert.deepEqual(ids, [
    "runtime_dependency_creep",
    "release_readiness",
    "canonical_v4_runtime_coupling",
    "original_v1_runtime_cutover",
    "original_v1_promotion",
    "final_character_runtime",
    "external_runtime_resources",
    "runtime_network",
    "production_output",
    "release_components",
    "release_allowlist",
  ]);

  const promotion = RELEASE_CHECKS.find(check => check.id === "original_v1_promotion");
  assert.deepEqual(promotion?.args, []);
});

test("release audit aggregation fails closed when any final gate fails", () => {
  const checks = [
    { id: "pass", script: "-e", args: ["process.exit(0)"] },
    { id: "fail", script: "-e", args: ["process.exit(7)"] },
  ];

  const result = runFirstPartyReleaseAudit(process.cwd(), checks);
  assert.equal(result.pass, false);
  assert.deepEqual(
    result.checks.map(check => ({
      id: check.id,
      pass: check.pass,
      status: check.status,
    })),
    [
      { id: "pass", pass: true, status: 0 },
      { id: "fail", pass: false, status: 7 },
    ],
  );
});
