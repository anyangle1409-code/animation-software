#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const ROOT_FILES=["index.html"];
const SOURCE_DIRS=["src"];
const EXT=/\.(?:ts|tsx|js|jsx|mts|mjs|css|html)$/i;
const IGNORE=new Set([".git","node_modules","dist","dist-web","coverage"]);

function walk(dir,out=[]){
  if(!fs.existsSync(dir)) return out;
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    if(ent.isDirectory() && IGNORE.has(ent.name)) continue;
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

const files=[
  ...ROOT_FILES.map(x=>path.join(ROOT,x)).filter(fs.existsSync),
  ...SOURCE_DIRS.flatMap(x=>walk(path.join(ROOT,x))),
];

const rules=[
  ["absolute_http", /https?:\/\/[^\s"'\)<>]+/g],
  ["protocol_relative", /(?:src|href|url)\s*\(?\s*["']?\/\/[^\s"'\)<>]+/gi],
  ["css_import", /@import\s+(?:url\()?\s*["'][^"']+["']/gi],
  ["font_face", /@font-face\b/gi],
  ["websocket", /\bnew\s+WebSocket\s*\(/g],
  ["event_source", /\bnew\s+EventSource\s*\(/g],
  ["remote_fetch", /\bfetch\s*\(\s*["']https?:\/\//g],
  ["remote_xhr", /\.open\s*\(\s*["'][A-Z]+["']\s*,\s*["']https?:\/\//gi],
];

const hits=[];
for(const file of files){
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  const text=fs.readFileSync(file,"utf8");
  const lines=text.split(/\r?\n/);
  lines.forEach((line,i)=>{
    for(const [rule,re] of rules){
      re.lastIndex=0;
      if(re.test(line)) hits.push({file:rel,line:i+1,rule,text:line.trim()});
    }
  });
}

const allowlisted=hits.filter(hit=>
  // No allowlist entries at present. This structure is intentional so a future
  // exception must be explicit and reviewable rather than silently ignored.
  false
);
const blockers=hits.filter(hit=>!allowlisted.includes(hit));
const result={
  generatedAt:new Date().toISOString(),
  pass:blockers.length===0,
  blockerCount:blockers.length,
  blockers,
  note:"Scans distributable source/HTML/CSS for remote runtime resources. System font family names are not remote fetches."
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
const out=path.join(ROOT,"reports","external_runtime_resources.json");
fs.writeFileSync(out,JSON.stringify(result,null,2)+"\n");
console.log(JSON.stringify(result,null,2));
process.exit(result.pass?0:1);
