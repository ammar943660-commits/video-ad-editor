/* ═══ C · DIGITAL_BUILDING_OUTLINE ═══
   مسارات مضيئة على واجهة المبنى. الحواف تُكتشف مرة واحدة في فضاء الواجهة المعدَّل (tools/detect_edges.py → edges.json)
   ثم تُتبَّع بـ pose الواجهة، فلا تهتز ولا تنزلق. بطاقات معلومات عربية مثبّتة على إحداثيات الواجهة.
   حد صريح: واجهة مستوية واحدة. المباني متعددة الأسطح تحتاج تتبع سطح لكل واجهة (planes[]). */
import { E } from '../core.js';
export const output = 'alpha';
let S;
export async function setup(c) {
  const { core, track, project } = c; if (!track) throw new Error('building_outline يحتاج track.json');
  await core.loadFonts(['Tajawal', 'Tajawal Black']);
  const edges = await (await fetch('/proj/edges.json')).json(), rnd = core.rng(c.params.seed || 3);
  const segs = edges.segments.map(s => ({ ...s, len: Math.hypot((s.u1 - s.u0) * track.plane.w, (s.v1 - s.v0) * track.plane.l) }));
  const P = c.params, T = { outline: [.1, 1.0], major: [.8, 2.4], detail: [1.5, 3.1], ...(P.timing || {}) };
  segs.forEach((s, k) => { const [a, b] = T[s.kind] || T.detail, sweep = 1 - (s.v0 + s.v1) / 2; // يصعد من الأسفل للأعلى
    s.t0 = s.kind === 'outline' ? a + (s.id % 4) * .22 : a + (b - a) * (.7 * sweep + .3 * rnd()); s.dur = s.kind === 'outline' ? .55 : .35 + Math.min(.5, s.len / track.plane.l * .5); s.ph = rnd() * 6.28; });
  S = { segs, K: core.intrinsics(c.W, c.H, track.fov_deg), cards: (P.cards || []).map((cd, k) => ({ at: 2.6 + k * .35, color: '#19d3ff', ...cd, k })) };
}
export async function frame(c, i, t) {
  const { core, g, W, H, track, params: P } = c, { K, segs, cards } = S, plane = track.plane, pose = track.frames[Math.min(i, track.frames.length - 1)];
  const pt = (u, v, h = 0) => { const o = core.planePoint(pose, K, plane, u, v, h); return { x: o.x, y: o.y }; }, lw = Math.max(2.2, Math.min(W, H) * .0036) * (P.line_scale || 1);
  const col = P.color || '#19d3ff', hi = P.core || '#d9fbff';
  // وهج خافت للواجهة
  const fp = core.clamp((t - .2) / 1.2) * .10; if (fp > 0) { const q = [pt(0, 0), pt(1, 0), pt(1, 1), pt(0, 1)]; g.save(); g.beginPath(); q.forEach((p, k) => (k ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y))); g.closePath(); g.globalAlpha = fp; g.fillStyle = col; g.fill(); g.restore(); }
  for (const s of segs) {
    const p = core.clamp((t - s.t0) / s.dur); if (p <= 0) continue; const e = E.inOutCubic(p), A = pt(s.u0, s.v0), B = pt(s.u1, s.v1), head = { x: core.lerp(A.x, B.x, e), y: core.lerp(A.y, B.y, e) };
    const pulse = .86 + .14 * Math.sin(t * 5 + s.ph), run = ((t * .5 + s.ph / 6.28) % 1), isMajor = s.kind !== 'detail';
    const w = s.kind === 'outline' ? lw * 1.35 : s.kind === 'major' ? lw : lw * .62;
    core.neonLine(g, [A, head], { color: col, core: hi, width: w, glow: isMajor ? 1.1 : .7, alpha: pulse * (isMajor ? 1 : .8) });
    if (p < 1) core.neonHead(g, head, { color: col, r: w * 2.6 });
    else if (isMajor) { const rp = { x: core.lerp(A.x, B.x, run), y: core.lerp(A.y, B.y, run) }; core.neonHead(g, rp, { color: '#aef4ff', r: w * 1.6, alpha: .55 }); }
  }
  // بطاقات معلومات: مرساة على الواجهة + إزاحة بكسلية ثابتة (لا اهتزاز: الموضع دالة ناعمة للـpose)
  for (const cd of cards) {
    const ap = core.clamp((t - cd.at) / .45); if (ap <= 0) continue; const e = E.outBack(ap), anc = pt(cd.u, cd.v), unit = Math.min(W, H) * .01;
    const sz = (cd.size || 3.9) * unit; let x = anc.x + (cd.dx || 0) * unit, y = anc.y + (cd.dy || 0) * unit;
    const ms = core.hudMeasure(g, { text: cd.text, sub: cd.sub || '', size: sz }), sf = P.safe || { x0: .055, y0: .065, x1: .945, y1: .8 };
    x = core.clamp(x, W * sf.x0 + ms.w / 2, W * sf.x1 - ms.w / 2); y = core.clamp(y, H * sf.y0 + ms.h / 2, H * sf.y1 - ms.h / 2);
    g.save(); g.globalCompositeOperation = 'lighter'; g.globalAlpha = ap * .9; g.fillStyle = '#fff'; g.beginPath(); g.arc(anc.x, anc.y, lw * 1.6, 0, 7); g.fill(); g.restore();
    core.neonHead(g, anc, { color: cd.color, r: lw * 1.5, alpha: ap });
    const r = core.hudCard(g, { x, y, text: cd.text, sub: cd.sub || '', size: sz, color: cd.color, alpha: ap, scale: .8 + .2 * e, link: anc });
    c.log.push({ i, kind: 'card', text: cd.text, sub: !!cd.sub, r: [+r.x.toFixed(2), +r.y.toFixed(2), +r.w.toFixed(2), +r.h.toFixed(2)], anchor: [+anc.x.toFixed(2), +anc.y.toFixed(2)] });
  }
}
export function meta(c) { return { recipe: 'building_outline', segments: S.segs.length, cards: S.cards.map(k => ({ text: k.text, at: k.at })) }; }
