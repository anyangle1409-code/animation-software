#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const checks=[
  ["runtime_dependency_creep","scripts/check-runtime-dependency-creep.mjs",true],
  ["dependency_inventory","scripts/audit-third-party-dependencies.mjs",false],
  ["runtime_usage","scripts/map-third-party-runtime.mjs",false],
  ["first_party_markers","scripts/audit-first-party-markers.mjs",false],
  ["legacy_coupling","scripts/audit-legacy-character-coupling.mjs",false],
  ["final_character_runtime","scripts/audit-final-character-runtime.mjs",true],
  ["external_runtime_resources","scripts/audit-external-runtime-resources.mjs",true],
  ["runtime_network","scripts/audit-runtime-network.mjs",true],
  ["release_readiness","scripts/check-first-party-release-readiness.mjs",true],
];

const results=[];
for(const [id,script,gate] of checks){
  const proc=spawnSync(process.execPath,[script],{
    cwd:ROOT,
    encoding:"utf8",
    stdio:["ignore","pipe","pipe"],
  });
  results.push({
    id,
    script,
    gate,
    status:proc.status,
    pass:proc.status===0,
    stdout:(proc.stdout||"").slice(-12000),
    stderr:(proc.stderr||"").slice(-6000),
  });
}

const summary={
  generatedAt:new Date().toISOString(),
  checks:results.map(({id,script,gate,status,pass})=>({id,script,gate,status,pass})),
  gatePass:results.filter(x=>x.gate).every(x=>x.pass),
  expectedToday:"Operational source/runtime readiness is expected to pass. Final release remains blocked separately by deny-by-default release assets, ORIGINAL v1, production-package offline acceptance and physical-device evidence."
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
fs.writeFileSync(
  path.join(ROOT,"reports","standalone_audit_summary.json"),
  JSON.stringify({summary,details:results},null,2)+"\n"
);

console.log(JSON.stringify(summary,null,2));
process.exit(summary.gatePass?0:1);
