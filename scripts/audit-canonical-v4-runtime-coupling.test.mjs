import assert from "node:assert/strict";
import { resolve } from "node:path";
import test from "node:test";
import { auditCanonicalV4RuntimeCoupling } from "./audit-canonical-v4-runtime-coupling.mjs";

const ROOT = resolve(".");

test("current runtime keeps v4 in shadow with one explicit v3 skeleton seam", () => {
  const result = auditCanonicalV4RuntimeCoupling(ROOT);
  assert.equal(result.pass, true, JSON.stringify(result, null, 2));
  assert.equal(result.mode, "shadow_v3_active");
  assert.deepEqual(result.v3Importers, ["src/rig/skeleton.ts"]);
  assert.equal(result.v4Reachable, false);
  assert.equal(result.blockers.length, 0);
});
