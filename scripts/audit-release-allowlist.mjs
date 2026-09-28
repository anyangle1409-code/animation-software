#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const DIST=process.argv[2] ? path.resolve(ROOT,process.argv[2]) : path.join(ROOT,"dist");
const POLICY=JSON.parse(
  fs.readFileSync(path.join(ROOT,"RELEASE_ASSET_ALLOWLIST.json"),"utf8")
);

function walk(dir,out=[]){
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()) walk(p,out);
    else out.push(p);
  }
  return out;
}

const SPECIAL=new Set(["\\","^","$",".","*","+","?","(",")","[","]","{","}","|"]);
function escapeChar(ch){
  return SPECIAL.has(ch) ? "\\"+ch : ch;
}

function globRegex(pattern){
  const normalized=pattern.replaceAll("\\","/");
  let out="^";
  for(let i=0;i<normalized.length;){
    if(normalized.startsWith("**/",i)){
      out+="(?:.*/)?";
      i+=3;
    }else if(normalized.startsWith("**",i)){
      out+=".*";
      i+=2;
    }else if(normalized[i]==="*"){
      out+="[^/]*";
      i+=1;
    }else if(normalized[i]==="?"){
      out+="[^/]";
      i+=1;
    }else{
      out+=escapeChar(normalized[i]);
      i+=1;
    }
  }
  return new RegExp(out+"$","i");
}

if(!fs.existsSync(DIST)){
  console.error(JSON.stringify({
    pass:false,
    error:"Missing production output: "+path.relative(ROOT,DIST)
  },null,2));
  process.exit(1);
}

const approved=(POLICY.approved_paths||[]).map(pattern=>({pattern,re:globRegex(pattern)}));
const denied=(POLICY.explicitly_denied_patterns||[]).map(pattern=>({pattern,re:globRegex(pattern)}));
const files=walk(DIST).map(file=>path.relative(DIST,file).replaceAll("\\","/")).sort();

const deniedHits=[];
const unapproved=[];

for(const file of files){
  const denial=denied.find(entry=>entry.re.test(file));
  if(denial) deniedHits.push({file,pattern:denial.pattern});

  const approval=approved.find(entry=>entry.re.test(file));
  if(!approval) unapproved.push(file);
}

const result={
  generatedAt:new Date().toISOString(),
  productionOutput:path.relative(ROOT,DIST).replaceAll("\\","/"),
  mode:POLICY.mode,
  approvedPatterns:approved.map(x=>x.pattern),
  fileCount:files.length,
  pass:approved.length>0 && deniedHits.length===0 && unapproved.length===0,
  blockers:{
    noApprovedPatterns:approved.length===0,
    deniedHits,
    unapproved,
  },
  note:"Deny-by-default production packaging gate. A file must be explicitly approved and must not match a denied pattern."
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
fs.writeFileSync(
  path.join(ROOT,"reports","release_allowlist_audit.json"),
  JSON.stringify(result,null,2)+"\n"
);
console.log(JSON.stringify(result,null,2));
process.exit(result.pass?0:1);
