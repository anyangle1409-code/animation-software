#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildRuntimeImportGraph } from "./audit-canonical-v4-runtime-coupling.mjs";

const ROOT = process.cwd();

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

export function auditOriginalV1RuntimeCutover(root = ROOT) {
  const contractPath = path.join(root, "ORIGINAL_V1_RUNTIME_CUTOVER_CONTRACT.json");
  if (!fs.existsSync(contractPath)) {
    return {
      schemaVersion: 1,
      pass: false,
      blockers: ["missing ORIGINAL_V1_RUNTIME_CUTOVER_CONTRACT.json"],
    };
  }

  const contract = readJson(contractPath);
  const blockers = [];

  const promotionPath = path.join(root, "ORIGINAL_V1_PROMOTION_CONTRACT.json");
  if (!fs.existsSync(promotionPath)) {
    blockers.push("missing ORIGINAL_V1_PROMOTION_CONTRACT.json");
  }
  const promotion = fs.existsSync(promotionPath) ? readJson(promotionPath) : null;
  const promotionPaths = promotion
    ? Object.values(promotion.production_targets || {})
        .filter(target => target?.required)
        .map(target => String(target.release_path || ""))
        .filter(Boolean)
        .sort()
    : [];
  const cutoverPaths = [...(contract.production_paths || [])].map(String).sort();
  if (
    promotion &&
    JSON.stringify(promotionPaths) !== JSON.stringify(cutoverPaths)
  ) {
    blockers.push(
      "runtime cutover production paths do not exactly match the promotion contract: " +
        JSON.stringify({ promotion: promotionPaths, cutover: cutoverPaths }),
    );
  }

  let graph;
  try {
    graph = buildRuntimeImportGraph(root, contract.entrypoint);
  } catch (error) {
    return {
      schemaVersion: 1,
      pass: false,
      mode: contract.mode,
      blockers: [String(error?.message || error)],
    };
  }

  const loaderModule = String(contract.prepared_loader_module || "");
  const registryModule = String(contract.registry_module || "");
  const loaderReachable = graph.reachable.includes(loaderModule);
  const registryReachable = graph.reachable.includes(registryModule);
  const blockedMode = contract.mode === "blocked_procedural_default";
  const activeMode = contract.mode === "original_v1_active";

  if (!blockedMode && !activeMode) {
    blockers.push(
      "unsupported runtime-cutover mode " +
        JSON.stringify(contract.mode) +
        "; expected blocked_procedural_default or original_v1_active",
    );
  }

  if (blockedMode && loaderReachable) {
    blockers.push(
      "prepared ORIGINAL v1 loader is reachable from " +
        contract.entrypoint +
        " before production approval",
    );
  }

  if (activeMode) {
    if (promotion?.mode !== "approved_for_promotion") {
      blockers.push(
        "ORIGINAL v1 runtime activation requires promotion mode approved_for_promotion",
      );
    }
    if (!loaderReachable) {
      blockers.push(
        "ORIGINAL v1 production loader is not reachable from " +
          contract.entrypoint +
          " after activation",
      );
    }
    if (contract.current_default_source !== contract.future_production_source) {
      blockers.push(
        "active runtime default " +
          JSON.stringify(contract.current_default_source) +
          " does not match future production source " +
          JSON.stringify(contract.future_production_source),
      );
    }
  }

  if (!registryReachable) {
    blockers.push(
      "live character registry is not reachable from " + contract.entrypoint,
    );
  }

  const registryPath = path.join(root, registryModule);
  if (!fs.existsSync(registryPath)) {
    blockers.push("missing registry module " + registryModule);
  } else {
    const source = fs.readFileSync(registryPath, "utf8");

    if (blockedMode) {
      if (!source.includes("let fallback = proceduralCharacter.id;")) {
        blockers.push(
          "live registry no longer pins the procedural character as its default fallback",
        );
      }
      if (!source.includes("registerCharacterSource(proceduralCharacter);")) {
        blockers.push(
          "live registry no longer registers the clean procedural character",
        );
      }
      if (
        source.includes("./bundled") ||
        source.includes("./originalV1Bundled") ||
        source.includes("bundledOriginalV1Source") ||
        source.includes("original-v1-dressed")
      ) {
        blockers.push(
          "live registry references the dormant ORIGINAL v1 production loader/source",
        );
      }
    }

    if (activeMode) {
      if (!source.includes("registerCharacterSource(proceduralCharacter);")) {
        blockers.push(
          "active registry must retain the clean procedural source as a diagnostic fallback",
        );
      }

      const dressed = source.match(
        /const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*bundledOriginalV1Source\(\s*["']dressed["']\s*\)\s*;/,
      );
      if (!dressed) {
        blockers.push(
          "active registry does not construct the exact dressed ORIGINAL v1 bundled source",
        );
      } else {
        const variable = dressed[1];
        if (!source.includes("registerCharacterSource(" + variable + ");")) {
          blockers.push(
            "active registry does not register the dressed ORIGINAL v1 source",
          );
        }
        const fallbackPattern = new RegExp(
          "let\\s+fallback\\s*=\\s*" + variable + "\\.id\\s*;",
        );
        if (!fallbackPattern.test(source)) {
          blockers.push(
            "active registry does not make the dressed ORIGINAL v1 source the default",
          );
        }
      }
    }
  }

  const loaderPath = path.join(root, loaderModule);
  if (!fs.existsSync(loaderPath)) {
    blockers.push("missing prepared loader module " + loaderModule);
  } else {
    const source = fs.readFileSync(loaderPath, "utf8");
    const expectedPaths = contract.production_paths || [];
    for (const expected of expectedPaths) {
      if (
        !source.includes("'" + expected + "'") &&
        !source.includes('"' + expected + '"')
      ) {
        blockers.push("prepared loader does not pin production path " + expected);
      }
    }

    const pathLiterals = [
      ...source.matchAll(/['"]([^'"]+\.glb)['"]/gi),
    ].map(match => match[1]);
    const unexpected = [...new Set(pathLiterals)]
      .filter(value => !expectedPaths.includes(value));
    if (unexpected.length) {
      blockers.push(
        "prepared loader contains unexpected GLB path(s): " +
          unexpected.join(", "),
      );
    }

    if (!source.includes("const response = await fetch(url);")) {
      blockers.push(
        "prepared loader no longer uses the reviewed exact local fetch seam",
      );
    }
    if (/fetch\s*\(\s*['"](?:https?:)?\/\//i.test(source)) {
      blockers.push(
        "prepared loader contains a remote/protocol-relative fetch",
      );
    }
  }

  return {
    schemaVersion: 1,
    pass: blockers.length === 0,
    mode: contract.mode,
    entrypoint: contract.entrypoint,
    registryModule,
    registryReachable,
    preparedLoaderModule: loaderModule,
    preparedLoaderReachable: loaderReachable,
    currentDefaultSource: contract.current_default_source,
    futureProductionSource: contract.future_production_source,
    productionPaths: contract.production_paths,
    promotionPaths,
    productionPathContractsMatch:
      JSON.stringify(promotionPaths) === JSON.stringify(cutoverPaths),
    reachableModuleCount: graph.reachable.length,
    blockers,
    note: blockedMode
      ? "Blocked-stage runtime cutover gate. PASS means ORIGINAL v1 loading is prepared but not reachable/active; it does not approve any production asset."
      : "Active-stage runtime cutover gate. PASS means an approved ORIGINAL v1 dressed source is reachable, registered and the runtime default; production approval remains governed by the promotion/release gates.",
  };
}

function main() {
  const result = auditOriginalV1RuntimeCutover(ROOT);
  fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
  fs.writeFileSync(
    path.join(ROOT, "reports", "original_v1_runtime_cutover.json"),
    JSON.stringify(result, null, 2) + "\n",
  );
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.pass ? 0 : 1);
}

const invoked =
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
