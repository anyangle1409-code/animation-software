#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const SRC=path.join(ROOT,"src");
const EXT=/\.(?:ts|tsx|js|jsx|mts|mjs)$/i;
const TOKENS=[
  "HomeGymPT_Male_BASELINE_v8",
  "CORNER_FINAL",
  "V13e",
  "V15f",
  "MakeHuman",
  "makehuman",
  "homeGymPTMale",
  "Meshy",
];

function walk(dir,out=[]){
  if(!fs.existsSync(dir)) return out;
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()) walk(p,out);
    else if(
      EXT.test(ent.name) &&
      !/\.(?:test|spec)\.(?:ts|tsx|js|jsx|mts|mjs)$/i.test(ent.name) &&
      !/(?:^|[\\/])test(?:s)?[\\/]/i.test(p)
    ) out.push(p);
  }
  return out;
}

const hits=[];
for(const file of walk(SRC)){
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  const lines=fs.readFileSync(file,"utf8").split(/\r?\n/);
  lines.forEach((line,index)=>{
    const found=TOKENS.filter(token=>line.includes(token));
    if(found.length){
      hits.push({file:rel,line:index+1,tokens:found,text:line.trim()});
    }
  });
}

const result={
  generatedAt:new Date().toISOString(),
  pass:hits.length===0,
  tokens:TOKENS,
  hits,
  note:"Final production character-path gate. Historical docs outside src are intentionally not scanned."
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
fs.writeFileSync(
  path.join(ROOT,"reports","legacy_character_runtime_path.json"),
  JSON.stringify(result,null,2)+"\n"
);
console.log(JSON.stringify(result,null,2));
process.exit(result.pass?0:1);
