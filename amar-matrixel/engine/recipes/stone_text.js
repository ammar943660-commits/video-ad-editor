/* ═══ A · STONE_TEXT_REVEAL ═══
   نص عربي حجري 3D حقيقي (بثق كنتور النص) ينبثق من مستوى الأرض، غبار حجمي + حطام + ظل تماس + اهتزاز عند الاستقرار.
   المخرج: طبقة RGBA شفافة (النص + الغبار + الظل) تلتصق بالأرض عبر كاميرا التتبع (track.json).
   ملاحظة صدق: بثق متعدد الأضلاع من خط المتصفح (تشكيل عربي سليم) — ليس نحتاً. ملف Blender المرافق لإعادة البناء كمجسم قابل للنحت. */
import { E } from '../core.js';
export const output = 'alpha';
let S;
const D = { beats: [{ lines: ['أرض للبيع'], t0: .35, rise: 1.5, hold: 1.6, sink: .9 }] };

export async function setup(c) {
  const { THREE, core, W, H, params: P, track } = c;
  if (!track) throw new Error('stone_text يحتاج track.json (شغّل tools/track.py أولاً)');
  await core.loadFonts([P.font || 'Tajawal Black']);
  const renderer = new THREE.WebGLRenderer({ alpha: true, premultipliedAlpha: true, antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(W, H, false); renderer.setClearColor(0, 0); renderer.localClippingEnabled = true; renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera();
  const sunDir = new THREE.Vector3(...(P.sun_dir || [-70, -50, 55])).normalize();
  const sun = new THREE.DirectionalLight(new THREE.Color(P.sun_color || '#ffe2bd'), P.sun_intensity ?? 2.6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -.0005; sun.shadow.normalBias = .02; sun.shadow.radius = 5; scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight(0xaec7ee, 0x9b8a70, P.ambient ?? 1.15));
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.ShadowMaterial({ opacity: P.shadow_opacity ?? .62 })); ground.receiveShadow = true; ground.position.z = track.plane.l * 1e-4; ground.material.depthWrite = false; ground.renderOrder = 1; scene.add(ground);
  const clip = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
  const plane = track.plane, pw = plane.w, N = core.makeNoise(5), rnd = core.rng(P.seed || 21);
  const gcol = (track.ground_color || [150, 135, 110]);
  const dustCol = new THREE.Color(`rgb(${Math.min(255, gcol[0] * 1.08 | 0)},${Math.min(255, gcol[1] * 1.06 | 0)},${Math.min(255, gcol[2] * 1.04 | 0)})`);
  /* مادة الحجر: ضوضاء 3D إجرائية (لون + شقوق + نتوء) مرتبطة بالجسم فلا «تسبح» أثناء الصعود */
  const pal = { stone: ['#6f6e6a', '#a7a49b'], sandstone: ['#9a8466', '#cdb792'], dark: ['#3c3c3e', '#6b6b6f'] }[P.material || 'stone'];
  const uni = { uScale: { value: 1 }, uC1: { value: new THREE.Color(pal[0]) }, uC2: { value: new THREE.Color(pal[1]) }, uBump: { value: P.bump ?? .22 } };
  const mat = new THREE.MeshStandardMaterial({ roughness: .93, metalness: 0, clippingPlanes: [clip], clipShadows: true });
  mat.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, uni);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vP;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvP = position;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vP; uniform float uScale; uniform vec3 uC1; uniform vec3 uC2; uniform float uBump;
float h3(vec3 p){ p=fract(p*0.3183099+.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float n3(vec3 x){ vec3 i=floor(x), f=fract(x); f=f*f*(3.-2.*f);
 return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x),mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x),mix(h3(i+vec3(0,1,1)),h3(i+vec3(1,1,1)),f.x),f.y),f.z); }
float fbm3(vec3 p){ float s=0.,a=.5; for(int i=0;i<5;i++){ s+=a*n3(p); p=p*2.03+7.1; a*=.5; } return s; }
float crack(vec3 p){ float r=abs(n3(p*0.9)*2.-1.); r=1.-r; return smoothstep(.93,.99,r); }
float stoneH(vec3 p){ float g=fbm3(p*uScale*1.0); float cr=crack(p*uScale*.22); return g*.55 - cr*.5 + n3(p*uScale*9.)*.06; }`)
      .replace('#include <color_fragment>', `#include <color_fragment>
{ float g=fbm3(vP*uScale*.35); float cr=crack(vP*uScale*.22); float sp=n3(vP*uScale*9.);
  vec3 c=mix(uC1,uC2,smoothstep(.2,.8,g)); c*=.92+.14*sp; c=mix(c,c*.7,cr*.6); diffuseColor.rgb*=c; }`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
{ float hh=stoneH(vP); vec3 sx=dFdx(-vViewPosition), sy=dFdy(-vViewPosition); float dx=dFdx(hh), dy=dFdy(hh);
  vec3 R1=cross(sy,normal), R2=cross(normal,sx); float det=dot(sx,R1); vec3 gr=sign(det)*(dx*R1+dy*R2); normal=normalize(abs(det)*normal - uBump*gr); }`);
  };
  /* بناء المجسمات: لكل beat نص → كنتور → ExtrudeGeometry */
  const beats = (P.beats || D.beats).map((b, k) => ({ rise: 1.5, hold: 1.6, sink: .9, size: .78, anchor: [0, -.12], ...b, k }));
  for (const b of beats) {
    const tc = core.textCanvas(b.lines, { font: P.font || 'Tajawal Black', px: 240, fit: 1500, lineGap: 1.3, pad: 60 });
    const polys = core.traceMask(tc.canvas, { threshold: 128, simplify: .55 });
    let minx = 1e9, maxx = -1e9, miny = 1e9, maxy = -1e9; polys.forEach(p => p.outer.forEach(([x, y]) => { minx = Math.min(minx, x); maxx = Math.max(maxx, x); miny = Math.min(miny, y); maxy = Math.max(maxy, y); }));
    const sc = (b.size * pw) / (maxx - minx), tw = (maxx - minx) * sc, th = (maxy - miny) * sc;
    const T = ([x, y]) => new THREE.Vector2((x - (minx + maxx) / 2) * sc, (maxy - y) * sc);
    const shapes = polys.map(p => { const s = new THREE.Shape(p.outer.map(T)); p.holes.forEach(h => s.holes.push(new THREE.Path(h.map(T)))); return s; });
    const dep = th * (b.depth ?? .34), g = new THREE.ExtrudeGeometry(shapes, { depth: dep, bevelEnabled: true, bevelThickness: dep * .1, bevelSize: th * .012, bevelSegments: 2, curveSegments: 1 });
    g.translate(0, 0, -dep / 2); g.computeVertexNormals();
    const mesh = new THREE.Mesh(g, mat); mesh.castShadow = true; mesh.receiveShadow = false; mesh.matrixAutoUpdate = false; mesh.visible = false; scene.add(mesh);
    Object.assign(b, { mesh, tw, th, dep, t1: b.t0 + b.rise, t2: b.t0 + b.rise + b.hold, t3: b.t0 + b.rise + b.hold + b.sink, wp: [b.anchor[0] * pw, b.anchor[1] * plane.l] });
  }
  uni.uScale.value = 1 / (beats[0].th * .05);
  /* اتجاه المواجهة: نحو كاميرا الفريم الأول (أفقياً) */
  const f0 = track.frames[0], Rm = f0.R, tt = f0.t, cw = [-(Rm[0] * tt[0] + Rm[3] * tt[1] + Rm[6] * tt[2]), -(Rm[1] * tt[0] + Rm[4] * tt[1] + Rm[7] * tt[2]), -(Rm[2] * tt[0] + Rm[5] * tt[1] + Rm[8] * tt[2])], cam0 = [cw[0], -cw[1], -cw[2]];
  let fx = cam0[0] - beats[0].wp[0], fy = cam0[1] - beats[0].wp[1]; const fl = Math.hypot(fx, fy) || 1; fx /= fl; fy /= fl;
  if (P.face_deg !== undefined) { const a = P.face_deg * Math.PI / 180; fx = Math.cos(a); fy = Math.sin(a); }
  const up = new THREE.Vector3(0, 0, 1), nrm = new THREE.Vector3(fx, fy, 0), right = new THREE.Vector3().crossVectors(up, nrm).normalize();
  const basis = new THREE.Matrix4().makeBasis(right, up, nrm);
  /* ظل تماس (AO) */
  const bc = document.createElement('canvas'); bc.width = 256; bc.height = 64; { const q = bc.getContext('2d'); q.translate(128, 32); q.scale(1, .25); const gr = q.createRadialGradient(0, 0, 4, 0, 0, 128); gr.addColorStop(0, 'rgba(0,0,0,.9)'); gr.addColorStop(.5, 'rgba(0,0,0,.45)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); q.fillStyle = gr; q.fillRect(-128, -128, 256, 256); }
  const blobTex = new THREE.CanvasTexture(bc);
  for (const b of beats) { const m = new THREE.Mesh(new THREE.PlaneGeometry(b.tw * 1.08, b.dep * 3.2 + b.th * .08), new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false, opacity: 0 })); m.renderOrder = 2; m.visible = false; scene.add(m); b.blob = m; }
  /* غبار: Sprites بنسيج سحابي */
  const puffTex = [0, 1, 2].map(s => { const q = document.createElement('canvas'); q.width = q.height = 192; const x = q.getContext('2d'), im = x.createImageData(192, 192), nn = core.makeNoise(50 + s);
    for (let j = 0; j < 192; j++) for (let i = 0; i < 192; i++) { const dx = (i - 96) / 96, dy = (j - 96) / 96, r = Math.hypot(dx, dy), f = Math.max(0, 1 - r), n = nn.fbm(i * .045, j * .045, 4); const a = Math.pow(f, 1.25) * (0.35 + 1.1 * n) ; const k = (j * 192 + i) * 4; im.data[k] = im.data[k + 1] = im.data[k + 2] = 255; im.data[k + 3] = Math.min(255, a * 255 * 1.1); }
    x.putImageData(im, 0, 0); const t = new THREE.CanvasTexture(q); t.colorSpace = THREE.SRGBColorSpace; return t; });
  const dust = [], nDust = P.dust_count ?? 150;
  for (const b of beats) for (let k = 0; k < nDust; k++) {
    const phase = k < nDust * .6 ? 'rise' : (k < nDust * .8 ? 'settle' : 'sink'), u = rnd();
    const ts = phase === 'rise' ? b.t0 + b.rise * Math.pow(u, .8) : phase === 'settle' ? b.t1 + u * .25 : b.t2 + b.sink * u * .9;
    const sp = (phase === 'settle' ? 1.8 : 1) * (.5 + rnd());
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: puffTex[k % 3], color: dustCol.clone().multiplyScalar(.85 + .3 * rnd()), transparent: true, depthWrite: false, opacity: 0, rotation: rnd() * 6.28 }));
    sprite.visible = false; scene.add(sprite);
    dust.push({ b, sprite, ts, life: 1.4 + rnd() * 1.6, x: (rnd() - .5) * b.tw * 1.05, y: (rnd() - .35) * b.dep * 3, vx: (rnd() - .5) * 1.6 * sp, vy: (rnd() - .2) * 1.2 * sp, vz: (.35 + rnd() * .8) * sp, s0: b.th * (.18 + rnd() * .22), s1: b.th * (.9 + rnd() * 1.0) * (P.dust_size ?? 1), a: (.28 + rnd() * .22) * (P.dust_amount ?? 1), rot: (rnd() - .5) * .8, seed: rnd() * 100 });
  }
  /* حطام: مكعبات/رباعيات صغيرة بباليستيك حتمي */
  const chipG = new THREE.IcosahedronGeometry(1, 0), chips = [], nChip = P.chip_count ?? 36;
  for (const b of beats) for (let k = 0; k < nChip; k++) { const m = new THREE.Mesh(chipG, mat); m.castShadow = true; m.matrixAutoUpdate = false; m.visible = false; scene.add(m);
    const ts = b.t0 + rnd() * (b.rise + .15), ang = rnd() * 6.28, spd = (1.2 + rnd() * 3.2) * Math.sqrt(b.th);
    chips.push({ b, m, ts, x: (rnd() - .5) * b.tw, y: (rnd() - .5) * b.dep * 2, vx: Math.cos(ang) * spd, vy: Math.sin(ang) * spd, vz: (1.5 + rnd() * 3.5) * Math.sqrt(b.th), r: b.th * (.012 + rnd() * .035), rx: rnd() * 6, ry: rnd() * 6, wv: (rnd() - .5) * 12 }); }
  const off = P.debug_off || []; if (off.includes('ground')) ground.visible = false; if (off.includes('blob')) beats.forEach(b => b.blob.userData.off = 1); if (off.includes('dust')) dust.length = 0; if (off.includes('chips')) chips.length = 0;
  S = { renderer, scene, camera, sun, ground, beats, dust, chips, basis, nrm, right, up, clip, THREE, N, sunDir };
}

const wobble = (t, a) => Math.exp(-5 * t) * Math.sin(t * 38) * a; // اهتزاز مخمّد عند الاستقرار

export async function frame(c, i, t) {
  const { THREE, core, W, H, track, params: P } = c, { renderer, scene, camera, beats, dust, chips, basis, sun, sunDir } = S;
  const pose = track.frames[Math.min(i, track.frames.length - 1)], plane0 = track.plane;
  core.applyPoseToCamera(THREE, camera, pose, W, H, track.fov_deg, track.plane.l * .02, track.plane.l * 40);
  const shakeAmp = (P.shake ?? 1) * 0.0025; let sx = 0, shx = 0;
  for (const b of beats) {
    const m = b.mesh, show = t >= b.t0 && t <= b.t3; m.visible = show; b.blob.visible = !b.blob.userData.off && t >= b.t0 && t <= b.t3 + .3;
    if (!show) { b.blob.material.opacity = 0; continue; }
    let z, vis = 1;
    if (t < b.t1) { const u = (t - b.t0) / b.rise; z = -b.th * 1.04 + b.th * 1.04 * E.outCubic(u) * 1.0 + b.th * .012 * Math.sin(u * 9) * (1 - u); }
    else if (t < b.t2) z = 0; else { const u = (t - b.t2) / b.sink; z = -b.th * 1.06 * E.inCubic(u); }
    const lean = (P.lean_deg ?? 18) * Math.PI / 180, wob = t >= b.t1 && t < b.t1 + 1.0 ? wobble(t - b.t1, shakeAmp * 14) : 0;
    const tilt = t < b.t1 ? (1 - E.outCubic((t - b.t0) / b.rise)) * .035 : 0;
    const jit = t >= b.t1 && t < b.t1 + .5 ? wobble(t - b.t1, b.th * .006) : 0;
    const M = new THREE.Matrix4().makeTranslation(b.wp[0], b.wp[1], z + jit).multiply(basis).multiply(new THREE.Matrix4().makeTranslation(0, b.th * 0, 0)).multiply(new THREE.Matrix4().makeRotationX(wob + tilt - lean * (t < b.t1 ? E.outCubic((t - b.t0) / b.rise) : (t < b.t2 ? 1 : 1 - E.inCubic((t - b.t2) / b.sink)))));
    // قاعدة النص = y∈[0,th] محلياً؛ المجسم مبنيّ بحيث الأسفل عند y=0
    m.matrix.copy(M); m.matrixWorldNeedsUpdate = true; m.updateMatrixWorld(true);
    const bu = t < b.t1 ? E.outCubic((t - b.t0) / b.rise) : (t < b.t2 ? 1 : 1 - E.inCubic((t - b.t2) / b.sink));
    b.blob.material.opacity = Math.max(0, Math.min(1, bu * 1.4)) * (P.contact_shadow ?? .6);
    b.blob.position.set(b.wp[0], b.wp[1], plane0.l * 5e-4); b.blob.position.addScaledVector(S.nrm, b.dep * 1.1);
    b.blob.matrixAutoUpdate = false; b.blob.matrix.makeBasis(S.right, S.nrm.clone().negate(), S.up).setPosition(b.blob.position); b.blob.matrixWorldNeedsUpdate = true;
    shx = Math.max(shx, 0);
    if (!b.shadowSet) { b.shadowSet = true; }
    sun.target.position.set(b.wp[0], b.wp[1], b.th * .4); sun.position.copy(sun.target.position).addScaledVector(sunDir, 120);
    const sc2 = Math.max(b.tw, b.th) * .9, scam = sun.shadow.camera; scam.left = -sc2; scam.right = sc2; scam.top = sc2; scam.bottom = -sc2; scam.near = 1; scam.far = 300; scam.updateProjectionMatrix();
  }
  /* غبار */
  for (const d of dust) {
    const tau = t - d.ts, b = d.b, alive = tau >= 0 && tau <= d.life && t <= b.t3 + 2.4;
    d.sprite.visible = alive; if (!alive) continue;
    const u = tau / d.life, drag = 1.6, k = (1 - Math.exp(-drag * tau)) / drag, turb = S.N.fbm(d.seed + tau * .6, d.seed * .3, 3) - .5;
    const lx = d.x + d.vx * k + turb * b.th * .5, ly = d.y + d.vy * k, lz = b.th * .02 + d.vz * k * .55 + u * b.th * .12;
    const wp = new THREE.Vector3().copy(S.right).multiplyScalar(lx).addScaledVector(S.nrm, ly).addScaledVector(S.up, lz); wp.x += b.wp[0]; wp.y += b.wp[1];
    d.sprite.position.copy(wp); const s = core.lerp(d.s0, d.s1, E.outCubic(u)); d.sprite.scale.set(s, s, 1);
    d.sprite.material.opacity = d.a * Math.min(1, tau / .12) * Math.pow(1 - u, 1.4); d.sprite.material.rotation += d.rot * .016;
  }
  for (const ch of chips) {
    const tau = t - ch.ts, g = 9.8 * .6, alive = tau >= 0 && tau < 2.2 && t <= ch.b.t3 + 1; ch.m.visible = alive; if (!alive) continue;
    const tl = Math.min(tau, 2 * ch.vz / g * 1.0 + .001); let lz = ch.vz * tau - .5 * g * tau * tau; const landed = lz < 0; if (landed) lz = 0;
    const kx = landed ? Math.min(tau, 2 * ch.vz / g) : tau; const lx = ch.x + ch.vx * kx * .6, ly = ch.y + ch.vy * kx * .6;
    const wp = new THREE.Vector3().copy(S.right).multiplyScalar(lx).addScaledVector(S.nrm, ly).addScaledVector(S.up, lz + ch.r); wp.x += ch.b.wp[0]; wp.y += ch.b.wp[1];
    const fade = tau > 1.6 ? Math.max(0, 1 - (tau - 1.6) / .6) : 1, rs = ch.r * fade;
    ch.m.matrix.compose(wp, new THREE.Quaternion().setFromEuler(new THREE.Euler(ch.rx + tau * ch.wv * (landed ? 0 : 1), ch.ry + tau * ch.wv * .7 * (landed ? 0 : 1), 0)), new THREE.Vector3(rs, rs * .8, rs * .9)); ch.m.matrixWorldNeedsUpdate = true;
  }
  renderer.render(S.scene, camera); c.g.drawImage(renderer.domElement, 0, 0, W, H);
}

export function meta(c) { return { recipe: 'stone_text', basis: { right: S.right.toArray(), nrm: S.nrm.toArray() }, beats: S.beats.map(b => ({ lines: b.lines, wp: b.wp, depth_units: b.dep, t0: b.t0, rise_end: b.t1, hold_end: b.t2, end: b.t3, width_units: b.tw, height_units: b.th })), settle_shake: 'damped sine ~38 rad/s', clip: 'ground plane h=0' }; }
