#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const SRC=path.join(ROOT,"src");
const TARGETS=[
  "react",
  "react-dom",
  "three",
  "@react-three/fiber",
  "@react-three/drei",
  "zustand",
];

function isTestFile(name){
  return /\.(?:test|spec)\.(?:ts|tsx|js|jsx|mts|mjs)$/i.test(name);
}

function walk(dir,out=[]){
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()){
      if(!/^tests?$/i.test(ent.name)) walk(p,out);
    }else if(/\.(?:ts|tsx|js|jsx|mts|mjs)$/.test(ent.name) && !isTestFile(ent.name)){
      out.push(p);
    }
  }
  return out;
}

function targetOf(specifier){
  return TARGETS.find(target =>
    specifier===target || specifier.startsWith(target+"/")
  ) || null;
}

if(!fs.existsSync(SRC)){
  console.error("Missing src directory. Run from repository root.");
  process.exit(1);
}

const usage=Object.fromEntries(TARGETS.map(target=>[target,[]]));

const fromImport=/\bimport\s+([^;\n]*?)\s+from\s+["']([^"']+)["']/g;
const bareImport=/\bimport\s+["']([^"']+)["']/g;
const dynamicImport=/\bimport\s*\(\s*["']([^"']+)["']\s*\)/g;

for(const file of walk(SRC)){
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  const text=fs.readFileSync(file,"utf8");

  for(const match of text.matchAll(fromImport)){
    const target=targetOf(match[2]);
    if(!target) continue;
    usage[target].push({
      file:rel,
      line:text.slice(0,match.index).split(/\r?\n/).length,
      specifier:match[2],
      imported:match[1].trim(),
    });
  }

  for(const match of text.matchAll(bareImport)){
    const target=targetOf(match[1]);
    if(!target) continue;
    usage[target].push({
      file:rel,
      line:text.slice(0,match.index).split(/\r?\n/).length,
      specifier:match[1],
      imported:"side effect",
    });
  }

  for(const match of text.matchAll(dynamicImport)){
    const target=targetOf(match[1]);
    if(!target) continue;
    usage[target].push({
      file:rel,
      line:text.slice(0,match.index).split(/\r?\n/).length,
      specifier:match[1],
      imported:"dynamic import",
    });
  }
}

const summary=Object.fromEntries(
  TARGETS.map(target=>[target,{
    importCount:usage[target].length,
    files:[...new Set(usage[target].map(x=>x.file))].sort(),
    specifiers:[...new Set(usage[target].map(x=>x.specifier))].sort(),
  }])
);

const report={
  generatedAt:new Date().toISOString(),
  scope:"Operational source only; test/spec files excluded.",
  targets:TARGETS,
  summary,
  usage,
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
const jsonPath=path.join(ROOT,"reports","third_party_runtime_usage.json");
fs.writeFileSync(jsonPath,JSON.stringify(report,null,2)+"\n");

let md="# Runtime dependency usage map\n\n";
md+="Generated from actual ESM import specifiers. Test/spec files are excluded.\n\n";
for(const target of TARGETS){
  const row=summary[target];
  md+="## "+target+"\n\n";
  md+="Imports: "+row.importCount+"; files: "+row.files.length+".\n\n";
  for(const file of row.files) md+="- "+file+"\n";
  if(row.files.length===0) md+="- none\n";
  md+="\n";
}

const mdPath=path.join(ROOT,"reports","third_party_runtime_usage.md");
fs.writeFileSync(mdPath,md);

console.log(JSON.stringify({
  json:path.relative(ROOT,jsonPath),
  markdown:path.relative(ROOT,mdPath),
  summary,
},null,2));
