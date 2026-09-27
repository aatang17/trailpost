const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium',args:['--proxy-server='+(process.env.HTTPS_PROXY||''),'--proxy-bypass-list=localhost;127.0.0.1','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:1300,height:850}});
 const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 await p.goto('http://127.0.0.1:8765/trailpost.html');await p.waitForTimeout(3000);await p.evaluate(()=>{const b=document.querySelector('#lantau3d');b.scrollIntoView()});
 const cdp=await p.context().newCDPSession(p);await cdp.send('Network.enable');
 await cdp.send('Network.emulateNetworkConditions',{offline:false,latency:60,downloadThroughput:9e6/8,uploadThroughput:3e6/8});
 let bytes=0,reqs=[];cdp.on('Network.loadingFinished',e=>{bytes+=e.encodedDataLength});cdp.on('Network.requestWillBeSent',e=>reqs.push(e.request.url.split('/').slice(-2).join('/')));
 const t0=Date.now();
 await p.click('#lantau3d');
 await p.waitForFunction(()=>window.__v3dFirstView,null,{timeout:120000});const first=Date.now()-t0;const firstBytes=bytes,firstReqs=reqs.length;
 await p.screenshot({path:'perf_first.png'});
 await p.waitForFunction(()=>window.__v3dFull,null,{timeout:120000}).catch(()=>{});await p.waitForTimeout(12000);
 console.log(JSON.stringify({firstViewMs:first,firstMB:(firstBytes/1e6).toFixed(2),firstRequests:firstReqs,afterMs:Date.now()-t0,totalMB:(bytes/1e6).toFixed(2),requests:reqs.length}));
 console.log(reqs.filter(u=>!u.includes('fonts')).join(' '));
 await p.screenshot({path:'perf_full.png'});
 console.log(errs.slice(0,8).join('\n'));await b.close();})();
