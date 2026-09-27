const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium',args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--autoplay-policy=no-user-gesture-required']});
 const p=await b.newPage({viewport:{width:1200,height:800},deviceScaleFactor:1});p.setDefaultTimeout(240000);
 p.on('pageerror',e=>console.log('ERR',e.message));p.on('console',m=>{if(m.type()==='error'||m.type()==='warning')console.log('CONSOLE',m.type(),m.text().slice(0,200))});
 await p.goto('http://127.0.0.1:8765/cap.html');await p.waitForTimeout(1500);
 await p.click('#lantau3d');await p.waitForFunction(()=>window.__v3dFull,null,{timeout:240000});
 await p.evaluate(()=>{const G=__G();if(G.cloudGrp)G.cloudGrp.visible=false});
 await p.click('#v3dWalk');await p.waitForTimeout(4000);
 console.log(JSON.stringify(await p.evaluate(()=>{const w=__V.walk;return {k:w.pace.k.toFixed(2),tob_min:(w.pace.tt[w.pace.N]/60).toFixed(0),total:Math.round(w.total),
   marks:w.marks.map(m=>[m.ty,Math.round(m.d),m.en||'',m.len?Math.round(m.len)+'m '+Math.round(m.avg*100)+'%':'',m.next?Math.round(m.next):'']),
   paces:[0,500,1000,1500,2000,2500,2800,3200,3600,4000].map(d=>[d,(__X.paceAt(w,d)*3.6).toFixed(1),Math.round(__X.timeLeft(w,d)/60)]),
   snd:{ctx:!!__X.SND().ctx,state:__X.SND().ctx&&__X.SND().ctx.state,bufs:Object.keys(__X.SND().buf)}}})));
 for(const [d,n] of [[2805,'s1'],[2596,'s2'],[1800,'s3'],[2200,'s4']]){
   await p.evaluate(d=>{const w=__V.walk;w.playing=false;w.d=d},d);await p.waitForTimeout(5000);
   await p.screenshot({path:`walk/${n}.png`});
   console.log(n,await p.evaluate(()=>[document.querySelector('#v3dFlyInfo').textContent,document.querySelector('#v3dWalkCard').innerText.replace(/\n/g,' | ')]));
 }
 console.log(JSON.stringify(await p.evaluate(()=>({gains:['wind','forest'].map(n=>__X.SND()[n]&&__X.SND()[n].gain.gain.value.toFixed(2)),bufs:Object.keys(__X.SND().buf)}))));
 await b.close();})();
