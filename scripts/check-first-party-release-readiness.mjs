#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const ROOT=process.cwd();
const SRC=path.join(ROOT,"src");
const PKG=JSON.parse(fs.readFileSync(path.join(ROOT,"package.json"),"utf8"));

const SOURCE_EXT=/\.(?:ts|tsx|js|jsx|mts|mjs)$/i;
const ASSET_EXT=/\.(?:glb|gltf|fbx|obj|blend|png|jpg|jpeg|webp|svg|ico|woff2?|ttf|otf|mp3|wav|ogg|mp4|mov)$/i;
const IGNORE=new Set([".git","node_modules","dist","coverage"]);
const isOperationalSource=(file)=>{
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  return !/\.(?:test|spec)\.(?:ts|tsx|js|jsx|mts|mjs)$/i.test(rel) &&
    !/(?:^|\/)test(?:s)?\//i.test(rel);
};
const LEGACY_PATTERNS=[
  /HOME_GYM_PT_GPT_MESH_HANDOFF/i,
  /review-assets[\\/]characters/i,
  /BASELINE_v[5-8]/i,
  /CORNER_FINAL/i,
  /(?:^|[_-])v(?:9|10|11|12|13|14|15)[a-z]?(?:[_-]|\.)/i,
  /MakeHuman/i,
];

function walk(dir,out=[]){
  for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
    if(ent.isDirectory() && IGNORE.has(ent.name)) continue;
    const p=path.join(dir,ent.name);
    if(ent.isDirectory()) walk(p,out);
    else out.push(p);
  }
  return out;
}

const sourceFiles=fs.existsSync(SRC)
  ? walk(SRC).filter(f=>SOURCE_EXT.test(f) && isOperationalSource(f))
  : [];
const bareImports=[];

const importPatterns=[
  /\bfrom\s+["']([^"']+)["']/g,
  /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g,
  /\bimport\s+["']([^"']+)["']/g,
];

for(const file of sourceFiles){
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  const text=fs.readFileSync(file,"utf8");
  for(const re of importPatterns){
    for(const match of text.matchAll(re)){
      const spec=match[1];
      if(spec.startsWith(".") || spec.startsWith("/") || spec.startsWith("node:")) continue;
      const line=text.slice(0,match.index).split(/\r?\n/).length;
      bareImports.push({file:rel,line,specifier:spec});
    }
  }
}

const allFiles=walk(ROOT);
const legacyFiles=allFiles
  .map(f=>path.relative(ROOT,f).replaceAll("\\","/"))
  .filter(rel=>ASSET_EXT.test(rel) && LEGACY_PATTERNS.some(re=>re.test(rel)));
const operationalLegacyAssets=legacyFiles.filter(rel=>
  /^(?:public|characters|src\/assets)\//i.test(rel)
);
const referenceLegacyFiles=legacyFiles.filter(rel=>!operationalLegacyAssets.includes(rel));

const makeHumanSourceFiles=[];
for(const file of sourceFiles){
  const rel=path.relative(ROOT,file).replaceAll("\\","/");
  const text=fs.readFileSync(file,"utf8");
  if(
    /^src\/body\/anatomical.*\.ts$/i.test(rel) ||
    /MakeHuman|makehuman|THIRD_PARTY_ASSETS/.test(text)
  ) {
    makeHumanSourceFiles.push(rel);
  }
}

const runtimeDependencies=Object.entries(PKG.dependencies||{}).map(([name,version])=>({name,version}));

const blockers={
  runtimeDependencies,
  bareImports,
  operationalLegacyAssets,
  makeHumanSourceFiles:[...new Set(makeHumanSourceFiles)].sort(),
};

const pass=
  runtimeDependencies.length===0 &&
  bareImports.length===0 &&
  operationalLegacyAssets.length===0 &&
  blockers.makeHumanSourceFiles.length===0;

const report={
  generatedAt:new Date().toISOString(),
  goal:"Zero third-party runtime dependencies and zero legacy/third-party creative assets in the standalone distributable source path.",
  pass,
  blockerCounts:Object.fromEntries(Object.entries(blockers).map(([k,v])=>[k,v.length])),
  blockers,
  advisory:{
    referenceLegacyFiles,
    note:"Reference/dev legacy files outside operational asset roots may remain in the repository but must stay excluded by the release allowlist."
  },
  notes:[
    "Development tools outside the shipped runtime are audited separately.",
    "A PASS here is an engineering gate, not a legal opinion.",
    "ORIGINAL v1 provenance and release allowlist approval remain separate required gates."
  ]
};

fs.mkdirSync(path.join(ROOT,"reports"),{recursive:true});
const out=path.join(ROOT,"reports","first_party_release_readiness.json");
fs.writeFileSync(out,JSON.stringify(report,null,2)+"\n");
console.log(JSON.stringify(report,null,2));
process.exit(pass ? 0 : 1);
