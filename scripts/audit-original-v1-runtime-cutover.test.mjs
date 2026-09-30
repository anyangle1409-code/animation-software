import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { auditOriginalV1RuntimeCutover } from "./audit-original-v1-runtime-cutover.mjs";

const ROOT = process.cwd();

function write(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
}

function writeJson(file, value) {
  write(file, JSON.stringify(value, null, 2) + "\n");
}

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "hgpt-original-runtime-cutover-"));
  const contract = {
    schema_version: 1,
    mode: "blocked_procedural_default",
    entrypoint: "src/main.ts",
    registry_module: "src/character/registry.ts",
    prepared_loader_module: "src/character/originalV1Bundled.ts",
    current_default_source: "procedural",
    future_production_source: "original-v1-dressed",
    production_paths: [
      "characters/HomeGymPT_Male_ORIGINAL_v1.glb",
      "characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb",
    ],
  };
  writeJson(path.join(root, "ORIGINAL_V1_RUNTIME_CUTOVER_CONTRACT.json"), contract);
  writeJson(path.join(root, "ORIGINAL_V1_PROMOTION_CONTRACT.json"), {
    mode: "blocked_pending_approval",
    production_targets: {
      bare: {
        release_path: "characters/HomeGymPT_Male_ORIGINAL_v1.glb",
        required: true,
      },
      dressed: {
        release_path: "characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb",
        required: true,
      },
    },
  });
  write(
    path.join(root, "src/main.ts"),
    "import './character/registry';\n",
  );
  write(
    path.join(root, "src/character/procedural.ts"),
    "export const proceduralCharacter = { id: 'procedural' };\n",
  );
  write(
    path.join(root, "src/character/registry.ts"),
    [
      "import { proceduralCharacter } from './procedural';",
      "const sources = new Map();",
      "let fallback = proceduralCharacter.id;",
      "function registerCharacterSource(source) { sources.set(source.id, source); return source; }",
      "registerCharacterSource(proceduralCharacter);",
      "",
    ].join("\n"),
  );
  write(
    path.join(root, "src/character/originalV1Bundled.ts"),
    [
      "const PATHS = {",
      "  bare: 'characters/HomeGymPT_Male_ORIGINAL_v1.glb',",
      "  dressed: 'characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb',",
      "};",
      "export async function load(variant) {",
      "  const url = PATHS[variant];",
      "  const response = await fetch(url);",
      "  return response.arrayBuffer();",
      "}",
      "",
    ].join("\n"),
  );
  return { root, contract };
}

test("current repository keeps the prepared ORIGINAL v1 loader dormant", () => {
  const result = auditOriginalV1RuntimeCutover(ROOT);
  assert.equal(result.pass, true, JSON.stringify(result, null, 2));
  assert.equal(result.mode, "blocked_procedural_default");
  assert.equal(result.registryReachable, true);
  assert.equal(result.preparedLoaderReachable, false);
  assert.equal(result.currentDefaultSource, "procedural");
  assert.equal(result.futureProductionSource, "original-v1-dressed");
});

test("minimal blocked fixture passes with procedural default and unreachable loader", () => {
  const { root } = fixture();
  try {
    const result = auditOriginalV1RuntimeCutover(root);
    assert.equal(result.pass, true, JSON.stringify(result, null, 2));
    assert.equal(result.preparedLoaderReachable, false);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("blocked stage rejects making the prepared loader runtime-reachable", () => {
  const { root } = fixture();
  try {
    const registry = path.join(root, "src/character/registry.ts");
    fs.appendFileSync(registry, "import './originalV1Bundled';\n");
    const result = auditOriginalV1RuntimeCutover(root);
    assert.equal(result.pass, false);
    assert.ok(
      result.blockers.some(message => message.includes("loader is reachable")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("activation cannot happen by changing the contract mode alone", () => {
  const { root, contract } = fixture();
  try {
    contract.mode = "approved_for_activation";
    writeJson(path.join(root, "ORIGINAL_V1_RUNTIME_CUTOVER_CONTRACT.json"), contract);
    const result = auditOriginalV1RuntimeCutover(root);
    assert.equal(result.pass, false);
    assert.ok(
      result.blockers.some(message => message.includes("unsupported runtime-cutover mode")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("prepared loader rejects unexpected/candidate GLB paths at audit time", () => {
  const { root } = fixture();
  try {
    fs.appendFileSync(
      path.join(root, "src/character/originalV1Bundled.ts"),
      "const bad = 'characters/HomeGymPT_Male_ORIGINAL_v1_CANDIDATE.glb';\n",
    );
    const result = auditOriginalV1RuntimeCutover(root);
    assert.equal(result.pass, false);
    assert.ok(
      result.blockers.some(message => message.includes("unexpected GLB path")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("runtime and promotion contracts must name the same exact production paths", () => {
  const { root } = fixture();
  try {
    const promotionPath = path.join(root, "ORIGINAL_V1_PROMOTION_CONTRACT.json");
    const promotion = JSON.parse(fs.readFileSync(promotionPath, "utf8"));
    promotion.production_targets.dressed.release_path =
      "characters/HomeGymPT_Male_ORIGINAL_v1_OTHER.glb";
    writeJson(promotionPath, promotion);

    const result = auditOriginalV1RuntimeCutover(root);
    assert.equal(result.pass, false);
    assert.ok(
      result.blockers.some(message => message.includes("do not exactly match the promotion contract")),
      JSON.stringify(result, null, 2),
    );
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
