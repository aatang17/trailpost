const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,hasTouch:true,isMobile:true});p.setDefaultTimeout(240000);
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('http://127.0.0.1:8765/capm.html');await p.waitForTimeout(1500);
 await p.click('#lantau3d');await p.waitForFunction(()=>window.__v3dFull,null,{timeout:240000});
 await p.evaluate(()=>{const G=__G();if(G.cloudGrp)G.cloudGrp.visible=false});
 await p.click('#v3dWalk');await p.evaluate(()=>{const w=__V.walk;w.d=2500});await p.waitForTimeout(9000);
 await p.screenshot({path:'walk/m1.png'});
 console.log(await p.evaluate(()=>({mobile:__G().grass.instanceMatrix.count,count:__G().grass.count,info:document.querySelector('#v3dFlyInfo').textContent,play:document.querySelector('#v3dWalkPlay').textContent})));
 await p.click('#v3dWalkPlay');await p.waitForTimeout(1500);console.log(await p.evaluate(()=>[__V.walk.playing,document.querySelector('#v3dWalkPlay').textContent]));
 await b.close();})();
