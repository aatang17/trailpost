// Renders a smooth, deterministic fly-through along Lantau Trail Stage 3 as PNG frames.
// usage: node capvid.js <nFrames> <outDir> [W H]
const { chromium } = require('playwright');
const fs = require('fs');
const N = +process.argv[2] || 3, OUT = process.argv[3] || 'frames', W = +process.argv[4] || 1280, H = +process.argv[5] || 720;
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--proxy-server=' + (process.env.HTTPS_PROXY || ''), '--proxy-bypass-list=localhost;127.0.0.1', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1300, height: 850 }, deviceScaleFactor: 1 }); p.setDefaultTimeout(300000);
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('http://127.0.0.1:8765/cap.html'); await p.waitForTimeout(2000);
  await p.click('#lantau3d'); await p.waitForFunction(() => window.__v3dBridge, null, { timeout: 240000 });
  const info = await p.evaluate(({ N, W, H }) => {
    const G = __G(), V = __V; const {ribbon,along,hAt,updateLOD,farLOD,keepAboveGround,moveCabins,followShadow}=__X; const D3=__X.D3(); cancelAnimationFrame(V.raf); V.open = false; // stop the app's own loop; we drive frames ourselves
    G.labelGrp.visible = false; if (G.cloudGrp) G.cloudGrp.visible = false;
    // replace the bright route with a thin earth-coloured path so the AI treats it as a real trail
    G.stageGrp.children.forEach(o => o.visible = false);
    const st = D3.stages['lantau-3']; const path = ribbon(st.pts, 2.6, 1.2, 0x6b5b47, 2, 0.85); path.visible = true; G.stageGrp.add(path);
    G.renderer.setPixelRatio(1); G.renderer.setSize(W, H, false); G.camera.aspect = W / H; G.camera.fov = 50; G.camera.updateProjectionMatrix();
    const pts = st.pts, cum = [0]; for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const f = { pts, cum, total: cum[cum.length - 1] };
    // find the summit along the stage, then fly the final climb and over the top
    let dPk = 0, hPk = -1; for (let d = 0; d < f.total; d += 20) { const q = along(f, d), h = hAt(q[0], q[1]); if (h > hPk) { hPk = h; dPk = d } }
    const dA = Math.max(0, dPk - 1500), dB = Math.min(f.total, dPk + 450);
    const avg = (d, off, span) => { let x = 0, z = 0, n = 0; for (let k = -4; k <= 4; k++) { const q = along(f, d + off + k * span / 8); x += q[0]; z += q[1]; n++ } return [x / n, z / n] };
    const cams = [];
    for (let i = 0; i < N; i++) {
      const u = N > 1 ? i / (N - 1) : 0; const e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2; const eu = 0.15 * e + 0.85 * u; // gentle ease in/out
      const d = dA + (dB - dA) * eu;
      const bh = avg(d, -260, 300), la = avg(d, 260, 300);
      let top = 0; for (let k = 0; k <= 10; k++) { const q = along(f, d - 300 + k * 60); top = Math.max(top, hAt(q[0], q[1])) }
      cams.push({ c: [bh[0], top + 115, bh[1]], l: [la[0], hAt(la[0], la[1]) + 10, la[1]] });
    }
    for (let pass = 0; pass < 3; pass++) for (let i = 1; i < N - 1; i++) { cams[i].c[1] = (cams[i - 1].c[1] + 2 * cams[i].c[1] + cams[i + 1].c[1]) / 4; cams[i].l[1] = (cams[i - 1].l[1] + 2 * cams[i].l[1] + cams[i + 1].l[1]) / 4 }
    window.__cams = cams;
    window.__frame = async (i) => {
      const cm = window.__cams[i], ex = V.ex; const t = 20000 + i * 1000 / 24;
      G.camera.position.set(cm.c[0] - G.cx, cm.c[1] * ex, cm.c[2] - G.cz); const L = new THREE.Vector3(cm.l[0] - G.cx, cm.l[1] * ex, cm.l[2] - G.cz);
      G.camera.lookAt(L); G.controls.target.copy(L); G.lookAt = L; keepAboveGround(); G.camera.updateMatrixWorld();
      for (let k = 0; k < 400; k++) { updateLOD(true); farLOD(true); if (!G.hiQueue.length && !G.hiLoading && G.full) break; await new Promise(r => setTimeout(r, 50)) }
      G.sky.position.copy(G.camera.position);
      if (G.scene.fog && G.fogBase && G.sunDir) { const fw = new THREE.Vector3(); G.camera.getWorldDirection(fw); const a = Math.pow(Math.max(0, fw.dot(G.sunDir)), 6) * 0.45; G.scene.fog.color.copy(G.fogBase).lerp(G.fogSun, a) }
      G.rip.offset.set((t * 0.0000035) % 1, (t * 0.0000021) % 1); moveCabins(t); G.shadowDirty = G.shadowDirty || i % 12 === 0; followShadow(t);
      G.renderer.render(G.scene, G.camera); return G.renderer.domElement.toDataURL('image/png');
    };
    return { dPk, hPk, dA, dB, total: f.total, stage: V.stage };
  }, { N, W, H });
  console.log(JSON.stringify(info));
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    const url = await p.evaluate(i => window.__frame(i), i);
    fs.writeFileSync(`${OUT}/f${String(i).padStart(4, '0')}.png`, Buffer.from(url.split(',')[1], 'base64'));
    if (i % 20 === 0) console.log('frame', i, ((Date.now() - t0) / 1000).toFixed(0) + 's');
  }
  await b.close();
})();
