#!/usr/bin/env node
/**
 * Owner-local, loopback-only HTTP server for the ORIGINAL_v1 diagnostic UI.
 * No uploads, model-file serving, npm packages, telemetry or public bind.
 */
import http from 'node:http';
import {readFile,realpath} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname,join,sep} from 'node:path';
const root=dirname(fileURLToPath(new URL('../src/viewer/',import.meta.url)));
const viewerRoot=join(root,'viewer');
const page='originalFullBodyOwnerLocalReview.html';
const allowed=new Set(['.mjs','.html']);
const contentType=p=>p.endsWith('.html')?'text/html; charset=utf-8':'text/javascript; charset=utf-8';
const blocked=(res,status=404)=>{
 res.writeHead(status,{'Content-Type':'text/plain; charset=utf-8',
 'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
 res.end('Not available');
};
export function createOriginalReviewLoopbackServer({directory=viewerRoot}={}){
 return http.createServer(async(req,res)=>{
  if(req.method!=='GET'&&req.method!=='HEAD')return blocked(res,405);
  const raw=(req.url||'').split('?')[0];
  if(!raw||raw.includes('%')||raw.includes('\\')||raw.includes('\0'))
   return blocked(res);
  const name=raw==='/'?page:raw.slice(1);
  if(!/^[A-Za-z][A-Za-z0-9._-]*\.(?:mjs|html)$/.test(name))
   return blocked(res);
  if(name.endsWith('.html')&&name!==page)return blocked(res);
  const filepath=join(directory,name);
  try{
   const [resolved,base]=await Promise.all([realpath(filepath),realpath(directory)]);
   if(!resolved.startsWith(base+sep))return blocked(res);
   const bytes=await readFile(resolved);
   res.writeHead(200,{'Content-Type':contentType(name),
    'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
    'Cross-Origin-Resource-Policy':'same-origin',
    'Referrer-Policy':'no-referrer'});
   res.end(req.method==='HEAD'?undefined:bytes);
  }catch{return blocked(res)}
 });
}
if(process.argv[1] && fileURLToPath(import.meta.url)===process.argv[1]){
 const server=createOriginalReviewLoopbackServer();
 server.listen(4175,'127.0.0.1',()=>{
  process.stdout.write('Private ORIGINAL_v1 review: http://127.0.0.1:4175/\n');
 });
}
