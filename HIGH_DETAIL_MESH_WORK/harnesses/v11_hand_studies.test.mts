import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {it,expect} from 'vitest';
import {Vector3} from 'three';
import {retargetedCharacterSource} from '../../src/character/retargetSource';
import {canonicalSkeleton as rig,PoseEvaluation} from '../../src/rig/skeleton';
import {generateClip} from '../../src/animation/generate';
import {sampleClip} from '../../src/animation/clip';
import {resolveFrame} from '../../src/animation/pipeline';
import {lockAnchors} from '../../src/constraints/locks';
import {applyCharacterPose} from '../../src/character/pose';
import {EXERCISES} from '../../src/exercises/library';

const version=process.env.CANDIDATE_VERSION??'v11_hand_cleanup';
const dest='../reports/poses_'+version;
const files={baseline:process.env.BASELINE_GLB??'../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb',
             candidate:'../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_'+version+'.glb'};

it('captures equipment-free open hand and closed fist review poses with the frozen runtime',async()=>{
 mkdirSync(dest,{recursive:true});
 const ex=EXERCISES.find(e=>e.id==='dumbbell_bicep_curl');
 if(!ex)throw new Error('Missing canonical curl');
 const clip=generateClip(rig,ex),ev=new PoseEvaluation(rig);
 const anchors=lockAnchors(ev,sampleClip(clip,0).pose,clip.locks);
 const frame=resolveFrame(rig,ev,clip,0,{anchors});
 const report:any={};
 for(const [id,path] of Object.entries(files)){
  const b=readFileSync(path);
  const source=retargetedCharacterSource({id,label:id,data:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)});
  const c=await source.build(rig);
  for(const [label,closure] of [['open_hand',0],['closed_fist',1]] as [string,number][]){
   applyCharacterPose(c,rig,frame.pose,ev,{contacts:frame.contacts,grip:{kind:ex.hands.grip,closure}});
   const meshes=[];const p=new Vector3();
   for(const m of c.meshes){
    m.skeleton.update();m.updateWorldMatrix(true,false);
    const positions=[];
    for(let i=0;i<m.geometry.getAttribute('position').count;i++){
     m.getVertexPosition(i,p);p.applyMatrix4(m.matrixWorld);
     positions.push(p.toArray());
    }
    meshes.push({name:m.name,positions,indices:Array.from(m.geometry.index!.array)});
   }
   const result={exercise:label==='open_hand'?'Open Hand':'Closed Fist',label:'review',
                 time:0,meshes,equipment:[]};
   writeFileSync(dest+'/'+label+'_review_'+id+'.json',JSON.stringify(result));
   report[label+'_'+id]={meshVertices:meshes.map(m=>m.positions.length)};
  }
  c.dispose();
 }
 expect(report.open_hand_baseline.meshVertices[0]).toBeGreaterThanOrEqual(33089);
 expect(report.open_hand_candidate.meshVertices[0]).toBeGreaterThan(33089);
 writeFileSync(`../reports/${version}_hand_studies.json`,JSON.stringify(report,null,2));
},900000);
