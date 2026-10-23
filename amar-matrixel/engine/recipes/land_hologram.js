/* ═══ B · LAND_HOLOGRAM_SEQUENCE ═══
   حدود أرض بنقاط قابلة للتعديل (corners في project.json) ← تتبع مستوي ← Neon Outline بتوهّج.
   قواعد الصدق (تُفرض بالكود):
   • المساحة تظهر فقط لو أدخلها المستخدم (params.area_m2) — لا تُحسب من الصورة أبداً.
   • المخطط المعماري يظهر فقط لو وُفّر (params.plan) ومعه approved.
   • المبنى Wireframe: يلزم building.approved صريح (true/false). false ← شارة «تصور مبدئي غير معتمد» ثابتة وظاهرة. */
import { E } from '../core.js';
export const output = 'alpha';
let S;
const CY = '#19d3ff', CORE = '#e8fbff';
export async function setup(c) {
  const { core, track, params: P } = c;
  if (!track) throw new Error('land_hologram يحتاج track.json');
  await core.loadFonts(['Tajawal', 'Tajawal Black']);
  if (P.area_m2 !== undefined && P.area_m2 !== null && !(typeof P.area_m2 === 'number' && P.area_m2 > 0)) throw new Error('area_m2 يجب أن تكون رقماً موجباً من بيانات المستخدم');
  if (P.building) { if (typeof P.building.approved !== 'boolean') throw new Error('building.approved مطلوب صراحةً (true=نموذج معتمد، false=تصور مبدئي يُوسم بوضوح)'); if (P.building.approved && !P.building.source) throw new Error('building.approved=true يتطلب building.source (اسم/مرجع النموذج المعتمد)'); }
  if (P.plan && !P.plan.approved) throw new Error('plan.approved مطلوب = true للمخطط المعماري');
  const K = core.intrinsics(c.W, c.H, track.fov_deg), plane = track.plane;
  // نص المساحة على كانفس (يُلصق على المستوى بمنظور صحيح)
  let areaCv = null;
  if (P.area_m2) {
    const txt = (P.numerals === 'arabic' ? String(P.area_m2).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]) : String(P.area_m2)) + ' م²';
    const tc = core.textCanvas([txt], { font: 'Tajawal Black', px: 200, pad: 40, color: '#fff' }), cv = document.createElement('canvas'); cv.width = tc.w + 120; cv.height = tc.h + 120; const q = cv.getContext('2d');
    q.shadowColor = CY; for (const [b, a] of [[60, .7], [30, .9], [14, 1]]) { q.shadowBlur = b; q.globalAlpha = a; q.drawImage(tc.canvas, 60, 60); } q.shadowBlur = 0; q.globalAlpha = 1; q.drawImage(tc.canvas, 60, 60);
    areaCv = { cv, aspect: cv.width / cv.height, tcw: tc.w };
    if (P.area_source) { const s2 = core.textCanvas([P.area_source], { font: 'Tajawal', px: 110, pad: 20, color: '#c8f6ff' }); areaCv.sub = s2.canvas; }
  }
  S = { K, plane, areaCv };
}
const T = { outline: [.15, 1.35], fill: [.9, 1.8], area: [1.7, 2.3], plan: [2.4, 3.3], build: [3.4, 5.0], badge: [.4, .9] };
export async function frame(c, i, t) {
  const { THREE, core, g, W, H, track, params: P } = c, { K, plane } = S, pose = track.frames[Math.min(i, track.frames.length - 1)];
  const tm = { ...T, ...(P.timing || {}) }, prog = ([a, b], e = 'inOutCubic') => core.ease(e, core.clamp((t - a) / (b - a)));
  const pp = (u, v, h = 0) => core.planePoint(pose, K, plane, u, v, h), pt = (u, v, h = 0) => { const o = pp(u, v, h); return { x: o.x, y: o.y }; };
  const quad = [pt(0, 0), pt(1, 0), pt(1, 1), pt(0, 1)], lw = Math.max(2.5, Math.min(W, H) * .0042) * (P.line_scale || 1);
  const log = (kind, r) => c.log.push({ i, kind, r: r.map(v => +v.toFixed(2)) });
  // 1) تعبئة الأرض + شبكة مسح
  const fp = prog(tm.fill, 'outCubic');
  if (fp > 0) {
    g.save(); g.beginPath(); quad.forEach((p, k) => (k ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); g.closePath(); g.clip();
    g.globalAlpha = .09 * fp; g.fillStyle = CY; g.fill();
    g.globalCompositeOperation = 'lighter'; g.strokeStyle = CY; g.lineWidth = Math.max(1, lw * .3); const n = P.grid || 10, sweep = (t * .55) % 1;
    for (let k = 1; k < n; k++) { const a = k / n, ph = Math.abs(((a - sweep + 1) % 1) - .5); g.globalAlpha = (.10 + .22 * Math.max(0, 1 - ph * 3)) * fp;
      let A = pt(a, 0), B = pt(a, 1); g.beginPath(); g.moveTo(A.x, A.y); g.lineTo(B.x, B.y); g.stroke(); A = pt(0, a); B = pt(1, a); g.beginPath(); g.moveTo(A.x, A.y); g.lineTo(B.x, B.y); g.stroke(); }
    g.restore();
  }
  // 2) Neon Outline يُرسم تدريجياً حول المحيط + رأس مضيء
  const op = prog(tm.outline), part = core.partialPath(quad, true, op);
  if (op > 0) { core.neonLine(g, part.pts, { color: CY, core: CORE, width: lw, closed: op >= 1, glow: 1.25 }); if (op < 1) core.neonHead(g, part.head, { color: CY, r: lw * 3.2 });
    if (op >= 1) quad.forEach((p, k) => { const q2 = quad[(k + 1) % 4], q0 = quad[(k + 3) % 4], L = lw * 7, d1 = Math.hypot(q2.x - p.x, q2.y - p.y), d0 = Math.hypot(q0.x - p.x, q0.y - p.y);
      core.neonLine(g, [{ x: p.x + (q0.x - p.x) / d0 * L, y: p.y + (q0.y - p.y) / d0 * L }, p, { x: p.x + (q2.x - p.x) / d1 * L, y: p.y + (q2.y - p.y) / d1 * L }], { color: '#7ff0ff', core: '#fff', width: lw * 1.5, glow: 1.5, alpha: .9 }); }); }
  // 3) المساحة (فقط من بيانات المستخدم) — نص على الأرض بمنظور صحيح
  if (S.areaCv) { const ap = prog(tm.area, 'outCubic'); if (ap > 0) {
    const asp = S.areaCv.aspect, wU = .62, hU = wU * asp ** -1 * (plane.w / plane.l), rect = [.5 - wU / 2, .5 - hU / 2 - .02, .5 + wU / 2, .5 + hU / 2 - .02];
    core.drawOnPlane(g, S.areaCv.cv, rect, pt, { alpha: ap * (.88 + .12 * Math.sin(t * 7)), comp: 'lighter', grid: 14 });
    if (S.areaCv.sub) core.drawOnPlane(g, S.areaCv.sub, [.5 - .2, rect[3] + .01, .5 + .2, rect[3] + .01 + .2 * S.areaCv.sub.height / S.areaCv.sub.width * (plane.w / plane.l)], pt, { alpha: ap * .8, comp: 'lighter', grid: 8 });
    const xs = rect.length && [pt(rect[0], rect[1]), pt(rect[2], rect[1]), pt(rect[2], rect[3]), pt(rect[0], rect[3])]; log('area', [Math.min(...xs.map(p => p.x)), Math.min(...xs.map(p => p.y)), Math.max(...xs.map(p => p.x)) - Math.min(...xs.map(p => p.x)), Math.max(...xs.map(p => p.y)) - Math.min(...xs.map(p => p.y))]); } }
  // 4) المخطط المعماري المعتمد (بصمة المبنى على الأرض)
  if (P.plan) { const pr = prog(tm.plan); for (const fpz of P.plan.footprints || []) { const pts = fpz.poly.map(([u, v]) => pt(u, v)); const part2 = core.partialPath(pts, true, pr); if (pr > 0) { core.neonLine(g, part2.pts, { color: '#5cffb0', core: '#eafff4', width: lw * .8, closed: pr >= 1, glow: 1 });
      if (pr >= 1) { g.save(); g.beginPath(); pts.forEach((p, k) => (k ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); g.closePath(); g.globalAlpha = .12; g.fillStyle = '#5cffb0'; g.fill(); g.restore(); } } } }
  // 5) Wireframe Building
  if (P.building) {
    const bp = prog(tm.build, 'outCubic'), metric = plane.units === 'meters', hOf = b => (metric ? (b.floors || 1) * (b.floor_h || 3) : (b.floors || 1) * .04 * plane.l);
    if (bp > 0) { const boxes = [...P.building.boxes].sort((a, b) => (pp(a.u, a.v).z < pp(b.u, b.v).z ? 1 : -1)); boxes.forEach((b, k) => {
      const lp = core.clamp((bp * boxes.length - k * .7) / 1.4), hh = hOf(b) * E.outCubic(lp); if (lp <= 0) return; const u0 = b.u - b.du / 2, u1 = b.u + b.du / 2, v0 = b.v - b.dv / 2, v1 = b.v + b.dv / 2;
      const B = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]].map(([u, v]) => pt(u, v)), Tp = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]].map(([u, v]) => pt(u, v, hh));
      const faces = [[0, 1], [1, 2], [2, 3], [3, 0]].map(([a, b2]) => { const mx = (B[a].x + B[b2].x) / 2, my = (B[a].y + B[b2].y) / 2, cx = (B[0].x + B[2].x) / 2, cy = (B[0].y + B[2].y) / 2; return { a, b: b2, front: (mx - cx) * 0 + (my - cy) > 0 }; });
      g.save(); g.globalCompositeOperation = 'lighter';
      faces.forEach(f => { g.beginPath(); [B[f.a], B[f.b], Tp[f.b], Tp[f.a]].forEach((p, q) => (q ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); g.closePath(); g.globalAlpha = f.front ? .10 : .05; g.fillStyle = CY; g.fill(); });
      g.beginPath(); Tp.forEach((p, q) => (q ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); g.closePath(); g.globalAlpha = .12; g.fill(); g.restore();
      const nF = Math.max(1, b.floors || 1);
      for (let k2 = 1; k2 < nF; k2++) { const z = hh * k2 / nF; core.neonLine(g, [[u0, v0], [u1, v0], [u1, v1], [u0, v1]].map(([u, v]) => pt(u, v, z)), { color: CY, core: '#bff6ff', width: lw * .45, closed: true, glow: .5, alpha: .55 * lp }); }
      for (let a2 = 0; a2 < 4; a2++) core.neonLine(g, [B[a2], Tp[a2]], { color: CY, core: CORE, width: lw * .8, glow: .9, alpha: faces.some(f => f.front && (f.a === a2 || f.b === a2)) ? 1 : .45 });
      core.neonLine(g, B, { color: CY, core: CORE, width: lw * .8, closed: true, glow: .8 }); core.neonLine(g, Tp, { color: CY, core: CORE, width: lw, closed: true, glow: 1.1 }); }); }
    // شارة الحالة: معتمد/تصوري (إلزامية الظهور)
    const bad = P.building.approved ? null : 'تصور مبدئي — غير معتمد';
    const badgeTxt = bad || ('نموذج معتمد: ' + P.building.source), bg = prog(tm.badge, 'outCubic');
    if (bg > 0) { const sz = Math.min(W, H) * .034, r = core.hudCard(g, { x: W / 2, y: H * .095 + (1 - bg) * 12, text: badgeTxt, size: sz, color: bad ? '#ffb347' : '#5cffb0', bg: 'rgba(10,14,20,.78)', alpha: bg }); log('badge', [r.x, r.y, r.w, r.h]); }
  }
}
export function meta(c) { return { recipe: 'land_hologram', area_shown: !!c.params.area_m2, area_source: c.params.area_source || null, plan_shown: !!c.params.plan, building: c.params.building ? { approved: c.params.building.approved, source: c.params.building.source || null } : null, timing: { ...T, ...(c.params.timing || {}) } }; }
