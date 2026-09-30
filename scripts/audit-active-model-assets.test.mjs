import assert from "node:assert/strict";
import { resolve } from "node:path";
import test from "node:test";
import {
  auditActiveModelAssets,
  evaluateActiveModelAssetBoundary,
} from "./audit-active-model-assets.mjs";

const ROOT = resolve(".");

function contract(mode) {
  return {
    mode,
    production_targets: {
      bare: {
        required: true,
        repository_path: "public/characters/HomeGymPT_Male_ORIGINAL_v1.glb",
      },
      dressed: {
        required: true,
        repository_path: "public/characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb",
      },
    },
  };
}

test("current standalone repository satisfies the blocked zero-asset stage", () => {
  const result = auditActiveModelAssets(ROOT);
  assert.equal(result.pass, true, JSON.stringify(result, null, 2));
  assert.equal(result.promotionMode, "blocked_pending_approval");
  assert.deepEqual(result.trackedModelOrTextureAssets, []);
});

test("blocked stage rejects any tracked model or texture asset", () => {
  const result = evaluateActiveModelAssetBoundary({
    tracked: [
      "src/index.ts",
      "public/characters/HomeGymPT_Male_ORIGINAL_v1.glb",
    ],
    contract: contract("blocked_pending_approval"),
  });
  assert.equal(result.pass, false);
  assert.deepEqual(result.allowedProductionAssetPaths, []);
  assert.deepEqual(result.unexpectedModelOrTextureAssets, [
    "public/characters/HomeGymPT_Male_ORIGINAL_v1.glb",
  ]);
});

test("approved stage permits only the exact production asset paths", () => {
  const result = evaluateActiveModelAssetBoundary({
    tracked: [
      "src/index.ts",
      "public/characters/HomeGymPT_Male_ORIGINAL_v1.glb",
      "public/characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb",
    ],
    contract: contract("approved_for_promotion"),
  });
  assert.equal(result.pass, true, JSON.stringify(result, null, 2));
  assert.deepEqual(result.unexpectedModelOrTextureAssets, []);
  assert.deepEqual(result.missingApprovedProductionAssets, []);
});

test("approved stage rejects an extra creative asset", () => {
  const result = evaluateActiveModelAssetBoundary({
    tracked: [
      "public/characters/HomeGymPT_Male_ORIGINAL_v1.glb",
      "public/characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb",
      "public/characters/extra.glb",
    ],
    contract: contract("approved_for_promotion"),
  });
  assert.equal(result.pass, false);
  assert.deepEqual(result.unexpectedModelOrTextureAssets, [
    "public/characters/extra.glb",
  ]);
});

test("approved stage rejects a missing required production asset", () => {
  const result = evaluateActiveModelAssetBoundary({
    tracked: [
      "public/characters/HomeGymPT_Male_ORIGINAL_v1.glb",
    ],
    contract: contract("approved_for_promotion"),
  });
  assert.equal(result.pass, false);
  assert.deepEqual(result.missingApprovedProductionAssets, [
    "public/characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb",
  ]);
});

test("legacy/reference asset paths remain prohibited in every stage", () => {
  const result = evaluateActiveModelAssetBoundary({
    tracked: [
      "public/characters/HomeGymPT_Male_ORIGINAL_v1.glb",
      "public/characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb",
      "archive/CORNER_FINAL.glb",
    ],
    contract: contract("approved_for_promotion"),
  });
  assert.equal(result.pass, false);
  assert.ok(result.legacyPathHits.includes("archive/CORNER_FINAL.glb"));
});
