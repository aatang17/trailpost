const { chromium } = require('playwright');
const VW=+process.argv[2]||1200,VH=+process.argv[3]||800,TAG=process.argv[4]||'d';
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:VW,height:VH},deviceScaleFactor:1});p.setDefaultTimeout(240000);
 p.on('pageerror',e=>console.log('ERR',e.message));p.on('console',m=>{if(m.type()==='error'||m.type()==='warning')console.log('CONSOLE',m.type(),m.text().slice(0,300))});
 await p.goto('http://127.0.0.1:8765/cap.html');await p.waitForTimeout(1500);
 await p.click('#lantau3d');await p.waitForFunction(()=>window.__v3dBridge,null,{timeout:240000});
 await p.evaluate(()=>{const G=__G();if(G.cloudGrp)G.cloudGrp.visible=false}); // test the ground itself; clouds follow live data
 await p.click('#v3dWalk');await p.waitForTimeout(5000);
 await p.screenshot({path:`walk/${TAG}0.png`});
 const shots=[[600,0,0,'1'],[1500,0,-0.1,'2'],[2750,0,0,'3'],[2750,2.8,0,'4'],[3500,0,-0.05,'5']];
 for(const [d,yaw,pitch,n] of shots){
   await p.evaluate(([d,yaw,pitch])=>{const w=__V.walk;w.playing=false;w.d=d;w.yaw=yaw;w.pitch=pitch;w.idle=0;w.drag=true},[d,yaw,pitch]);
   await p.waitForTimeout(8000);
   await p.screenshot({path:`walk/${TAG}${n}.png`});
   console.log(n, await p.evaluate(()=>document.querySelector('#v3dFlyInfo').textContent+' grass='+__G().grass.count));
 }
 await p.evaluate(()=>{__V.walk.drag=false});
 await p.click('#v3dWalk');await p.waitForTimeout(3000);await p.screenshot({path:`walk/${TAG}exit.png`});
 await b.close();})();
