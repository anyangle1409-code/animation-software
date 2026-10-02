#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.cwd();
const SOURCE_EXT = /\.(?:ts|tsx|js|jsx|mts|mjs)$/i;
const TEST_FILE = /\.(?:test|spec)\.(?:ts|tsx|js|jsx|mts|mjs)$/i;
const ANIMATION_ASSET = /\.(?:bvh|fbx|gltf|glb|blend|dae|abc|usd|usda|usdc|usdz|anim)(?:["'\s?]|$)/i;
const LEGACY = /MakeHuman|makehuman|CORNER_FINAL|BASELINE_v[0-9]+|(?:^|[^A-Za-z0-9])V(?:9|10|11|12|13|14|15)[a-z]?(?:[^A-Za-z0-9]|$)|HIGH_DETAIL_MESH_WORK|review-assets\/characters/i;

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(file, out);
    else if (SOURCE_EXT.test(entry.name) && !TEST_FILE.test(entry.name)) out.push(file);
  }
  return out;
}

function importedSpecifiers(source) {
  const found = [];
  const patterns = [
    /\bimport\s+(?:type\s+)?[^;\n]*?\s+from\s+["']([^"']+)["']/g,
    /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g,
    /\bimport\s+["']([^"']+)["']/g,
  ];
  for (const pattern of patterns) {
    for (const match of source.matchAll(pattern)) found.push(match[1]);
  }
  return found;
}

export function auditExerciseAnimationProvenance(root = ROOT) {
  const recordPath = path.join(root, "EXERCISE_ANIMATION_PROVENANCE.json");
  const blockers = [];
  if (!fs.existsSync(recordPath)) {
    return { schemaVersion: 1, pass: false, blockers: ["missing EXERCISE_ANIMATION_PROVENANCE.json"] };
  }

  const record = JSON.parse(fs.readFileSync(recordPath, "utf8"));
  if (record.component_id !== "exercise_animation_data") {
    blockers.push("provenance component_id must be exercise_animation_data");
  }
  if (record.classification !== "first_party_project_authored") {
    blockers.push("provenance classification must be first_party_project_authored");
  }
  if (!Array.isArray(record.third_party_sources) || record.third_party_sources.length !== 0) {
    blockers.push("third_party_sources must be an explicitly empty array");
  }
  if (!Array.isArray(record.external_animation_inputs) || record.external_animation_inputs.length !== 0) {
    blockers.push("external_animation_inputs must be an explicitly empty array");
  }

  const sourceRoot = path.join(root, record.operational_source_root || "src/exercises");
  const files = walk(sourceRoot);
  if (files.length === 0) blockers.push("operational exercise source set is empty");

  const bareImports = [];
  const assetReferences = [];
  const remoteReads = [];
  const legacyHits = [];

  for (const file of files) {
    const rel = path.relative(root, file).replaceAll("\\", "/");
    const source = fs.readFileSync(file, "utf8");

    for (const specifier of importedSpecifiers(source)) {
      if (!specifier.startsWith(".") && !specifier.startsWith("/") && !specifier.startsWith("node:")) {
        bareImports.push({ file: rel, specifier });
      }
      if (ANIMATION_ASSET.test(specifier)) {
        assetReferences.push({ file: rel, value: specifier, kind: "import" });
      }
    }

    const lines = source.split(/\r?\n/);
    for (const [index, line] of lines.entries()) {
      if (ANIMATION_ASSET.test(line)) {
        assetReferences.push({ file: rel, line: index + 1, value: line.trim(), kind: "source" });
      }
      if (/https?:\/\//i.test(line) || /\bfetch\s*\(|\bnew\s+(?:XMLHttpRequest|WebSocket|EventSource)\s*\(/.test(line)) {
        remoteReads.push({ file: rel, line: index + 1, value: line.trim() });
      }
      if (LEGACY.test(line)) {
        legacyHits.push({ file: rel, line: index + 1, value: line.trim() });
      }
    }
  }

  if (bareImports.length) blockers.push("operational exercise data contains bare/non-project imports");
  if (assetReferences.length) blockers.push("operational exercise data references prerecorded/external animation assets");
  if (remoteReads.length) blockers.push("operational exercise data contains remote/runtime resource reads");
  if (legacyHits.length) blockers.push("operational exercise data contains legacy/reference implementation identities");

  const definitions = files.filter(file => file.includes(path.sep + "definitions" + path.sep)).length;
  const families = files.filter(file => file.includes(path.sep + "families" + path.sep)).length;

  return {
    schemaVersion: 1,
    pass: blockers.length === 0,
    componentId: record.component_id,
    classification: record.classification,
    operationalSourceRoot: path.relative(root, sourceRoot).replaceAll("\\", "/"),
    sourceFileCount: files.length,
    definitionFileCount: definitions,
    familyFileCount: families,
    blockers,
    evidence: {
      bareImports,
      assetReferences,
      remoteReads,
      legacyHits,
    },
    note:
      "PASS proves the operational exercise-animation data path is project-source code with no external animation clips, remote reads, bare third-party imports or legacy character implementation identities.",
  };
}

function main() {
  const result = auditExerciseAnimationProvenance(ROOT);
  fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
  fs.writeFileSync(
    path.join(ROOT, "reports", "exercise_animation_provenance.json"),
    JSON.stringify(result, null, 2) + "\n",
  );
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.pass ? 0 : 1);
}

const invoked =
  process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
