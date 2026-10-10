/**
 * Home Gym PT first-party WebGL2 posed bone preview.
 * Native GPU path; NO Three.js, React, Vite or shader library imports.
 * Experimental skeletal LINE preview only. Does NOT render skinned character,
 * muscle deformation, articular contacts, shadows or full production geometry.
 */
export const NATIVE_RENDERER_KIND = 'hgpt-native-webgl2-bones-v1';
const finite = values => { if(!Array.from(values).every(Number.isFinite)) throw new RangeError('Nonfinite geometry'); };
const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
export function unit3(v) {
  finite(v);
  const n=Math.hypot(...v);
  if(n<1e-12) throw new RangeError('Degenerate 3D direction');
  return v.map(x=>x/n);
}
/** Column-major view transform, positive Y up, camera looks down its local -Z. */
export function nativeLookAt(eye,target,up=[0,1,0]) {
  finite([...eye,...target,...up]);
  const z=unit3(eye.map((n,i)=>n-target[i]));
  const x=unit3(cross(up,z));
  const y=cross(z,x);
  return new Float32Array([
    x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,
    -dot(x,eye),-dot(y,eye),-dot(z,eye),1,
  ]);
}
export function nativePerspective(fov,aspect,near,far) {
  finite([fov,aspect,near,far]);
  if(!(fov>0&&fov<Math.PI&&aspect>0&&near>0&&far>near))
    throw new RangeError('Invalid native perspective frustum');
  const s=1/Math.tan(fov/2);
  return new Float32Array([
    s/aspect,0,0,0,0,s,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0
  ]);
}
export function multiplyNativeMat4(a,b) {
  if(a.length!==16||b.length!==16)throw new RangeError('Need 4x4 column-major matrices');
  finite(a);finite(b);
  const out=new Float32Array(16);
  for(let j=0;j<4;j++)for(let i=0;i<4;i++)for(let k=0;k<4;k++)
    out[j*4+i]+=a[k*4+i]*b[j*4+k];
  return out;
}
export function clipPoint(matrix,point) {
  if(matrix.length!==16||point.length!==3)throw new RangeError('Malformed clip input');
  finite(matrix);finite(point);
  return [
    matrix[0]*point[0]+matrix[4]*point[1]+matrix[8]*point[2]+matrix[12],
    matrix[1]*point[0]+matrix[5]*point[1]+matrix[9]*point[2]+matrix[13],
    matrix[2]*point[0]+matrix[6]*point[1]+matrix[10]*point[2]+matrix[14],
    matrix[3]*point[0]+matrix[7]*point[1]+matrix[11]*point[2]+matrix[15],
  ];
}
export function packBoneSegments(rig,evaluation,names=rig.names) {
  if(!Array.isArray(names)||names.length===0)throw new RangeError('No bones to render');
  const points=new Float32Array(names.length*6);
  let o=0;
  for(const name of names) {
    if(!rig.has(name))throw new RangeError('Unknown bone '+name);
    const a=evaluation.head(name),b=evaluation.tail(name);
    const values=[a.x,a.y,a.z,b.x,b.y,b.z];
    finite(values);
    if(Math.hypot(b.x-a.x,b.y-a.y,b.z-a.z)<=1e-12)
      throw new RangeError('Degenerate posed bone '+name);
    points.set(values,o);o+=6;
  }
  return points;
}
const VERTEX_SHADER='#version 300 es\nprecision highp float;\nlayout(location=0) in vec3 aPosition;\nuniform mat4 uViewProjection;\nvoid main(){gl_Position=uViewProjection*vec4(aPosition,1.0);}';
const FRAGMENT_SHADER='#version 300 es\nprecision highp float;\nuniform vec4 uColor;\nout vec4 outColor;\nvoid main(){outColor=uColor;}';
function compile(gl,type,source){
  const shader=gl.createShader(type);
  if(!shader)throw new Error('WebGL shader creation failed');
  gl.shaderSource(shader,source);gl.compileShader(shader);
  if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS)){
    const message=gl.getShaderInfoLog(shader)||'unknown';
    gl.deleteShader(shader);throw new Error('WebGL shader compilation: '+message);
  }
  return shader;
}
function link(gl){
  const vertex=compile(gl,gl.VERTEX_SHADER,VERTEX_SHADER);
  const fragment=compile(gl,gl.FRAGMENT_SHADER,FRAGMENT_SHADER);
  const p=gl.createProgram();
  if(!p){gl.deleteShader(vertex);gl.deleteShader(fragment);throw new Error('GPU program creation failed');}
  gl.attachShader(p,vertex);gl.attachShader(p,fragment);gl.linkProgram(p);
  gl.deleteShader(vertex);gl.deleteShader(fragment);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS)){
    const message=gl.getProgramInfoLog(p)||'unknown';
    gl.deleteProgram(p);throw new Error('WebGL program link: '+message);
  }
  return p;
}
export function createFirstPartyWebGL2BoneRenderer(canvas) {
  const gl=canvas.getContext('webgl2',{antialias:true,alpha:false,depth:true});
  if(!gl)throw new Error('WebGL2 unavailable: existing Three renderer remains the default');
  let gpu=null,buffer=null,vao=null,loc=null,colorLoc=null,disposed=false,lost=false,frames=0;
  let width=1,height=1;
  const init=()=>{
    gpu=link(gl);buffer=gl.createBuffer();vao=gl.createVertexArray();
    if(!buffer||!vao)throw new Error('Native WebGL2 resources unavailable');
    loc=gl.getUniformLocation(gpu,'uViewProjection');
    colorLoc=gl.getUniformLocation(gpu,'uColor');
    if(loc===null||colorLoc===null)throw new Error('Required native uniforms unavailable');
    gl.bindVertexArray(vao);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);
    gl.bindVertexArray(null);gl.enable(gl.DEPTH_TEST);
  };
  const onLost=e=>{e.preventDefault();lost=true;};
  const onRestore=()=>{if(disposed)return;lost=false;init();};
  canvas.addEventListener('webglcontextlost',onLost);
  canvas.addEventListener('webglcontextrestored',onRestore);
  try{init();}catch(error){
    canvas.removeEventListener('webglcontextlost',onLost);
    canvas.removeEventListener('webglcontextrestored',onRestore);
    throw error;
  }
  return {
    setSize(w,h,dpr=1){
      if(disposed)throw new Error('Disposed GPU renderer');
      finite([w,h,dpr]);
      if(!(w>0&&h>0&&dpr>0))throw new RangeError('Invalid viewport');
      width=Math.max(1,Math.floor(w*dpr));height=Math.max(1,Math.floor(h*dpr));
      canvas.width=width;canvas.height=height;
      if(!lost)gl.viewport(0,0,width,height);
    },
    render(segments,options={}){
      if(disposed)throw new Error('Disposed GPU renderer');
      if(lost)return false;
      if(!(segments instanceof Float32Array)||segments.length===0||segments.length%6!==0)
        throw new RangeError('Expected interleaved three-dimensional line segments');
      finite(segments);
      const eye=options.eye||[2.3,1.35,2.7];
      const target=options.target||[0,0.9,0];
      const color=options.color||[0.62,0.83,1,1];
      if(color.length!==4||color.some(x=>!Number.isFinite(x)||x<0||x>1))
        throw new RangeError('Invalid color');
      const vp=multiplyNativeMat4(nativePerspective(38*Math.PI/180,width/height,0.05,100),nativeLookAt(eye,target));
      gl.viewport(0,0,width,height);
      gl.clearColor(0.062,0.073,0.094,1);
      gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      gl.useProgram(gpu);gl.uniformMatrix4fv(loc,false,vp);gl.uniform4fv(colorLoc,color);
      gl.bindVertexArray(vao);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
      gl.bufferData(gl.ARRAY_BUFFER,segments,gl.DYNAMIC_DRAW);
      gl.drawArrays(gl.LINES,0,segments.length/3);
      gl.bindVertexArray(null);frames++;
      return true;
    },
    get frameCount(){return frames;},get contextLost(){return lost;},
    get kind(){return NATIVE_RENDERER_KIND;},
    dispose(){
      if(disposed)return;disposed=true;
      canvas.removeEventListener('webglcontextlost',onLost);
      canvas.removeEventListener('webglcontextrestored',onRestore);
      if(!lost){gl.deleteBuffer(buffer);gl.deleteVertexArray(vao);gl.deleteProgram(gpu);}
    }
  };
}
