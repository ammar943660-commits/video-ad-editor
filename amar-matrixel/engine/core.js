/* ═══ core.js — مكتبة مشتركة لوصفات AMAR Matrixel ═══
   رياضيات · كاميرا من pose التتبع · نص عربي · تتبّع كنتور للبثق 3D · نيون Glow
   كل شيء حتمي (deterministic): الفريم t يعتمد على t فقط. */

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smoothstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const E = {
  linear: t => t,
  inCubic: t => t * t * t,
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inOutCubic: t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  outExpo: t => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
  outBack: (t, s = 1.4) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
  /** cubic-bezier(x1,y1,x2,y2) مثل CSS — للتسارع/التباطؤ المحدد بملف الإخراج */
  bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = t => ((ax * t + bx) * t + cx) * t, sy = t => ((ay * t + by) * t + cy) * t, dx = t => (3 * ax * t + 2 * bx) * t + cx;
    return x => { x = clamp(x); let t = x; for (let i = 0; i < 8; i++) { const e = sx(t) - x; if (Math.abs(e) < 1e-6) break; const d = dx(t); if (Math.abs(d) < 1e-6) break; t -= e / d; } return sy(clamp(t)); };
  },
};
export const ease = (name, t) => {
  if (Array.isArray(name)) return E.bezier(...name)(t);
  return (E[name] || E.linear)(t);
};

export function rng(seed) { let a = seed >>> 0; return () => { a += 0x6D2B79F5; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

/** ضوضاء قيمة 2D حتمية */
export function makeNoise(seed = 1) {
  const r = rng(seed), P = new Float32Array(256 * 256); for (let i = 0; i < P.length; i++) P[i] = r();
  const g = (x, y) => P[((y & 255) << 8) | (x & 255)];
  const n2 = (x, y) => { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    return lerp(lerp(g(xi, yi), g(xi + 1, yi), u), lerp(g(xi, yi + 1), g(xi + 1, yi + 1), u), v); };
  const fbm = (x, y, o = 4) => { let s = 0, a = .5; for (let i = 0; i < o; i++) { s += a * n2(x, y); x *= 2.03; y *= 2.03; a *= .5; } return s; };
  return { n2, fbm };
}

/* ───────────────── كاميرا من pose ─────────────────
   pose = {R:[9 row-major], t:[3]}  (OpenCV: X_c = R·X_w + t, +Z أمام، +Y تحت)
   عالم المستوى (three): x يمين · y للأمام/بعيد (فوق الصورة) · z ارتفاع فوق المستوى.
   العلاقة: X_w(cv) = diag(1,-1,-1)·P3  ← دوران صحيح (180° حول x) فلا انعكاس بالنص. */
export function intrinsics(W, H, fovDeg) { const f = (H / 2) / Math.tan(fovDeg * Math.PI / 360); return { fx: f, fy: f, cx: W / 2, cy: H / 2 }; }

export function projectP3(pose, K, p) {
  const [x, y, h] = p, Xw = [x, -y, -h], R = pose.R, t = pose.t;
  const Xc = [R[0] * Xw[0] + R[1] * Xw[1] + R[2] * Xw[2] + t[0], R[3] * Xw[0] + R[4] * Xw[1] + R[5] * Xw[2] + t[1], R[6] * Xw[0] + R[7] * Xw[1] + R[8] * Xw[2] + t[2]];
  return { x: K.fx * Xc[0] / Xc[2] + K.cx, y: K.fy * Xc[1] / Xc[2] + K.cy, z: Xc[2] };
}

export function applyPoseToCamera(THREE, camera, pose, W, H, fovDeg, near = .01, far = 1000) {
  const R = pose.R, t = pose.t;
  // R3 = R · diag(1,-1,-1)  (أعمدة y,z مقلوبة)
  const R3 = [R[0], -R[1], -R[2], R[3], -R[4], -R[5], R[6], -R[7], -R[8]];
  // view_cv = [R3 t] ثم نقلب y,z للتحويل لقاعدة three (تنظر نحو -Z و Y فوق)
  const v = new THREE.Matrix4().set(
    R3[0], R3[1], R3[2], t[0],
    -R3[3], -R3[4], -R3[5], -t[1],
    -R3[6], -R3[7], -R3[8], -t[2],
    0, 0, 0, 1);
  camera.matrixAutoUpdate = false;
  camera.matrix.copy(v).invert(); camera.matrixWorld.copy(camera.matrix); camera.matrixWorldInverse.copy(v);
  camera.matrixWorldNeedsUpdate = false;
  camera.fov = fovDeg; camera.aspect = W / H; camera.near = near; camera.far = far; camera.updateProjectionMatrix();
}

/* ───────────────── نص عربي ───────────────── */
export async function loadFonts(list) {
  const fonts = { 'Tajawal Black': '/fonts/Tajawal-Black.ttf', 'Tajawal': '/fonts/Tajawal-Bold.ttf', 'Cairo': '/fonts/Cairo-VF.ttf', 'Lalezar': '/fonts/Lalezar-Regular.ttf', 'Noto Kufi Arabic': '/fonts/NotoKufiArabic-VF.ttf', 'IBM Plex Sans Arabic': '/fonts/IBMPlexSansArabic-Bold.ttf', 'Inter': '/fonts/Inter-VF.ttf', 'Aref Ruqaa': '/fonts/ArefRuqaa-Bold.ttf' };
  for (const n of list) { if (!fonts[n]) continue; const f = new FontFace(n, `url(${fonts[n]})`); await f.load(); document.fonts.add(f); }
}

/** يرسم أسطر نص (rtl) على كانفس ويُرجع {canvas, w, h, lines} — shaping عربي من المتصفح */
export function textCanvas(lines, { font = 'Tajawal Black', weight = 900, px = 220, lineGap = 1.12, pad = 24, color = '#fff', rtl = true, fit = 0 } = {}) {
  const m = document.createElement('canvas').getContext('2d');
  const setf = s => { m.font = `${weight} ${s}px "${font}"`; m.direction = rtl ? 'rtl' : 'ltr'; };
  setf(px);
  let widths = lines.map(l => m.measureText(l).width);
  if (fit && Math.max(...widths) > fit) { px = px * fit / Math.max(...widths); setf(px); widths = lines.map(l => m.measureText(l).width); }
  const W = Math.ceil(Math.max(...widths) + pad * 2), lh = px * lineGap, H = Math.ceil(lh * lines.length + pad * 2);
  const c = document.createElement('canvas'); c.width = W; c.height = H; const g = c.getContext('2d');
  g.font = m.font; g.direction = rtl ? 'rtl' : 'ltr'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = color;
  lines.forEach((l, i) => g.fillText(l, W / 2, pad + lh * (i + .5)));
  return { canvas: c, w: W, h: H, px, lines };
}

/* ───────────────── كنتور من قناع (Marching Squares) ─────────────────
   يحوّل ألفا النص إلى مضلعات (خارجية + ثقوب) لبثق 3D حقيقي (ExtrudeGeometry) */
export function traceMask(canvas, { threshold = 128, step = 1, simplify = .6 } = {}) {
  const w = canvas.width, h = canvas.height, d = canvas.getContext('2d').getImageData(0, 0, w, h).data;
  const gw = Math.ceil(w / step) + 1, gh = Math.ceil(h / step) + 1, F = new Float32Array(gw * gh);
  for (let y = 0; y < gh; y++) for (let x = 0; x < gw; x++) { const px = Math.min(w - 1, x * step), py = Math.min(h - 1, y * step); F[y * gw + x] = d[(py * w + px) * 4 + 3]; }
  // حدود الصورة صفر حتى تُغلق الكنتورات
  for (let x = 0; x < gw; x++) { F[x] = 0; F[(gh - 1) * gw + x] = 0; } for (let y = 0; y < gh; y++) { F[y * gw] = 0; F[y * gw + gw - 1] = 0; }
  const key = (t, x, y) => t + x + ',' + y, pts = new Map(), adj = new Map();
  const vert = (k, x, y) => { if (!pts.has(k)) pts.set(k, [x, y]); return k; };
  const edgeV = (cx, cy, e) => { // e: 0 أعلى،1 يمين،2 أسفل،3 يسار
    const v = (x, y) => F[y * gw + x];
    if (e === 0) { const a = v(cx, cy), b = v(cx + 1, cy), t = (threshold - a) / (b - a); return vert(key('h', cx, cy), (cx + t) * step, cy * step); }
    if (e === 2) { const a = v(cx, cy + 1), b = v(cx + 1, cy + 1), t = (threshold - a) / (b - a); return vert(key('h', cx, cy + 1), (cx + t) * step, (cy + 1) * step); }
    if (e === 3) { const a = v(cx, cy), b = v(cx, cy + 1), t = (threshold - a) / (b - a); return vert(key('v', cx, cy), cx * step, (cy + t) * step); }
    const a = v(cx + 1, cy), b = v(cx + 1, cy + 1), t = (threshold - a) / (b - a); return vert(key('v', cx + 1, cy), (cx + 1) * step, (cy + t) * step);
  };
  const link = (a, b) => { (adj.get(a) || adj.set(a, []).get(a)).push(b); (adj.get(b) || adj.set(b, []).get(b)).push(a); };
  const T = [[], [[3, 0]], [[0, 1]], [[3, 1]], [[1, 2]], 'S5', [[0, 2]], [[3, 2]], [[2, 3]], [[0, 2]], 'S10', [[1, 2]], [[3, 1]], [[0, 1]], [[3, 0]], []];
  for (let cy = 0; cy < gh - 1; cy++) for (let cx = 0; cx < gw - 1; cx++) {
    const a = F[cy * gw + cx] >= threshold ? 1 : 0, b = F[cy * gw + cx + 1] >= threshold ? 1 : 0, c = F[(cy + 1) * gw + cx + 1] >= threshold ? 1 : 0, dd = F[(cy + 1) * gw + cx] >= threshold ? 1 : 0;
    const idx = a | (b << 1) | (c << 2) | (dd << 3); let segs = T[idx];
    if (segs === 'S5') { const m = (F[cy * gw + cx] + F[cy * gw + cx + 1] + F[(cy + 1) * gw + cx + 1] + F[(cy + 1) * gw + cx]) / 4 >= threshold; segs = m ? [[0, 1], [2, 3]] : [[3, 0], [1, 2]]; }
    if (segs === 'S10') { const m = (F[cy * gw + cx] + F[cy * gw + cx + 1] + F[(cy + 1) * gw + cx + 1] + F[(cy + 1) * gw + cx]) / 4 >= threshold; segs = m ? [[3, 0], [1, 2]] : [[0, 1], [2, 3]]; }
    for (const [e1, e2] of segs) link(edgeV(cx, cy, e1), edgeV(cx, cy, e2));
  }
  const used = new Set(), loops = [];
  for (const [start] of adj) {
    if (used.has(start)) continue;
    const loop = []; let prev = null, cur = start, guard = 0;
    while (cur && !used.has(cur) && guard++ < 1e6) { used.add(cur); loop.push(pts.get(cur)); const nb = adj.get(cur); const nx = nb.find(n => n !== prev && !used.has(n)); prev = cur; cur = nx; }
    if (loop.length >= 4) loops.push(loop);
  }
  const dp = (P, eps) => { // Douglas-Peucker لحلقة مغلقة
    if (P.length < 8) return P; const n = P.length; let far = 0, fd = 0; for (let i = 1; i < n; i++) { const dd = Math.hypot(P[i][0] - P[0][0], P[i][1] - P[0][1]); if (dd > fd) { fd = dd; far = i; } }
    const rec = (a, b) => { // a..b شامل
      let md = 0, mi = -1; const [x1, y1] = a === b ? P[a] : P[a], [x2, y2] = P[b % n]; const L = Math.hypot(x2 - x1, y2 - y1) || 1e-9;
      for (let i = a + 1; i < b; i++) { const dd = Math.abs((x2 - x1) * (y1 - P[i][1]) - (x1 - P[i][0]) * (y2 - y1)) / L; if (dd > md) { md = dd; mi = i; } }
      if (md > eps) return [...rec(a, mi).slice(0, -1), ...rec(mi, b)]; return [P[a], P[b % n]]; };
    return [...rec(0, far).slice(0, -1), ...rec(far, n)].slice(0, -1);
  };
  const polys = loops.map(l => dp(l, simplify)).filter(l => l.length >= 3);
  const area = P => { let s = 0; for (let i = 0; i < P.length; i++) { const [x1, y1] = P[i], [x2, y2] = P[(i + 1) % P.length]; s += x1 * y2 - x2 * y1; } return s / 2; };
  const inside = (p, P) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const [xi, yi] = P[i], [xj, yj] = P[j]; if ((yi > p[1]) !== (yj > p[1]) && p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi) c = !c; } return c; };
  const items = polys.map(P => ({ P, a: Math.abs(area(P)) })).filter(o => o.a > 3).sort((x, y) => y.a - x.a);
  items.forEach(o => { o.depth = items.filter(q => q !== o && q.a > o.a && inside(o.P[0], q.P)).length; });
  const outers = items.filter(o => o.depth % 2 === 0), holes = items.filter(o => o.depth % 2 === 1);
  return outers.map(o => ({ outer: o.P, holes: holes.filter(hh => inside(hh.P[0], o.P)).map(hh => hh.P) }));
}

/* ───────────────── نيون Glow على كانفس 2D ───────────────── */
export function polyPath(g, pts, closed) { g.beginPath(); pts.forEach((p, i) => (i ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); if (closed) g.closePath(); }

/** يقتطع جزءاً من مسار (0..prog من الطول الكلي) */
export function partialPath(pts, closed, prog) {
  const P = closed ? [...pts, pts[0]] : pts; let tot = 0; const seg = [];
  for (let i = 0; i < P.length - 1; i++) { const l = Math.hypot(P[i + 1].x - P[i].x, P[i + 1].y - P[i].y); seg.push(l); tot += l; }
  let rem = tot * clamp(prog), out = [P[0]];
  for (let i = 0; i < seg.length; i++) { if (rem >= seg[i]) { out.push(P[i + 1]); rem -= seg[i]; } else { const t = rem / seg[i]; out.push({ x: lerp(P[i].x, P[i + 1].x, t), y: lerp(P[i].y, P[i + 1].y, t) }); rem = 0; break; } }
  return { pts: out, head: out[out.length - 1], total: tot };
}

/** خط نيون: طبقات عريضة خافتة (توهّج) + نواة بيضاء — كل شيء additive */
export function neonLine(g, pts, { color = '#19d3ff', core = '#e8fbff', width = 4, glow = 1, closed = false, alpha = 1 } = {}) {
  if (pts.length < 2) return;
  g.save(); g.lineCap = 'round'; g.lineJoin = 'round'; g.globalCompositeOperation = 'lighter';
  const layers = [[width * 9, .05], [width * 5, .09], [width * 3, .16], [width * 1.7, .35]];
  for (const [w, a] of layers) { g.globalAlpha = clamp(a * glow * alpha); g.strokeStyle = color; g.lineWidth = w; polyPath(g, pts, closed); g.stroke(); }
  g.globalAlpha = clamp(alpha); g.strokeStyle = color; g.lineWidth = width; polyPath(g, pts, closed); g.stroke();
  g.globalAlpha = clamp(alpha * .95); g.strokeStyle = core; g.lineWidth = Math.max(1, width * .38); polyPath(g, pts, closed); g.stroke();
  g.restore();
}

/** مقبض مضيء يتحرك مع رأس الخط */
export function neonHead(g, p, { color = '#19d3ff', r = 10, alpha = 1 } = {}) {
  g.save(); g.globalCompositeOperation = 'lighter';
  const gr = g.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 3); gr.addColorStop(0, `rgba(255,255,255,${alpha})`); gr.addColorStop(.25, color); gr.addColorStop(1, 'rgba(0,0,0,0)');
  g.globalAlpha = alpha; g.fillStyle = gr; g.beginPath(); g.arc(p.x, p.y, r * 3, 0, 7); g.fill(); g.restore();
}

/** قياس بطاقة HUD بلا رسم */
export function hudMeasure(g, { text, sub = '', font = 'Tajawal', size = 34 }) { g.save(); g.font = `800 ${size}px "${font}"`; g.direction = 'rtl'; const tw = g.measureText(text).width; g.font = `600 ${size * .62}px "${font}"`; const sw = sub ? g.measureText(sub).width : 0; g.restore(); return { w: Math.max(tw, sw) + size * 1.1, h: size * (sub ? 2.15 : 1.5) }; }

/** مربع نص عربي (بطاقة معلومات HUD) — يُرجع المستطيل المرسوم */
export function hudCard(g, { x, y, text, sub = '', font = 'Tajawal', size = 34, color = '#19d3ff', bg = 'rgba(4,20,28,.72)', anchor = 'center', alpha = 1, scale = 1, link = null }) {
  g.save(); g.globalAlpha = alpha; g.font = `800 ${size}px "${font}"`; g.direction = 'rtl';
  const tw = g.measureText(text).width; g.font = `600 ${size * .62}px "${font}"`; const sw = sub ? g.measureText(sub).width : 0;
  const w = Math.max(tw, sw) + size * 1.1, h = size * (sub ? 2.15 : 1.5), x0 = x - w / 2, y0 = y - h / 2;
  g.translate(x, y); g.scale(scale, scale); g.translate(-x, -y);
  if (link) { g.globalCompositeOperation = 'lighter'; g.strokeStyle = color; g.globalAlpha = alpha * .8; g.lineWidth = 2; g.beginPath(); g.moveTo(x, y + h / 2); g.lineTo(link.x, link.y); g.stroke(); g.globalCompositeOperation = 'source-over'; g.globalAlpha = alpha; }
  g.fillStyle = bg; g.strokeStyle = color; g.lineWidth = 2; const r = size * .22;
  g.beginPath(); g.roundRect(x0, y0, w, h, r); g.fill(); g.stroke();
  g.fillStyle = color; g.fillRect(x0 + w - 5, y0 + h * .2, 3, h * .6);
  g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#eafcff'; g.font = `800 ${size}px "${font}"`;
  g.fillText(text, x, y - (sub ? size * .38 : 0));
  if (sub) { g.fillStyle = color; g.font = `600 ${size * .62}px "${font}"`; g.fillText(sub, x, y + size * .58); }
  g.restore(); return { x: x0, y: y0, w, h };
}

export function aspectSize(aspect, longSide = 1920) {
  const m = { '9:16': [1080, 1920], '4:5': [1080, 1350], '16:9': [1920, 1080] }[aspect]; if (!m) throw new Error('نسبة غير مدعومة: ' + aspect);
  const s = longSide / 1920; return [Math.round(m[0] * s), Math.round(m[1] * s)];
}

/** pose (OpenCV) لكاميرا three داخل مشهد z-up. A: مصفوفة 3×3 row-major من إحداثيات المشهد إلى P3 (افتراضي: هوية) */
export function poseFromCamera(THREE, camera, A = [1, 0, 0, 0, 1, 0, 0, 0, 1], origin = [0, 0, 0]) {
  camera.updateMatrixWorld(true); const e = camera.matrixWorldInverse.elements, r = (i, j) => e[j * 4 + i];
  const Rs = [r(0, 0), r(0, 1), r(0, 2), -r(1, 0), -r(1, 1), -r(1, 2), -r(2, 0), -r(2, 1), -r(2, 2)], t = [r(0, 3), -r(1, 3), -r(2, 3)];
  const At = [A[0], A[3], A[6], A[1], A[4], A[7], A[2], A[5], A[8]];
  const mul = (X, Y) => { const o = new Array(9); for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) o[i * 3 + j] = X[i * 3] * Y[j] + X[i * 3 + 1] * Y[3 + j] + X[i * 3 + 2] * Y[6 + j]; return o; };
  const t2 = [t[0] + Rs[0] * origin[0] + Rs[1] * origin[1] + Rs[2] * origin[2], t[1] + Rs[3] * origin[0] + Rs[4] * origin[1] + Rs[5] * origin[2], t[2] + Rs[6] * origin[0] + Rs[7] * origin[1] + Rs[8] * origin[2]]; // origin: مركز المستوى بإحداثيات المشهد
  return { R: mul(mul(Rs, At), [1, 0, 0, 0, -1, 0, 0, 0, -1]), t: t2 };
}

/** إسقاط نقطة مستوى (u,v ∈ 0..1 ، v من الأعلى ، h ارتفاع بوحدات المستوى) إلى بكسلات الصورة */
export function planePoint(pose, K, plane, u, v, h = 0) { return projectP3(pose, K, [(u - .5) * plane.w, (.5 - v) * plane.l, h]); }

/** يرسم كانفس (نص/شعار) «ملصوقاً» على المستوى بتحويل منظوري (شبكة مثلثات affine) — نص على الأرض بمنظور صحيح.
    rect = [u0,v0,u1,v1] مكان الكانفس على المستوى. */
export function drawOnPlane(g, src, rect, proj, { grid = 14, alpha = 1, comp = 'source-over' } = {}) {
  const [u0, v0, u1, v1] = rect, sw = src.width, sh = src.height; g.save(); g.globalAlpha = alpha; g.globalCompositeOperation = comp;
  const P = (i, j) => proj(u0 + (u1 - u0) * i / grid, v0 + (v1 - v0) * j / grid);
  const tri = (a, b, c, sa, sb, sc) => { // affine من مثلث المصدر إلى الهدف
    const d = (sa[0] * (sb[1] - sc[1]) + sb[0] * (sc[1] - sa[1]) + sc[0] * (sa[1] - sb[1])); if (Math.abs(d) < 1e-9) return;
    const m11 = (a.x * (sb[1] - sc[1]) + b.x * (sc[1] - sa[1]) + c.x * (sa[1] - sb[1])) / d, m12 = (a.y * (sb[1] - sc[1]) + b.y * (sc[1] - sa[1]) + c.y * (sa[1] - sb[1])) / d,
      m21 = (a.x * (sc[0] - sb[0]) + b.x * (sa[0] - sc[0]) + c.x * (sb[0] - sa[0])) / d, m22 = (a.y * (sc[0] - sb[0]) + b.y * (sa[0] - sc[0]) + c.y * (sb[0] - sa[0])) / d,
      dx = (a.x * (sb[0] * sc[1] - sc[0] * sb[1]) + b.x * (sc[0] * sa[1] - sa[0] * sc[1]) + c.x * (sa[0] * sb[1] - sb[0] * sa[1])) / d, dy = (a.y * (sb[0] * sc[1] - sc[0] * sb[1]) + b.y * (sc[0] * sa[1] - sa[0] * sc[1]) + c.y * (sa[0] * sb[1] - sb[0] * sa[1])) / d;
    g.save(); g.beginPath(); const cx = (a.x + b.x + c.x) / 3, cy = (a.y + b.y + c.y) / 3, ex = (p) => ({ x: p.x + Math.sign(p.x - cx) * .6, y: p.y + Math.sign(p.y - cy) * .6 });
    const A = ex(a), B = ex(b), C = ex(c); g.moveTo(A.x, A.y); g.lineTo(B.x, B.y); g.lineTo(C.x, C.y); g.closePath(); g.clip(); g.transform(m11, m12, m21, m22, dx, dy); g.drawImage(src, 0, 0); g.restore(); };
  for (let j = 0; j < grid; j++) for (let i = 0; i < grid; i++) {
    const p00 = P(i, j), p10 = P(i + 1, j), p01 = P(i, j + 1), p11 = P(i + 1, j + 1), s = (x, y) => [sw * x / grid, sh * y / grid];
    tri(p00, p10, p01, s(i, j), s(i + 1, j), s(i, j + 1)); tri(p10, p11, p01, s(i + 1, j), s(i + 1, j + 1), s(i, j + 1));
  }
  g.restore();
}
