#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, "package.json"), "utf8"));
const policy = JSON.parse(fs.readFileSync(path.join(ROOT, "RUNTIME_MIGRATION_ALLOWLIST.json"), "utf8"));

const current = Object.keys(pkg.dependencies || {}).sort();
const allowed = new Set(policy.allowed_existing_runtime_dependencies || []);
const introduced = current.filter((name) => !allowed.has(name));

const isTestFile = (name) => /\.(?:test|spec)\.(?:ts|tsx|js|jsx|mts|mjs)$/i.test(name);

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!/^tests?$/i.test(entry.name)) walk(file, out);
    } else if (/\.(?:ts|tsx|js|jsx|mts|mjs)$/.test(entry.name) && !isTestFile(entry.name)) {
      out.push(file);
    }
  }
  return out;
}

function importedSpecifiers(text) {
  const found = [];
  const fromImport = /\bimport\s+[^;\n]*?\s+from\s+["']([^"']+)["']/g;
  const bareImport = /\bimport\s+["']([^"']+)["']/g;
  const dynamicImport = /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g;
  for (const expression of [fromImport, bareImport, dynamicImport]) {
    for (const match of text.matchAll(expression)) found.push(match[1]);
  }
  return found;
}

const sourceFiles = walk(path.join(ROOT, "src"));
const ceilings = policy.source_import_ceilings || {};
const sourceImportResults = {};
const sourceFailures = [];

for (const [target, ceiling] of Object.entries(ceilings)) {
  const imports = [];
  for (const file of sourceFiles) {
    const text = fs.readFileSync(file, "utf8");
    const rel = path.relative(ROOT, file).replaceAll("\\", "/");
    for (const specifier of importedSpecifiers(text)) {
      if (specifier === target || specifier.startsWith(target + "/")) {
        imports.push({ file: rel, specifier });
      }
    }
  }

  const allowedFiles = new Set(ceiling.allowed_files || []);
  const unexpectedFiles = [...new Set(imports.map((entry) => entry.file))]
    .filter((file) => !allowedFiles.has(file))
    .sort();
  const maxImports = Number(ceiling.max_imports);
  const overCeiling = Number.isFinite(maxImports) && imports.length > maxImports;

  sourceImportResults[target] = {
    importCount: imports.length,
    maxImports,
    files: [...new Set(imports.map((entry) => entry.file))].sort(),
    unexpectedFiles,
    pass: !overCeiling && unexpectedFiles.length === 0,
  };

  if (overCeiling) {
    sourceFailures.push(`${target} import count ${imports.length} exceeds migration ceiling ${maxImports}`);
  }
  for (const file of unexpectedFiles) {
    sourceFailures.push(`${target} imported from new/unapproved source file: ${file}`);
  }
}

const pass = introduced.length === 0 && sourceFailures.length === 0;
const result = {
  generatedAt: new Date().toISOString(),
  pass,
  currentRuntimeDependencies: current,
  currentCount: current.length,
  allowedMigrationCeiling: [...allowed].sort(),
  newlyIntroduced: introduced,
  sourceImportResults,
  sourceFailures,
  finalTarget: [],
  note:
    "PASS means no new runtime dependency or guarded source import has crept in. Final standalone readiness still requires runtime dependency/import counts to reach zero.",
};

fs.mkdirSync(path.join(ROOT, "reports"), { recursive: true });
fs.writeFileSync(
  path.join(ROOT, "reports", "runtime_dependency_creep_guard.json"),
  JSON.stringify(result, null, 2) + "\n",
);
console.log(JSON.stringify(result, null, 2));
process.exit(pass ? 0 : 1);
