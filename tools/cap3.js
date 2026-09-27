const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium',args:['--proxy-server='+(process.env.HTTPS_PROXY||''),'--proxy-bypass-list=localhost;127.0.0.1','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:1300,height:850},deviceScaleFactor:1});p.setDefaultTimeout(150000);
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('http://127.0.0.1:8765/cap.html');await p.waitForTimeout(2000);
 await p.click('#lantau3d');await p.waitForFunction(()=>window.__v3dBridge,null,{timeout:180000});
 await p.addStyleTag({content:'.v3dCtl,.v3dAttr,.v3dGrade,.v3dStatus,.v3dFlyInfo{display:none!important}'});
 const box=await p.evaluate(()=>{const r=document.querySelector('#v3dCanvas').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}});console.log(JSON.stringify(box));
 await p.mouse.move(820,520);for(let i=0;i<2;i++){await p.mouse.wheel(0,-300);await p.waitForTimeout(400)}
 await p.evaluate(()=>{const G=__G();G.labelGrp.visible=false;if(G.cloudGrp)G.cloudGrp.visible=false;G.stageGrp.children.forEach(o=>{if(o.isMesh)o.visible=false;else o.material.opacity=0});G.labelGrp.children.forEach(o=>o.material.opacity=0)});
 await p.waitForTimeout(15000);
 const w=Math.floor(box.h*1.5),clip={x:Math.floor((box.w-w)/2),y:Math.ceil(box.y),width:w,height:Math.floor(box.h)};
 await p.screenshot({path:'ai/a_clean.png',clip});
 await p.evaluate(()=>{const G=__G();G.stageGrp.children.forEach(o=>{if(o.isMesh)o.visible=true})});await p.waitForTimeout(1000);
 await p.screenshot({path:'ai/b_route.png',clip});
 await p.evaluate(()=>{const G=__G();G.stageGrp.children.forEach(o=>{o.visible=true;if(o.material)o.material.opacity=o.isSprite?1:o.material.opacity});G.labelGrp.visible=true;G.labelGrp.children.forEach(o=>o.material.opacity=1)});await p.waitForTimeout(1000);
 await p.screenshot({path:'ai/c_labels.png',clip});
 console.log(JSON.stringify(clip));await b.close();})();
