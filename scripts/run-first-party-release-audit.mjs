#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const checks=[
  ["standalone_source","scripts/run-standalone-audit.mjs",[]],
  ["production_output","scripts/audit-production-output.mjs",["dist"]],
  ["release_components","scripts/audit-first-party-release-components.mjs",[]],
  ["release_allowlist","scripts/audit-release-allowlist.mjs",["dist"]],
];

const results=[];
for(const [id,script,args] of checks){
  const proc=spawnSync(process.execPath,[script,...args],{
    cwd:ROOT,
    encoding:"utf8",
    stdio:["ignore","pipe","pipe"]
  });
  results.push({
    id,
    pass:proc.status===0,
    status:proc.status,
    stdout:(proc.stdout||"").slice(-12000),
    stderr:(proc.stderr||"").slice(-6000),
  });
}

const result={
  generatedAt:new Date().toISOString(),
  pass:results.every(x=>x.pass),
  checks:results.map(({id,pass,status})=>({id,pass,status})),
  note:"Automated release gate. Offline browser acceptance remains an additional required gate."
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
fs.writeFileSync(
  path.join(ROOT,"reports","first_party_release_audit.json"),
  JSON.stringify({result,details:results},null,2)+"\n"
);
console.log(JSON.stringify(result,null,2));
process.exit(result.pass?0:1);
