const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:1200,height:800}});p.setDefaultTimeout(240000);
 await p.goto('http://127.0.0.1:8765/cap.html');await p.waitForTimeout(1500);await p.click('#lantau3d');await p.waitForFunction(()=>window.__v3dFull,null,{timeout:240000});
 await p.evaluate(()=>{const G=__G();if(G.cloudGrp)G.cloudGrp.visible=false;document.querySelector('.v3dCtl').style.display='none'});
 await p.evaluate(()=>{__X.startWalk();const c=__G().camera;c.fov=60;c.updateProjectionMatrix();document.querySelector('#v3dWalkUI').style.display='none';document.querySelector('#v3dWalkCard').style.display='none'});
 for(const [d,n] of [[2470,'t1'],[2710,'t2']]){await p.evaluate(d=>{const w=__V.walk;w.playing=false;w.d=d;w.yaw=0;w.drag=true},d);await p.waitForTimeout(7000);await p.screenshot({path:'walk/'+n+'.png'})}
 await b.close()})();
