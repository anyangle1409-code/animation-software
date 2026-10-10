/**
 * First-party indexed TRIANGLE mesh and CPU linear-blend skinning reference.
 * NO Three.js or external runtime package. Browser WebGL2 owns rasterization.
 *
 * This is an independently testable MESH rendering path. It does NOT yet
 * replace production GLB loading, realistic shading, original body topology,
 * cartilage physics or production skeletal skinning performance.
 */
import { nativeLookAt, nativePerspective, multiplyNativeMat4 } from './firstPartyWebGL2SkeletonPreview.mjs';
export const NATIVE_SKINNED_KIND = 'hgpt-native-webgl2-indexed-cpu-lbs-v1';

const finite = a => {
  if(!Array.from(a).every(Number.isFinite))throw new RangeError('Nonfinite indexed-mesh input');
};
function assertAffine(m) {
  if(m.length!==16)throw new RangeError('Expected 16-element affine matrix');
  finite(m);
  if(Math.abs(m[3])+Math.abs(m[7])+Math.abs(m[11])+Math.abs(m[15]-1)>1e-4)
    throw new RangeError('Only affine skin matrices permitted');
}
function matricesFromBuffer(values) {
  if(!(values instanceof Float32Array)||!values.length||values.length%16)
    throw new RangeError('Joint palette must be packed Float32Array of affine matrices');
  for(let i=0;i<values.length;i+=16)assertAffine(values.subarray(i,i+16));
  return values.length/16;
}
export function validateNativeSkinnedMesh(mesh) {
  if(!mesh || !(mesh.positions instanceof Float32Array) ||
      !(mesh.jointIndices instanceof Uint16Array) ||
      !(mesh.weights instanceof Float32Array) ||
      !(mesh.indices instanceof Uint16Array || mesh.indices instanceof Uint32Array))
    throw new TypeError('Expected explicit typed indexed geometry/skin arrays');
  if(mesh.positions.length<9 || mesh.positions.length%3)
    throw new RangeError('Mesh must contain >=3 3D rest vertices');
  const n=mesh.positions.length/3;
  if(mesh.jointIndices.length!==n*4 || mesh.weights.length!==n*4)
    throw new RangeError('Every vertex must have four explicit joint influences');
  if(!mesh.indices.length || mesh.indices.length%3 || mesh.indices.length>1000000)
    throw new RangeError('Nonempty bounded triangle index array required');
  if(n>250000)throw new RangeError('Reference CPU skinning size limit');
  if(!(mesh.inverseBindMatrices instanceof Float32Array))
    throw new TypeError('Explicit inverse bind palette is required');
  const bones=matricesFromBuffer(mesh.inverseBindMatrices);
  if(bones>128)throw new RangeError('Reference CPU skinning max 128 palette bones');
  finite(mesh.positions);finite(mesh.weights);
  for(let i=0;i<mesh.indices.length;i++)if(mesh.indices[i]>=n)
    throw new RangeError('Out-of-range triangle vertex');
  for(let i=0;i<n;i++){
    let sum=0;
    for(let k=0;k<4;k++){
      const j=i*4+k,w=mesh.weights[j];
      if(w<0||w>1||mesh.jointIndices[j]>=bones)throw new RangeError('Bad skin index/weight');
      sum+=w;
    }
    if(Math.abs(sum-1)>0.0001)
      throw new RangeError('Four influence weights must sum exactly to one');
  }
  return {vertices:n,triangles:mesh.indices.length/3,bones};
}
export function deformIndexedSkin(mesh,posedWorldMatrices) {
  const shape=validateNativeSkinnedMesh(mesh);
  if(matricesFromBuffer(posedWorldMatrices)!==shape.bones)
    throw new RangeError('Posed joint palette must match inverse bind palette');
  const palette=[];
  for(let j=0;j<shape.bones;j++){
    const posed=posedWorldMatrices.subarray(j*16,j*16+16);
    const bindInv=mesh.inverseBindMatrices.subarray(j*16,j*16+16);
    palette.push(multiplyNativeMat4(posed,bindInv));
  }
  const position=new Float32Array(mesh.positions.length);
  for(let i=0;i<shape.vertices;i++){
    const x=mesh.positions[i*3],y=mesh.positions[i*3+1],z=mesh.positions[i*3+2];
    let px=0,py=0,pz=0;
    for(let k=0;k<4;k++){
      const offset=i*4+k,weight=mesh.weights[offset];
      if(weight===0)continue;
      const matrix=palette[mesh.jointIndices[offset]];
      px+=weight*(matrix[0]*x+matrix[4]*y+matrix[8]*z+matrix[12]);
      py+=weight*(matrix[1]*x+matrix[5]*y+matrix[9]*z+matrix[13]);
      pz+=weight*(matrix[2]*x+matrix[6]*y+matrix[10]*z+matrix[14]);
    }
    position[i*3]=px;position[i*3+1]=py;position[i*3+2]=pz;
  }
  finite(position);
  const normals=new Float32Array(position.length);
  let nondegenerate=0;
  for(let i=0;i<mesh.indices.length;i+=3){
    const ia=mesh.indices[i],ib=mesh.indices[i+1],ic=mesh.indices[i+2];
    const ax=position[ib*3]-position[ia*3],ay=position[ib*3+1]-position[ia*3+1],az=position[ib*3+2]-position[ia*3+2];
    const bx=position[ic*3]-position[ia*3],by=position[ic*3+1]-position[ia*3+1],bz=position[ic*3+2]-position[ia*3+2];
    const nx=ay*bz-az*by,ny=az*bx-ax*bz,nz=ax*by-ay*bx;
    if(Math.hypot(nx,ny,nz)<=1e-14)continue;
    nondegenerate++;
    for(const v of [ia,ib,ic]){
      normals[v*3]+=nx;normals[v*3+1]+=ny;normals[v*3+2]+=nz;
    }
  }
  if(!nondegenerate)throw new RangeError('Every deformed triangle is degenerate');
  for(let i=0;i<shape.vertices;i++){
    const x=normals[i*3],y=normals[i*3+1],z=normals[i*3+2];
    const len=Math.hypot(x,y,z);
    if(len>1e-10){
      normals[i*3]=x/len;normals[i*3+1]=y/len;normals[i*3+2]=z/len;
    }else{
      // No invented normal; zero remains zero and fragment receives ambient.
      normals[i*3]=normals[i*3+1]=normals[i*3+2]=0;
    }
  }
  return {positions:position,normals,indices:mesh.indices,
    triangleCount:nondegenerate,skinningMode:'first-party-cpu-four-weights'};
}
/** First-party rigid affine inverse for rest pose matrices. No scaling/shear. */
export function invertRigidBind(m){
  assertAffine(m);
  const out=new Float32Array(16);
  out[0]=m[0];out[1]=m[4];out[2]=m[8];
  out[4]=m[1];out[5]=m[5];out[6]=m[9];
  out[8]=m[2];out[9]=m[6];out[10]=m[10];
  const tx=m[12],ty=m[13],tz=m[14];
  out[12]=-(out[0]*tx+out[4]*ty+out[8]*tz);
  out[13]=-(out[1]*tx+out[5]*ty+out[9]*tz);
  out[14]=-(out[2]*tx+out[6]*ty+out[10]*tz);
  out[15]=1;
  const rows=[
    [m[0],m[4],m[8]],
    [m[1],m[5],m[9]],
    [m[2],m[6],m[10]],
  ];
  for(let i=0;i<3;i++){
    const len=Math.hypot(...rows[i]);
    if(Math.abs(len-1)>0.001)throw new RangeError('Rigid bind requires orthonormal rotation, no scale');
    for(let j=0;j<i;j++){
      const dot=rows[i].reduce((v,x,k)=>v+x*rows[j][k],0);
      if(Math.abs(dot)>0.001)throw new RangeError('Rigid bind shear/nonorthogonal rotation is forbidden');
    }
  }
  const [u,v,w]=rows;
  const det=u[0]*(v[1]*w[2]-v[2]*w[1])
    -u[1]*(v[0]*w[2]-v[2]*w[0])
    +u[2]*(v[0]*w[1]-v[1]*w[0]);
  if(Math.abs(det-1)>0.002)
    throw new RangeError('Rigid bind must have right-handed rotation, no reflection');
  return out;
}
function triangleShader(gl,type,source){
  const id=gl.createShader(type);
  if(!id)throw new Error('Native triangle shader creation failed');
  gl.shaderSource(id,source);gl.compileShader(id);
  if(!gl.getShaderParameter(id,gl.COMPILE_STATUS)){
    const msg=gl.getShaderInfoLog(id)||'unknown';
    gl.deleteShader(id);throw new Error('Native triangle shader compile: '+msg);
  }
  return id;
}
function triangleProgram(gl){
  const vs='#version 300 es\nprecision highp float;\nlayout(location=0) in vec3 aPos;\nlayout(location=1) in vec3 aNormal;\nuniform mat4 uViewProjection;\nout vec3 vNormal;\nvoid main(){gl_Position=uViewProjection*vec4(aPos,1.0);vNormal=aNormal;}';
  const fs='#version 300 es\nprecision highp float;\nin vec3 vNormal;\nuniform vec3 uColor;\nout vec4 outColor;\nvoid main(){vec3 n=normalize(vNormal);float light=0.25+0.75*max(dot(n,normalize(vec3(0.3,0.65,0.72))),0.0);outColor=vec4(uColor*light,1.0);}';
  const a=triangleShader(gl,gl.VERTEX_SHADER,vs);
  const b=triangleShader(gl,gl.FRAGMENT_SHADER,fs);
  const p=gl.createProgram();
  if(!p){gl.deleteShader(a);gl.deleteShader(b);throw new Error('Triangle GPU program unavailable');}
  gl.attachShader(p,a);gl.attachShader(p,b);gl.linkProgram(p);
  gl.deleteShader(a);gl.deleteShader(b);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS)){
    const msg=gl.getProgramInfoLog(p)||'unknown';
    gl.deleteProgram(p);throw new Error('Native triangle program link: '+msg);
  }
  return p;
}
export function createNativeIndexedMeshWebGL2(canvas){
  const gl=canvas.getContext('webgl2',{antialias:true,alpha:false,depth:true});
  if(!gl)throw new Error('WebGL2 unavailable for native indexed mesh');
  let program=null,vao=null,pos=null,norm=null,indexBuffer=null,loc=null,colorLoc=null;
  let disposed=false,lost=false,draws=0,width=1,height=1;
  const prepare=()=>{
    program=triangleProgram(gl);
    vao=gl.createVertexArray();pos=gl.createBuffer();norm=gl.createBuffer();indexBuffer=gl.createBuffer();
    if(!vao||!pos||!norm||!indexBuffer)throw new Error('Native indexed mesh GPU buffers unavailable');
    loc=gl.getUniformLocation(program,'uViewProjection');
    colorLoc=gl.getUniformLocation(program,'uColor');
    if(loc===null||colorLoc===null)throw new Error('Triangle shader uniform missing');
    gl.bindVertexArray(vao);
    for(const [offset,buffer] of [[0,pos],[1,norm]]){
      gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
      gl.enableVertexAttribArray(offset);
      gl.vertexAttribPointer(offset,3,gl.FLOAT,false,0,0);
    }
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indexBuffer);
    gl.bindVertexArray(null);gl.enable(gl.DEPTH_TEST);
  };
  const onLost=e=>{e.preventDefault();lost=true;};
  const onRestore=()=>{if(disposed)return;lost=false;prepare();};
  canvas.addEventListener('webglcontextlost',onLost);
  canvas.addEventListener('webglcontextrestored',onRestore);
  try{prepare();}catch(e){
    canvas.removeEventListener('webglcontextlost',onLost);
    canvas.removeEventListener('webglcontextrestored',onRestore);
    throw e;
  }
  return {
    setSize(w,h,dpr=1){
      if(disposed)throw new Error('Native mesh renderer disposed');
      finite([w,h,dpr]);
      if(w<=0||h<=0||dpr<=0)throw new RangeError('Invalid indexed viewport size');
      width=Math.max(1,Math.floor(w*dpr));height=Math.max(1,Math.floor(h*dpr));
      canvas.width=width;canvas.height=height;
      if(!lost)gl.viewport(0,0,width,height);
    },
    render(geometry,{eye=[1.6,1.4,2.8],target=[0,1,0],color=[0.74,0.8,0.92]}={}){
      if(disposed)throw new Error('Native mesh renderer disposed');
      if(lost)return false;
      if(!(geometry.positions instanceof Float32Array)||
          !(geometry.normals instanceof Float32Array)||
          !(geometry.indices instanceof Uint16Array||geometry.indices instanceof Uint32Array)||
          geometry.positions.length!==geometry.normals.length||
          geometry.positions.length<9||geometry.positions.length%3||
          geometry.indices.length<3||geometry.indices.length%3)
        throw new RangeError('Malformed posed indexed triangle mesh');
      finite(geometry.positions);finite(geometry.normals);
      finite([...eye,...target,...color]);
      if(color.length!==3||color.some(v=>v<0||v>1))throw new RangeError('Invalid material color');
      for(const i of geometry.indices)if(i>=geometry.positions.length/3)throw new RangeError('Invalid triangle index');
      const vp=multiplyNativeMat4(nativePerspective(38*Math.PI/180,width/height,.05,100),nativeLookAt(eye,target));
      gl.viewport(0,0,width,height);gl.clearColor(.055,.075,.1,1);
      gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      gl.useProgram(program);gl.uniformMatrix4fv(loc,false,vp);gl.uniform3fv(colorLoc,color);
      gl.bindVertexArray(vao);
      gl.bindBuffer(gl.ARRAY_BUFFER,pos);gl.bufferData(gl.ARRAY_BUFFER,geometry.positions,gl.DYNAMIC_DRAW);
      gl.bindBuffer(gl.ARRAY_BUFFER,norm);gl.bufferData(gl.ARRAY_BUFFER,geometry.normals,gl.DYNAMIC_DRAW);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indexBuffer);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,geometry.indices,gl.DYNAMIC_DRAW);
      gl.drawElements(gl.TRIANGLES,geometry.indices.length,
        geometry.indices instanceof Uint32Array?gl.UNSIGNED_INT:gl.UNSIGNED_SHORT,0);
      gl.bindVertexArray(null);draws++;return true;
    },
    get frameCount(){return draws;},get contextLost(){return lost;},
    get kind(){return NATIVE_SKINNED_KIND;},
    dispose(){
      if(disposed)return;disposed=true;
      canvas.removeEventListener('webglcontextlost',onLost);
      canvas.removeEventListener('webglcontextrestored',onRestore);
      if(!lost){gl.deleteBuffer(pos);gl.deleteBuffer(norm);gl.deleteBuffer(indexBuffer);
        gl.deleteVertexArray(vao);gl.deleteProgram(program);}
    }
  };
}
/**
 * Synthetic TWO-BONE continuous closed tube around rest-pose world-space bone
 * centres. Deliberately a low-detail deformable proxy, not human skin asset.
 */
export function makeTwoBoneSkinProbe(start,elbow,end,{radius=.055,sides=10}={}){
  if(![start,elbow,end].every(p=>p.length===3))throw new RangeError('Expected three rest joints');
  finite([...start,...elbow,...end,radius,sides]);
  if(!(radius>0&&sides>=3&&sides<=64&&Number.isInteger(sides)))
    throw new RangeError('Invalid tube geometry');
  const lerp=(a,b,t)=>a.map((v,i)=>v*(1-t)+b[i]*t);
  const sub=(a,b)=>a.map((v,i)=>v-b[i]);
  const len=a=>Math.hypot(...a);
  const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const norm=v=>{const n=len(v);if(n<1e-7)throw new RangeError('Degenerate source bone');return v.map(x=>x/n);};
  const sections=[
    [start,0,1.06],[lerp(start,elbow,.35),.04,1.04],
    [lerp(start,elbow,.8),.22,.95],[elbow,.5,.83],
    [lerp(elbow,end,.2),.79,.84],[lerp(elbow,end,.65),.97,.76],
    [end,1,.61]
  ];
  const vertices=[],joints=[],weights=[],tri=[];
  sections.forEach(([centre,influence,scale],index)=>{
    const before=sections[Math.max(0,index-1)][0];
    const after=sections[Math.min(sections.length-1,index+1)][0];
    const axis=norm(sub(after,before));
    const seed=Math.abs(axis[1])>.9?[1,0,0]:[0,1,0];
    const side=norm(cross(axis,seed));
    const other=norm(cross(axis,side));
    for(let k=0;k<sides;k++){
      const theta=2*Math.PI*k/sides;
      const p=centre.map((v,j)=>v+radius*scale*(Math.cos(theta)*side[j]+Math.sin(theta)*other[j]));
      vertices.push(...p);
      joints.push(0,1,0,0);
      weights.push(1-influence,influence,0,0);
    }
  });
  for(let i=0;i<sections.length-1;i++)for(let k=0;k<sides;k++){
    const a=i*sides+k,b=i*sides+(k+1)%sides;
    const c=(i+1)*sides+k,d=(i+1)*sides+(k+1)%sides;
    tri.push(a,b,c,b,d,c);
  }
  // closed ends: triangle fan (no additional vertices/influences required)
  for(let k=1;k<sides-1;k++){
    tri.push(0,k+1,k);
    const j=(sections.length-1)*sides;
    tri.push(j,j+k,j+k+1);
  }
  return {
    positions:new Float32Array(vertices),
    indices:new Uint16Array(tri),
    jointIndices:new Uint16Array(joints),
    weights:new Float32Array(weights),
  };
}
