import assert from "node:assert/strict";
import { resolve } from "node:path";
import test from "node:test";
import { auditCanonicalV4RuntimeCoupling } from "./audit-canonical-v4-runtime-coupling.mjs";

const ROOT = resolve(".");

test("current runtime activates canonical v4 with no reachable v3 rig seam", () => {
  const result = auditCanonicalV4RuntimeCoupling(ROOT);
  assert.equal(result.pass, true, JSON.stringify(result, null, 2));
  assert.equal(result.mode, "v4_active");
  assert.deepEqual(result.v3Importers, []);
  assert.equal(result.v4Reachable, true);
  assert.equal(result.blockers.length, 0);
});
