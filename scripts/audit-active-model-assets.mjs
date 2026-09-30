#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.cwd();

const MODEL_OR_TEXTURE_EXT =
  /\.(?:glb|gltf|blend|blend1|fbx|obj|dae|stl|ply|abc|usd|usda|usdc|usdz|3ds|c4d|max|ma|mb|lwo|lws|x3d|3mf|step|stp|iges|igs|mtl|bin|ktx|ktx2|dds|png|jpe?g|webp|bmp|tga|exr|hdr|tiff?|psd|kra|xcf|zip|7z|rar|tar|tgz|gz)$/i;

const LEGACY_PATH_PATTERNS = [
  /HOME_GYM_PT_GPT_MESH_HANDOFF/i,
  /HIGH_DETAIL_MESH_WORK/i,
  /review-assets[\\/]characters/i,
  /HAND_REPAIR_CANDIDATE/i,
  /BASELINE_v(?:5|6|7|8)/i,
  /CORNER_FINAL/i,
  /(?:^|[_-])v(?:9|10|11|12|13|14|15)[a-z]?(?:[_-]|\.|$)/i,
  /MakeHuman/i,
  /Meshy/i,
];

const ignoredLocalAuthoringPatterns = [
  "ORIGINAL_V1_WORK/*.blend",
  "ORIGINAL_V1_WORK/*.blend1",
  "ORIGINAL_V1_WORK/*.glb",
  "ORIGINAL_V1_WORK/*.fbx",
  "ORIGINAL_V1_WORK/checkpoints/",
];

function enumerateTracked(root) {
  const git = spawnSync("git", ["ls-files", "-z"], {
    cwd: root,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  if (git.status !== 0) {
    throw new Error(
      "Unable to enumerate tracked files with git ls-files: " + (git.stderr || "").trim(),
    );
  }
  return (git.stdout || "")
    .split("\0")
    .filter(Boolean)
    .map(file => file.replaceAll("\\", "/"))
    .sort();
}

export function evaluateActiveModelAssetBoundary({ tracked, contract }) {
  const trackedModelOrTextureAssets = tracked.filter(file =>
    MODEL_OR_TEXTURE_EXT.test(file),
  );
  const legacyPathHits = tracked.filter(file =>
    LEGACY_PATH_PATTERNS.some(pattern => pattern.test(file)),
  );

  const blockers = [];
  let allowedProductionAssetPaths = [];

  if (contract.mode === "blocked_pending_approval") {
    allowedProductionAssetPaths = [];
  } else if (contract.mode === "approved_for_promotion") {
    allowedProductionAssetPaths = Object.values(contract.production_targets || {})
      .filter(target => target?.required)
      .map(target => String(target.repository_path || "").replaceAll("\\", "/"))
      .filter(Boolean)
      .sort();
    if (allowedProductionAssetPaths.length === 0) {
      blockers.push("approved promotion contract declares no required production asset paths");
    }
  } else {
    blockers.push(`unsupported promotion mode ${JSON.stringify(contract.mode)}`);
  }

  const allowed = new Set(allowedProductionAssetPaths);
  const unexpectedModelOrTextureAssets = trackedModelOrTextureAssets.filter(
    file => !allowed.has(file),
  );
  const missingApprovedProductionAssets =
    contract.mode === "approved_for_promotion"
      ? allowedProductionAssetPaths.filter(file => !trackedModelOrTextureAssets.includes(file))
      : [];

  if (unexpectedModelOrTextureAssets.length) {
    blockers.push(
      "tracked model/texture assets outside the exact approved production set: " +
        unexpectedModelOrTextureAssets.join(", "),
    );
  }
  if (missingApprovedProductionAssets.length) {
    blockers.push(
      "approved production assets are not tracked: " +
        missingApprovedProductionAssets.join(", "),
    );
  }
  if (legacyPathHits.length) {
    blockers.push("legacy/reference paths are tracked: " + legacyPathHits.join(", "));
  }

  const pass = blockers.length === 0;

  return {
    schemaVersion: 2,
    pass,
    promotionMode: contract.mode,
    policy:
      contract.mode === "blocked_pending_approval"
        ? "Before explicit ORIGINAL v1 approval, the active standalone branch must track zero model/texture creative assets."
        : "After explicit ORIGINAL v1 approval, the active standalone branch may track only the exact production asset paths named by the approved promotion contract.",
    trackedFileCount: tracked.length,
    trackedModelOrTextureAssetCount: trackedModelOrTextureAssets.length,
    trackedModelOrTextureAssets,
    allowedProductionAssetPaths,
    unexpectedModelOrTextureAssets,
    missingApprovedProductionAssets,
    legacyPathHitCount: legacyPathHits.length,
    legacyPathHits,
    ignoredLocalAuthoringPatterns,
    blockers,
    nextPromotionRule:
      "Stage transition is controlled only by ORIGINAL_V1_PROMOTION_CONTRACT.json plus exact-path/hash promotion audits. Never replace this with a broad directory or extension exception.",
  };
}

export function auditActiveModelAssets(root = ROOT) {
  const contractPath = path.join(root, "ORIGINAL_V1_PROMOTION_CONTRACT.json");
  if (!fs.existsSync(contractPath)) {
    return {
      schemaVersion: 2,
      pass: false,
      promotionMode: null,
      blockers: ["missing ORIGINAL_V1_PROMOTION_CONTRACT.json"],
    };
  }
  const contract = JSON.parse(fs.readFileSync(contractPath, "utf8"));
  const tracked = enumerateTracked(root);
  return evaluateActiveModelAssetBoundary({ tracked, contract });
}

function main() {
  let result;
  try {
    result = auditActiveModelAssets(ROOT);
  } catch (error) {
    result = {
      schemaVersion: 2,
      pass: false,
      promotionMode: null,
      blockers: [String(error?.message || error)],
    };
  }

  fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
  fs.writeFileSync(
    path.join(ROOT, "reports", "active_model_asset_boundary.json"),
    JSON.stringify(result, null, 2) + "\n",
  );

  console.log(JSON.stringify(result, null, 2));
  process.exit(result.pass ? 0 : 1);
}

const invoked = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
