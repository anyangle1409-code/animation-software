#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const SRC=path.join(ROOT,"src");
const EXT=/\.(?:ts|tsx|js|jsx|mts|mjs)$/i;

const TOKENS=[
  "ANATOMICAL_",
  "SHOULDER_WIDENING",
  "SHOULDER_SETBACK",
  "BASELINE_CHARACTER_URL",
  "DRESSED_CHARACTER_URL",
  "handleGripOffsets",
  "HomeGymPT_Male_BASELINE",
  "CORNER_FINAL",
  "MakeHuman",
  "makehuman",
];

function walk(dir,out=[]){
  if(!fs.existsSync(dir)) return out;
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()) walk(p,out);
    else if(EXT.test(ent.name) && !/\.(?:test|spec)\.(?:ts|tsx|js|jsx|mts|mjs)$/i.test(ent.name) && !/(?:^|[\\/])test(?:s)?[\\/]/i.test(p)) out.push(p);
  }
  return out;
}

const hits=[];
for(const file of walk(SRC)){
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  const lines=fs.readFileSync(file,"utf8").split(/\r?\n/);
  lines.forEach((line,i)=>{
    const tokens=TOKENS.filter(t=>line.includes(t));
    if(tokens.length) hits.push({file:rel,line:i+1,tokens,text:line.trim()});
  });
}

const byToken={};
for(const token of TOKENS){
  const rows=hits.filter(h=>h.tokens.includes(token));
  byToken[token]={
    matches:rows.length,
    files:[...new Set(rows.map(r=>r.file))].sort()
  };
}

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
const out=path.join(ROOT,"reports","legacy_character_coupling.json");
fs.writeFileSync(out,JSON.stringify({
  generatedAt:new Date().toISOString(),
  tokens:TOKENS,
  byToken,
  hits
},null,2)+"\n");

console.log(JSON.stringify({output:path.relative(ROOT,out),byToken},null,2));
