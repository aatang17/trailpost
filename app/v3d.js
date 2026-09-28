/* ---------- 3D terrain viewer (one area at a time: Lantau Peak, Dragon's Back, …) ----------
   Fast start: 10 m heights + one overview photo (~0.6 MB) give a first view; 5 m heights, buildings and sharp
   photos for what is on screen stream in afterwards. Shadows are redrawn only when something changes. */
/* Each area is a folder made by pipeline/area/build_area.py (Lantau was made by the older scripts).
   bridge: the Hong Kong–Zhuhai–Macao Bridge layer; cable: the Ngong Ping cable car; cam: HKO camera nearest the area. */
const AREAS={
  lantau:{dir:'l3/',stages:['lantau-2','lantau-3','lantau-4'],first:'lantau-3',title:['Lantau Peak in 3D','鳳凰山立體地形'],bridge:true,cam:'CS2',lon:113.93},
  drag:{dir:'l3/drag/',stages:['hktrail-6','hktrail-7','hktrail-8'],first:'hktrail-8',title:["Dragon's Back in 3D",'龍脊立體地形'],cam:'VPA',lon:114.24}
};
const V3D_STAGES=Object.values(AREAS).flatMap(a=>a.stages);
const areaOf=id=>Object.keys(AREAS).find(k=>AREAS[k].stages.includes(id));
const trail3D=tid=>Object.keys(AREAS).find(k=>AREAS[k].stages.some(s=>s.startsWith(tid+'-'))); // first 3D area on a trail
let AREA='lantau';
const V={gen:0,loaded:false,loading:false,stage:'lantau-3',ex:1,sunMin:null,fly:null,walk:null,raf:0,open:false,look:'photo',route:true,clouds:true,trees:true};
const MOBILE=Math.min(screen.width||innerWidth,screen.height||innerHeight)<700;
let L3=AREAS.lantau.dir;const SND_DIR='l3/'; // sounds are shared by all areas
function loadScript(src){return new Promise((ok,no)=>{const s=document.createElement('script');s.src=src;s.onload=ok;s.onerror=()=>no(new Error('script '+src));document.head.appendChild(s)})}
const W3={};// warm-up promises: the libraries once, the area data per area
function warm3D(which){
  const area=typeof which==='string'?(AREAS[which]?which:areaOf(which)||AREA):AREA;
  if(!W3.started){W3.started=true;
  W3.three=(window.THREE?Promise.resolve():loadScript('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'))
    .then(()=>THREE.OrbitControls?0:loadScript('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js'));
  W3.sky=W3.three.then(()=>THREE.Sky?0:loadScript('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/objects/Sky.js')).catch(()=>null);
  W3.three.catch(()=>{});W3.areas={}}
  if(V.loaded||V.loading)if(area!==AREA)return; // do not fetch another area while one is on screen
  if(W3.areas[area])return;const D=AREAS[area].dir,A=W3.areas[area]={};
  const j=u=>fetch(D+u).then(r=>{if(!r.ok)throw new Error(u+' '+r.status);return r.json()});
  A.meta=j('meta.json');A.chunks=j('chunks.json');
  A.dem10=fetch(D+'dem10.webp').then(r=>{if(!r.ok)throw new Error('dem10 '+r.status);return r.blob()});
  A.overview=fetch(D+'overview.webp').then(r=>r.ok?r.blob():null).catch(()=>null);
  A.can10=fetch(D+'can10.webp').then(r=>r.ok?r.blob():null).catch(()=>null);
  [A.meta,A.chunks,A.dem10].forEach(p=>p.catch(()=>{}));
}
async function decodeGray(blob){ // canopy height: grey value / 4 = metres
  const bmp=await createImageBitmap(blob,{colorSpaceConversion:'none',premultiplyAlpha:'none'});
  const cv=document.createElement('canvas');cv.width=bmp.width;cv.height=bmp.height;const cx=cv.getContext('2d',{willReadFrequently:true});cx.drawImage(bmp,0,0);
  const px=cx.getImageData(0,0,bmp.width,bmp.height).data;const out=new Float32Array(bmp.width*bmp.height);
  for(let i=0;i<out.length;i++)out[i]=px[i*4]/4;
  return {w:bmp.width,h:bmp.height,d:out};
}
function up2(src,C,R){const out=new Float32Array(C*R),w=src.w,h=src.h,s=src.d;
  for(let i=0;i<R;i++){const fi=Math.min(h-1.001,i/2),i0=fi|0,ti=fi-i0;for(let j=0;j<C;j++){const fj=Math.min(w-1.001,j/2),j0=fj|0,tj=fj-j0;const a=i0*w+j0;
    out[i*C+j]=s[a]*(1-ti)*(1-tj)+s[a+1]*(1-ti)*tj+s[a+w]*ti*(1-tj)+s[a+w+1]*ti*tj}}return out}
async function decodeDem(blob){
  const bmp=await createImageBitmap(blob,{colorSpaceConversion:'none',premultiplyAlpha:'none'});
  const cv=document.createElement('canvas');cv.width=bmp.width;cv.height=bmp.height;const cx=cv.getContext('2d',{willReadFrequently:true});cx.drawImage(bmp,0,0);
  const px=cx.getImageData(0,0,bmp.width,bmp.height).data;const out=new Float32Array(bmp.width*bmp.height);
  for(let i=0;i<out.length;i++){const v=px[i*4]*256+px[i*4+1]-10;out[i]=v>-3&&v<0.5?0.5:v} // flat coastal land sits just above the sea surface
  return {w:bmp.width,h:bmp.height,d:out};
}
function sunPos(date,min){ // HK solar azimuth (deg from north, clockwise) and elevation (deg)
  const rad=Math.PI/180,lat=22.25,lon=AREAS[AREA].lon||114.1;
  const start=new Date(date.getFullYear(),0,0);const doy=Math.floor((date-start)/864e5);
  const g=2*Math.PI/365*(doy-1+(min/60-12)/24);
  const eqt=229.18*(0.000075+0.001868*Math.cos(g)-0.032077*Math.sin(g)-0.014615*Math.cos(2*g)-0.040849*Math.sin(2*g));
  const dec=0.006918-0.399912*Math.cos(g)+0.070257*Math.sin(g)-0.006758*Math.cos(2*g)+0.000907*Math.sin(2*g)-0.002697*Math.cos(3*g)+0.00148*Math.sin(3*g);
  const tst=min+eqt+4*lon-480;const ha=(tst/4-180)*rad;
  const cz=Math.sin(lat*rad)*Math.sin(dec)+Math.cos(lat*rad)*Math.cos(dec)*Math.cos(ha);const zen=Math.acos(Math.max(-1,Math.min(1,cz)));
  let az=Math.acos(Math.max(-1,Math.min(1,(Math.sin(lat*rad)*Math.cos(zen)-Math.sin(dec))/(Math.cos(lat*rad)*Math.sin(zen)))))/rad;
  az=ha>0?(az+180)%360:(540-az)%360;
  return {az,el:90-zen/rad};
}
function open3D(stageId){
  const area=areaOf(stageId)||(AREAS[stageId]?stageId:AREA);
  if(area!==AREA){teardown3D();AREA=area;L3=AREAS[area].dir}
  V.stage=AREAS[area].stages.includes(stageId)?stageId:AREAS[area].stages.includes(V.stage)?V.stage:AREAS[area].first;
  const el=$('#v3d');el.hidden=false;V.open=true;document.body.style.overflow='hidden';
  if(V.sunMin==null){const n=hkNow();const m=n.getHours()*60+n.getMinutes();V.sunMin=(m>7*60&&m<18*60)?m:16*60+30;}
  render3DChrome();
  if(!V.loaded&&!V.loading)init3D();else if(V.loaded){applyStage(true);resize3D();loop3D()}
}
function teardown3D(){ // free the current area before loading another one
  V.gen++;if(V.walk)stopWalk(true);if(V.fly)stopFly();cancelAnimationFrame(V.raf);
  if(G.ro)G.ro.disconnect();
  if(G.renderer){
    const free=m=>{if(!m)return;[].concat(m).forEach(x=>{['map','aoMap','normalMap'].forEach(k=>{if(x[k]&&x[k].dispose)x[k].dispose()});x.dispose()})};
    if(G.scene)G.scene.traverse(o=>{if(o.geometry)o.geometry.dispose();free(o.material)});
    (G.chunks||[]).forEach(c=>{Object.values(c.geos).forEach(g=>g.dispose());free(c.hi)});(G.farChunks||[]).forEach(c=>Object.values(c.geos).forEach(g=>g.dispose()));
    free(G.lowMat);free(G.mapMat);free(G.farMat);if(G.ao)G.ao.dispose();if(G.shoreTex)G.shoreTex.dispose();if(G.seaColTex)G.seaColTex.dispose();
    G.renderer.dispose();try{G.renderer.forceContextLoss()}catch(e){}G.renderer.domElement.remove()}
  G={};D3=CH=EX=null;V.loaded=false;V.loading=false;$('#v3dStatus').textContent='';$('#v3dCloudInfo').textContent='';
}
function close3D(){$('#v3d').hidden=true;V.open=false;document.body.style.overflow='';stopWalk(true);stopFly();cancelAnimationFrame(V.raf)}
function render3DChrome(){
  const AR=AREAS[AREA];$('#v3dTitle').textContent=T(...AR.title);
  $('#v3dClose').setAttribute('aria-label',T('Close 3D view','關閉立體地圖'));
  $('#v3dStages').innerHTML=AR.stages.filter(id=>byId[id]).map(id=>{const r=byId[id];return `<button type="button" class="fchip" data-s="${id}" aria-pressed="${V.stage===id}">${T('Stage ','第')}${r.n}${T('','段')} · ${esc(F(r,'end'))}</button>`}).join('')
    +Object.keys(AREAS).filter(k=>k!==AREA).map(k=>`<button type="button" class="fchip v3dArea" data-a="${k}">→ ${esc(T(...AREAS[k].title))}</button>`).join('');
  $('#v3dStages').querySelectorAll('button[data-s]').forEach(b=>b.onclick=()=>{V.stage=b.dataset.s;stopWalk(true);stopFly();render3DChrome();applyStage(true)});
  $('#v3dStages').querySelectorAll('button[data-a]').forEach(b=>b.onclick=()=>open3D(b.dataset.a));
  $('#v3dFly').textContent=V.fly?T('Stop','停止'):T('Fly the stage','沿路段飛行');
  $('#v3dWalk').textContent=V.walk?T('Exit walk','結束步行'):T('Walk the trail','沿路徑步行');
  $('#v3dEx').textContent=V.ex===1?T('Heights: true','高度：真實'):T('Heights: ×1.6','高度：×1.6');
  $('#v3dLook').textContent=V.look==='photo'?T('View: aerial photo','顯示：航空照片'):T('View: map','顯示：地圖');
  $('#v3dRoute').textContent=V.route?T('Route line: on','路線：顯示'):T('Route line: off','路線：隱藏');
  $('#v3dSunLbl').textContent=T('Sun','太陽')+' '+hm(V.sunMin);
  $('#v3dSun').value=V.sunMin;
  $('#v3dClouds').textContent=V.clouds?T('Clouds: live','雲：即時'):T('Clouds: off','雲：隱藏');
  $('#v3dCam').textContent=T('Live camera','即時相片');
  $('#v3dTrees').textContent=V.trees?T('Trees: 3D','樹木：立體'):T('Trees: flat','樹木：平面');
  $('#v3dBridge').textContent=T('View the bridge','看港珠澳大橋');$('#v3dBridge').style.display=AR.bridge?'':'none';
  const cl=COND.cloud;let ci='';
  if(cl){const ls=(cl.layers||[]).filter(l=>l.base_m<3000);const when=cl.obsTime?new Date(cl.obsTime).toLocaleTimeString(ZH()?'zh-HK':'en-GB',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Hong_Kong'}):'';
    ci=(ls.length?T('Clouds shown as reported by the airport at ','雲層按機場於')+when+T(': ','報告：')+ls.map(l=>`${T(...(COVN[l.cover]||[l.cover,l.cover]))} ${T('at','於')} ${l.base_m} m`).join(T(', ','，'))+T('.','。'):T('The airport reports no low cloud at ','機場於')+when+T('.','報告沒有低雲。'))+T(' Cloud shapes are illustrative; heights and amount are real.',' 雲的形狀為示意，高度及雲量按實況。');}
  $('#v3dCloudInfo').textContent=ci;
  $('#v3dHint').textContent=V.walk?(MOBILE?T('Drag to look around · use the slider to jump ahead','拖動環顧四周 · 用滑桿跳到其他位置'):T('Drag to look around · scroll or ↑ ↓ to move · ← → to turn · space to pause','拖動環顧四周 · 滾輪或 ↑ ↓ 前後移動 · ← → 轉向 · 空白鍵暫停')):MOBILE?T('Drag to turn · pinch to zoom · two fingers to tilt','拖動旋轉 · 雙指縮放及傾斜'):T('Drag to turn · scroll to zoom · right-drag to move','拖動旋轉 · 滾輪縮放 · 右鍵拖動平移');
  $('#v3dSrc').textContent=AR.bridge?T('Ground and tree heights: CEDD 2020 LiDAR survey (5 m) and Lands Department terrain model. Aerial Photograph and GBA Satellite Image 2024 (Landsat) from Lands Department. Wider terrain: AWS Terrain Tiles. Buildings, cable car and bridge route: OpenStreetMap. Bridge tower heights from published figures; deck heights approximate. Trail: AFCD.','地面及樹木高度：土木工程拓展署2020年激光雷達測量（5米）及地政總署地形模型。航空照片及2024年大灣區衞星影像（Landsat）：地政總署。外圍地形：AWS地形圖塊。建築物、纜車及大橋路線：OpenStreetMap。橋塔高度按公開數字，橋面高度為約數。路線：漁護署。')
    :T('Ground and tree heights: CEDD 2020 LiDAR survey (5 m) and Lands Department terrain model. Aerial Photograph from Lands Department. Wider terrain: Lands Department terrain model and AWS Terrain Tiles. Buildings, place names and trail markers: OpenStreetMap contributors. Trail: AFCD.','地面及樹木高度：土木工程拓展署2020年激光雷達測量（5米）及地政總署地形模型。航空照片：地政總署。外圍地形：地政總署地形模型及AWS地形圖塊。建築物、地名及沿途標記：OpenStreetMap貢獻者。路線：漁護署。');
}
$('#v3dClose').onclick=close3D;
document.addEventListener('keydown',e=>{if(!V.open)return;if(e.key==='Escape'){if(V.walk){stopWalk();render3DChrome()}else close3D();return}
  const w=V.walk;if(!w||/INPUT|SELECT|TEXTAREA|BUTTON/.test((e.target&&e.target.tagName)||''))return;
  if(e.key===' '){e.preventDefault();walkPlay()}else if(e.key==='ArrowUp'){e.preventDefault();w.d=Math.min(w.total,w.d+40)}else if(e.key==='ArrowDown'){e.preventDefault();w.d=Math.max(0,w.d-40)}
  else if(e.key==='ArrowLeft'){e.preventDefault();w.yaw+=0.2;w.idle=0}else if(e.key==='ArrowRight'){e.preventDefault();w.yaw-=0.2;w.idle=0}});
$('#v3dFly').onclick=()=>{stopWalk();V.fly?stopFly():startFly();render3DChrome()};
$('#v3dWalk').onclick=()=>{V.walk?stopWalk():startWalk();render3DChrome()};
$('#v3dWalkPlay').onclick=()=>{sndStart();walkPlay()};
$('#v3dWalkGyro').onclick=()=>toggleGyro();
$('#v3dWalkSnd').onclick=()=>toggleSound();
$('#v3dWalkSpd').onclick=()=>{const w=V.walk;if(!w)return;const L=[1,10,30,60];w.spd=L[(L.indexOf(w.spd)+1)%L.length];walkUI()};
{const sl=$('#v3dWalkPos');sl.addEventListener('pointerdown',()=>{if(V.walk)V.walk.scrub=true});const end=()=>{if(V.walk)V.walk.scrub=false};sl.addEventListener('pointerup',end);sl.addEventListener('change',end);sl.addEventListener('input',()=>{const w=V.walk;if(w){w.d=+sl.value/1000*w.total;w.scrub=true;clearTimeout(w.st);w.st=setTimeout(end,400)}})}
$('#v3dEx').onclick=()=>{stopWalk();V.ex=V.ex===1?1.6:1;applyHeights();render3DChrome()};
$('#v3dLook').onclick=()=>{V.look=V.look==='photo'?'map':'photo';applyLook();render3DChrome()};
$('#v3dRoute').onclick=()=>{V.route=!V.route;if(V.walk){if(G.walkPath)G.walkPath.visible=V.route}else if(G.stageGrp)G.stageGrp.children.forEach(o=>{if(o.isMesh)o.visible=V.route});render3DChrome()};
$('#v3dClouds').onclick=()=>{V.clouds=!V.clouds;if(G.cloudGrp)G.cloudGrp.visible=V.clouds;render3DChrome()};
$('#v3dCam').onclick=()=>openCams(AREAS[AREA].cam);
$('#v3dTrees').onclick=()=>{V.trees=!V.trees;applyHeights();render3DChrome()};
$('#v3dBridge').onclick=()=>{stopWalk(true);stopFly();bridgeView()};
$('#v3dSun').oninput=e=>{V.sunMin=+e.target.value;applySun();$('#v3dSunLbl').textContent=T('Sun','太陽')+' '+hm(V.sunMin)};

let D3=null,CH=null,EX=null,G={};
async function init3D(){
  V.loading=true;const gen=V.gen,A0=AREA;const msg=$('#v3dMsg');msg.hidden=false;msg.textContent=T('Loading terrain…','正在載入地形…');
  const t0=performance.now();const live=()=>gen===V.gen;
  try{
    V.loading=false;warm3D(A0);V.loading=true;const A=W3.areas[A0];
    const [,meta,chunks,dblob]=await Promise.all([W3.three,A.meta,A.chunks,A.dem10]);if(!live())return;
    D3=meta;CH=chunks;const C=meta.cols,R=meta.rows;
    // 10 m heights upsampled to the 5 m grid for the first view
    const d10=await decodeDem(dblob);const H=new Float32Array(C*R);const w=d10.w,h=d10.h,s=d10.d;
    for(let i=0;i<R;i++){const fi=Math.min(h-1.001,i/2),i0=fi|0,ti=fi-i0;for(let j=0;j<C;j++){const fj=Math.min(w-1.001,j/2),j0=fj|0,tj=fj-j0;const a=i0*w+j0;
      H[i*C+j]=s[a]*(1-ti)*(1-tj)+s[a+1]*(1-ti)*tj+s[a+w]*ti*(1-tj)+s[a+w+1]*ti*tj}}
    G.H=H;G.CAN=new Float32Array(C*R);
    const cb=await A.can10;if(cb){try{G.CAN=up2(await decodeGray(cb),C,R)}catch(e){}}
    await W3.sky;if(!live())return;
    build3D();
    const ov=await A.overview;if(!live())return;if(ov){const t=await blobTex(ov);G.lowMat.map=t;G.lowMat.color.set(0xffffff);G.lowMat.needsUpdate=true}
    V.loaded=true;msg.hidden=true;render3DChrome();applyStage(true);buildClouds();loop3D();
    G.firstView=Math.round(performance.now()-t0);window.__v3dFirstView=G.firstView;
    // in the background: 5 m heights, then buildings and cable car
    const blob=u=>fetch(L3+u).then(r=>{if(!r.ok)throw new Error(u+' '+r.status);return r.blob()});
    const stop=()=>{if(!live())throw 'stale'};
    Promise.all([blob('dem5.webp').then(decodeDem),blob('can5.webp').then(decodeGray).catch(()=>null)]).then(([d,c])=>{stop();G.H=d.d;if(c)G.CAN=c.d;G.full=true;buildShore();
      G.chunks.forEach(ch=>{Object.values(ch.geos).forEach(g=>g.dispose());ch.geos={};ch.dirty=true});
      applyStage(false);placeOverlays();return fetch(L3+'extras.json').then(r=>r.json())}).then(ex=>{stop();EX=ex;buildExtras();G.shadowDirty=true;window.__v3dFull=Math.round(performance.now()-t0);
      return blob('ao.webp').then(blobTex)}).then(ao=>{stop();G.ao=ao;[G.lowMat,G.mapMat,...G.chunks.map(c=>c.hi)].forEach(m=>{if(m){m.aoMap=ao;m.aoMapIntensity=1;m.needsUpdate=true}});
      return loadFar()}).then(()=>{stop();window.__v3dFar=Math.round(performance.now()-t0);if(!AREAS[A0].bridge)return;
        return fetch(L3+'bridge.json').then(r=>r.json()).then(b=>{stop();G.BR=b;buildBridge();window.__v3dBridge=Math.round(performance.now()-t0)})}).catch(e=>{if(e!=='stale')console.warn(e)});
  }catch(err){if(!live())return;msg.hidden=false;msg.textContent=T('The 3D view could not load. ','未能載入立體地圖。')+(err&&err.message?err.message:'');console.error(err)}
  V.loading=false;
}
function blobTex(blob){return createImageBitmap(blob,{imageOrientation:'flipY'}).then(b=>{const t=new THREE.CanvasTexture(b);t.flipY=false;t.encoding=THREE.sRGBEncoding;t.anisotropy=Math.min(MOBILE?4:8,G.renderer.capabilities.getMaxAnisotropy());t.needsUpdate=true;return t})}
function hAt(x,z){ // world metres from NW corner -> ground height (m, true scale)
  const C=D3.cols,R=D3.rows,cs=D3.cs;let c=x/cs-0.5,r=z/cs-0.5;
  if(G.FAR&&(c<0||r<0||c>C-1||r>R-1))return hFar(x,z);
  c=Math.max(0,Math.min(C-1.001,c));r=Math.max(0,Math.min(R-1.001,r));
  const i=r|0,j=c|0,fr=r-i,fc=c-j,H=G.H;
  return H[i*C+j]*(1-fr)*(1-fc)+H[i*C+j+1]*(1-fr)*fc+H[(i+1)*C+j]*fr*(1-fc)+H[(i+1)*C+j+1]*fr*fc;
}
const Hc=(i,j)=>{const C=D3.cols,R=D3.rows;i=i<0?0:i>=R?R-1:i;j=j<0?0:j>=C?C-1:j;return G.H[i*C+j]};
const Hs=(i,j)=>{const C=D3.cols,R=D3.rows;i=i<0?0:i>=R?R-1:i;j=j<0?0:j>=C?C-1:j;const k=i*C+j;const g=G.H[k];return g<=0?g:g+(V.trees&&G.CAN?G.CAN[k]:0)}; // surface incl. tree canopy
function hFar(x,z){const F=G.FAR;const E=x+D3.x0hk,N=D3.ytophk-z;let c=(E-F.E0)/F.fs,r=(F.N1-N)/F.fs;if(c<0||r<0||c>F.cols-1.001||r>F.rows-1.001)return 0;
  const i=r|0,j=c|0,fr=r-i,fc=c-j,H=F.H,W=F.cols;const v=H[i*W+j]*(1-fr)*(1-fc)+H[i*W+j+1]*(1-fr)*fc+H[(i+1)*W+j]*fr*(1-fc)+H[(i+1)*W+j+1]*fr*fc;return Math.max(0,v)}

function makeSky(){
  const mat=new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,fog:false,
    uniforms:{sunDir:{value:new THREE.Vector3(0,1,0)},zenith:{value:new THREE.Color()},horizon:{value:new THREE.Color()},sunCol:{value:new THREE.Color()},sunI:{value:1}},
    vertexShader:'varying vec3 vDir;void main(){vDir=normalize((modelMatrix*vec4(position,1.0)).xyz-cameraPosition);gl_Position=projectionMatrix*viewMatrix*modelMatrix*vec4(position,1.0);}',
    fragmentShader:`uniform vec3 sunDir,zenith,horizon,sunCol;uniform float sunI;varying vec3 vDir;
      void main(){vec3 d=normalize(vDir);float t=clamp(d.y,0.0,1.0);vec3 c=mix(horizon,zenith,pow(t,0.42));
      float s=max(dot(d,normalize(sunDir)),0.0);c+=sunCol*(pow(s,900.0)*6.0+pow(s,40.0)*0.25+pow(s,6.0)*0.12)*sunI;
      c=mix(c,horizon,smoothstep(0.0,-0.08,d.y));gl_FragColor=vec4(c,1.0);}`});
  const m=new THREE.Mesh(new THREE.SphereGeometry(45000,32,16),mat);m.renderOrder=-10;m.frustumCulled=false;return m;
}
function rippleNormals(){
  const N=128,c=document.createElement('canvas');c.width=c.height=N;const g=c.getContext('2d');const img=g.createImageData(N,N);
  const h=new Float32Array(N*N);const waves=[];for(let k=0;k<14;k++){const a=Math.random()*Math.PI*2,f=(2+Math.floor(Math.random()*7));waves.push([Math.round(Math.cos(a)*f),Math.round(Math.sin(a)*f),Math.random()*6.28,1/f])}
  for(let y=0;y<N;y++)for(let x=0;x<N;x++){let s=0;for(const w of waves)s+=Math.sin((w[0]*x+w[1]*y)/N*2*Math.PI+w[2])*w[3];h[y*N+x]=s}
  for(let y=0;y<N;y++)for(let x=0;x<N;x++){const dx=h[y*N+(x+1)%N]-h[y*N+(x+N-1)%N],dy=h[((y+1)%N)*N+x]-h[((y+N-1)%N)*N+x];
    const nx=-dx*3,ny=-dy*3,l=Math.hypot(nx,ny,1);const o=(y*N+x)*4;img.data[o]=(nx/l*0.5+0.5)*255;img.data[o+1]=(ny/l*0.5+0.5)*255;img.data[o+2]=(1/l*0.5+0.5)*255;img.data[o+3]=255}
  g.putImageData(img,0,0);const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;return t;
}
function heightFog(){ // exponential height fog: thicker near the sea, thinner up on the peaks
  if(G.fogPatched)return;G.fogPatched=true;const S=THREE.ShaderChunk;
  S.fog_pars_vertex='#ifdef USE_FOG\n varying float fogDepth; varying vec3 vFogW;\n#endif';
  S.fog_vertex='#ifdef USE_FOG\n fogDepth=-mvPosition.z;\n #ifdef USE_INSTANCING\n vFogW=(modelMatrix*instanceMatrix*vec4(transformed,1.0)).xyz;\n #else\n vFogW=(modelMatrix*vec4(transformed,1.0)).xyz;\n #endif\n#endif';
  S.fog_pars_fragment='#ifdef USE_FOG\n uniform vec3 fogColor; varying float fogDepth; varying vec3 vFogW;\n #ifdef FOG_EXP2\n uniform float fogDensity;\n #else\n uniform float fogNear; uniform float fogFar;\n #endif\n#endif';
  S.fog_fragment='#ifdef USE_FOG\n float fd=length(vFogW-cameraPosition); float kk=1.0/750.0; float dy=(vFogW.y-cameraPosition.y)*kk;\n float tt=abs(dy)>1e-3?(1.0-exp(-dy))/dy:1.0;\n #ifdef FOG_EXP2\n float od=fogDensity*fd*exp(-max(cameraPosition.y,0.0)*kk)*tt;\n #else\n float od=fd/fogFar;\n #endif\n float fogFactor=1.0-exp(-od);\n gl_FragColor.rgb=mix(gl_FragColor.rgb,fogColor,fogFactor);\n#endif';
}
function physicalSky(){
  if(!THREE.Sky)return null;
  try{const SS=THREE.Sky.SkyShader;if(SS&&!SS._p){SS.fragmentShader=SS.fragmentShader.replace(/const vec3 cameraPos = vec3\( 0\.0, 0\.0, 0\.0 \);/,'').replace(/cameraPos\b/g,'cameraPosition').replace('uniform vec3 up;','uniform vec3 up; uniform float skyGain;').replace('gl_FragColor = vec4( retColor, 1.0 );','gl_FragColor = vec4( retColor*skyGain, 1.0 );');SS._p=1}
    const s=new THREE.Sky();s.scale.setScalar(100000);s.frustumCulled=false;const u=s.material.uniforms;u.skyGain={value:0.45};u.turbidity.value=4.2;u.rayleigh.value=2.2;u.mieCoefficient.value=0.004;u.mieDirectionalG.value=0.8;return s}catch(e){return null}
}
/* ----- sea: see-through near the coast so the real colour in the aerial photo (sand, rock, reef) shows, with a
   moving foam line where water meets land. Distance to land comes from the height grid (sea cells are −6 m). ----- */
function seaMaterial(rip){
  const m=new THREE.MeshPhongMaterial({color:0x2b5a6c,specular:0xb8c8d2,shininess:260,normalMap:rip,normalScale:new THREE.Vector2(0.3,0.3),
    transparent:true});
  const U=G.seaU={shoreTex:{value:null},shoreOn:{value:0},shoreOff:{value:new THREE.Vector2()},shoreSize:{value:new THREE.Vector2(1,1)},seaT:{value:0},foamL:{value:1},shoreFade:{value:70},seaCol:{value:null},seaColOn:{value:0},skyRef:{value:new THREE.Color(0.6,0.66,0.7)}};
  m.onBeforeCompile=sh=>{Object.assign(sh.uniforms,U);
    sh.vertexShader='varying vec3 vSeaW;\n'+sh.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n vSeaW=(modelMatrix*vec4(transformed,1.0)).xyz;');
    sh.fragmentShader=`varying vec3 vSeaW;uniform sampler2D shoreTex,seaCol;uniform float shoreOn,seaColOn,seaT,foamL,shoreFade;uniform vec2 shoreOff,shoreSize;uniform vec3 skyRef;
      float sHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float sNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(sHash(i),sHash(i+vec2(1,0)),f.x),mix(sHash(i+vec2(0,1)),sHash(i+vec2(1,1)),f.x),f.y);}
      `+sh.fragmentShader /* gusty patches: the sun sparkle comes and goes */ .replace('vec3 outgoingLight = reflectedLight.directDiffuse','{float gp=sNoise(vSeaW.xz*0.004+vec2(seaT*0.006,seaT*0.004))*0.6+sNoise(vSeaW.xz*0.017-vec2(seaT*0.02,0.0))*0.4;reflectedLight.directSpecular*=0.15+1.1*smoothstep(0.35,0.75,gp);}\n vec3 outgoingLight = reflectedLight.directDiffuse').replace('#include <map_fragment>',`#include <map_fragment>
      if(seaColOn>0.5){vec2 cuv=(vSeaW.xz+shoreOff)/shoreSize;float e=min(min(cuv.x,1.0-cuv.x),min(cuv.y,1.0-cuv.y));
        if(e>0.0)diffuseColor.rgb=mix(diffuseColor.rgb,sRGBToLinear(texture2D(seaCol,cuv)).rgb,smoothstep(0.0,0.06,e));} // the sea's own colour, from the aerial photo
      `).replace('#include <tonemapping_fragment>',`
      {float cv=max(dot(normalize(cameraPosition-vSeaW),vec3(0.0,1.0,0.0)),0.0);float fr=0.02+0.98*pow(1.0-cv,5.0); // sky reflection (Schlick), stronger towards the horizon
       gl_FragColor.rgb=mix(gl_FragColor.rgb,skyRef,fr*0.85);}
      {vec2 suv=(vSeaW.xz+shoreOff)/shoreSize;float d=255.0;
       if(shoreOn>0.5&&suv.x>0.0&&suv.x<1.0&&suv.y>0.0&&suv.y<1.0)d=texture2D(shoreTex,suv).r*255.0;
       if(d<254.0){
        float n=sNoise(vSeaW.xz*0.05+vec2(seaT*0.04,0.0)),n2=sNoise(vSeaW.xz*0.21-vec2(0.0,seaT*0.09));
        float clear=1.0-smoothstep(3.0,shoreFade*(0.65+0.7*n),d);          // 1 at the coast, 0 offshore
        float wave=0.5+0.5*sin(d*0.5+seaT*1.3+n*6.0);                        // bands that move in towards the shore
        float foam=(1.0-smoothstep(1.0,4.0+6.0*n,d))*(0.5+0.5*wave)*smoothstep(0.2,0.55,n2+0.15);
        float lines=(1.0-smoothstep(5.0,20.0+10.0*n,d))*smoothstep(0.86,0.98,wave)*smoothstep(0.35,0.8,n2)*0.7;
        float f=clamp(foam+lines,0.0,1.0);
        gl_FragColor.rgb=mix(gl_FragColor.rgb,vec3(0.90,0.93,0.94)*foamL,f*0.85);
        gl_FragColor.a=max(1.0-clear*0.9,f*0.9);
       }}
      #include <tonemapping_fragment>`)};
  return m;
}
function buildShore(){ // metres from each sea cell to the nearest land cell, capped at 255 (two-pass chamfer)
  const C=D3.cols,R=D3.rows,cs=D3.cs,H=G.H,N=C*R,D=new Float32Array(N),a=cs,b=cs*Math.SQRT2;
  for(let k=0;k<N;k++)D[k]=H[k]>-3?0:1e6;
  for(let i=0;i<R;i++)for(let j=0;j<C;j++){const k=i*C+j;let v=D[k];if(!v)continue;
    if(j>0)v=Math.min(v,D[k-1]+a);if(i>0){v=Math.min(v,D[k-C]+a);if(j>0)v=Math.min(v,D[k-C-1]+b);if(j<C-1)v=Math.min(v,D[k-C+1]+b)}D[k]=v}
  for(let i=R-1;i>=0;i--)for(let j=C-1;j>=0;j--){const k=i*C+j;let v=D[k];if(!v)continue;
    if(j<C-1)v=Math.min(v,D[k+1]+a);if(i<R-1){v=Math.min(v,D[k+C]+a);if(j<C-1)v=Math.min(v,D[k+C+1]+b);if(j>0)v=Math.min(v,D[k+C-1]+b)}D[k]=v}
  const u8=new Uint8Array(N);for(let k=0;k<N;k++)u8[k]=D[k]>255?255:D[k];
  if(G.shoreTex)G.shoreTex.dispose();
  const t=new THREE.DataTexture(u8,C,R,THREE.LuminanceFormat,THREE.UnsignedByteType);t.unpackAlignment=1;t.magFilter=t.minFilter=THREE.LinearFilter;t.generateMipmaps=false;t.needsUpdate=true;G.shoreTex=t;
  const U=G.seaU;U.shoreTex.value=t;U.shoreOff.value.set(G.cx,G.cz);U.shoreSize.value.set(C*cs,R*cs);U.shoreOn.value=1;
  seaColour(D);
}
function seaColour(D){ // average the photo over open water (15 m+ from land) in 20 m blocks, fill under the land, smooth away boats
  const OV=W3.areas[AREA]&&W3.areas[AREA].overview,g0=V.gen;if(!OV)return;
  OV.then(b=>b&&createImageBitmap(b)).then(bmp=>{if(!bmp||g0!==V.gen)return;
    const C=D3.cols,R=D3.rows,cv=document.createElement('canvas');cv.width=C;cv.height=R;const x=cv.getContext('2d',{willReadFrequently:true});
    x.imageSmoothingQuality='high';x.drawImage(bmp,0,0,C,R);const px=x.getImageData(0,0,C,R).data;
    const B=4,w=Math.ceil(C/B),h=Math.ceil(R/B),acc=new Float32Array(w*h*4);
    for(let i=0;i<R;i++)for(let j=0;j<C;j++){const k=i*C+j;if(D[k]<15)continue;const o=((i/B|0)*w+(j/B|0))*4;acc[o]+=px[k*4];acc[o+1]+=px[k*4+1];acc[o+2]+=px[k*4+2];acc[o+3]++}
    let col=new Float32Array(w*h*3),ok=new Uint8Array(w*h),sum=[0,0,0],n=0;
    for(let q=0;q<w*h;q++)if(acc[q*4+3]>=4){for(let c=0;c<3;c++){col[q*3+c]=acc[q*4+c]/acc[q*4+3];sum[c]+=col[q*3+c]}ok[q]=1;n++}
    if(n<20)return; // almost no sea in this area
    for(let pass=0;pass<60;pass++){let left=0;const nc=col.slice(),no=ok.slice();
      for(let i=0;i<h;i++)for(let j=0;j<w;j++){const q=i*w+j;if(ok[q])continue;let s0=0,s1=0,s2=0,m=0;
        for(const [di,dj] of [[-1,0],[1,0],[0,-1],[0,1]]){const a=i+di,b=j+dj;if(a<0||b<0||a>=h||b>=w)continue;const r=a*w+b;if(ok[r]){s0+=col[r*3];s1+=col[r*3+1];s2+=col[r*3+2];m++}}
        if(m){nc[q*3]=s0/m;nc[q*3+1]=s1/m;nc[q*3+2]=s2/m;no[q]=1}else left++}
      col=nc;ok=no;if(!left)break}
    for(let q=0;q<w*h;q++)if(!ok[q])for(let c=0;c<3;c++)col[q*3+c]=sum[c]/n;
    for(let pass=0;pass<3;pass++){const nc=col.slice();for(let i=0;i<h;i++)for(let j=0;j<w;j++){const q=i*w+j;for(let c=0;c<3;c++){let s=0,m=0;
      for(let a=Math.max(0,i-1);a<=Math.min(h-1,i+1);a++)for(let b=Math.max(0,j-1);b<=Math.min(w-1,j+1);b++){s+=col[(a*w+b)*3+c];m++}nc[q*3+c]=s/m}}col=nc}
    const u8=new Uint8Array(w*h*4);for(let q=0;q<w*h;q++){u8[q*4]=col[q*3];u8[q*4+1]=col[q*3+1];u8[q*4+2]=col[q*3+2];u8[q*4+3]=255}
    if(G.seaColTex)G.seaColTex.dispose();
    const t=new THREE.DataTexture(u8,w,h,THREE.RGBAFormat,THREE.UnsignedByteType);t.magFilter=t.minFilter=THREE.LinearFilter;t.generateMipmaps=false;t.needsUpdate=true;G.seaColTex=t;
    const lin=v=>{v/=255;return v<=0.04045?v/12.92:Math.pow((v+0.055)/1.055,2.4)};
    G.seaDay=new THREE.Color(lin(sum[0]/n),lin(sum[1]/n),lin(sum[2]/n)); // the sea beyond this area: the average photo colour
    G.seaU.seaCol.value=t;G.seaU.seaColOn.value=1;applySun();
  }).catch(e=>console.warn(e));
}
function build3D(){
  const wrap=$('#v3dCanvas');const C=D3.cols,R=D3.rows,cs=D3.cs;
  const renderer=new THREE.WebGLRenderer({antialias:!MOBILE,powerPreference:'high-performance'});
  G.prMax=Math.min(devicePixelRatio||1,MOBILE?1.5:2);G.pr=MOBILE?Math.min(1.25,G.prMax):G.prMax;renderer.setPixelRatio(G.pr);
  renderer.outputEncoding=THREE.sRGBEncoding;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=0.72;heightFog();renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;
  wrap.insertBefore(renderer.domElement,wrap.firstChild);
  const scene=new THREE.Scene();
  G.W=C*cs;G.Hh=R*cs;G.cx=G.W/2;G.cz=G.Hh/2;
  const camera=new THREE.PerspectiveCamera(45,1,5,160000);
  const psky=physicalSky();const sky=psky||makeSky();G.psky=!!psky;scene.add(sky);
  const sun=new THREE.DirectionalLight(0xffffff,1.0);sun.castShadow=true;
  const sm=MOBILE?2048:4096;sun.shadow.mapSize.set(sm,sm);const sc=sun.shadow.camera;sc.left=-3200;sc.right=3200;sc.top=3200;sc.bottom=-3200;sc.near=100;sc.far=40000;
  sun.shadow.bias=-0.0004;sun.shadow.normalBias=1.5;scene.add(sun);scene.add(sun.target);
  const hemi=new THREE.HemisphereLight(0xe8f1ff,0x5b6552,0.8);scene.add(hemi);
  const rip=rippleNormals();rip.repeat.set(6000,6000); // one ripple tile ≈ 67 m
  const sea=new THREE.Mesh(new THREE.PlaneGeometry(400000,400000),seaMaterial(rip));
  sea.rotation.x=-Math.PI/2;sea.receiveShadow=true;scene.add(sea);
  const controls=new THREE.OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=0.08;
  controls.maxPolarAngle=Math.PI*0.49;controls.minDistance=60;controls.maxDistance=45000;controls.screenSpacePanning=false;
  controls.addEventListener('start',()=>{if(V.fly){stopFly();render3DChrome()}});
  G.detTex=detailTexture();G.detU={value:0};
  G.lowMat=addDetail(new THREE.MeshLambertMaterial({color:0x7d8f6a}));
  Object.assign(G,{renderer,scene,camera,controls,sun,hemi,sea,sky,rip,labels:[],chunks:[],hiQueue:[],hiLoading:0,frustum:new THREE.Frustum(),pm:new THREE.Matrix4(),box:new THREE.Box3(),ft:[]});
  const terrain=new THREE.Group();scene.add(terrain);G.terrain=terrain;
  CH.chunks.forEach(c=>{const x0=(c.c0+0.5)*cs,x1=(c.c1+0.5)*cs,z0=(c.r0+0.5)*cs,z1=(c.r1+0.5)*cs;
    const ch={...c,x0,x1,z0,z1,geos:{},stride:0,mesh:null,hi:null,hiState:0,lastUse:0};
    let mx=-1e9,mn=1e9;for(let i=c.r0;i<=c.r1;i+=4)for(let j=c.c0;j<=c.c1;j+=4){const h=Hc(i,j);if(h>mx)mx=h;if(h<mn)mn=h}ch.hmax=mx+60;ch.hmin=Math.min(mn,-6);
    G.chunks.push(ch)});
  const grp=new THREE.Group();scene.add(grp);G.labelGrp=grp;relabel();
  applyLook();
  G.ro=new ResizeObserver(resize3D);G.ro.observe(wrap);resize3D();walkPointer(renderer.domElement);
}
function chunkGeo(ch,stride){
  const key=stride+'@'+V.ex;if(ch.geos[key])return ch.geos[key];
  const cs=D3.cs,ex=V.ex,C=D3.cols,R=D3.rows;const cols=[],rows=[];
  for(let j=ch.c0;j<ch.c1;j+=stride)cols.push(j);cols.push(ch.c1);for(let i=ch.r0;i<ch.r1;i+=stride)rows.push(i);rows.push(ch.r1);
  const nc=cols.length,nr=rows.length;const cap=nc*nr+2*nc+2*nr;
  const pos=new Float32Array(cap*3),nor=new Float32Array(cap*3),uv=new Float32Array(cap*2);
  let k=0;const s=Math.max(1,stride);
  const put=(i,j,drop)=>{const h=Math.max(-6,Hs(i,j))*ex-(drop||0);pos[k*3]=(j+0.5)*cs-G.cx;pos[k*3+1]=h;pos[k*3+2]=(i+0.5)*cs-G.cz;
    const dx=(Hs(i,j+s)-Hs(i,j-s))/(2*s*cs)*ex,dz=(Hs(i+s,j)-Hs(i-s,j))/(2*s*cs)*ex;const l=Math.sqrt(dx*dx+1+dz*dz);
    nor[k*3]=-dx/l;nor[k*3+1]=1/l;nor[k*3+2]=-dz/l;uv[k*2]=j/(C-1);uv[k*2+1]=1-i/(R-1);return k++};
  for(let a=0;a<nr;a++)for(let b=0;b<nc;b++)put(rows[a],cols[b]);
  const idx=[];for(let a=0;a<nr-1;a++)for(let b=0;b<nc-1;b++){const p=a*nc+b,q=p+1,r=p+nc,t=r+1;idx.push(p,r,q,q,r,t)}
  const drop=30*ex;const edge=list=>{const start=k;list.forEach(([i,j])=>put(i,j,drop));return start};
  const top=cols.map(j=>[rows[0],j]),bot=cols.map(j=>[rows[nr-1],j]),lef=rows.map(i=>[i,cols[0]]),rig=rows.map(i=>[i,cols[nc-1]]);
  const sk=(list,startTop,stepTop,sb)=>{for(let t=0;t<list.length-1;t++){const a=startTop+t*stepTop,b=startTop+(t+1)*stepTop,c=sb+t,d=sb+t+1;idx.push(a,c,b,b,c,d,a,b,c,b,d,c)}};
  sk(top,0,1,edge(top));sk(bot,(nr-1)*nc,1,edge(bot));sk(lef,0,nc,edge(lef));sk(rig,nc-1,nc,edge(rig));
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos.subarray(0,k*3),3));g.setAttribute('normal',new THREE.BufferAttribute(nor.subarray(0,k*3),3));const uva=new THREE.BufferAttribute(uv.subarray(0,k*2),2);g.setAttribute('uv',uva);g.setAttribute('uv2',uva);
  g.setIndex(k>65535?new THREE.Uint32BufferAttribute(idx,1):new THREE.Uint16BufferAttribute(idx,1));g.computeBoundingSphere();
  ch.geos[key]=g;return g;
}
function hiTexture(ch,url){ // sharp photo for one chunk, mapped onto the whole-area UVs
  return fetch(url).then(r=>r.ok?r.blob():null).then(b=>b?blobTex(b):null).then(t=>{if(!t)return null;const C=D3.cols,R=D3.rows;
    const us=(ch.c1-ch.c0)/(C-1),vs=(ch.r1-ch.r0)/(R-1);t.repeat.set(1/us,1/vs);t.offset.set(-(ch.c0/(C-1))/us,-((R-1-ch.r1)/(R-1))/vs);return t}).catch(()=>null);
}
function applyLook(){
  if(V.look==='map'&&!G.mapMat){G.mapMat=addDetail(new THREE.MeshLambertMaterial({color:0x9fb08a,aoMap:G.ao||null}));fetch(L3+'map.webp').then(r=>r.blob()).then(blobTex).then(t=>{G.mapMat.map=t;G.mapMat.color.set(0xffffff);G.mapMat.needsUpdate=true}).catch(()=>{})}
  G.chunks.forEach(ch=>{if(ch.mesh)ch.mesh.material=pickMat(ch)});applySun();if(V.loaded)updateLOD();
}
function pickMat(ch){if(V.look==='map')return G.mapMat||G.lowMat;return (ch.hi&&ch.hiState===2)?ch.hi:G.lowMat}
/* level of detail: finer mesh near the camera; sharp photos only for chunks on screen */
function updateLOD(force){
  if(!G.chunks||!G.chunks.length||!G.camera)return;const cam=G.camera.position;const now=performance.now();
  G.camera.updateMatrixWorld();G.pm.multiplyMatrices(G.camera.projectionMatrix,G.camera.matrixWorldInverse);G.frustum.setFromProjectionMatrix(G.pm);
  const f=MOBILE?0.6:1;const maxHi=MOBILE?5:10;
  const scored=G.chunks.map(ch=>{const px=Math.max(ch.x0-G.cx,Math.min(cam.x,ch.x1-G.cx)),pz=Math.max(ch.z0-G.cz,Math.min(cam.z,ch.z1-G.cz));
    const py=Math.max(ch.hmin*V.ex,Math.min(cam.y,ch.hmax*V.ex));const d=Math.hypot(cam.x-px,cam.y-py,cam.z-pz);
    G.box.min.set(ch.x0-G.cx,ch.hmin*V.ex,ch.z0-G.cz);G.box.max.set(ch.x1-G.cx,ch.hmax*V.ex,ch.z1-G.cz);ch.vis=G.frustum.intersectsBox(G.box);ch.d=d;return ch}).sort((a,b)=>a.d-b.d);
  let builds=0;const budget=force?99:2;
  for(const ch of scored){
    let s=ch.d<1500*f?1:ch.d<3400*f?2:ch.d<7500*f?4:8;if(MOBILE)s=Math.max(2,s);if(!G.full&&s<2)s=2;
    if(!ch.mesh){const g=chunkGeo(ch,8);ch.mesh=new THREE.Mesh(g,pickMat(ch));ch.mesh.castShadow=true;ch.mesh.receiveShadow=true;G.terrain.add(ch.mesh);ch.stride=8;G.shadowDirty=true}
    if((s!==ch.stride||ch.dirty)&&builds<budget){const g=chunkGeo(ch,s);ch.mesh.geometry=g;ch.stride=s;ch.dirty=false;builds++;if(ch.d<4000)G.shadowDirty=true;
      Object.keys(ch.geos).forEach(k=>{if(ch.geos[k]!==g&&(+k.split('@')[0]<=2||!k.endsWith('@'+V.ex))){ch.geos[k].dispose();delete ch.geos[k]}})}
    ch.want=V.look==='photo'&&ch.vis&&ch.d<(MOBILE?2200:3600);if(ch.want)ch.lastUse=now;
  }
  G.hiQueue=scored.filter(ch=>ch.want&&ch.hiState===0);pumpHi();
  const his=G.chunks.filter(c=>c.hiState===2&&!c.want).sort((a,b)=>a.lastUse-b.lastUse);let count=G.chunks.filter(c=>c.hiState===2).length;
  while(count>maxHi&&his.length){const c=his.shift();c.hi.map.dispose();c.hi.dispose();c.hi=null;c.hiState=0;count--;if(c.mesh)c.mesh.material=pickMat(c)}
  const pending=G.hiQueue.length+G.hiLoading+(G.full?0:1);$('#v3dStatus').textContent=pending?T('Sharpening…','正在提升清晰度…'):'';
}
function pumpHi(){
  while(G.hiLoading<3&&G.hiQueue.length){const ch=G.hiQueue.shift();if(!ch.want||ch.hiState!==0)continue;ch.hiState=1;G.hiLoading++;
    const g0=V.gen;hiTexture(ch,`${L3}h_${ch.id}.webp`).then(t=>{if(g0!==V.gen){if(t)t.dispose();return}G.hiLoading--;if(t){ch.hi=addDetail(new THREE.MeshLambertMaterial({map:t,aoMap:G.ao||null}));ch.hiState=2;if(ch.mesh)ch.mesh.material=pickMat(ch)}else ch.hiState=0;pumpHi()})}
}
function buildExtras(){
  if(!EX)return;
  if(G.extras){G.scene.remove(G.extras);G.extras.traverse(o=>{if(o.geometry)o.geometry.dispose()})}
  const grp=new THREE.Group();G.extras=grp;G.scene.add(grp);const ex=V.ex;
  let nt=0;EX.buildings.forEach(b=>{const n=(b.length-3)/2;nt+=n*2+Math.max(0,n-2)});
  const P=new Float32Array(nt*9),N=new Float32Array(nt*9),Cc=new Float32Array(nt*9);let o=0;
  const wall=[0.86,0.84,0.80],tower=[0.9,0.91,0.93],roof=[0.66,0.63,0.6];
  const v3=(x,y,z,n,c)=>{P[o]=x;P[o+1]=y;P[o+2]=z;N[o]=n[0];N[o+1]=n[1];N[o+2]=n[2];Cc[o]=c[0];Cc[o+1]=c[1];Cc[o+2]=c[2];o+=3};
  EX.buildings.forEach(b=>{const base=b[0],h=b[1],isT=b[2];const pts=[];for(let k=3;k<b.length;k+=2)pts.push([b[k]-G.cx,b[k+1]-G.cz]);
    if(pts.length<3)return;const y0=base*ex-1.5,y1=y0+1.5+h;const wc=isT?tower:wall;
    for(let k=0;k<pts.length;k++){const a=pts[k],c=pts[(k+1)%pts.length];const dx=c[0]-a[0],dz=c[1]-a[1];const l=Math.hypot(dx,dz)||1;const n=[dz/l,0,-dx/l];
      v3(a[0],y0,a[1],n,wc);v3(c[0],y0,c[1],n,wc);v3(c[0],y1,c[1],n,wc);v3(a[0],y0,a[1],n,wc);v3(c[0],y1,c[1],n,wc);v3(a[0],y1,a[1],n,wc)}
    let tris=[];try{tris=THREE.ShapeUtils.triangulateShape(pts.map(p=>new THREE.Vector2(p[0],-p[1])),[])}catch(e){}
    tris.slice(0,Math.max(0,pts.length-2)).forEach(t=>{const up=[0,1,0];v3(pts[t[0]][0],y1,pts[t[0]][1],up,roof);v3(pts[t[2]][0],y1,pts[t[2]][1],up,roof);v3(pts[t[1]][0],y1,pts[t[1]][1],up,roof)});
  });
  const bg=new THREE.BufferGeometry();bg.setAttribute('position',new THREE.BufferAttribute(P.subarray(0,o),3));bg.setAttribute('normal',new THREE.BufferAttribute(N.subarray(0,o),3));bg.setAttribute('color',new THREE.BufferAttribute(Cc.subarray(0,o),3));
  const bm=new THREE.Mesh(bg,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));bm.castShadow=true;bm.receiveShadow=true;grp.add(bm);
  G.cabins=null;if(!EX.cable||EX.cable.length<2)return;
  const cab=EX.cable.map(p=>new THREE.Vector3(p[0]-G.cx,(p[3]-p[2])*ex+p[2],p[1]-G.cz));
  const side=off=>cab.map((v,i)=>{const a=cab[Math.max(0,i-1)],b=cab[Math.min(cab.length-1,i+1)];const dx=b.x-a.x,dz=b.z-a.z,l=Math.hypot(dx,dz)||1;return new THREE.Vector3(v.x-dz/l*off,v.y,v.z+dx/l*off)});
  const cm=new THREE.MeshLambertMaterial({color:0x2a2e33});G.cableCurves=[];
  [-4,4].forEach(off=>{const pts=side(off);const curve=new THREE.CatmullRomCurve3(pts);curve.arcLengthDivisions=400;G.cableCurves.push(curve);grp.add(new THREE.Mesh(new THREE.TubeGeometry(curve,pts.length*2,0.9,3,false),cm))});
  const tm=new THREE.MeshLambertMaterial({color:0x8a9096});
  (EX.towers||[]).forEach(t=>{if(t[3]!=='pylon')return;const g=hAt(t[0],t[1])*ex;const m=new THREE.Mesh(new THREE.CylinderGeometry(1.4,3.2,t[2],4),tm);m.position.set(t[0]-G.cx,g+t[2]/2,t[1]-G.cz);m.castShadow=true;grp.add(m)});
  const cabinGeo=new THREE.BoxGeometry(3,2.6,3);cabinGeo.translate(0,-3.2,0);
  const nCab=MOBILE?24:50;const inst=new THREE.InstancedMesh(cabinGeo,new THREE.MeshLambertMaterial({color:0xc8312b}),nCab);grp.add(inst);G.cabins=inst;G.nCab=nCab;
  G.cableLen=G.cableCurves[0].getLength();
}
function moveCabins(t){
  if(!G.cabins)return;const m=G._m||(G._m=new THREE.Matrix4()),q=G._q||(G._q=new THREE.Quaternion()),one=G._one||(G._one=new THREE.Vector3(1,1,1)),p=G._p||(G._p=new THREE.Vector3());
  for(let i=0;i<G.nCab;i++){const dir=i%2;let u=((i/G.nCab)+(dir?-1:1)*(t/1000*6/G.cableLen))%1;if(u<0)u+=1;G.cableCurves[dir].getPointAt(u,p);m.compose(p,q,one);G.cabins.setMatrixAt(i,m)}
  G.cabins.instanceMatrix.needsUpdate=true;
}
function relabel(){
  if(!G.labelGrp)return;G.labels.forEach(s=>{G.labelGrp.remove(s);s.material.map.dispose();s.material.dispose()});G.labels=[];
  const PST={in:[' · in cloud',' · 雲中'],patches:[' · passing cloud',' · 零散雲']};
  (G.BR?G.BR.labels:[]).forEach(l=>{const s=makeLabel(T(l.en,l.zh),l.kind==='bridge'?'bridge':'place');Object.assign(s.userData,{x:l.x,z:l.z,fixedY:l.y,far:1});G.labelGrp.add(s);G.labels.push(s)});
  D3.labels.forEach(l=>{const pk=l.kind==='peak'&&COND.cloud&&COND.cloud.peaks?COND.cloud.peaks.find(p=>p.en===l.en):null;const st=pk&&PST[pk.status]?T(...PST[pk.status]):'';
    const s=makeLabel(l.kind==='peak'?`${T(l.en,l.zh)} ${l.h} m${st}`:T(l.en,l.zh),l.kind);Object.assign(s.userData,{x:l.p[0],z:l.p[1],lift:l.kind==='peak'?60:40});G.labelGrp.add(s);G.labels.push(s)});
  placeOverlays();
}
/* ----- live cloud layers at the heights the airport reports ----- */
function buildClouds(){
  if(!G.scene)return;if(G.cloudGrp){G.scene.remove(G.cloudGrp);G.cloudGrp.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material)o.material.dispose()})}
  const grp=new THREE.Group();G.cloudGrp=grp;grp.visible=V.clouds;G.scene.add(grp);G.cloudMats=[];
  const cl=COND.cloud;if(!cl)return;const layers=(cl.layers||[]).filter(l=>l.base_m<3000);
  const geo=new THREE.PlaneGeometry(40000,40000,1,1);geo.rotateX(-Math.PI/2);
  layers.forEach((L,li)=>{[[0,1],[45,0.8],[100,0.55]].forEach(([dz,wt],k)=>{
    const thr=0.5+(0.5-L.frac)*0.5;
    const mat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,fog:false,
      uniforms:{t:{value:0},off:{value:new THREE.Vector2()},thr:{value:thr},wt:{value:wt},seed:{value:li*7.3+k*3.1},sunCol:{value:new THREE.Color(1,1,1)},li:{value:1},cam:{value:new THREE.Vector3()},fogCol:{value:new THREE.Color()},fogD:{value:0.00004}},
      vertexShader:'varying vec3 vW;void main(){vec4 w=modelMatrix*vec4(position,1.0);vW=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;}',
      fragmentShader:`uniform vec2 off;uniform float thr,wt,seed,li,fogD;uniform vec3 sunCol,cam,fogCol;varying vec3 vW;
        float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7))+seed)*43758.5453);}
        float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
        float fbm(vec2 p){float s=0.0,a=0.5;for(int i=0;i<5;i++){s+=a*n(p);p=p*2.03+vec2(1.7,9.2);a*=0.5;}return s;}
        void main(){vec2 p=(vW.xz-off)/1100.0;float v=fbm(p);float d=smoothstep(thr-0.04,thr+0.16,v)*wt;
          float dist=length(vW-cam);d*=1.0-smoothstep(11000.0,19000.0,length(vW.xz-cam.xz));
          vec3 c=mix(vec3(0.60,0.64,0.70),sunCol,0.45+0.55*smoothstep(thr,thr+0.3,v))*li;
          float f=1.0-exp(-pow(dist*fogD,2.0));c=mix(c,fogCol,f*0.8);
          gl_FragColor=vec4(c,d*0.82);}`});
    const m=new THREE.Mesh(geo,mat);m.position.y=(L.base_m+dz)*V.ex;m.renderOrder=5;m.frustumCulled=false;grp.add(m);G.cloudMats.push(mat)})});
  // drift with the airport wind (sped up 20x so the movement is visible)
  let dir=typeof cl.wdir==='number'?cl.wdir:null;const words={North:0,Northeast:45,East:90,Southeast:135,South:180,Southwest:225,West:270,Northwest:315};
  if(dir==null&&cl.wind_ngongping)dir=words[cl.wind_ngongping[0]]??270;
  const b=((dir??270)+180)*Math.PI/180,sp=Math.max(1,(cl.wspd_kt||4))*0.514*20;G.cloudWind=new THREE.Vector2(Math.sin(b)*sp,-Math.cos(b)*sp);
  cloudLight();
}
function cloudLight(){
  if(!G.cloudMats||!G.sun)return;const s=sunPos(hkNow(),V.sunMin);const li=s.el<-2?0.25:0.55+0.45*Math.min(1,Math.max(0,(s.el+2)/20));
  G.cloudMats.forEach(m=>{m.uniforms.sunCol.value.copy(G.sun.color).lerp(new THREE.Color(1,1,1),0.35);m.uniforms.li.value=li;if(G.scene.fog){m.uniforms.fogCol.value.copy(G.scene.fog.color);m.uniforms.fogD.value=G.scene.fog.density}});
}
function makeLabel(text,kind){
  const f=kind==='post'?26:30,pad=10;const c=document.createElement('canvas');const g=c.getContext('2d');
  g.font=`600 ${f}px "Noto Sans HK","Barlow Condensed",sans-serif`;const w=Math.ceil(g.measureText(text).width)+pad*2,h=f+pad*1.6+14;
  c.width=w;c.height=h;g.font=`600 ${f}px "Noto Sans HK","Barlow Condensed",sans-serif`;
  const bg=kind==='post'?'#15241d':kind==='peak'?'#ffffff':kind==='bridge'?'#0e3a5a':'rgba(255,255,255,.92)',fg=(kind==='post'||kind==='bridge')?'#ffffff':'#15241d';
  g.fillStyle=bg;const rr=8,bh=h-14;g.beginPath();g.moveTo(rr,0);g.lineTo(w-rr,0);g.quadraticCurveTo(w,0,w,rr);g.lineTo(w,bh-rr);g.quadraticCurveTo(w,bh,w-rr,bh);g.lineTo(w/2+8,bh);g.lineTo(w/2,h);g.lineTo(w/2-8,bh);g.lineTo(rr,bh);g.quadraticCurveTo(0,bh,0,bh-rr);g.lineTo(0,rr);g.quadraticCurveTo(0,0,rr,0);g.fill();
  if(kind==='peak'){g.strokeStyle='#b8660f';g.lineWidth=3;g.stroke()}
  g.fillStyle=fg;g.textBaseline='middle';g.fillText(text,pad,bh/2+1);
  const t=new THREE.CanvasTexture(c);t.encoding=THREE.sRGBEncoding;t.anisotropy=4;
  const s=new THREE.Sprite(new THREE.SpriteMaterial({map:t,depthTest:false,transparent:true,fog:false}));
  s.center.set(0.5,0);s.userData.aspect=w/h;s.renderOrder=10;return s;
}
function applyHeights(){
  G.chunks.forEach(ch=>{Object.values(ch.geos).forEach(g=>g.dispose());ch.geos={};ch.dirty=true});
  buildExtras();updateLOD(true);placeOverlays();applyStage(false);buildClouds();if(G.farChunks){G.farChunks.forEach(c=>{Object.values(c.geos).forEach(g=>g.dispose());c.geos={};c.dirty=true});farLOD(true)}buildBridge();G.shadowDirty=true;
}
function placeOverlays(){if(!G.labels)return;G.labels.forEach(s=>{const y=s.userData.fixedY!=null?s.userData.fixedY*V.ex:hAt(s.userData.x,s.userData.z)*V.ex+(s.userData.lift||20);s.position.set(s.userData.x-G.cx,y,s.userData.z-G.cz)})}
function ribbon(pts,width,lift,color,order,opacity){
  const n=pts.length;const pos=new Float32Array(n*2*3);const idx=[];
  for(let i=0;i<n;i++){const a=pts[Math.max(0,i-1)],b=pts[Math.min(n-1,i+1)];let dx=b[0]-a[0],dz=b[1]-a[1];const L=Math.hypot(dx,dz)||1;dx/=L;dz/=L;
    const nx=-dz*width/2,nz=dx*width/2;const x=pts[i][0],z=pts[i][1];
    pos.set([x+nx-G.cx,hAt(x+nx,z+nz)*V.ex+lift,z+nz-G.cz,x-nx-G.cx,hAt(x-nx,z-nz)*V.ex+lift,z-nz-G.cz],i*6);
    if(i<n-1){const q=i*2;idx.push(q,q+1,q+2,q+1,q+3,q+2)}}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setIndex(idx);
  const m=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color,side:THREE.DoubleSide,transparent:true,opacity,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-4,polygonOffsetUnits:-4}));m.renderOrder=order;m.visible=V.route;return m;
}
function applyStage(frame){
  if(!G.scene||!D3)return;
  if(G.stageGrp){G.scene.remove(G.stageGrp);G.stageGrp.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material){if(o.material.map)o.material.map.dispose();o.material.dispose()}})}
  const grp=new THREE.Group();G.stageGrp=grp;G.scene.add(grp);
  const st=D3.stages[V.stage];if(!st)return;
  grp.add(ribbon(st.pts,11,2.5,0xffffff,1,0.85));grp.add(ribbon(st.pts,5,3,0xff6a1a,2,0.999));
  const r=byId[V.stage];const a=r.post_list[0][0],b=r.post_list[r.post_list.length-1][0];const na=+a.slice(1),nb=+b.slice(1);
  D3.posts.filter(p=>{const n=+p[0].slice(1);return p[0][0]===a[0]&&n>=na&&n<=nb}).forEach(p=>{const s=makeLabel(p[0],'post');Object.assign(s.userData,{x:p[1],z:p[2],lift:14,post:1});grp.add(s)});
  const s0=st.pts[0],s1=st.pts[st.pts.length-1];
  [[s0,T('Start','起點')+' · '+F(r,'start')],[s1,T('End','終點')+' · '+F(r,'end')]].forEach(([p,t])=>{const s=makeLabel(t,'place');Object.assign(s.userData,{x:p[0],z:p[1],lift:45});grp.add(s)});
  grp.children.forEach(o=>{if(o.isSprite)o.position.set(o.userData.x-G.cx,hAt(o.userData.x,o.userData.z)*V.ex+o.userData.lift,o.userData.z-G.cz)});
  placeOverlays();applySun();if(V.walk)walkDress();
  if(frame){
    let x0=1e9,x1=-1e9,z0=1e9,z1=-1e9;st.pts.forEach(p=>{x0=Math.min(x0,p[0]);x1=Math.max(x1,p[0]);z0=Math.min(z0,p[1]);z1=Math.max(z1,p[1])});
    const cx=(x0+x1)/2-G.cx,cz=(z0+z1)/2-G.cz,span=Math.max(x1-x0,z1-z0,2500);const ty=hAt((x0+x1)/2,(z0+z1)/2)*V.ex*0.6;
    G.controls.target.set(cx,ty,cz);G.camera.position.set(cx+span*0.55,ty+span*0.7,cz+span*1.0);G.controls.update();
  }
  if(V.loaded)updateLOD();
}
function applySun(){
  if(!G.sun)return;const s=sunPos(hkNow(),V.sunMin);const rad=Math.PI/180;const photo=V.look==='photo';
  const el=Math.max(s.el,-3);const dir=new THREE.Vector3(Math.sin(s.az*rad)*Math.cos(el*rad),Math.sin(Math.max(el,0.5)*rad),-Math.cos(s.az*rad)*Math.cos(el*rad)).normalize();
  G.sunDir=dir;G.shadowDirty=true;
  const day=Math.max(0,Math.min(1,s.el/25)),dusk=1-day,night=s.el<-2;
  const warm=new THREE.Color(0xff9d5c),white=new THREE.Color(0xfff4e2);
  G.sun.color.copy(warm.clone().lerp(white,day));
  const sunI=night?0:Math.min(1,Math.max(0,(s.el+1)/12));
  G.sun.intensity=(photo?0.55:1.0)*sunI;G.sun.castShadow=!night&&s.el>0.5;
  G.hemi.intensity=night?0.18:(photo?0.78:0.5)*(0.55+0.45*Math.min(1,Math.max(0,(s.el+4)/14)));
  G.hemi.color.set(night?0x6d7a99:0xe8f1ff);
  const zen=new THREE.Color(0x3e78b8).lerp(new THREE.Color(0x35507e),dusk*0.7),hor=new THREE.Color(0xd0dde4).lerp(new THREE.Color(0xf3b98a),dusk*(s.el<12?1:0.4));
  if(night){zen.set(0x0c1424);hor.set(0x2a3448)}
  const u=G.sky.material.uniforms;
  if(G.psky){const raw=new THREE.Vector3(Math.sin(s.az*rad)*Math.cos(s.el*rad),Math.sin(s.el*rad),-Math.cos(s.az*rad)*Math.cos(s.el*rad));u.sunPosition.value.copy(raw);u.skyGain.value=0.34+0.5*(1-Math.min(1,Math.max(0,s.el/35)))}
  else{u.sunDir.value.copy(dir);u.zenith.value.copy(zen);u.horizon.value.copy(hor);u.sunCol.value.copy(warm.clone().lerp(white,day));u.sunI.value=night?0:1}
  G.fogBase=night?new THREE.Color(0x1c2433):new THREE.Color(0xc4d2da).lerp(new THREE.Color(0xe6b996),dusk*(s.el<10?0.85:0.3));G.fogSun=warm.clone().lerp(white,day);
  G.scene.fog=new THREE.FogExp2(G.fogBase.clone(),0.000055);
  if(G.seaU)G.seaU.skyRef.value.copy(G.fogBase).multiplyScalar(night?0.5:0.8);if(night)G.sea.material.color.set(0x0f1f28);else if(G.seaDay)G.sea.material.color.copy(G.seaDay);else G.sea.material.color.set(0x2b5a6c);if(G.seaU)G.seaU.foamL.value=night?0.12:0.3+0.7*sunI;
  cloudLight();
  $('#v3dSunInfo').textContent=night?T('Sun below the horizon','太陽已落山'):T(`Sun ${Math.round(s.el)}° up, from the ${compass(s.az)}`,`太陽仰角${Math.round(s.el)}°，${compassZh(s.az)}方`);
}
const compass=a=>['north','north-east','east','south-east','south','south-west','west','north-west'][Math.round(a/45)%8];
const compassZh=a=>['北','東北','東','東南','南','西南','西','西北'][Math.round(a/45)%8];
function resize3D(){if(!G.renderer)return;const w=$('#v3dCanvas');const W=w.clientWidth,H=w.clientHeight;if(!W||!H)return;G.renderer.setSize(W,H);G.camera.aspect=W/H;G.camera.updateProjectionMatrix()}
function scaleSprites(){
  const H=$('#v3dCanvas').clientHeight||600;const k=2*Math.tan(G.camera.fov*Math.PI/360)/H;
  let all=G.stageGrp?G.labels.concat(G.stageGrp.children.filter(o=>o.isSprite)):G.labels;if(G.walkGrp)all=all.concat(G.walkGrp.children.filter(o=>o.isSprite));
  all.forEach(s=>{const d=G.camera.position.distanceTo(s.position);const wpp=d*k;const hpx=(s.userData.post?22:28);s.scale.set(hpx*wpp*s.userData.aspect,hpx*wpp,1);if(s.userData.pin)s.visible=d<450;else if(s.userData.post)s.visible=d<(V.walk?700:4500);else if(V.walk)s.visible=false;else if(s.userData.far)s.visible=d<42000;else s.visible=d<30000});
}
function followShadow(t){ // shadow map is redrawn only when the view moves far, the sun moves or the terrain changes
  const mv=V.fly||V.walk;const tg=mv&&G.lookAt?G.lookAt:G.controls.target;
  if(!G.shadowAt||G.shadowAt.distanceTo(tg)>250||(mv&&t-(G.shadowT||0)>500))G.shadowDirty=true;
  if(G.shadowDirty){const d=G.sunDir||new THREE.Vector3(0,1,0);G.sun.target.position.copy(tg);G.sun.position.copy(tg).addScaledVector(d,15000);G.sun.target.updateMatrixWorld();
    G.renderer.shadowMap.needsUpdate=true;G.shadowAt=(G.shadowAt||new THREE.Vector3()).copy(tg);G.shadowT=t;G.shadowDirty=false}
}
function keepAboveGround(){const c=G.camera.position;const g=hAt(c.x+G.cx,c.z+G.cz)*V.ex;if(c.y<g+30)c.y=g+30}
function adapt(dt){ // lower the drawing resolution on slow devices
  const a=G.ft;a.push(dt);if(a.length<45)return;const avg=a.reduce((x,y)=>x+y,0)/a.length;a.length=0;
  if(avg>30&&G.pr>1){G.pr=Math.max(1,G.pr-0.25);G.renderer.setPixelRatio(G.pr);resize3D()}
  else if(avg<14&&G.pr<G.prMax){G.pr=Math.min(G.prMax,G.pr+0.25);G.renderer.setPixelRatio(G.pr);resize3D()}
}
function loop3D(){
  cancelAnimationFrame(V.raf);let lastLod=0,last=0;
  const tick=t=>{if(!V.open)return;V.raf=requestAnimationFrame(tick);
    if(last)adapt(t-last);last=t;
    if(V.fly)stepFly(t);else if(V.walk)stepWalk(t);else{G.controls.update();keepAboveGround()}
    if(t-lastLod>250){updateLOD();farLOD();lastLod=t}
    G.sky.position.copy(G.camera.position);
    if(G.scene.fog&&G.fogBase&&G.sunDir){const fw=G._fw||(G._fw=new THREE.Vector3());G.camera.getWorldDirection(fw);const a=Math.pow(Math.max(0,fw.dot(G.sunDir)),6)*0.45;G.scene.fog.color.copy(G.fogBase).lerp(G.fogSun,a)}G.rip.offset.set((t*0.0000035)%1,(t*0.0000021)%1);if(G.seaU)G.seaU.seaT.value=(t/1000)%10000;
    if(G.cloudMats&&G.cloudWind){const sec=t/1000;G.cloudMats.forEach(m=>{m.uniforms.off.value.set(G.cloudWind.x*sec,G.cloudWind.y*sec);m.uniforms.cam.value.copy(G.camera.position)})}
    moveCabins(t);followShadow(t);scaleSprites();G.renderer.render(G.scene,G.camera)};
  V.raf=requestAnimationFrame(tick);
}
function startFly(){
  const st=D3.stages[V.stage];if(!st)return;const pts=st.pts;const cum=[0];for(let i=1;i<pts.length;i++)cum.push(cum[i-1]+Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]));
  const total=cum[cum.length-1];V.fly={pts,cum,total,t0:null,dur:Math.max(30000,total*11)};G.controls.enabled=false;
}
function stopFly(){if(!V.fly)return;V.fly=null;if(G.controls){G.controls.enabled=true;if(G.lookAt)G.controls.target.copy(G.lookAt)}$('#v3dFlyInfo').textContent=''}
function along(f,d){d=Math.max(0,Math.min(f.total,d));let lo=1,hi=f.cum.length-1;while(lo<hi){const m=(lo+hi)>>1;if(f.cum[m]<d)lo=m+1;else hi=m}const i=lo;const a=f.pts[i-1],b=f.pts[i],t=(d-f.cum[i-1])/((f.cum[i]-f.cum[i-1])||1);return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t]}
function stepFly(t){
  const f=V.fly;if(f.t0==null)f.t0=t;const u=Math.min(1,(t-f.t0)/f.dur);const e=u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2;const d=e*f.total;
  const here=along(f,d),ahead=along(f,d+180),behind=along(f,d-320);
  let camY=hAt(here[0],here[1])*V.ex;for(let k=0;k<=6;k++){const p=along(f,d-320+k*80);camY=Math.max(camY,hAt(p[0],p[1])*V.ex)}camY+=120*V.ex;
  const cp=new THREE.Vector3(behind[0]-G.cx,camY,behind[1]-G.cz);G.camera.position.lerp(cp,0.06);
  const la=new THREE.Vector3(ahead[0]-G.cx,hAt(ahead[0],ahead[1])*V.ex,ahead[1]-G.cz);G.lookAt=(G.lookAt||la.clone()).lerp(la,0.08);G.camera.lookAt(G.lookAt);
  keepAboveGround();
  $('#v3dFlyInfo').textContent=`${(d/1000).toFixed(1)} / ${(f.total/1000).toFixed(1)} km · ${T('height','高度')} ${Math.round(hAt(here[0],here[1]))} m`;
  if(u>=1){stopFly();render3DChrome()}
}

/* ----- wide area: Chek Lap Kok, the bridge, Zhuhai and Macau (40 m heights, 20 m satellite image) ----- */
async function loadFar(){
  const [fm,hb,tb]=await Promise.all([fetch(L3+'far.json').then(r=>r.json()),fetch(L3+'farh.webp').then(r=>r.blob()),fetch(L3+'fartex.webp').then(r=>r.blob())]);
  const bmp=await createImageBitmap(hb,{colorSpaceConversion:'none',premultiplyAlpha:'none'});const cv=document.createElement('canvas');cv.width=bmp.width;cv.height=bmp.height;
  const cx=cv.getContext('2d',{willReadFrequently:true});cx.drawImage(bmp,0,0);const px=cx.getImageData(0,0,bmp.width,bmp.height).data;const H=new Float32Array(bmp.width*bmp.height);
  for(let i=0;i<H.length;i++)H[i]=px[i*4]*256+px[i*4+1]-100;
  G.FAR={...fm,H};const tex=await blobTex(tb);G.farMat=new THREE.MeshLambertMaterial({map:tex});
  const grp=new THREE.Group();G.scene.add(grp);G.farGrp=grp;G.farChunks=[];
  const bc=184,br=209;
  for(let r0=0;r0<fm.rows-1;r0+=br)for(let c0=0;c0<fm.cols-1;c0+=bc){const c1=Math.min(fm.cols-1,c0+bc),r1=Math.min(fm.rows-1,r0+br);
    let mx=-1e9;for(let i=r0;i<=r1;i+=4)for(let j=c0;j<=c1;j+=4)mx=Math.max(mx,H[i*fm.cols+j]);
    if(mx<0)continue; // open sea: nothing to draw
    const x0=fm.E0+c0*fm.fs-D3.x0hk,x1=fm.E0+c1*fm.fs-D3.x0hk,z0=D3.ytophk-(fm.N1-r0*fm.fs),z1=D3.ytophk-(fm.N1-r1*fm.fs);
    G.farChunks.push({c0,c1,r0,r1,x0,x1,z0,z1,hmax:mx,geos:{},stride:0,mesh:null})}
  farLOD(true);
}
function farGeo(ch,s){
  const key=s+'@'+V.ex;if(ch.geos[key])return ch.geos[key];const F=G.FAR,W=F.cols,ex=V.ex;
  const cols=[],rows=[];for(let j=ch.c0;j<ch.c1;j+=s)cols.push(j);cols.push(ch.c1);for(let i=ch.r0;i<ch.r1;i+=s)rows.push(i);rows.push(ch.r1);
  const nc=cols.length,nr=rows.length,n=nc*nr;const pos=new Float32Array(n*3),nor=new Float32Array(n*3),uv=new Float32Array(n*2);let k=0;
  const Hf=(i,j)=>F.H[Math.max(0,Math.min(F.rows-1,i))*W+Math.max(0,Math.min(W-1,j))];
  for(const i of rows)for(const j of cols){const h=Hf(i,j);pos[k*3]=F.E0+j*F.fs-D3.x0hk-G.cx;pos[k*3+1]=(h<0.5?Math.max(Math.min(h,-20),-60):h)*ex;pos[k*3+2]=D3.ytophk-(F.N1-i*F.fs)-G.cz;
    const dx=(Hf(i,j+s)-Hf(i,j-s))/(2*s*F.fs)*ex,dz=(Hf(i+s,j)-Hf(i-s,j))/(2*s*F.fs)*ex,l=Math.sqrt(dx*dx+1+dz*dz);nor[k*3]=-dx/l;nor[k*3+1]=1/l;nor[k*3+2]=-dz/l;
    uv[k*2]=j/(W-1);uv[k*2+1]=1-i/(F.rows-1);k++}
  const idx=[];for(let a=0;a<nr-1;a++)for(let b=0;b<nc-1;b++){const p=a*nc+b,q=p+1,r=p+nc,t=r+1;idx.push(p,r,q,q,r,t)}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('normal',new THREE.BufferAttribute(nor,3));g.setAttribute('uv',new THREE.BufferAttribute(uv,2));
  g.setIndex(n>65535?new THREE.Uint32BufferAttribute(idx,1):new THREE.Uint16BufferAttribute(idx,1));g.computeBoundingSphere();ch.geos[key]=g;return g;
}
function farLOD(force){
  if(!G.farChunks)return;const cam=G.camera.position;let builds=0;
  for(const ch of G.farChunks){const px=Math.max(ch.x0-G.cx,Math.min(cam.x,ch.x1-G.cx)),pz=Math.max(ch.z0-G.cz,Math.min(cam.z,ch.z1-G.cz));const d=Math.hypot(cam.x-px,cam.z-pz,Math.max(0,cam.y));
    let s=d<7000?1:d<18000?2:4;if(MOBILE)s=Math.max(2,s);
    if(!ch.mesh){ch.mesh=new THREE.Mesh(farGeo(ch,4),G.farMat);ch.mesh.receiveShadow=true;G.farGrp.add(ch.mesh);ch.stride=4}
    if((s!==ch.stride||ch.dirty)&&(builds<1||force)){ch.mesh.geometry=farGeo(ch,s);ch.stride=s;ch.dirty=false;builds++;
      Object.keys(ch.geos).forEach(k=>{if(ch.geos[k]!==ch.mesh.geometry&&(+k.split('@')[0]===1||!k.endsWith('@'+V.ex))){ch.geos[k].dispose();delete ch.geos[k]}})}}
}
/* ----- Hong Kong–Zhuhai–Macao Bridge ----- */
function buildBridge(){
  const B=G.BR;if(!B)return;if(G.bridgeGrp){G.scene.remove(G.bridgeGrp);G.bridgeGrp.traverse(o=>{if(o.geometry)o.geometry.dispose()})}
  const grp=new THREE.Group();G.bridgeGrp=grp;G.scene.add(grp);const ex=V.ex;const X=x=>x-G.cx,Z=z=>z-G.cz;
  // deck: box girder = asphalt top + light sides + underside
  const P=[],N=[],Cl=[];const top=[0.36,0.37,0.39],side=[0.86,0.87,0.88],under=[0.62,0.63,0.64],kerb=[0.93,0.93,0.92];
  const quad=(a,b,c,d,n,col)=>{[a,b,c,a,c,d].forEach(p=>{P.push(p[0],p[1],p[2]);N.push(n[0],n[1],n[2]);Cl.push(col[0],col[1],col[2])})};
  B.deck.forEach(dk=>{const pts=dk.pts,hw=dk.w/2,th=dk.br?3.5:0.6;
    for(let i=0;i<pts.length-1;i++){const a=pts[i],b=pts[i+1];let dx=b[0]-a[0],dz=b[1]-a[1];const L=Math.hypot(dx,dz);if(L<0.5)continue;dx/=L;dz/=L;const nx=-dz*hw,nz=dx*hw;
      const ya=a[2]*ex,yb=b[2]*ex;
      const aL=[X(a[0]+nx),ya,Z(a[1]+nz)],aR=[X(a[0]-nx),ya,Z(a[1]-nz)],bL=[X(b[0]+nx),yb,Z(b[1]+nz)],bR=[X(b[0]-nx),yb,Z(b[1]-nz)];
      quad(aL,bL,bR,aR,[0,1,0],top);
      const pa=[X(a[0]+nx),ya+1.1,Z(a[1]+nz)],pb=[X(b[0]+nx),yb+1.1,Z(b[1]+nz)],qa=[X(a[0]-nx),ya+1.1,Z(a[1]-nz)],qb=[X(b[0]-nx),yb+1.1,Z(b[1]-nz)];
      quad(aL,pa,pb,bL,[-dz,0,dx],kerb);quad(aR,bR,qb,qa,[dz,0,-dx],kerb);
      const dL=[aL[0],ya-th,aL[2]],dR=[aR[0],ya-th,aR[2]],eL=[bL[0],yb-th,bL[2]],eR=[bR[0],yb-th,bR[2]];
      quad(dL,eL,bL,aL,[-dz,0,dx],side);quad(aR,bR,eR,dR,[dz,0,-dx],side);quad(dL,dR,eR,eL,[0,-1,0],under)}});
  const dg=new THREE.BufferGeometry();dg.setAttribute('position',new THREE.Float32BufferAttribute(P,3));dg.setAttribute('normal',new THREE.Float32BufferAttribute(N,3));dg.setAttribute('color',new THREE.Float32BufferAttribute(Cl,3));
  const dm=new THREE.Mesh(dg,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));dm.castShadow=true;dm.receiveShadow=true;grp.add(dm);
  // piers (instanced)
  const pg=new THREE.BoxGeometry(1,1,1);pg.translate(0,0.5,0);const pm=new THREE.MeshLambertMaterial({color:0xc9ccce});
  const pins=new THREE.InstancedMesh(pg,pm,B.piers.length);const m4=new THREE.Matrix4(),q=new THREE.Quaternion(),sc=new THREE.Vector3(),ps=new THREE.Vector3(),yax=new THREE.Vector3(0,1,0);
  B.piers.forEach((p,i)=>{const h=Math.max(1,(p[3]-p[2]))*ex;q.setFromAxisAngle(yax,-p[4]);ps.set(X(p[0]),p[2]*ex-2,Z(p[1]));sc.set(4.5,h+2,11);m4.compose(ps,q,sc);pins.setMatrixAt(i,m4)});
  pins.castShadow=true;grp.add(pins);
  // towers
  const white=new THREE.MeshLambertMaterial({color:0xf1f1ee}),conc=new THREE.MeshLambertMaterial({color:0xd4d6d6}),steel=new THREE.MeshLambertMaterial({color:0xe9ecef});
  const box=(w,h,d,mat,x,y,z,ry)=>{const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(x,y,z);m.rotation.y=ry||0;m.castShadow=true;grp.add(m);return m};
  B.towers.forEach(t=>{const ax=new THREE.Vector2(t.ax[0],t.ax[1]),nr=new THREE.Vector2(-t.ax[1],t.ax[0]);const ry=-Math.atan2(t.ax[1],t.ax[0]);const cx=X(t.x),cz=Z(t.z);const top=t.top*ex,deck=t.deck*ex;
    if(t.kind==='portal'){ // Qingzhou: two tall legs with a "Chinese knot" crossbeam
      [-1,1].forEach(sd=>{const ox=nr.x*(t.hw+4)*sd,oz=nr.y*(t.hw+4)*sd;const leg=new THREE.Mesh(new THREE.CylinderGeometry(3.2,4.8,top,4),conc);leg.position.set(cx+ox,top/2,cz+oz);leg.rotation.y=ry+Math.PI/4;leg.castShadow=true;grp.add(leg)});
      box(7,6,(t.hw+4)*2+8,conc,cx,deck-8,cz,ry);
      box(6,14,(t.hw+4)*2+6,conc,cx,top-18,cz,ry);
      const knot=new THREE.Mesh(new THREE.TorusGeometry(9,2.2,6,4),steel);knot.position.set(cx,top-18,cz);knot.rotation.y=ry+Math.PI/2;knot.rotation.z=Math.PI/4;grp.add(knot);
    }else{ // Jianghai "dolphin" and Jiuzhou "sail": single central tower in the median
      box(10,deck,14,conc,cx,deck/2,cz,ry);
      const sh=new THREE.Shape();const H=top-deck;
      if(t.kind==='dolphin'){sh.moveTo(-9,0);sh.bezierCurveTo(-10,H*0.45,-4,H*0.8,6,H);sh.bezierCurveTo(10,H*0.96,4,H*0.86,3,H*0.8);sh.bezierCurveTo(6,H*0.5,9,H*0.2,9,0);sh.lineTo(-9,0)}
      else{sh.moveTo(-6,0);sh.lineTo(-2.5,H);sh.quadraticCurveTo(12,H*0.55,22,0);sh.lineTo(-6,0)}
      const g=new THREE.ExtrudeGeometry(sh,{depth:t.kind==='dolphin'?5:3,bevelEnabled:false});g.translate(0,0,t.kind==='dolphin'?-2.5:-1.5);
      const m=new THREE.Mesh(g,t.kind==='dolphin'?white:steel);m.position.set(cx,deck,cz);m.rotation.y=ry;m.castShadow=true;grp.add(m)}
  });
  // stay cables
  const cp=[];B.cables.forEach(c=>{cp.push(X(c[0]),c[2]*ex,Z(c[1]),X(c[3]),c[5]*ex,Z(c[4]))});
  const cg=new THREE.BufferGeometry();cg.setAttribute('position',new THREE.Float32BufferAttribute(cp,3));grp.add(new THREE.LineSegments(cg,new THREE.LineBasicMaterial({color:0xdfe3e6})));
  relabel();G.shadowDirty=true;
}
function bridgeView(){
  const q=G.BR?G.BR.towers.filter(t=>t.n==='Qingzhou'):null;const tx=q&&q.length?(q[0].x+q[1].x)/2:-15900,tz=q&&q.length?(q[0].z+q[1].z)/2:730;
  const from=G.camera.position.clone(),to=new THREE.Vector3(tx-G.cx+1900,420*V.ex,tz-G.cz+1300),tFrom=G.controls.target.clone(),tTo=new THREE.Vector3(tx-G.cx-300,70*V.ex,tz-G.cz);
  const t0=performance.now(),dur=3500;G.controls.enabled=false;
  const step=()=>{const u=Math.min(1,(performance.now()-t0)/dur),e=u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2;G.camera.position.lerpVectors(from,to,e);G.controls.target.lerpVectors(tFrom,tTo,e);G.camera.lookAt(G.controls.target);
    if(u<1&&V.open)requestAnimationFrame(step);else{G.controls.enabled=true;G.controls.update()}};step();
  if(!G.BR)$('#v3dStatus').textContent=T('Loading the bridge…','正在載入大橋…');
}

/* ----- walk mode: first-person walk along the stage at eye height (1.7 m) ----- */
function detailTexture(){ // fine ground grain so close-up ground does not look like smeared paint
  const N=256,c=document.createElement('canvas');c.width=c.height=N;const g=c.getContext('2d');const img=g.createImageData(N,N);
  const oct=[[8,0.45],[16,0.3],[32,0.25]];const grids=oct.map(([n])=>{const a=new Float32Array(n*n);for(let i=0;i<a.length;i++)a[i]=Math.random();return a});
  for(let y=0;y<N;y++)for(let x=0;x<N;x++){let v=0;
    oct.forEach(([n,w],k)=>{const fx=x/N*n,fy=y/N*n,x0=Math.floor(fx),y0=Math.floor(fy),tx=fx-x0,ty=fy-y0,sx=tx*tx*(3-2*tx),sy=ty*ty*(3-2*ty),A=grids[k];
      const at=(i,j)=>A[(j%n)*n+(i%n)];v+=w*((at(x0,y0)*(1-sx)+at(x0+1,y0)*sx)*(1-sy)+(at(x0,y0+1)*(1-sx)+at(x0+1,y0+1)*sx)*sy)});
    v=0.5+(v-0.5)*1.9;v=v*0.75+Math.random()*0.25;const o=(y*N+x)*4;img.data[o]=img.data[o+1]=img.data[o+2]=Math.max(0,Math.min(255,Math.round(v*255)));img.data[o+3]=255}
  g.putImageData(img,0,0);const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=4;return t;
}
function addDetail(m){
  if(!m||m.userData.det)return m;m.userData.det=1;
  m.onBeforeCompile=sh=>{sh.uniforms.detailMap={value:G.detTex};sh.uniforms.uDetail=G.detU;
    sh.fragmentShader='uniform sampler2D detailMap;uniform float uDetail;\n'+sh.fragmentShader.replace('#include <map_fragment>',
      '#include <map_fragment>\n#ifdef USE_FOG\nif(uDetail>0.0){float dd=length(vFogW-cameraPosition);float df=uDetail*(1.0-smoothstep(10.0,160.0,dd));'+
      'if(df>0.0){float n=texture2D(detailMap,vFogW.xz*0.37).r*0.5+texture2D(detailMap,vFogW.xz*0.07).r*0.5;diffuseColor.rgb*=mix(1.0,0.5+n,df);}}\n#endif')};
  m.needsUpdate=true;return m;
}
function smoothPath(P){ // Catmull-Rom through every GPX point, one point about every 2 m
  const out=[];
  for(let i=0;i<P.length-1;i++){const p0=P[Math.max(0,i-1)],p1=P[i],p2=P[i+1],p3=P[Math.min(P.length-1,i+2)];const n=Math.max(1,Math.ceil(Math.hypot(p2[0]-p1[0],p2[1]-p1[1])/2));
    for(let k=0;k<n;k++){const t=k/n,t2=t*t,t3=t2*t;const f=(a,b,c,d)=>0.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t2+(-a+3*b-3*c+d)*t3);out.push([f(p0[0],p1[0],p2[0],p3[0]),f(p0[1],p1[1],p2[1],p3[1])])}}
  out.push([P[P.length-1][0],P[P.length-1][1]]);
  const cum=[0];for(let i=1;i<out.length;i++)cum.push(cum[i-1]+Math.hypot(out[i][0]-out[i-1][0],out[i][1]-out[i-1][1]));return {pts:out,cum,total:cum[cum.length-1]};
}
function sAt(x,z){ // surface height including tree canopy, matching the drawn terrain
  const C=D3.cols,R=D3.rows,cs=D3.cs;let c=x/cs-0.5,r=z/cs-0.5;if(c<0||r<0||c>C-1.001||r>R-1.001)return hAt(x,z);
  const i=r|0,j=c|0,fr=r-i,fc=c-j;return Hs(i,j)*(1-fr)*(1-fc)+Hs(i,j+1)*(1-fr)*fc+Hs(i+1,j)*fr*(1-fc)+Hs(i+1,j+1)*fr*fc;
}
function canAt(x,z){if(!V.trees||!G.CAN)return 0;const C=D3.cols,cs=D3.cs;const i=Math.round(z/cs-0.5),j=Math.round(x/cs-0.5);if(i<0||j<0||i>=D3.rows||j>=C)return 0;return G.CAN[i*C+j]}
function startWalk(){
  if(!V.loaded||!D3)return;stopFly();const st=D3.stages[V.stage];if(!st)return;const r=byId[V.stage];
  const f=smoothPath(st.pts);
  const a=r.post_list[0][0],b=r.post_list[r.post_list.length-1][0];const na=+a.slice(1),nb=+b.slice(1);const seen={};
  const posts=D3.posts.filter(p=>{const n=+p[0].slice(1);if(p[0][0]!==a[0]||n<na||n>nb||seen[p[0]])return false;return seen[p[0]]=1}).map(p=>{
    let bi=0,bd=1e18;for(let i=0;i<f.pts.length;i++){const q=f.pts[i];const dd=(q[0]-p[1])**2+(q[1]-p[2])**2;if(dd<bd){bd=dd;bi=i}}return {code:p[0],x:p[1],z:p[2],d:f.cum[bi]}}).sort((u,v)=>u.d-v.d);
  const prof=[];for(let i=0;i<=160;i++){const q=along(f,f.total*i/160);prof.push(hAt(q[0],q[1]))}
  const grid=new Map();f.pts.forEach(q=>{const k=Math.floor(q[0]/4)+','+Math.floor(q[1]/4);if(!grid.has(k))grid.set(k,[]);grid.get(k).push(q)});
  V.walk={...f,posts,prof,grid,d:0,playing:true,spd:30,hours:r.hours,gyro:false,yaw:0,pitch:0,idle:9,last:null,head:null,y:null,snap:true,lastD:0,ui:0,drag:false,scrub:false,gx:null,gz:null};
  G.controls.enabled=false;G.camera.near=0.5;G.camera.fov=58;G.camera.updateProjectionMatrix();G.detU.value=1;
  G.labelGrp.visible=false;$('#v3d').classList.add('walking');
  const w=V.walk;w.pace=walkPace(w,r.hours);w.marks=[];
  const withPoi=()=>{if(V.walk!==w)return;walkMarks(w);walkPins();drawProfile()};
  if(G.WPOI)withPoi();else fetch(L3+'walkpoi.json').then(r=>r.json()).then(j=>{G.WPOI=j.poi;withPoi()}).catch(()=>{G.WPOI=[];withPoi()});
  walkDress();$('#v3dWalkUI').hidden=false;drawProfile();walkUI();G.shadowDirty=true;sndStart();
}
function stopWalk(silent){
  const w=V.walk;if(!w)return;V.walk=null;G.detU.value=0;
  if(G.walkGrp){G.scene.remove(G.walkGrp);G.walkGrp.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material){if(o.material.map)o.material.map.dispose();o.material.dispose()}});G.walkGrp=null;G.walkPath=null;G.grass=null}
  if(G.stageGrp)G.stageGrp.children.forEach(o=>{if(o.isMesh)o.visible=V.route;else if(o.userData.post){o.userData.lift=14;o.position.y=hAt(o.userData.x,o.userData.z)*V.ex+14}});
  G.labelGrp.visible=true;$('#v3d').classList.remove('walking');$('#v3dWalkUI').hidden=true;$('#v3dFlyInfo').textContent='';const wc=$('#v3dWalkCard');wc.hidden=true;wc.dataset.h='';sndStop();
  G.camera.near=5;G.camera.fov=45;G.camera.updateProjectionMatrix();
  if(!silent){const c=G.camera.position.clone(),hd=w.head||0;G.controls.target.copy(c);G.camera.position.set(c.x-Math.sin(hd)*650,c.y+700,c.z-Math.cos(hd)*650)}
  G.controls.enabled=true;G.controls.update();G.shadowDirty=true;
}
function pathTexture(){ // packed earth with small stones; edges fade into the grass
  const W=64,H=256,c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');const img=g.createImageData(W,H);
  const nz=new Float32Array(17*65);for(let i=0;i<nz.length;i++)nz[i]=Math.random();const N=(x,y)=>{const fx=x/4,fy=y/4,x0=fx|0,y0=fy|0,tx=fx-x0,ty=fy-y0,A=(a,b)=>nz[(b%64)*17+(a%16)];return (A(x0,y0)*(1-tx)+A(x0+1,y0)*tx)*(1-ty)+(A(x0,y0+1)*(1-tx)+A(x0+1,y0+1)*tx)*ty};
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){const e=Math.min(x,W-1-x)/W;const edge=Math.min(1,e/(0.16+0.12*N(3,y)));
    const n=0.78+N(x,y)*0.22+Math.random()*0.14;const o=(y*W+x)*4;img.data[o]=Math.min(255,160*n);img.data[o+1]=Math.min(255,143*n);img.data[o+2]=Math.min(255,118*n);img.data[o+3]=Math.round(255*Math.max(0,Math.min(1,edge)))}
  g.putImageData(img,0,0);
  for(let k=0;k<34;k++){const x=10+Math.random()*(W-20),y=Math.random()*H,r=0.7+Math.random()*1.8,l=140+Math.random()*60;g.fillStyle=`rgba(${l},${l*0.97|0},${l*0.93|0},0.75)`;g.beginPath();g.ellipse(x,y,r*1.3,r,Math.random()*3,0,7);g.fill()}
  const t=new THREE.CanvasTexture(c);t.wrapS=THREE.ClampToEdgeWrapping;t.wrapT=THREE.RepeatWrapping;t.encoding=THREE.sRGBEncoding;t.anisotropy=8;return t;
}
function grassTexture(){ // a clump of fine grass blades, darker at the base; the colour comes from the aerial photo underneath
  const S=128,c=document.createElement('canvas');c.width=c.height=S;const g=c.getContext('2d');
  for(let k=0;k<95;k++){const x=S*0.5+(Math.random()-0.5)*S*0.9,h=S*(0.35+Math.random()*0.65),lean=(Math.random()-0.5)*S*0.45,w=0.8+Math.random()*1.5,l=150+Math.random()*105;
    const gr=g.createLinearGradient(0,S,0,S-h);gr.addColorStop(0,`rgb(${l*0.45|0},${l*0.5|0},${l*0.3|0})`);gr.addColorStop(1,`rgb(${l*0.95|0},${l|0},${l*0.72|0})`);
    g.strokeStyle=gr;g.lineWidth=w;g.lineCap='round';g.beginPath();g.moveTo(x,S);g.quadraticCurveTo(x+lean*0.25,S-h*0.6,x+lean,S-h);g.stroke()}
  const t=new THREE.CanvasTexture(c);t.encoding=THREE.sRGBEncoding;return t;
}
function walkDress(){ // textured path, real distance posts and near-field grass, sized for eye level
  const w=V.walk;if(!w)return;
  if(G.walkGrp){G.scene.remove(G.walkGrp);G.walkGrp.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material){if(o.material.map)o.material.map.dispose();o.material.dispose()}})}
  const grp=new THREE.Group();G.walkGrp=grp;G.scene.add(grp);const ex=V.ex;
  // path: 1.3 m wide strip draped on the ground, texture repeats every 2.6 m
  const n=w.pts.length,pos=new Float32Array(n*6),uv=new Float32Array(n*4),nor=new Float32Array(n*6),idx=[];
  for(let i=0;i<n;i++){const a=w.pts[Math.max(0,i-1)],b=w.pts[Math.min(n-1,i+1)];let dx=b[0]-a[0],dz=b[1]-a[1];const L=Math.hypot(dx,dz)||1;const nx=-dz/L*0.65,nz=dx/L*0.65;const x=w.pts[i][0],z=w.pts[i][1];
    pos.set([x+nx-G.cx,sAt(x+nx,z+nz)*ex+0.12,z+nz-G.cz,x-nx-G.cx,sAt(x-nx,z-nz)*ex+0.12,z-nz-G.cz],i*6);uv.set([0,w.cum[i]/2.6,1,w.cum[i]/2.6],i*4);nor.set([0,1,0,0,1,0],i*6);
    if(i<n-1){const q=i*2;idx.push(q,q+1,q+2,q+1,q+3,q+2)}}
  const pg=new THREE.BufferGeometry();pg.setAttribute('position',new THREE.BufferAttribute(pos,3));pg.setAttribute('uv',new THREE.BufferAttribute(uv,2));pg.setAttribute('normal',new THREE.BufferAttribute(nor,3));pg.setIndex(idx);
  const path=new THREE.Mesh(pg,new THREE.MeshLambertMaterial({map:pathTexture(),side:THREE.DoubleSide,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-4,polygonOffsetUnits:-4}));
  path.receiveShadow=true;path.renderOrder=2;path.visible=V.route;grp.add(path);G.walkPath=path;
  // distance posts (about 1.1 m tall)
  const bg=new THREE.BoxGeometry(0.22,1.1,0.22);bg.translate(0,0.55,0);const bm=new THREE.MeshLambertMaterial({color:0x6d7a73});
  w.posts.forEach(p=>{const m=new THREE.Mesh(bg,bm);m.position.set(p.x-G.cx,hAt(p.x,p.z)*ex,p.z-G.cz);m.castShadow=true;grp.add(m)});
  // grass clumps: two crossed quads each, drawn only within ~60 m of the walker
  const q=new THREE.PlaneGeometry(1,1,1,1);q.translate(0,0.5,0);const q2=q.clone();q2.rotateY(Math.PI/2);
  const gg=new THREE.BufferGeometry();const merge=(A,B,attr,k)=>{const a=A.getAttribute(attr).array,b=B.getAttribute(attr).array;const o=new Float32Array(a.length+b.length);o.set(a);o.set(b,a.length);gg.setAttribute(attr,new THREE.BufferAttribute(o,k))};
  merge(q,q2,'position',3);merge(q,q2,'uv',2);const nn=new Float32Array(24);for(let i=0;i<8;i++)nn.set([0,1,0],i*3);gg.setAttribute('normal',new THREE.BufferAttribute(nn,3));
  const ia=q.index.array;gg.setIndex([...ia,...Array.from(ia).map(v=>v+4)]);
  const max=MOBILE?4200:13000;const gm=new THREE.MeshLambertMaterial({map:grassTexture(),alphaTest:0.45,side:THREE.DoubleSide});
  const grass=new THREE.InstancedMesh(gg,gm,max);grass.instanceColor=new THREE.InstancedBufferAttribute(new Float32Array(max*3),3);grass.frustumCulled=false;grass.receiveShadow=true;grass.count=0;grp.add(grass);G.grass=grass;w.gx=null;
  if(G.stageGrp)G.stageGrp.children.forEach(o=>{if(o.isMesh)o.visible=false;else if(o.userData.post){o.userData.lift=1.9;o.position.y=hAt(o.userData.x,o.userData.z)*ex+1.9}});
  walkPins();
  const OV=W3.areas&&W3.areas[AREA]&&W3.areas[AREA].overview,g0=V.gen;
  if(!G.ovPix&&OV)OV.then(b=>b&&createImageBitmap(b)).then(bmp=>{if(!bmp||g0!==V.gen)return;const c=document.createElement('canvas');c.width=bmp.width;c.height=bmp.height;const x=c.getContext('2d',{willReadFrequently:true});x.drawImage(bmp,0,0);G.ovPix={w:bmp.width,h:bmp.height,d:x.getImageData(0,0,bmp.width,bmp.height).data};if(V.walk)V.walk.gx=null}).catch(()=>{});
}
function nearPath(w,x,z,r){const cx=Math.floor(x/4),cz=Math.floor(z/4);for(let a=-1;a<=1;a++)for(let b=-1;b<=1;b++){const l=w.grid.get((cx+a)+','+(cz+b));if(l)for(const q of l)if((q[0]-x)**2+(q[1]-z)**2<r*r)return true}return false}
function walkGrass(){ // re-scatter grass on a fixed world grid around the walker (no swimming), coloured from the photo
  const w=V.walk,gr=G.grass;if(!w||!gr||!G.ovPix)return;const c=G.camera.position,X=c.x+G.cx,Z=c.z+G.cz;
  if(w.gx!=null&&Math.hypot(X-w.gx,Z-w.gz)<5)return;w.gx=X;w.gz=Z;
  const ex=V.ex,P=G.ovPix,C=D3.cols,RR=D3.rows,cs=D3.cs;const m=G._gm||(G._gm=new THREE.Matrix4()),qq=G._gq||(G._gq=new THREE.Quaternion()),sc=G._gs||(G._gs=new THREE.Vector3()),ps=G._gp||(G._gp=new THREE.Vector3()),ax=new THREE.Vector3(0,1,0);
  const col=gr.instanceColor.array;let k=0;const max=gr.instanceMatrix.count;
  const tiers=MOBILE?[[0,18,0.72,1],[18,40,1.6,2]]:[[0,26,0.58,1],[26,62,1.35,2]];const Rmax=tiers[1][1];
  for(const [r0,r1,cell,salt] of tiers){
  const i0=Math.floor((X-r1)/cell),i1=Math.floor((X+r1)/cell),j0=Math.floor((Z-r1)/cell),j1=Math.floor((Z+r1)/cell);
  for(let i=i0;i<=i1&&k<max;i++)for(let j=j0;j<=j1&&k<max;j++){
    let h=Math.imul(i,374761393)^Math.imul(j,668265263)^Math.imul(salt,1442695041);h=Math.imul(h^(h>>>13),1274126177);h^=h>>>16;const r1_=((h>>>0)%10007)/10007,r2=((h>>>5)%9973)/9973,r3=((h>>>11)%8191)/8191;
    const x=(i+r1_)*cell,z=(j+r2)*cell;const d=Math.hypot(x-X,z-Z);if(d>r1||d<r0)continue;
    const gh=hAt(x,z);if(gh<2)continue;const can=canAt(x,z);if(can>2.5)continue;
    if(nearPath(w,x,z,0.7+r3*0.35))continue;
    const px=Math.max(0,Math.min(P.w-1,Math.round((x/cs-0.5)/(C-1)*(P.w-1)))),py=Math.max(0,Math.min(P.h-1,Math.round((z/cs-0.5)/(RR-1)*(P.h-1))));const o=(py*P.w+px)*4;
    const rr=P.d[o],gg=P.d[o+1],bb=P.d[o+2];const mx=Math.max(rr,gg,bb),mn=Math.min(rr,gg,bb);if(mx-mn<14&&mx>120)continue; // bare rock, paving, roofs
    const fade=1-Math.max(0,(d-Rmax*0.72)/(Rmax*0.28));const hgt=(0.3+r3*0.42+Math.min(can,1.5)*0.3)*fade,wid=(0.85+r1_*0.55)*(0.8+0.2*fade)*(salt===2?1.25:1);
    ps.set(x-G.cx,sAt(x,z)*ex-0.05,z-G.cz);qq.setFromAxisAngle(ax,r2*6.283);sc.set(wid,hgt,wid);m.compose(ps,qq,sc);gr.setMatrixAt(k,m);
    const v=0.8+r1_*0.35,lin=t=>Math.pow(t/255,2.2)*1.45*v;col[k*3]=lin(rr);col[k*3+1]=lin(gg)*1.06;col[k*3+2]=lin(bb)*0.88;k++}}
  gr.count=k;gr.instanceMatrix.needsUpdate=true;gr.instanceColor.needsUpdate=true;
}
function walkPlay(){const w=V.walk;if(!w)return;if(w.d>=w.total-0.5){w.d=0;w.snap=true;w.playing=true}else w.playing=!w.playing;walkUI()}
function walkUI(){
  const w=V.walk;if(!w)return;const end=w.d>=w.total-0.5;
  $('#v3dWalkPlay').textContent=end?'↺ '+T('Start again','重新開始'):w.playing?'❚❚ '+T('Pause','暫停'):'▶ '+T('Walk','步行');
  $('#v3dWalkSpd').textContent=w.spd===1?T('Real pace','真實步速'):T(`${w.spd}× faster`,`${w.spd}倍速`);
  $('#v3dWalkSpd').title=T('Real pace is the AFCD walking time for this stage','真實步速按漁護署建議步行時間計算');
  $('#v3dWalkPos').setAttribute('aria-label',T('Position along the stage','在路段上的位置'));
  const gb=$('#v3dWalkGyro');gb.hidden=!(('DeviceOrientationEvent' in window)&&matchMedia('(pointer:coarse)').matches);gb.textContent='📱 '+(w.gyro?T('Motion: on','動作：開'):T('Motion: off','動作：關'));gb.setAttribute('aria-pressed',w.gyro);
  const sb=$('#v3dWalkSnd');sb.textContent=(sndPref()?'🔊 ':'🔇 ')+(sndPref()?T('Sound: on','聲音：開'):T('Sound: off','聲音：關'));sb.setAttribute('aria-pressed',sndPref());
}
function drawProfile(){
  const w=V.walk,svg=$('#v3dWalkProf');const mn=Math.min(...w.prof),mx=Math.max(...w.prof),rg=Math.max(50,mx-mn);
  const pts=w.prof.map((h,i)=>`${(i/160*300).toFixed(1)},${(34-(h-mn)/rg*30).toFixed(1)}`).join(' ');
  const ticks=w.posts.map(p=>`<line x1="${(p.d/w.total*300).toFixed(1)}" x2="${(p.d/w.total*300).toFixed(1)}" y1="34" y2="38" stroke="#fff" stroke-opacity=".55"/>`).join('');
  const X=d=>(d/w.total*300).toFixed(1);const steep=(w.marks||[]).filter(m=>m.ty==='steep').map(m=>`<rect x="${X(m.d)}" width="${Math.max(1,m.len/w.total*300).toFixed(1)}" y="35" height="3" fill="#ff6b4a"/>`).join('');
  const icons=(w.marks||[]).filter(m=>['summit','wc','water','shelter','exit','bus','cable'].includes(m.ty)).map(m=>`<text x="${X(m.d)}" y="9" font-size="8" text-anchor="middle">${MK[m.ty][0]}</text>`).join('');
  svg.innerHTML=`<polygon points="0,38 ${pts} 300,38" fill="rgba(255,255,255,.18)"/>${steep}${icons}<polyline points="${pts}" fill="none" stroke="#ffb36b" stroke-width="1.6" vector-effect="non-scaling-stroke"/>${ticks}<line id="v3dWalkMark" x1="0" x2="0" y1="0" y2="38" stroke="#fff" stroke-width="2" vector-effect="non-scaling-stroke"/>`;
  $('#v3dWalkLo').textContent=Math.round(mn)+' m';$('#v3dWalkHi').textContent=Math.round(mx)+' m';
}
function stepWalk(t){
  const w=V.walk;const dt=w.last==null?0:Math.min(0.1,(t-w.last)/1000);w.last=t;
  if(w.playing&&!w.scrub&&!w.drag){w.d=Math.min(w.total,w.d+paceAt(w,w.d)*w.spd*dt);if(w.d>=w.total){w.playing=false;walkUI()}}
  if(Math.abs(w.d-w.lastD)>40)w.snap=true;w.lastD=w.d;
  const p=along(w,w.d),a=along(w,w.d+10),b=along(w,w.d-10);
  const hd=Math.atan2(a[0]-b[0],a[1]-b[1]);
  if(w.head==null||w.snap)w.head=hd;else{let dh=hd-w.head;dh=Math.atan2(Math.sin(dh),Math.cos(dh));w.head+=dh*(1-Math.exp(-dt*(2.2+w.spd/12)))}
  const g=Math.max(hAt(p[0],p[1]),sAt(p[0],p[1]))*V.ex;const eye=g+1.7;
  if(w.y==null||w.snap)w.y=eye;else w.y+=(eye-w.y)*(1-Math.exp(-dt*9));w.y=Math.max(w.y,g+1.0);w.snap=false;
  const q=along(w,w.d+30);const slope=w.gyro?0:(Math.atan2(hAt(q[0],q[1])*V.ex-hAt(p[0],p[1])*V.ex,30)*0.5)*Math.max(0,Math.cos(w.yaw))-0.06;
  if(!w.drag&&!w.gyro){w.idle+=dt;if(w.idle>2.5&&w.playing){const k=Math.exp(-dt*1.1);w.yaw*=k;w.pitch*=k}}
  const yaw=w.head+w.yaw,pit=Math.max(-1.35,Math.min(1.35,slope+w.pitch));
  const cam=G.camera;cam.position.set(p[0]-G.cx,w.y,p[1]-G.cz);
  const L=G._wl||(G._wl=new THREE.Vector3());L.set(cam.position.x+Math.sin(yaw)*Math.cos(pit),cam.position.y+Math.sin(pit),cam.position.z+Math.cos(yaw)*Math.cos(pit));cam.lookAt(L);
  const la=along(w,w.d+220);G.lookAt=(G.lookAt||new THREE.Vector3()).set(la[0]-G.cx,hAt(la[0],la[1])*V.ex,la[1]-G.cz);
  walkGrass();sndStep(w,t);
  if(t-w.ui>150){w.ui=t;
    const h=Math.round(hAt(p[0],p[1]));const u=along(w,w.d+25),v=along(w,w.d-25);const span=Math.min(w.total,w.d+25)-Math.max(0,w.d-25);const gr=Math.round((hAt(u[0],u[1])-hAt(v[0],v[1]))/Math.max(1,span)*100);
    const np=w.posts.find(o=>o.d>w.d+3);const tl=timeLeft(w,w.d),lt=fmtMin(tl),ltz=fmtMin(tl,1);const kmh=(paceAt(w,w.d)*3.6).toFixed(1);
    const grTxt=gr>3?T(`uphill ${gr}%`,`上坡 ${gr}%`):gr<-3?T(`downhill ${-gr}%`,`下坡 ${-gr}%`):T('level','平路');
    $('#v3dFlyInfo').textContent=`${(w.d/1000).toFixed(2)} / ${(w.total/1000).toFixed(1)} km · ${h} m · ${grTxt}`+T(` · pace here ${kmh} km/h`,` · 此處步速 ${kmh} km/h`)+(np?T(` · post ${np.code} in ${Math.round(np.d-w.d)} m`,` · 距標距柱 ${np.code} ${Math.round(np.d-w.d)} 米`):'')+T(` · about ${lt} left on foot`,` · 步行尚餘約${ltz}`);walkCard(w);
    if(!w.scrub)$('#v3dWalkPos').value=Math.round(w.d/w.total*1000);
    const mk=document.getElementById('v3dWalkMark');if(mk){const x=(w.d/w.total*300).toFixed(1);mk.setAttribute('x1',x);mk.setAttribute('x2',x)}
    const pb=$('#v3dWalkPlay');const want=w.d>=w.total-0.5?'end':w.playing?'p':'s';if(pb.dataset.s!==want){pb.dataset.s=want;walkUI()}}
}
function walkPointer(el){ // drag to look around; the view slowly turns back to the path while walking
  let id=null,lx=0,ly=0;
  el.addEventListener('pointerdown',e=>{if(!V.walk)return;id=e.pointerId;lx=e.clientX;ly=e.clientY;V.walk.drag=true;V.walk.idle=0;try{el.setPointerCapture(id)}catch(_){}});
  el.addEventListener('pointermove',e=>{const w=V.walk;if(!w||e.pointerId!==id)return;const k=G.camera.fov*Math.PI/180/(el.clientHeight||600);
    if(w.gyro){if(w.gyroRef!=null)w.gyroRef-=(e.clientX-lx)*k}else{w.yaw+=(e.clientX-lx)*k;w.pitch=Math.max(-1.3,Math.min(1.3,w.pitch+(e.clientY-ly)*k))}lx=e.clientX;ly=e.clientY;w.idle=0});
  const up=e=>{if(e.pointerId!==id)return;id=null;if(V.walk){V.walk.drag=false;V.walk.idle=0}};el.addEventListener('pointerup',up);el.addEventListener('pointercancel',up);
  el.addEventListener('wheel',e=>{const w=V.walk;if(!w)return;e.preventDefault();w.d=Math.max(0,Math.min(w.total,w.d-e.deltaY*0.4))},{passive:false});
}

/* ----- walk: pace that follows the slope (Tobler), trail markers, phone motion, sound ----- */
function walkPace(f,hours){ // Tobler's hiking function, scaled so the whole stage takes the official AFCD time
  const N=Math.max(2,Math.ceil(f.total/10)),seg=f.total/N,h=[];for(let i=0;i<=N;i++){const q=along(f,i*seg);h.push(hAt(q[0],q[1]))}
  const tt=[0];for(let i=1;i<=N;i++){const a=Math.max(0,i-4),b=Math.min(N,i+3);const s=(h[b]-h[a])/((b-a)*seg);const v=6*Math.exp(-3.5*Math.abs(s+0.05))/3.6;tt.push(tt[i-1]+seg/v)}
  return {N,seg,tt,k:hours*3600/tt[N]};
}
function paceAt(w,d){const P=w.pace;const i=Math.max(1,Math.min(P.N,Math.ceil(d/P.seg)));return P.seg/((P.tt[i]-P.tt[i-1])*P.k)} // m/s at real pace
function timeLeft(w,d){const P=w.pace;const x=Math.max(0,Math.min(P.N,d/P.seg)),i=Math.floor(x);const t=i>=P.N?P.tt[P.N]:P.tt[i]+(P.tt[i+1]-P.tt[i])*(x-i);return (P.tt[P.N]-t)*P.k}
const fmtMin=(s,zh)=>{const m=Math.max(0,Math.round(s/60));return m>=60?(zh?`${Math.floor(m/60)}小時${m%60}分鐘`:`${Math.floor(m/60)} h ${m%60} min`):(zh?`${m}分鐘`:`${m} min`)};
const MK={summit:['🏔','Summit','山頂'],peak:['⛰','Peak','山峰'],view:['📷','Viewpoint','觀景點'],shelter:['🛖','Shelter','涼亭'],wc:['🚻','Toilets','廁所'],water:['🚰','Drinking water','飲用水'],
  camp:['⛺','Campsite','營地'],bus:['🚌','Bus stop','巴士站'],cable:['🚡','Cable car','纜車站'],exit:['↩','Exit route','退出路線'],steep:['⚠','Steep section','陡峭路段']};
const TRAILNAME={lantau:['Lantau Trail','鳳凰徑'],maclehose:['MacLehose Trail','麥理浩徑'],wilson:['Wilson Trail','衞奕信徑'],hktrail:['Hong Kong Trail','港島徑']};
function walkMarks(w){
  const out=[];const near=(x,z)=>{let bi=0,bd=1e18;for(let i=0;i<w.pts.length;i+=2){const q=w.pts[i];const dd=(q[0]-x)**2+(q[1]-z)**2;if(dd<bd){bd=dd;bi=i}}return [w.cum[bi],Math.sqrt(bd)]};
  (G.WPOI||[]).forEach(([ty,x,z,en,zh,ele])=>{const [d,off]=near(x,z);const lim=ty==='peak'?90:ty==='bus'?70:ty==='exit'?30:55;if(off>lim)return;if(ty==='bus'&&d>150&&d<w.total-150)return;out.push({ty,x,z,en,zh,ele,d})});
  let dm=0,hm=-1;for(let d=0;d<=w.total;d+=10){const q=along(w,d),h=hAt(q[0],q[1]);if(h>hm){hm=h;dm=d}}
  if(dm>100&&dm<w.total-100){const pk=out.filter(m=>m.ty==='peak'&&Math.abs(m.d-dm)<250).sort((a,b)=>(b.ele||0)-(a.ele||0))[0];const q=along(w,dm);
    out.push({ty:'summit',x:q[0],z:q[1],en:pk&&pk.en||'',zh:pk&&pk.zh||'',ele:pk&&pk.ele||Math.round(hm),d:dm})}
  // steep sections: at least 150 m where the 50 m average gradient is 25% or more
  const g=[];for(let d=0;d<=w.total;d+=10){const a=along(w,d-25),b=along(w,d+25);g.push((hAt(b[0],b[1])-hAt(a[0],a[1]))/Math.max(1,Math.min(w.total,d+25)-Math.max(0,d-25)))}
  let s=-1,sg=0;const flush=i=>{if(s>=0){const len=(i-s)*10;if(len>=150){let sum=0;for(let k=s;k<i;k++)sum+=g[k];const q=along(w,s*10);out.push({ty:'steep',x:q[0],z:q[1],d:s*10,len,avg:sum/(i-s)})}}s=-1};
  for(let i=0;i<g.length;i++){const st=Math.abs(g[i])>=0.25?Math.sign(g[i]):0;if(st!==0&&s>=0&&st===sg)continue;flush(i);if(st!==0){s=i;sg=st}}flush(g.length);
  out.sort((a,b)=>a.d-b.d);const res=[];
  out.forEach(m=>{if(m.ty==='peak'&&out.some(o=>o.ty==='summit'&&Math.abs(o.d-m.d)<250))return;if(res.some(o=>o.ty===m.ty&&o.ty!=='steep'&&Math.abs(o.d-m.d)<60))return;res.push(m)});
  ['wc','water'].forEach(ty=>{const l=res.filter(m=>m.ty===ty);l.forEach((m,i)=>{m.next=i+1<l.length?l[i+1].d-m.d:null})});
  w.marks=res;
}
function markText(m,w){
  const [ic,en,zh]=MK[m.ty];let a=m.en||en,b=m.zh||zh,x='',y='';const km=v=>(v/1000).toFixed(1);
  if(m.ty==='summit'){a=(m.en||'Summit')+` · ${Math.round(m.ele)} m`;b=(m.zh||'山頂')+` · ${Math.round(m.ele)}米`;x='Highest point of this stage. Often windy, and it can be in cloud.';y='本段最高點，常有大風，或會被雲霧籠罩。'}
  else if(m.ty==='peak'&&m.ele){a+=` · ${Math.round(m.ele)} m`;b+=` · ${Math.round(m.ele)}米`}
  else if(m.ty==='steep'){const up=m.avg>0,p=Math.round(Math.abs(m.avg)*100);a=`Steep ${up?'climb':'descent'} · ${Math.round(m.len)} m at about ${p}%`;b=`陡峭${up?'上坡':'下坡'} · ${Math.round(m.len)}米，約${p}%`;
    x=up?'Mostly stone steps. Go slowly and rest often.':'Steep and rocky going down. Watch your footing.';y=up?'多為石級，慢行並多休息。':'下坡陡峭多石，小心腳步。'}
  else if(m.ty==='wc'||m.ty==='water'){const rest=w.total-m.d;if(m.next){x=`Next ${en.toLowerCase()} in ${km(m.next)} km.`;y=`下一個${zh}在${km(m.next)}公里後。`}else if(rest>500){x=`Last ${en.toLowerCase()} for the next ${km(rest)} km.`;y=`之後${km(rest)}公里沒有${zh}。`}}
  else if(m.ty==='exit'){a='Exit route';b='退出路線';x=m.en;y=m.zh}
  else if(m.ty==='bus'){a=(m.en||'Bus stop')+(m.en?' (bus stop)':'');b=(m.zh||'巴士站')+(m.zh?'（巴士站）':'')}
  else if(m.ty==='shelter'){x='Covered rest spot.';y='有蓋休息處。'}
  return {ic,title:T(a,b),detail:T(x,y)};
}
function walkPins(){ // small 3D signs for the markers (not for steep sections)
  const w=V.walk;if(!w||!w.marks||!G.walkGrp)return;
  G.walkGrp.children.filter(o=>o.userData.pin).forEach(o=>{G.walkGrp.remove(o);o.material.map.dispose();o.material.dispose()});
  w.marks.forEach(m=>{if(m.ty==='steep')return;const t=markText(m,w);const s=makeLabel(t.ic+' '+t.title,'place');Object.assign(s.userData,{x:m.x,z:m.z,lift:3.2,pin:1});
    s.position.set(m.x-G.cx,hAt(m.x,m.z)*V.ex+3.2,m.z-G.cz);G.walkGrp.add(s)});
}
function walkCard(w){ // what is here or just ahead
  const el=$('#v3dWalkCard');let html='';
  const PRI=['summit','exit','wc','water','shelter','peak','bus','cable','camp','view'];const here=(w.marks||[]).filter(m=>m.ty!=='steep'&&m.d>=w.d-25&&m.d<=w.d+15).sort((a,b)=>PRI.indexOf(a.ty)-PRI.indexOf(b.ty))[0];
  const post=w.posts.find(p=>w.d>=p.d-8&&w.d<=p.d+50);
  const inSteep=(w.marks||[]).find(m=>m.ty==='steep'&&w.d>=m.d&&w.d<=m.d+m.len);
  const next=(w.marks||[]).find(m=>m.d>w.d+15&&m.d<w.d+250);
  if(here){const t=markText(here,w);html=`<b>${t.ic} ${esc(t.title)}</b>${t.detail?`<span>${esc(t.detail)}</span>`:''}`}
  else if(post){const tn=TRAILNAME[byId[V.stage].trail]||['this trail','此路線'];html=`<b>📍 ${T('Distance post','標距柱')} ${post.code}</b><span>${esc(T(`Emergency? Call 999 and say: "${tn[0]}, distance post ${post.code}".`,`如遇緊急情況，致電999並說明：「${tn[1]}標距柱${post.code}」。`))}</span>`}
  else if(inSteep){const t=markText(inSteep,w);html=`<b>${t.ic} ${esc(t.title)}</b><span>${esc(T(`${Math.round(inSteep.d+inSteep.len-w.d)} m to go on this section.`,`此路段尚餘${Math.round(inSteep.d+inSteep.len-w.d)}米。`))} ${esc(t.detail)}</span>`}
  else if(next){const t=markText(next,w);html=`<b><em>${T('In','前方')} ${Math.round(next.d-w.d)} ${T('m','米')}</em> ${t.ic} ${esc(t.title)}</b>`}
  if(el.dataset.h!==html){el.dataset.h=html;el.innerHTML=html;el.hidden=!html}
  const fi=$('#v3dFlyInfo');if(fi.offsetHeight)el.style.top=(fi.offsetTop+fi.offsetHeight+8)+'px';
}
/* phone motion: look around by turning the phone (angles from the device, as in three.js DeviceOrientationControls) */
function gyroDir(e){
  const d=Math.PI/180,orient=(((screen.orientation&&screen.orientation.angle)||window.orientation||0))*d;
  const eu=G._ge||(G._ge=new THREE.Euler()),q=G._gq2||(G._gq2=new THREE.Quaternion()),q1=G._gq1||(G._gq1=new THREE.Quaternion(-Math.sqrt(0.5),0,0,Math.sqrt(0.5))),q0=G._gq0||(G._gq0=new THREE.Quaternion()),zee=G._gz||(G._gz=new THREE.Vector3(0,0,1)),v=G._gv||(G._gv=new THREE.Vector3());
  eu.set((e.beta||0)*d,(e.alpha||0)*d,-(e.gamma||0)*d,'YXZ');q.setFromEuler(eu);q.multiply(q1);q.multiply(q0.setFromAxisAngle(zee,-orient));
  v.set(0,0,-1).applyQuaternion(q);return {yaw:Math.atan2(v.x,v.z),pitch:Math.asin(Math.max(-1,Math.min(1,v.y)))};
}
window.addEventListener('deviceorientation',e=>{const w=V.walk;if(!w||!w.gyro||e.alpha==null)return;const g=gyroDir(e);w.gyroSeen=true;
  if(w.gyroRef==null)w.gyroRef=g.yaw-w.yaw;const y=g.yaw-w.gyroRef;w.yaw=Math.atan2(Math.sin(y),Math.cos(y));w.pitch=g.pitch;w.idle=0});
async function toggleGyro(){
  const w=V.walk;if(!w)return;if(w.gyro){w.gyro=false;w.pitch=0;walkUI();return}
  try{if(typeof DeviceOrientationEvent!=='undefined'&&typeof DeviceOrientationEvent.requestPermission==='function'){const r=await DeviceOrientationEvent.requestPermission();if(r!=='granted')return}}catch(err){return}
  w.gyro=true;w.gyroRef=null;w.gyroSeen=false;walkUI();
  setTimeout(()=>{const v=V.walk;if(v&&v.gyro&&!v.gyroSeen){v.gyro=false;walkUI();const c=$('#v3dWalkCard');c.hidden=false;c.dataset.h='';c.innerHTML=`<b>📱 ${T('No motion sensor found','找不到動作感應器')}</b><span>${T('Drag the view to look around instead.','請改用拖動畫面環顧四周。')}</span>`}},1800);
}
/* sound: wind (stronger high up and in the open), cicadas and birds (in trees), footsteps */
const SND={ctx:null,on:null,buf:{},meta:{wind:20,forest:20,steps:[[0.25,0.42],[0.87,0.42],[1.49,0.42],[2.11,0.42],[2.73,0.42],[3.35,0.42],[3.97,0.42],[4.59,0.42],[5.21,0.42],[5.83,0.42]],stepsDur:6.55},nextStep:0,lastStep:-1};
function sndPref(){if(SND.on==null){try{SND.on=localStorage.getItem('tp_walk_sound')!=='off'}catch(e){SND.on=true}}return SND.on}
function sndStart(){ // called from a click, so browsers allow audio
  if(!sndPref())return;try{if(!SND.ctx){const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;SND.ctx=new AC();SND.master=SND.ctx.createGain();SND.master.gain.value=0.9;SND.master.connect(SND.ctx.destination)}
    if(SND.ctx.state==='suspended')SND.ctx.resume();}catch(e){return}
  const c=SND.ctx;const load=n=>SND.buf[n]?Promise.resolve(SND.buf[n]):fetch(SND_DIR+'snd_'+n+'.mp3').then(r=>r.arrayBuffer()).then(a=>new Promise((ok,no)=>c.decodeAudioData(a,ok,no))).then(b=>SND.buf[n]=b);
  ['wind','forest'].forEach(n=>{if(SND[n])return;SND[n]={gain:c.createGain()};SND[n].gain.gain.value=0;SND[n].gain.connect(SND.master);
    load(n).then(b=>{const s=c.createBufferSource();s.buffer=b;const off=Math.max(0,Math.min(0.08,b.duration-(SND.meta[n]+0.5)));s.loop=true;s.loopStart=off;s.loopEnd=off+SND.meta[n];s.connect(SND[n].gain);s.start(0,off+Math.random()*SND.meta[n]*0.9);SND[n].src=s}).catch(()=>{})});
  load('steps').catch(()=>{});
}
function sndStop(){['wind','forest'].forEach(n=>{if(SND[n]){try{SND[n].src&&SND[n].src.stop()}catch(e){}SND[n].gain.disconnect();SND[n]=null}})}
function toggleSound(){SND.on=!sndPref();try{localStorage.setItem('tp_walk_sound',SND.on?'on':'off')}catch(e){}if(SND.on)sndStart();else sndStop();walkUI()}
function sndStep(w,t){ // mix follows height, open ground vs trees, and live wind; footsteps follow the walking pace
  if(!SND.ctx||!sndPref()||!SND.wind)return;const c=SND.ctx,now=c.currentTime,p=along(w,w.d);
  const h=hAt(p[0],p[1]);let can=0,n=0;for(let a=-2;a<=2;a++)for(let b=-2;b<=2;b++){can+=canAt(p[0]+a*8,p[1]+b*8);n++}can/=n;
  const ws=(()=>{try{const v=COND.cloud&&COND.cloud.wind_ngongping;const s=v&&parseFloat(v[1]);return isFinite(s)?Math.max(0.35,Math.min(1.3,s/22)):0.7}catch(e){return 0.7}})();
  const open=Math.max(0,1-can/4);const wind=Math.min(1,(0.2+0.8*Math.max(0,Math.min(1,(h-150)/650)))*(0.35+0.65*open)*ws*1.2);
  const mon=hkNow().getMonth(),summer=mon>=3&&mon<=9,sunUp=V.sunMin>6*60+15&&V.sunMin<18*60+30;const forest=Math.min(1,Math.max(0,(can-0.8)/3))*(summer?1:0.35)*(sunUp?1:0.3)*(h<700?1:0.5);
  SND.wind.gain.gain.setTargetAtTime(wind*0.9,now,0.6);SND.forest.gain.gain.setTargetAtTime(forest*0.55,now,0.8);
  const moving=w.playing&&!w.scrub&&w.d<w.total-0.5;const b=SND.buf.steps;
  if(moving&&b){const rate=w.spd===1?Math.max(0.8,Math.min(2,paceAt(w,w.d)/0.62)):1.8;
    if(now>=SND.nextStep){let k;do{k=Math.floor(Math.random()*SND.meta.steps.length)}while(k===SND.lastStep&&SND.meta.steps.length>1);SND.lastStep=k;
      const [st,du]=SND.meta.steps[k];const off=Math.max(0,Math.min(0.08,b.duration-SND.meta.stepsDur));const s=c.createBufferSource(),g=c.createGain();s.buffer=b;s.playbackRate.value=0.92+Math.random()*0.16;
      g.gain.value=0.45+Math.random()*0.2;s.connect(g);g.connect(SND.master);s.start(now,st+off,du);SND.nextStep=Math.max(now,SND.nextStep)+1/rate*(0.93+Math.random()*0.14)}}
  else SND.nextStep=now+0.2;
}
