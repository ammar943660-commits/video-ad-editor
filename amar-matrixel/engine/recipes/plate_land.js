/* plate_land — لقطة جوية تركيبية لأرض فضاء (مواد اختبار بحقيقة أرضية Ground Truth)
   ليست لقطة حقيقية: تُستخدم لقياس التتبع والمنظور بدقة. المخرجات: فريمات JPEG + meta.json (pose لكل فريم). */
export const output = 'opaque';
let st;
export async function setup(c) {
  const { THREE, core, W, H, params: P } = c, N = core.makeNoise(7), R = core.rng(11);
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); renderer.setSize(W, H, false); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene(); const PLOT = { w: P.plot_w || 50, l: P.plot_l || 40 };
  /* سماء */
  const sk = document.createElement('canvas'); sk.width = 8; sk.height = 512; const sg = sk.getContext('2d'), gr = sg.createLinearGradient(0, 0, 0, 512);
  gr.addColorStop(0, '#5f86b8'); gr.addColorStop(.55, '#e7c9a0'); gr.addColorStop(1, '#f1d6aa'); sg.fillStyle = gr; sg.fillRect(0, 0, 8, 512);
  const skyTex = new THREE.CanvasTexture(sk); skyTex.colorSpace = THREE.SRGBColorSpace; scene.background = skyTex; scene.fog = new THREE.FogExp2(0xe3c9a2, .0042);
  /* أرضية 240×240 م على نسيج 4096 */
  const TS = 4096, EXT = 240, ppm = TS / EXT, gc = document.createElement('canvas'); gc.width = gc.height = TS; const g = gc.getContext('2d');
  const img = g.createImageData(TS, TS), d = img.data;
  const px2w = v => (v / TS - .5) * EXT; // بكسل → متر
  const inPlot = (x, y) => Math.abs(x) < PLOT.w / 2 && Math.abs(y) < PLOT.l / 2;
  const sw = 3, rw = 14, ox = PLOT.w / 2 + sw, oy = PLOT.l / 2 + sw; // حدود الرصيف/الطريق
  const roadAt = (x, y) => { const ax = Math.abs(x), ay = Math.abs(y); const inner = ax < ox && ay < oy; const outer = ax < ox + rw && ay < oy + rw; return !inner && outer; };
  for (let j = 0; j < TS; j++) for (let i = 0; i < TS; i++) {
    const x = px2w(i), y = -px2w(j), k = (j * TS + i) * 4; let r, gg, b;
    const n = N.fbm(i * .02, j * .02, 3), n2 = N.n2(i * .45, j * .45);
    if (inPlot(x, y)) { const b0 = 150 + n * 70 + n2 * 24; r = b0 + 18; gg = b0 - 6; b = b0 - 48; const ptc = N.fbm(i * .006 + 40, j * .006, 2); if (ptc > .62) { r -= 28; gg -= 22; b -= 18; } }
    else if (roadAt(x, y)) { const a = 78 + n * 22 + n2 * 14; r = a; gg = a; b = a + 4; }
    else if (Math.abs(x) < ox && Math.abs(y) < oy) { const a = 168 + n * 30 + n2 * 14; r = a; gg = a - 6; b = a - 16; } // رصيف
    else { const a = 138 + n * 40 + n2 * 14; r = a + 10; gg = a - 4; b = a - 28; }
    d[k] = r; d[k + 1] = gg; d[k + 2] = b; d[k + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  const W2 = (x, y) => [(x / EXT + .5) * TS, (-y / EXT + .5) * TS];
  // حدود القطعة (حافة خرسانية) + آثار إطارات + أحجار + شجيرات جافة
  g.strokeStyle = '#cbbfa6'; g.lineWidth = .7 * ppm; { const [x0, y0] = W2(-PLOT.w / 2, PLOT.l / 2), [x1, y1] = W2(PLOT.w / 2, -PLOT.l / 2); g.strokeRect(x0, y0, x1 - x0, y1 - y0); }
  g.strokeStyle = 'rgba(70,55,38,.28)'; for (let k = 0; k < 7; k++) { const y = (R() - .5) * PLOT.l * .9, x0 = -PLOT.w / 2 + 1, x1 = PLOT.w / 2 - 1, [a, b] = W2(x0, y), [c, dd] = W2(x1, y + (R() - .5) * 8); g.lineWidth = 1.1 * ppm; g.beginPath(); g.moveTo(a, b); g.quadraticCurveTo((a + c) / 2, (b + dd) / 2 + (R() - .5) * 60, c, dd); g.stroke(); }
  for (let k = 0; k < 900; k++) { const x = (R() - .5) * PLOT.w * .96, y = (R() - .5) * PLOT.l * .96, [a, b] = W2(x, y), rr = (.08 + R() * .35) * ppm; g.fillStyle = R() < .5 ? 'rgba(60,48,36,.55)' : 'rgba(205,190,165,.55)'; g.beginPath(); g.ellipse(a, b, rr, rr * .7, R() * 3, 0, 7); g.fill(); }
  for (let k = 0; k < 16; k++) { const x = (R() - .5) * PLOT.w * .9, y = (R() - .5) * PLOT.l * .9, [a, b] = W2(x, y); g.fillStyle = 'rgba(92,96,52,.55)'; for (let q = 0; q < 14; q++) { g.beginPath(); g.arc(a + (R() - .5) * 2.4 * ppm, b + (R() - .5) * 2.4 * ppm, (.1 + R() * .3) * ppm, 0, 7); g.fill(); } }
  // خطوط الطريق المتقطعة + معابر
  g.strokeStyle = 'rgba(235,235,225,.85)'; g.lineWidth = .25 * ppm; g.setLineDash([3 * ppm, 3 * ppm]);
  const lanes = [[-ox - rw / 2, oy + rw / 2, ox + rw / 2, oy + rw / 2], [-ox - rw / 2, -oy - rw / 2, ox + rw / 2, -oy - rw / 2], [-ox - rw / 2, -oy - rw / 2, -ox - rw / 2, oy + rw / 2], [ox + rw / 2, -oy - rw / 2, ox + rw / 2, oy + rw / 2]];
  for (const [x0, y0, x1, y1] of lanes) { const [a, b] = W2(x0, y0), [c, dd] = W2(x1, y1); g.beginPath(); g.moveTo(a, b); g.lineTo(c, dd); g.stroke(); } g.setLineDash([]);
  const gt = new THREE.CanvasTexture(gc); gt.colorSpace = THREE.SRGBColorSpace; gt.anisotropy = 8; gt.generateMipmaps = true; gt.minFilter = THREE.LinearMipmapLinearFilter;
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(EXT, EXT), new THREE.MeshLambertMaterial({ map: gt })); ground.receiveShadow = true; scene.add(ground);
  /* مبانٍ حول الحلقة */
  const winTex = (cols, rows, lit) => { const c2 = document.createElement('canvas'); c2.width = 128 * cols / 2; c2.height = 128 * rows / 2; const q = c2.getContext('2d'); q.fillStyle = ['#cdb596', '#bfa684', '#d6c3a5', '#b9a07f'][(R() * 4) | 0]; q.fillRect(0, 0, c2.width, c2.height);
    const cw = c2.width / cols, ch = c2.height / rows; for (let a = 0; a < cols; a++) for (let b = 0; b < rows; b++) { q.fillStyle = R() < lit ? '#e9c27a' : '#3a4a5c'; q.fillRect(a * cw + cw * .22, b * ch + ch * .2, cw * .56, ch * .5); q.fillStyle = 'rgba(0,0,0,.25)'; q.fillRect(a * cw + cw * .2, b * ch + ch * .72, cw * .6, ch * .06); }
    const t = new THREE.CanvasTexture(c2); t.colorSpace = THREE.SRGBColorSpace; return t; };
  const bm = (w, dd, h) => { const cols = Math.max(2, Math.round(w / 3.2)), rows = Math.max(2, Math.round(h / 3.1)); const mats = [0, 1, 2, 3].map(() => new THREE.MeshLambertMaterial({ map: winTex(cols, rows, .25) })); const top = new THREE.MeshLambertMaterial({ color: 0x9a8f80 });
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, dd, h), [mats[0], mats[1], mats[2], mats[3], top, top]); m.castShadow = m.receiveShadow = true; return m; };
  const ringX = ox + rw + 3, ringY = oy + rw + 3;
  const place = (side) => { let pos = -95; while (pos < 95) { const w = 12 + R() * 9, h = (side === 'N' ? 13 + R() * 20 : 9 + R() * 8), dd = 15 + R() * 6; pos += w / 2 + 1.5; const m = bm(w, dd, h); m.rotation.set(0, 0, 0);
      if (side === 'N') m.position.set(pos, ringY + dd / 2, h / 2); if (side === 'S') m.position.set(pos, -ringY - dd / 2, h / 2); if (side === 'E') { m.geometry = new THREE.BoxGeometry(dd, w, h); m.position.set(ringX + dd / 2, pos, h / 2); } if (side === 'W') { m.geometry = new THREE.BoxGeometry(dd, w, h); m.position.set(-ringX - dd / 2, pos, h / 2); }
      if (Math.abs(m.position.x) < 100 && Math.abs(m.position.y) < 100) scene.add(m); pos += w / 2; } };
  ['N', 'E', 'W'].forEach(place); // جهة الكاميرا (S) مفتوحة حتى لا تحجب المباني الأمامية القطعة
  /* سيارات: ثابتة ومتحركة على حلقة الطريق */
  const carCols = [0xd8d8d8, 0x20242a, 0x8a1f1f, 0x2c4d73, 0xcfa23a, 0xeeeeee, 0x5a5f66];
  const cars = []; const loopW = ox + rw / 2, loopH = oy + rw / 2;
  for (let k = 0; k < 26; k++) { const car = new THREE.Group(); const col = carCols[(R() * carCols.length) | 0];
    const body = new THREE.Mesh(new THREE.BoxGeometry(4.4, 1.8, .8), new THREE.MeshLambertMaterial({ color: col })), cab = new THREE.Mesh(new THREE.BoxGeometry(2.3, 1.6, .65), new THREE.MeshLambertMaterial({ color: 0x1b2430 }));
    body.position.z = .65; cab.position.set(-.2, 0, 1.28); body.castShadow = cab.castShadow = true; car.add(body, cab); scene.add(car); cars.push({ car, s: R(), v: (R() < .6 ? 1 : 0) * (5 + R() * 5), lane: R() < .5 ? 1 : -1, off: (R() - .5) * 2.4 }); }
  const per = 2 * (2 * loopW) + 2 * (2 * loopH);
  const carPos = (cr, t) => { let s = ((cr.s * per + cr.v * t) % per + per) % per; const a = 2 * loopW, b = 2 * loopH; const L = cr.off; let x, y, ang;
    if (s < a) { x = -loopW + s; y = loopH + L; ang = 0; } else if ((s -= a) < b) { x = loopW + L; y = loopH - s; ang = -Math.PI / 2; } else if ((s -= b) < a) { x = loopW - s; y = -loopH + L; ang = Math.PI; } else { s -= a; x = -loopW + L; y = -loopH + s; ang = Math.PI / 2; } return [x, y, ang]; };
  /* إضاءة */
  const sun = new THREE.DirectionalLight(0xffdcae, 2.4); sun.position.set(-70, -50, 55); sun.target.position.set(0, 0, 0); sun.castShadow = true; sun.shadow.mapSize.set(4096, 4096);
  const sc = sun.shadow.camera; sc.left = -110; sc.right = 110; sc.top = 110; sc.bottom = -110; sc.near = 1; sc.far = 400; sun.shadow.bias = -.0004; sun.shadow.normalBias = .4; scene.add(sun, sun.target, new THREE.HemisphereLight(0xa8c4ee, 0xb09a78, 1.05));
  const camera = new THREE.PerspectiveCamera(); camera.up.set(0, 0, 1);
  st = { renderer, scene, camera, cars, carPos, PLOT, ground };
}
/* مسار الكاميرا: ارتفاع (Rise) + ميل (Tilt) + انجراف أفقي بسيط */
export function pathAt(c, t01) {
  const { params: P, W, H } = c; const fov = P.fov || ({ '9:16': 60, '4:5': 52, '16:9': 42 }[c.project.aspect] || 50); const e = c.core.E.inOutSine(t01);
  const asp = W / H, vf = fov * Math.PI / 180, hf = 2 * Math.atan(Math.tan(vf / 2) * asp), half = Math.min(vf, hf) / 2, Rb = Math.hypot(st.PLOT.w, st.PLOT.l) / 2 * (P.fit || 1.08);
  const d = Rb / Math.sin(half) * (1 - .1 * e), elev = (P.elev0 ?? 24) + ((P.elev1 ?? 62) - (P.elev0 ?? 24)) * e, az = (-90 + (P.az0 ?? -14) + ((P.az1 ?? 10) - (P.az0 ?? -14)) * e) * Math.PI / 180;
  const el = elev * Math.PI / 180, tgt = [0, (1 - e) * 6, 0];
  return { fov, pos: [tgt[0] + d * Math.cos(el) * Math.cos(az), tgt[1] + d * Math.cos(el) * Math.sin(az), tgt[2] + d * Math.sin(el)], tgt };
}
const setCam = (c, t) => { const dur = c.project.duration || 6, p = pathAt(c, Math.min(1, t / dur)); st.camera.position.set(...p.pos); st.camera.lookAt(...p.tgt); st.camera.fov = p.fov; st.camera.aspect = c.W / c.H; st.camera.updateProjectionMatrix(); st.camera.updateMatrixWorld(true); return p; };
export async function frame(c, i, t) {
  setCam(c, t);
  st.cars.forEach(cr => { const [x, y, a] = st.carPos(cr, t); cr.car.position.set(x, y, 0); cr.car.rotation.z = a; });
  if (c.params.depth_pass) { const T = c.THREE; if (!st.dm) st.dm = new T.ShaderMaterial({ uniforms: { uN: { value: 20 }, uF: { value: 260 } }, vertexShader: 'varying float vZ; void main(){ vec4 m = modelViewMatrix*vec4(position,1.); vZ = -m.z; gl_Position = projectionMatrix*m; }', fragmentShader: 'varying float vZ; uniform float uN; uniform float uF; void main(){ float d = clamp(1.-(vZ-uN)/(uF-uN),0.,1.); gl_FragColor = vec4(vec3(d),1.); }' });
    st.scene.overrideMaterial = st.dm; st.scene.background = null; st.scene.fog = null; st.renderer.setClearColor(0x000000, 1); }
  st.renderer.render(st.scene, st.camera); c.g.drawImage(st.renderer.domElement, 0, 0, c.W, c.H);
}
export function meta(c) {
  const { core, THREE, W, H } = c, PL = st.PLOT, n = Math.round((c.project.duration || 6) * c.fps);
  const corners3 = [[-PL.w / 2, PL.l / 2, 0], [PL.w / 2, PL.l / 2, 0], [PL.w / 2, -PL.l / 2, 0], [-PL.w / 2, -PL.l / 2, 0]], frames = [];
  for (let i = 0; i < n; i++) { const p = setCam(c, i / c.fps), pose = core.poseFromCamera(THREE, st.camera), K = core.intrinsics(W, H, p.fov);
    frames.push({ i, R: pose.R, t: pose.t, fov: p.fov, corners: corners3.map(q => { const o = core.projectP3(pose, K, q); return [o.x, o.y]; }) }); }
  // فحص تطابق إسقاط three مع إسقاط pose (اختبار وحدة لمعادلة الكاميرا)
  const pose = { R: frames[n >> 1].R, t: frames[n >> 1].t }, pr = new THREE.Vector3(7, 3, 5).project(setCam(c, (n >> 1) / c.fps) && st.camera), K = core.intrinsics(W, H, frames[n >> 1].fov), q = core.projectP3(pose, K, [7, 3, 5]);
  const err = Math.hypot((pr.x * .5 + .5) * W - q.x, (-pr.y * .5 + .5) * H - q.y);
  return { kind: 'ground_truth', width: W, height: H, fps: c.fps, plane: { w: PL.w, l: PL.l, area_m2: PL.w * PL.l }, corners3, pose_unit_test_px: err, frames };
}
