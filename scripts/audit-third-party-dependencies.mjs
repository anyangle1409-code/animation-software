#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const packageJsonPath = path.join(root, "package.json");
const lockPath = path.join(root, "package-lock.json");

if (!fs.existsSync(packageJsonPath) || !fs.existsSync(lockPath)) {
  console.error("Run from repository root; package.json and package-lock.json are required.");
  process.exit(1);
}

const pkg = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
const lock = JSON.parse(fs.readFileSync(lockPath, "utf8"));

const directRuntime = Object.keys(pkg.dependencies || {}).sort();
const directDev = Object.keys(pkg.devDependencies || {}).sort();

const packages = [];
const licenseCounts = {};
for (const [lockKey, meta] of Object.entries(lock.packages || {})) {
  if (!lockKey || !meta || typeof meta !== "object") continue;
  const name = lockKey.replace(/^node_modules\//, "");
  const license = meta.license || "UNKNOWN";
  licenseCounts[license] = (licenseCounts[license] || 0) + 1;
  packages.push({
    name,
    version: meta.version || null,
    license,
    dev: Boolean(meta.dev),
    optional: Boolean(meta.optional),
  });
}

const runtimeDirectRecords = directRuntime.map((name) => {
  const meta = lock.packages?.[`node_modules/${name}`] || {};
  return {
    name,
    declared: pkg.dependencies[name],
    installed: meta.version || null,
    license: meta.license || "UNKNOWN",
  };
});

const devDirectRecords = directDev.map((name) => {
  const meta = lock.packages?.[`node_modules/${name}`] || {};
  return {
    name,
    declared: pkg.devDependencies[name],
    installed: meta.version || null,
    license: meta.license || "UNKNOWN",
  };
});

const report = {
  generatedAt: new Date().toISOString(),
  packageName: pkg.name || null,
  directRuntime: runtimeDirectRecords,
  directDev: devDirectRecords,
  licenseCounts,
  allInstalledPackages: packages.sort((a, b) => a.name.localeCompare(b.name)),
  firstPartyStandaloneGate: {
    runtimeDirectDependencyCount: directRuntime.length,
    pass: directRuntime.length === 0,
    note:
      directRuntime.length === 0
        ? "No direct runtime dependencies declared."
        : "Standalone Level 1 is not yet complete; runtime dependencies remain.",
  },
};

const outDir = path.join(root, "reports");
fs.mkdirSync(outDir, { recursive: true });
const outPath = path.join(outDir, "third_party_dependency_audit.json");
fs.writeFileSync(outPath, JSON.stringify(report, null, 2) + "\n");

console.log(JSON.stringify({
  output: path.relative(root, outPath),
  directRuntimeCount: directRuntime.length,
  directDevCount: directDev.length,
  licenseCounts,
  standaloneRuntimeGatePass: report.firstPartyStandaloneGate.pass,
}, null, 2));
