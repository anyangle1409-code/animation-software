import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test from "node:test";
import { auditOriginalV1Promotion } from "./audit-original-v1-promotion.mjs";

const ROOT = resolve(".");

function copyJson(from, to) {
  mkdirSync(dirname(to), { recursive: true });
  writeFileSync(to, readFileSync(from));
}

function makeBlockedFixture() {
  const root = mkdtempSync(join(tmpdir(), "hgpt-original-promotion-"));
  copyJson(
    join(ROOT, "ORIGINAL_V1_PROMOTION_CONTRACT.json"),
    join(root, "ORIGINAL_V1_PROMOTION_CONTRACT.json"),
  );
  copyJson(
    join(ROOT, "RELEASE_ASSET_ALLOWLIST.json"),
    join(root, "RELEASE_ASSET_ALLOWLIST.json"),
  );
  copyJson(
    join(ROOT, "FIRST_PARTY_COMPONENT_MANIFEST.json"),
    join(root, "FIRST_PARTY_COMPONENT_MANIFEST.json"),
  );
  copyJson(
    join(ROOT, "ORIGINAL_V1_WORK", "hgpt_canonical_v4_original.json"),
    join(root, "ORIGINAL_V1_WORK", "hgpt_canonical_v4_original.json"),
  );
  return root;
}

test("current standalone repo keeps ORIGINAL v1 promotion correctly blocked", () => {
  const result = auditOriginalV1Promotion(ROOT);
  assert.equal(result.pass, true, JSON.stringify(result, null, 2));
  assert.equal(result.expectedBlockedState, true);
  assert.deepEqual(result.productionTargetsPresent, []);
  assert.deepEqual(result.blockers, []);
});

test("blocked promotion state rejects a premature production asset", () => {
  const root = makeBlockedFixture();
  try {
    const target = join(root, "public", "characters", "HomeGymPT_Male_ORIGINAL_v1.glb");
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, Buffer.from("not approved"));

    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, false);
    assert.equal(result.expectedBlockedState, true);
    assert.ok(
      result.blockers.some(message => message.includes("production target exists before approval")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("blocked promotion state rejects exact or broad premature allowlisting", () => {
  const root = makeBlockedFixture();
  try {
    const allowlistPath = join(root, "RELEASE_ASSET_ALLOWLIST.json");
    const allowlist = JSON.parse(readFileSync(allowlistPath, "utf8"));
    allowlist.approved_paths = [
      "characters/HomeGymPT_Male_ORIGINAL_v1.glb",
      "characters/*.glb",
    ];
    writeFileSync(allowlistPath, JSON.stringify(allowlist, null, 2) + "\n");

    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, false);
    assert.ok(
      result.blockers.some(message => message.includes("release allowlist already permits the unapproved target")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("blocked promotion state rejects premature component approval", () => {
  const root = makeBlockedFixture();
  try {
    const componentsPath = join(root, "FIRST_PARTY_COMPONENT_MANIFEST.json");
    const components = JSON.parse(readFileSync(componentsPath, "utf8"));
    for (const component of components.components) {
      if (["male_character", "male_shorts", "canonical_rig"].includes(component.id)) {
        component.status = "first_party_approved";
      }
    }
    writeFileSync(componentsPath, JSON.stringify(components, null, 2) + "\n");

    const result = auditOriginalV1Promotion(root);
    assert.equal(result.pass, false);
    for (const id of ["male_character", "male_shorts", "canonical_rig"]) {
      assert.ok(
        result.blockers.some(message => message.startsWith(id + ": cannot be first_party_approved")),
        JSON.stringify(result, null, 2),
      );
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
