#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const pkg=JSON.parse(fs.readFileSync(path.join(ROOT,"package.json"),"utf8"));
const policy=JSON.parse(fs.readFileSync(path.join(ROOT,"RUNTIME_MIGRATION_ALLOWLIST.json"),"utf8"));

const current=Object.keys(pkg.dependencies||{}).sort();
const allowed=new Set(policy.allowed_existing_runtime_dependencies||[]);
const introduced=current.filter(name=>!allowed.has(name));

const result={
  generatedAt:new Date().toISOString(),
  pass:introduced.length===0,
  currentRuntimeDependencies:current,
  currentCount:current.length,
  allowedMigrationCeiling:[...allowed].sort(),
  newlyIntroduced:introduced,
  finalTarget:[],
  note:"PASS only means no new runtime dependency has crept in. Final standalone readiness still requires currentCount=0."
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
fs.writeFileSync(
  path.join(ROOT,"reports","runtime_dependency_creep_guard.json"),
  JSON.stringify(result,null,2)+"\n"
);
console.log(JSON.stringify(result,null,2));
process.exit(result.pass?0:1);
