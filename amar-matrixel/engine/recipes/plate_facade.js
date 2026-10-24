/* plate_facade — فيلا بواجهة مستوية (مسقط ليلي/غروب) كمواد اختبار بحقيقة أرضية.
   الواجهة مستوية تقريباً مع بروز صغير للبلاطة (تحدٍّ حقيقي للتتبع). ليست لقطة حقيقية. */
export const output = 'opaque';
let st; const FW = 16, FH = 7.4;
export async function setup(c) {
  const { THREE, core, W, H } = c, R = core.rng(5), N = core.makeNoise(9);
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); renderer.setSize(W, H, false); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const sk = document.createElement('canvas'); sk.width = 8; sk.height = 256; { const q = sk.getContext('2d'), g = q.createLinearGradient(0, 0, 0, 256); g.addColorStop(0, '#0e1a33'); g.addColorStop(.6, '#2b3556'); g.addColorStop(1, '#6a5a6a'); q.fillStyle = g; q.fillRect(0, 0, 8, 256); }
  const st0 = new THREE.CanvasTexture(sk); st0.colorSpace = THREE.SRGBColorSpace; scene.background = st0;
  /* نسيج الواجهة: albedo + emissive (2048×~950) */
  const TW = 2048, TH = Math.round(TW * FH / FW), A = document.createElement('canvas'), Em = document.createElement('canvas'); A.width = Em.width = TW; A.height = Em.height = TH; const a = A.getContext('2d'), e = Em.getContext('2d');
  const im = a.createImageData(TW, TH); for (let j = 0; j < TH; j++) for (let i = 0; i < TW; i++) { const k = (j * TW + i) * 4, n = N.fbm(i * .05, j * .05, 3) * 28 + N.n2(i * .6, j * .6) * 14; im.data[k] = 188 + n; im.data[k + 1] = 164 + n; im.data[k + 2] = 132 + n; im.data[k + 3] = 255; } a.putImageData(im, 0, 0);
  e.fillStyle = '#000'; e.fillRect(0, 0, TW, TH);
  const U = u => u * TW, V = v => v * TH; // v من الأعلى
  const rect = (ctx, u, v, w, h, col) => { ctx.fillStyle = col; ctx.fillRect(U(u), V(v), U(w), V(h)); };
  // أشرطة أفقية (بلاطة الطابق + الإفريز)
  rect(a, 0, .46, 1, .03, '#6e5d49'); rect(a, 0, 0, 1, .05, '#5a4b3b'); rect(a, 0, .985, 1, .015, '#4a3f33');
  // نوافذ الطابق الثاني + إطارات
  const win = (u, v, w, h) => { rect(a, u - .006, v - .012, w + .012, h + .024, '#3b3226'); rect(a, u, v, w, h, '#1d2733'); const g = e.createLinearGradient(0, V(v), 0, V(v + h)); g.addColorStop(0, 'rgba(255,214,140,.95)'); g.addColorStop(1, 'rgba(255,170,90,.8)'); e.fillStyle = g; e.fillRect(U(u + .004), V(v + .008), U(w - .008), V(h - .016)); rect(a, u + w / 2 - .0025, v, .005, h, '#3b3226'); rect(e, u + w / 2 - .0025, v, .005, h, '#000'); };
  win(.06, .12, .24, .28); win(.36, .12, .16, .28); win(.58, .12, .12, .28);
  // لوفر عمودي يمين
  for (let k = 0; k < 14; k++) { rect(a, .76 + k * .0165, .08, .006, .36, '#4a3f33'); }
  // الطابق الأرضي: باب كراج + باب دخول + نوافذ صغيرة
  rect(a, .06, .56, .36, .42, '#2a2f36'); for (let k = 0; k < 16; k++) rect(a, .06, .56 + k * .0262, .36, .004, '#161a20');
  rect(a, .50, .56, .10, .42, '#4b3a28'); rect(e, .615, .56, .008, .42, '#ffe0a0'); rect(a, .615, .56, .008, .42, '#fff0cc');
  win(.68, .6, .08, .14); win(.80, .6, .14, .22);
  /* شريط إضاءة جداري */
  const g2 = e.createLinearGradient(0, V(.9), 0, V(1)); g2.addColorStop(0, 'rgba(255,200,120,0)'); g2.addColorStop(1, 'rgba(255,200,120,.35)'); e.fillStyle = g2; e.fillRect(0, V(.9), TW, V(.1));
  const mapA = new THREE.CanvasTexture(A); mapA.colorSpace = THREE.SRGBColorSpace; mapA.anisotropy = 8; const mapE = new THREE.CanvasTexture(Em); mapE.colorSpace = THREE.SRGBColorSpace;
  const front = new THREE.Mesh(new THREE.PlaneGeometry(FW, FH), new THREE.MeshStandardMaterial({ map: mapA, emissiveMap: mapE, emissive: 0xffffff, emissiveIntensity: 1.0, roughness: .9 }));
  front.rotation.x = Math.PI / 2; front.position.set(0, 0, FH / 2); scene.add(front); // الوجه نحو -y (الكاميرا)
  const box = (w, d, h, x, y, z, col) => { const m = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), new THREE.MeshStandardMaterial({ color: col, roughness: .95 })); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; scene.add(m); return m; };
  box(FW, 9, FH, 0, 4.5 + .02, FH / 2, 0x9a8468); // كتلة خلف الواجهة
  box(FW + 1.2, .6, .22, 0, -.3, FH * .54, 0x6e5d49); // بروز بلاطة 0.6م (تحدٍّ للتتبع المستوي)
  box(FW + .6, 1.4, .4, 0, -.4, FH + .2, 0x5a4b3b); // إفريز السطح
  box(9, 7, 3, 4, 8, FH + 1.5, 0x8e7a60);
  /* محيط: أرضية رصف + سور منخفض + مبانٍ مجاورة داكنة */
  const gcv = document.createElement('canvas'); gcv.width = gcv.height = 1024; { const q = gcv.getContext('2d'); q.fillStyle = '#3c3a3d'; q.fillRect(0, 0, 1024, 1024); for (let k = 0; k < 2600; k++) { q.fillStyle = `rgba(${R() < .5 ? '255,255,255' : '0,0,0'},${.03 + R() * .08})`; q.fillRect(R() * 1024, R() * 1024, 4 + R() * 22, 3 + R() * 10); } q.strokeStyle = 'rgba(0,0,0,.35)'; q.lineWidth = 2; for (let k = 0; k <= 16; k++) { q.beginPath(); q.moveTo(k * 64, 0); q.lineTo(k * 64, 1024); q.moveTo(0, k * 64); q.lineTo(1024, k * 64); q.stroke(); } }
  const gt = new THREE.CanvasTexture(gcv); gt.wrapS = gt.wrapT = THREE.RepeatWrapping; gt.repeat.set(8, 8); gt.colorSpace = THREE.SRGBColorSpace; gt.anisotropy = 8;
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(160, 160), new THREE.MeshStandardMaterial({ map: gt, roughness: .85 })); ground.receiveShadow = true; scene.add(ground);
  box(5.5, .35, .9, -6.5, -5, .45, 0x7a6a55); box(5.5, .35, .9, 6.5, -5, .45, 0x7a6a55); box(1.1, .35, 1.3, 0, -5, .65, 0x2a2a2e);
  box(14, 10, 9, -22, 4, 4.5, 0x2b2c34); box(14, 10, 12, 22, 4, 6, 0x24262e); box(20, 10, 7, 0, 16, 3.5, 0x25262c);
  const hemi = new THREE.HemisphereLight(0x6f86b8, 0x2a2430, .55); scene.add(hemi);
  const moon = new THREE.DirectionalLight(0x8fa7e0, .9); moon.position.set(25, -30, 30); scene.add(moon);
  [[-5, -2.4], [0, -2.4], [5, -2.4]].forEach(([x, y]) => { const l = new THREE.PointLight(0xffb870, 55, 14, 1.6); l.position.set(x, y, .5); scene.add(l); });
  const camera = new THREE.PerspectiveCamera(); camera.up.set(0, 0, 1);
  st = { renderer, scene, camera };
}
const setCam = (c, t) => {
  const { core, W, H, params: P } = c, u = core.E.inOutSine(Math.min(1, t / (c.project.duration || 6))), fov = P.fov || ({ '9:16': 68, '4:5': 56, '16:9': 40 }[c.project.aspect] || 50);
  const asp = W / H, hf = 2 * Math.atan(Math.tan(fov * Math.PI / 360) * asp), dfit = (FW / 2 * (P.fit || 1.22)) / Math.tan(hf / 2) , d = dfit * (1 - (P.push ?? .16) * u);
  const az = (-90 + (P.az0 ?? -26) + ((P.az1 ?? -9) - (P.az0 ?? -26)) * u) * Math.PI / 180, tgt = [0, 0, 3.2 + .3 * u], hgt = (P.h0 ?? 1.7) + ((P.h1 ?? 3.4) - (P.h0 ?? 1.7)) * u;
  const cam = st.camera; cam.position.set(tgt[0] + d * Math.cos(az), tgt[1] + d * Math.sin(az), hgt); cam.lookAt(...tgt); cam.fov = fov; cam.aspect = asp; cam.updateProjectionMatrix(); cam.updateMatrixWorld(true); return fov;
};
export async function frame(c, i, t) { setCam(c, t); if (c.params.depth_pass) { const T = c.THREE; if (!st.dm) st.dm = new T.ShaderMaterial({ uniforms: { uN: { value: 8 }, uF: { value: 90 } }, vertexShader: 'varying float vZ; void main(){ vec4 m = modelViewMatrix*vec4(position,1.); vZ = -m.z; gl_Position = projectionMatrix*m; }', fragmentShader: 'varying float vZ; uniform float uN; uniform float uF; void main(){ float d = clamp(1.-(vZ-uN)/(uF-uN),0.,1.); gl_FragColor = vec4(vec3(d),1.); }' });
    st.scene.overrideMaterial = st.dm; st.scene.background = null; st.scene.fog = null; st.renderer.setClearColor(0x000000, 1); }
  st.renderer.render(st.scene, st.camera); c.g.drawImage(st.renderer.domElement, 0, 0, c.W, c.H); }
export function meta(c) {
  const { core, THREE, W, H } = c, n = Math.round((c.project.duration || 6) * c.fps), A = [1, 0, 0, 0, 0, 1, 0, -1, 0];
  const corners3 = [[-FW / 2, FH / 2, 0], [FW / 2, FH / 2, 0], [FW / 2, -FH / 2, 0], [-FW / 2, -FH / 2, 0]], frames = []; // مركز الواجهة = أصل المستوى (نفس اصطلاح track.py)
  for (let i = 0; i < n; i++) { const fov = setCam(c, i / c.fps), pose = core.poseFromCamera(THREE, st.camera, A, [0, 0, FH / 2]), K = core.intrinsics(W, H, fov);
    frames.push({ i, R: pose.R, t: pose.t, fov, corners: corners3.map(q => { const o = core.projectP3(pose, K, q); return [o.x, o.y]; }) }); }
  return { kind: 'ground_truth', width: W, height: H, fps: c.fps, plane: { w: FW, l: FH, units: 'meters' }, corners3, frames,
    gt_lines_uv: { note: 'خطوط الواجهة الحقيقية (u من اليسار، v من الأعلى) لقياس الانزلاق', h: [0, .05, .46, .49, .56, .98, 1], v: [.06, .24, .30, .36, .42, .52, .58, .64] } };
}
