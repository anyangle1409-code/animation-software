#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.cwd();

function normalise(file, root) {
  return path.relative(root, file).replaceAll("\\", "/");
}

function relativeSpecifiers(source) {
  const specs = new Set();
  for (const match of source.matchAll(/\bfrom\s+["'](\.[^"']+)["']/g)) {
    specs.add(match[1]);
  }
  for (const match of source.matchAll(/\bimport\s*\(\s*["'](\.[^"']+)["']\s*\)/g)) {
    specs.add(match[1]);
  }
  for (const match of source.matchAll(/\bimport\s*["'](\.[^"']+)["']/g)) {
    specs.add(match[1]);
  }
  return [...specs];
}

function resolveRelative(fromFile, specifier) {
  const base = path.resolve(path.dirname(fromFile), specifier);
  const candidates = [
    base,
    base + ".ts",
    base + ".tsx",
    base + ".js",
    base + ".mjs",
    path.join(base, "index.ts"),
    path.join(base, "index.tsx"),
    path.join(base, "index.js"),
    path.join(base, "index.mjs"),
  ];
  return candidates.find(candidate => fs.existsSync(candidate) && fs.statSync(candidate).isFile()) ?? null;
}

export function buildRuntimeImportGraph(root, entrypoint) {
  const start = path.resolve(root, entrypoint);
  const queue = [start];
  const seen = new Set();
  const edges = [];

  while (queue.length) {
    const file = queue.shift();
    if (!file || seen.has(file)) continue;
    if (!fs.existsSync(file)) {
      throw new Error(`runtime graph file is missing: ${normalise(file, root)}`);
    }
    seen.add(file);
    const source = fs.readFileSync(file, "utf8");
    for (const specifier of relativeSpecifiers(source)) {
      const target = resolveRelative(file, specifier);
      if (!target) {
        throw new Error(
          `cannot resolve runtime import ${specifier} from ${normalise(file, root)}`,
        );
      }
      edges.push({
        from: normalise(file, root),
        to: normalise(target, root),
        specifier,
      });
      if (!seen.has(target)) queue.push(target);
    }
  }

  return {
    reachable: [...seen].map(file => normalise(file, root)).sort(),
    edges,
  };
}

export function auditCanonicalV4RuntimeCoupling(root = ROOT) {
  const contractPath = path.join(root, "CANONICAL_V4_RUNTIME_CONTRACT.json");
  if (!fs.existsSync(contractPath)) {
    return {
      schemaVersion: 1,
      pass: false,
      blockers: ["missing CANONICAL_V4_RUNTIME_CONTRACT.json"],
    };
  }

  const contract = JSON.parse(fs.readFileSync(contractPath, "utf8"));
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

  const v3Edges = graph.edges.filter(edge => edge.to === contract.v3_module);
  const v3Importers = [...new Set(v3Edges.map(edge => edge.from))].sort();
  const v4Reachable = graph.reachable.includes(contract.v4_module);

  if (contract.mode === "shadow_v3_active") {
    const allowed = [...(contract.allowed_v3_runtime_importers || [])].sort();
    const unexpected = v3Importers.filter(file => !allowed.includes(file));
    const missingExpected = allowed.filter(file => !v3Importers.includes(file));

    if (unexpected.length) {
      blockers.push(
        "unexpected reachable v3 rig importers: " + unexpected.join(", "),
      );
    }
    if (missingExpected.length) {
      blockers.push(
        "expected shadow-stage v3 importer(s) missing: " + missingExpected.join(", "),
      );
    }
    if (v4Reachable) {
      blockers.push(
        "v4 rig module is already reachable while contract remains shadow_v3_active",
      );
    }
  } else if (contract.mode === "v4_active") {
    if (v3Importers.length) {
      blockers.push(
        "v3 humanoid rig remains reachable after v4 activation: " + v3Importers.join(", "),
      );
    }
    if (!v4Reachable) {
      blockers.push("v4 rig module is not reachable from the runtime entrypoint");
    }
  } else {
    blockers.push(`unsupported v4 runtime mode ${JSON.stringify(contract.mode)}`);
  }

  return {
    schemaVersion: 1,
    pass: blockers.length === 0,
    mode: contract.mode,
    entrypoint: contract.entrypoint,
    reachableModuleCount: graph.reachable.length,
    v3Module: contract.v3_module,
    v3Importers,
    v3Edges,
    v4Module: contract.v4_module,
    v4Reachable,
    blockers,
    note:
      "Runtime import-graph gate only. A PASS does not approve the ORIGINAL v1 mesh or authorize v4 activation.",
  };
}

function main() {
  const result = auditCanonicalV4RuntimeCoupling(ROOT);
  fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
  fs.writeFileSync(
    path.join(ROOT, "reports", "canonical_v4_runtime_coupling.json"),
    JSON.stringify(result, null, 2) + "\n",
  );
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.pass ? 0 : 1);
}

const invoked = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invoked) main();
