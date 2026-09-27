#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const EXT=/\.(?:ts|tsx|js|jsx|mts|mjs|json|md|html|css)$/i;
const MARKERS=[
  "MakeHuman",
  "makehuman",
  "THIRD_PARTY",
  "third-party",
  "CC0",
  "Meshy",
  "imported source",
  "imported character",
  "BASELINE_v8",
  "CORNER_FINAL",
  "V13e",
  "v13e",
  "V15f",
  "v15f",
];

const IGNORE_DIRS=new Set([".git","node_modules","dist"]);

function walk(dir,out=[]){
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    if(ent.isDirectory() && IGNORE_DIRS.has(ent.name)) continue;
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()) walk(p,out);
    else if(EXT.test(ent.name)) out.push(p);
  }
  return out;
}

const hits=[];
for(const file of walk(ROOT)){
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  const lines=fs.readFileSync(file,"utf8").split(/\r?\n/);
  lines.forEach((line,i)=>{
    const markers=MARKERS.filter(m=>line.includes(m));
    if(markers.length) hits.push({file:rel,line:i+1,markers,text:line.trim()});
  });
}

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
const out=path.join(ROOT,"reports","first_party_marker_audit.json");
fs.writeFileSync(out,JSON.stringify({
  generatedAt:new Date().toISOString(),
  markers:MARKERS,
  hitCount:hits.length,
  hits
},null,2)+"\n");

console.log(JSON.stringify({
  output:path.relative(ROOT,out),
  hitCount:hits.length,
  files:[...new Set(hits.map(x=>x.file))].sort()
},null,2));
