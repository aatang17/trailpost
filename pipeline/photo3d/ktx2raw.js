// KTX2 (Basis) -> raw RGBA using three's basis transcoder in Node
const fs=require('fs');const dir='/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/node_modules/three/examples/jsm/libs/basis/';
const BASIS=require('./basis.cjs');
const OUT='/tmp/claude-0/-home-claude/c7d8c276-2091-5060-bd47-7c600a435b45/scratchpad/t3d/out/';fs.mkdirSync(OUT+'raw',{recursive:true});
BASIS({wasmBinary:fs.readFileSync(dir+'basis_transcoder.wasm')}).then(M=>{M.initializeBasis();const files=fs.readdirSync(OUT+'ktx');const meta={};
  for(const f of files){const u8=new Uint8Array(fs.readFileSync(OUT+'ktx/'+f));const k=new M.KTX2File(u8);
    if(!k.isValid()){console.log('bad',f);continue}const W=k.getWidth(),H=k.getHeight();k.startTranscoding();
    const n=k.getImageTranscodedSizeInBytes(0,0,0,13);const dst=new Uint8Array(n);const ok=k.transcodeImage(dst,0,0,0,13,0,-1,-1);k.close();k.delete();
    if(!ok){console.log('fail',f);continue}fs.writeFileSync(OUT+'raw/'+f.replace('.ktx2','.rgba'),dst);meta[f.replace('.ktx2','')]=[W,H]}
  fs.writeFileSync(OUT+'rawdims.json',JSON.stringify(meta));console.log('done',Object.keys(meta).length)});
