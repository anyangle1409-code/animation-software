#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const DIST=process.argv[2] ? path.resolve(ROOT,process.argv[2]) : path.join(ROOT,"dist");

const TEXT_EXT=/\.(?:js|mjs|cjs|css|html|json|map|txt|svg)$/i;
const ASSET_EXT=/\.(?:glb|gltf|fbx|obj|png|jpg|jpeg|webp|svg|ico|woff2?|ttf|otf|mp3|wav|ogg|mp4|mov)$/i;
const FORBIDDEN_TEXT=[
  ["react", /(?:^|[^A-Za-z0-9_$])React(?:DOM)?(?:[^A-Za-z0-9_$]|$)|react-dom|react\/jsx-runtime/i],
  ["three", /three\.module|THREE\.|three\/examples|three-stdlib|GLTFLoader|GLTFExporter/i],
  ["react_three", /@react-three|react-three-fiber|react-three\/drei/i],
  ["zustand", /zustand/i],
  ["makehuman", /MakeHuman|makehuman/i],
  ["legacy_character", /CORNER_FINAL|BASELINE_v[5-8]|V13e|V15f|HIGH_DETAIL_CANDIDATE/i],
  ["remote_url", /https?:\/\/|(?:src|href)=["']\/\//i],
];

function walk(dir,out=[]){
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()) walk(p,out);
    else out.push(p);
  }
  return out;
}

if(!fs.existsSync(DIST)){
  const result={pass:false,error:`Production output not found: ${path.relative(ROOT,DIST)}`};
  console.error(JSON.stringify(result,null,2));
  process.exit(1);
}

const files=walk(DIST);
const textHits=[];
const assetHits=[];

for(const file of files){
  const rel=path.relative(DIST,file).replaceAll("\\","/");
  if(TEXT_EXT.test(file)){
    const content=fs.readFileSync(file,"utf8");
    const lines=content.split(/\r?\n/);
    for(let i=0;i<lines.length;i++){
      for(const [rule,re] of FORBIDDEN_TEXT){
        re.lastIndex=0;
        if(re.test(lines[i])){
          textHits.push({
            file:rel,
            line:i+1,
            rule,
            sample:lines[i].trim().slice(0,240),
          });
        }
      }
    }
  }
  if(ASSET_EXT.test(file)){
    if(/(?:CORNER_FINAL|BASELINE_v[5-8]|v(?:9|10|11|12|13|14|15)[a-z]?|makehuman)/i.test(rel)){
      assetHits.push(rel);
    }
  }
}

const packageArtifacts=files
  .map(f=>path.relative(DIST,f).replaceAll("\\","/"))
  .filter(rel=>/(?:^|\/)node_modules(?:\/|$)|package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$/i.test(rel));

const result={
  generatedAt:new Date().toISOString(),
  productionOutput:path.relative(ROOT,DIST).replaceAll("\\","/"),
  pass:textHits.length===0 && assetHits.length===0 && packageArtifacts.length===0,
  counts:{
    files:files.length,
    forbiddenTextHits:textHits.length,
    forbiddenAssetHits:assetHits.length,
    packageArtifacts:packageArtifacts.length,
  },
  blockers:{
    textHits,
    assetHits,
    packageArtifacts,
  },
  note:"Heuristic production-output audit. Source provenance and component manifest gates are separately required."
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
fs.writeFileSync(
  path.join(ROOT,"reports","production_output_third_party_audit.json"),
  JSON.stringify(result,null,2)+"\n"
);
console.log(JSON.stringify(result,null,2));
process.exit(result.pass?0:1);
