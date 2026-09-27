const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
 for(const [w,h,m,n] of [[390,844,true,'home_m'],[1280,800,false,'home_d']]){
 const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:1,hasTouch:m,isMobile:m});
 await p.goto('http://127.0.0.1:8765/capm.html');await p.waitForTimeout(2500);
 console.log(n,await p.evaluate(()=>[innerWidth,document.documentElement.scrollWidth]));await p.screenshot({path:'walk/'+n+'.png'});await p.close()}
 await b.close();})();
