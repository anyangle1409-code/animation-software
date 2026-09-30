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

  if (contract.mode !== "blocked_procedural_default") {
    blockers.push(
      `unsupported runtime-cutover mode ${JSON.stringify(contract.mode)}; activation requires a reviewed code/audit change after production approval`,
    );
  }

  if (loaderReachable) {
    blockers.push(
      `prepared ORIGINAL v1 loader is reachable from ${contract.entrypoint} before production approval`,
    );
  }
  if (!registryReachable) {
    blockers.push(`live character registry is not reachable from ${contract.entrypoint}`);
  }

  const registryPath = path.join(root, registryModule);
  if (!fs.existsSync(registryPath)) {
    blockers.push(`missing registry module ${registryModule}`);
  } else {
    const source = fs.readFileSync(registryPath, "utf8");
    if (!source.includes("let fallback = proceduralCharacter.id;")) {
      blockers.push("live registry no longer pins the procedural character as its default fallback");
    }
    if (!source.includes("registerCharacterSource(proceduralCharacter);")) {
      blockers.push("live registry no longer registers the clean procedural character");
    }
    if (
      source.includes("./bundled") ||
      source.includes("bundledOriginalV1Source") ||
      source.includes("original-v1-dressed")
    ) {
      blockers.push("live registry references the dormant ORIGINAL v1 production loader/source");
    }
  }

  const loaderPath = path.join(root, loaderModule);
  if (!fs.existsSync(loaderPath)) {
    blockers.push(`missing prepared loader module ${loaderModule}`);
  } else {
    const source = fs.readFileSync(loaderPath, "utf8");
    const expectedPaths = contract.production_paths || [];
    for (const expected of expectedPaths) {
      if (!source.includes(`'${expected}'`) && !source.includes(`"${expected}"`)) {
        blockers.push(`prepared loader does not pin production path ${expected}`);
      }
    }

    const pathLiterals = [
      ...source.matchAll(/['"]([^'"]+\.glb)['"]/gi),
    ].map(match => match[1]);
    const unexpected = [...new Set(pathLiterals)]
      .filter(value => !expectedPaths.includes(value));
    if (unexpected.length) {
      blockers.push(
        "prepared loader contains unexpected GLB path(s): " + unexpected.join(", "),
      );
    }

    if (!source.includes("const response = await fetch(url);")) {
      blockers.push("prepared loader no longer uses the reviewed exact local fetch seam");
    }
    if (/fetch\s*\(\s*['"](?:https?:)?\/\//i.test(source)) {
      blockers.push("prepared loader contains a remote/protocol-relative fetch");
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
    reachableModuleCount: graph.reachable.length,
    blockers,
    note:
      "Blocked-stage runtime cutover gate. PASS means ORIGINAL v1 loading is prepared but not reachable/active; it does not approve any production asset.",
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
  process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
