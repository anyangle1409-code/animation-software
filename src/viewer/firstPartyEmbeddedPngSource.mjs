/**
 * G1e — first-party embedded GLB PNG base-colour SOURCE intake (data only).
 *
 * No images decoded, uploaded to GPU, sampled or fetched. Fail closed on
 * unsupported glTF image types, PNG colour modes, unknown chunks/fields,
 * decompression-bomb dimensions and dangling/unused image declarations.
 * Uses no npm dependencies, Three.js, network, Node-only PNG decoder or CT data.
 */
export const HGPT_EMBEDDED_PNG_KIND='hgpt-original-embedded-png-source-v1';
const fail=m=>{throw new RangeError('Embedded PNG rejection: '+m);};
const need=(ok,m)=>{if(!ok)fail(m);};
const rec=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const array=Array.isArray;
const keys=(v,allowed)=>rec(v)&&Object.keys(v).every(k=>allowed.includes(k));
const integer=v=>Number.isSafeInteger(v)&&v>=0;
const MAX_PNG_BYTES=8*1024*1024;
const MAX_PIXELS=4*1024*1024;
const SIGNATURE=[137,80,78,71,13,10,26,10];
const decoder=new TextDecoder('ascii',{fatal:true});

function crc32(bytes,start,end){
  let crc=0xffffffff;
  for(let p=start;p<end;p++){
    crc^=bytes[p];
    for(let j=0;j<8;j++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);
  }
  return (crc^0xffffffff)>>>0;
}
function pngSize(bytes){
  need(bytes.length>=57&&bytes.length<=MAX_PNG_BYTES,
    'bounded original embedded PNG bytes required');
  need(SIGNATURE.every((v,i)=>bytes[i]===v),'invalid PNG signature');
  const v=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength);
  let offset=8,w=0,h=0,seenIDAT=false,endedIDAT=false,seenIEND=false,chunkCount=0;
  while(offset<bytes.length){
    need(offset+12<=bytes.length,'truncated PNG chunk header');
    const n=v.getUint32(offset,false),typeAt=offset+4;
    need(n<=MAX_PNG_BYTES && offset+12+n<=bytes.length,
      'chunk payload exceeds PNG length');
    const type=decoder.decode(bytes.subarray(typeAt,typeAt+4));
    const payload=typeAt+4,crcAt=payload+n;
    need(v.getUint32(crcAt,false)===crc32(bytes,typeAt,crcAt),
      'PNG chunk CRC mismatch');
    need(++chunkCount<=256,'too many source PNG chunks');
    if(chunkCount===1){
      need(type==='IHDR'&&n===13,'PNG must begin with 13-byte IHDR');
      w=v.getUint32(payload,false);h=v.getUint32(payload+4,false);
      need(w>=1&&h>=1&&w<=4096&&h<=4096&&w*h<=MAX_PIXELS,
        'PNG dimensions exceed bounded source budget');
      need(bytes[payload+8]===8 &&
        [2,6].includes(bytes[payload+9]) &&
        bytes[payload+10]===0 &&
        bytes[payload+11]===0 &&
        bytes[payload+12]===0,
        'only 8-bit RGB/RGBA noninterlaced PNG supported');
    }else if(type==='IDAT'){
      need(!endedIDAT && !seenIEND && n>0,
        'IDAT must be contiguous and nonempty');
      seenIDAT=true;
    }else if(type==='IEND'){
      need(seenIDAT && n===0 && !seenIEND,
        'nonempty data then empty terminal IEND required');
      seenIEND=true;
      need(crcAt+4===bytes.length,'PNG trailing bytes forbidden');
    }else{
      // Deliberate strict subset: no PLTE, tRNS, iCCP, eXIf,
      // unknown critical chunks or textual executable metadata.
      fail('unsupported PNG chunk '+type);
    }
    if(seenIDAT&&type!=='IDAT')endedIDAT=true;
    offset=crcAt+4;
  }
  need(seenIEND&&offset===bytes.length,'PNG IEND missing');
  return {width:w,height:h};
}

/**
 * Validate all source images, textures and samplers together. It is invalid
 * for an image/texture/sampler to be unreferenced in the source GLB; caller
 * checks every texture was used by a validated opaque baseColor material.
 * Result holds an independent COPY of image bytes for future native decoder.
 */
export function readRestrictedEmbeddedPngSources(root,bin){
  need(rec(root)&&bin instanceof Uint8Array,
    'source GLB root and embedded BIN required');
  const {images,textures,samplers}=root;
  need(array(images)&&images.length>=1&&images.length<=4,
    '1..4 explicitly embedded images required');
  need(array(textures)&&textures.length>=1&&textures.length<=4,
    '1..4 image textures required');
  need(array(samplers)&&samplers.length>=1&&samplers.length<=4,
    '1..4 explicit simple samplers required');
  const declared=root.buffers?.[0]?.byteLength;
  need(integer(declared)&&declared>0 && declared<=bin.byteLength &&
    bin.length-declared<4,'declared source BIN bytes invalid');
  const imageData=images.map((im,i)=>{
    need(keys(im,['bufferView','mimeType','name']) &&
      integer(im.bufferView)&&im.mimeType==='image/png'&&
      (im.name===undefined||(typeof im.name==='string'&&im.name.length<=80)),
      'image '+i+' must be embedded PNG bufferView, not URI');
    const b=root.bufferViews?.[im.bufferView];
    need(keys(b,['buffer','byteOffset','byteLength','name'])&&b.buffer===0 &&
      integer(b.byteOffset??0)&&integer(b.byteLength)&&b.byteLength>=57 &&
      (b.byteOffset??0)%4===0 && b.byteLength<=MAX_PNG_BYTES &&
      (b.byteOffset??0)+b.byteLength<=declared &&
      (b.byteOffset??0)+b.byteLength<=bin.length,
      'PNG image bufferView outside aligned embedded BIN');
    need(!root.accessors?.some(a=>a?.bufferView===im.bufferView),
      'PNG image bufferView cannot alias a geometry accessor');
    const bytes=bin.slice(b.byteOffset??0,(b.byteOffset??0)+b.byteLength);
    const size=pngSize(bytes);
    return {bytes,width:size.width,height:size.height};
  });
  const sampleInfo=samplers.map((sampler,i)=>{
    need(keys(sampler,['name','magFilter','minFilter','wrapS','wrapT']) &&
      sampler.magFilter===9729 && sampler.minFilter===9729 &&
      sampler.wrapS===33071 && sampler.wrapT===33071,
      'sampler '+i+' must be explicit linear clamp-to-edge with no mipmaps');
    return {minFilter:9729,magFilter:9729,wrapS:33071,wrapT:33071};
  });
  const usedImages=new Set(),usedSamplers=new Set();
  const result=textures.map((tex,i)=>{
    need(keys(tex,['name','source','sampler']) &&
      integer(tex.source)&&tex.source<images.length &&
      integer(tex.sampler)&&tex.sampler<samplers.length,
      'texture '+i+' requires explicit embedded image and sampler');
    usedImages.add(tex.source);usedSamplers.add(tex.sampler);
    const im=imageData[tex.source];
    return {kind:HGPT_EMBEDDED_PNG_KIND,
      sourceTextureIndex:i,sourceImageIndex:tex.source,
      width:im.width,height:im.height,
      bytes:im.bytes,sampler:sampleInfo[tex.sampler]};
  });
  need(usedImages.size===images.length && usedSamplers.size===samplers.length,
    'unused source image or sampler forbidden');
  return result;
}
