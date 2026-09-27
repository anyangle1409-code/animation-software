#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const SRC=path.join(ROOT,"src");
const EXT=/\.(?:ts|tsx|js|jsx|mts|mjs)$/i;
const IGNORE=new Set([".git","node_modules","dist","coverage"]);
const ALLOWLIST=JSON.parse(
  fs.readFileSync(path.join(ROOT,"RUNTIME_NETWORK_ALLOWLIST.json"),"utf8")
);
const ALLOWED=ALLOWLIST.entries||[];

function walk(dir,out=[]){
  if(!fs.existsSync(dir)) return out;
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    if(ent.isDirectory() && IGNORE.has(ent.name)) continue;
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()) walk(p,out);
    else if(EXT.test(ent.name)) out.push(p);
  }
  return out;
}

const blockers=[];
const localResources=[];
const reviewedDynamic=[];

function reviewed(file,line){
  return ALLOWED.find(entry =>
    entry.file===file &&
    typeof entry.contains==="string" &&
    line.includes(entry.contains)
  );
}
const primitives=[
  ["websocket", /\bnew\s+WebSocket\s*\(/],
  ["event_source", /\bnew\s+EventSource\s*\(/],
  ["xml_http_request", /\bnew\s+XMLHttpRequest\s*\(/],
  ["send_beacon", /\bnavigator\.sendBeacon\s*\(/],
];

for(const file of walk(SRC)){
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  const lines=fs.readFileSync(file,"utf8").split(/\r?\n/);

  lines.forEach((line,index)=>{
    const lineNo=index+1;

    for(const [rule,re] of primitives){
      re.lastIndex=0;
      if(re.test(line)){
        blockers.push({file:rel,line:lineNo,rule,text:line.trim()});
      }
    }

    if(/\bfetch\s*\(/.test(line)){
      const literal=line.match(/\bfetch\s*\(\s*["']([^"']+)["']/);
      if(!literal){
        const approval=reviewed(rel,line);
        if(approval){
          reviewedDynamic.push({
            file:rel,
            line:lineNo,
            classification:approval.classification,
            constraint:approval.constraint,
            text:line.trim()
          });
        }else{
          blockers.push({
            file:rel,line:lineNo,rule:"dynamic_fetch_requires_review",text:line.trim()
          });
        }
      }else{
        const target=literal[1];
        if(/^(?:https?:)?\/\//i.test(target)){
          blockers.push({
            file:rel,line:lineNo,rule:"remote_fetch",target,text:line.trim()
          });
        }else{
          localResources.push({file:rel,line:lineNo,target});
        }
      }
    }
  });
}

const result={
  generatedAt:new Date().toISOString(),
  pass:blockers.length===0,
  blockers,
  localResourceFetches:localResources,
  reviewedDynamicLocalFetches:reviewedDynamic,
  note:"Relative/local packaged resource fetches are not third-party dependencies. Dynamic fetches require a narrow source allowlist; remote network access is never allowlisted here."
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
fs.writeFileSync(
  path.join(ROOT,"reports","runtime_network_audit.json"),
  JSON.stringify(result,null,2)+"\n"
);
console.log(JSON.stringify(result,null,2));
process.exit(result.pass?0:1);
