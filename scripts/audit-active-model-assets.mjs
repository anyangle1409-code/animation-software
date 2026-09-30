#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

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

const git = spawnSync("git", ["ls-files", "-z"], {
  cwd: ROOT,
  encoding: "utf8",
  stdio: ["ignore", "pipe", "pipe"],
});

if (git.status !== 0) {
  console.error(JSON.stringify({
    pass: false,
    error: "Unable to enumerate tracked files with git ls-files.",
    stderr: (git.stderr || "").trim(),
  }, null, 2));
  process.exit(1);
}

const tracked = (git.stdout || "")
  .split("\0")
  .filter(Boolean)
  .map((file) => file.replaceAll("\\", "/"))
  .sort();

const trackedModelOrTextureAssets = tracked.filter((file) =>
  MODEL_OR_TEXTURE_EXT.test(file)
);

const legacyPathHits = tracked.filter((file) =>
  LEGACY_PATH_PATTERNS.some((pattern) => pattern.test(file))
);

const ignoredLocalAuthoringPatterns = [
  "ORIGINAL_V1_WORK/*.blend",
  "ORIGINAL_V1_WORK/*.blend1",
  "ORIGINAL_V1_WORK/*.glb",
  "ORIGINAL_V1_WORK/*.fbx",
  "ORIGINAL_V1_WORK/checkpoints/",
];

const pass =
  trackedModelOrTextureAssets.length === 0 &&
  legacyPathHits.length === 0;

const result = {
  generatedAt: new Date().toISOString(),
  pass,
  policy:
    "Until HomeGymPT_Male_ORIGINAL_v1 is explicitly provenance-approved, the active branch must track zero model/texture creative assets. Guarded local Blender authoring remains git-ignored and is audited separately.",
  trackedFileCount: tracked.length,
  trackedModelOrTextureAssetCount: trackedModelOrTextureAssets.length,
  trackedModelOrTextureAssets,
  legacyPathHitCount: legacyPathHits.length,
  legacyPathHits,
  ignoredLocalAuthoringPatterns,
  nextPromotionRule:
    "When ORIGINAL v1 is ready for repository/release promotion, replace this zero-asset stage rule only with an exact first-party asset allowlist plus provenance/hash verification. Never weaken it to a broad extension or directory exception.",
};

fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
fs.writeFileSync(
  path.join(ROOT, "reports", "active_model_asset_boundary.json"),
  JSON.stringify(result, null, 2) + "\n",
);

console.log(JSON.stringify(result, null, 2));
process.exit(pass ? 0 : 1);
