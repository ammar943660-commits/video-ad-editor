#!/usr/bin/env python3
"""qa.py — فحص جودة نتيجة وصفة (بعد الريندر) مقابل بوابات direction/director.json.
  python3 qa.py <project_dir> [--gt <plate_project_dir>] [--out report.json]
--gt: مجلد مشروع plate تركيبي فيه renders/meta.json (Ground Truth) لقياس الدقة المطلقة؛ بدونه تُقاس الثباتات فقط
        وتُوسم القياسات المطلقة «غير مختبرة (لا GT)».
يطبع جدول فحوص + حكم: pass / needs_fix / reject."""
import sys, os, json, argparse, difflib, subprocess, tempfile, re
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__)); DIR = json.load(open(os.path.join(HERE, '..', 'direction', 'director.json')))
RECIPE2KEY = {v['recipe']: k for k, v in DIR.items() if isinstance(v, dict) and 'recipe' in v}
SAFE = {'9:16': (.05, .06, .95, .82), '4:5': (.05, .05, .95, .90), '16:9': (.05, .06, .95, .90)}  # x0,y0,x1,y1 كنسب (الأسفل محجوز لواجهات المنصات بالعمودي)

def load_json(p): return json.load(open(p)) if os.path.exists(p) else None
def pose_pt(f, K, P3, plane=None):
    R = np.array(f['R']).reshape(3, 3); t = np.array(f['t']); X = np.array([P3[0], -P3[1], -P3[2]]); c = R @ X + t
    return np.array([K[0] * c[0] / c[2] + K[2], K[1] * c[1] / c[2] + K[3]])
def Kof(W, H, fov): f = (H / 2) / np.tan(np.radians(fov) / 2); return (f, f, W / 2, H / 2)
def rgba(p): im = cv2.imread(p, cv2.IMREAD_UNCHANGED); return im
def plate_frame(path, i):
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_FRAMES, i); ok, f = cap.read(); return f if ok else None
def composite(plate, ov):
    a = ov[:, :, 3:4].astype(np.float32) / 255; return (plate.astype(np.float32) * (1 - a) + ov[:, :, :3].astype(np.float32) * a).astype(np.uint8)
def ocr(img, lang='ara+eng', psm=7):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, 'a.png'); cv2.imwrite(p, img)
        r = subprocess.run(['tesseract', p, 'stdout', '-l', lang, '--psm', str(psm)], capture_output=True, text=True); return re.sub(r'\s+', '', r.stdout)
def sim(a, b):
    norm = lambda s: re.sub(r'[^\w]', '', s.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))); return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()
def ocr_best(img, expect, psms=(7, 6, 8)):
    best = 0.0; txt = ''
    g0 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    for sc in (1.0, 2.0, 3.0):
        g = cv2.resize(g0, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC) if sc != 1 else g0
        for v in (g, 255 - g, cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1], 255 - cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]):
            for psm in psms:
                t = ocr(cv2.copyMakeBorder(v, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=int(v.mean())), psm=psm); s = sim(t, expect)
                if s > best: best, txt = s, t
    return best, txt

class Rep:
    def __init__(s, key): s.key = key; s.checks = []; s.gates = DIR[key]['quality_gates']; s.rej = DIR[key]['reject_if']
    def add(s, name, value, unit='', note='', gate=None, mode='max', info=False):
        """mode='max': يجب أن تكون القيمة ≤ العتبة ، 'min': ≥ العتبة"""
        thr = s.gates.get(gate or name); st = 'info' if (info or thr is None or value is None) else ('pass' if ((value <= thr) if mode == 'max' else (value >= thr)) else 'fail')
        if value is None: st = 'untested'
        s.checks.append({'name': name, 'value': None if value is None else (round(float(value), 4) if isinstance(value, (float, np.floating)) else value), 'threshold': thr, 'mode': mode, 'unit': unit, 'status': st, 'note': note})
    def verdict(s):
        fails = [c for c in s.checks if c['status'] == 'fail']
        rej = [c for c in fails if (c['name'] in s.rej)]
        return ('reject' if rej else ('needs_fix' if fails else 'pass')), [DIR[s.key]['reject_reasons'].get(c['name'], c['name']) for c in rej]

def track_checks(R, proj, tr, gt, W, H):
    fr = tr['frames']; C = np.array([f['corners'] for f in fr]); n = len(fr)
    flagged = sum(1 for f in fr if f['flag']) / n * 100
    R.add('track_flagged_frames_pct', flagged, '%', 'فريمات فقد/رفض فيها التتبع', gate='track_flagged_frames_pct') if 'track_flagged_frames_pct' in R.gates else R.add('track_flagged_frames_pct', flagged, '%', info=True)
    if gt:
        G = np.array([f['corners'] for f in gt['frames']][:n]); m = min(len(G), n); e = C[:m] - G[:m]; d = np.linalg.norm(e, axis=2)
        R.add('track_err_mean_pct', d.mean() / W * 100, '% of W', f'متوسط {d.mean():.2f}px — أقصى {d.max():.2f}px'); R.add('track_err_max_pct', d.max() / W * 100, '% of W', info=True)
        j = np.diff(e, 2, axis=0); R.add('track_jitter_px_rel_pct', float(np.std(j)) / W * 100, '% of W', f'اهتزاز ذو تردد عالٍ (انحراف معياري للفرق الثاني) {np.std(j):.3f}px'); R.add('track_drift_px', float(d[m // 2:].mean() - d[:m // 4 + 1].mean()), 'px', 'نمو الخطأ بين بداية ونهاية المقطع', info=True)
    else:
        j = np.diff(C, 2, axis=0); R.add('track_jitter_px_rel_pct', float(np.std(j)) / W * 100, '% of W', 'بلا GT: اهتزاز الفرق الثاني للزوايا المنعّمة'); R.add('track_err_mean_pct', None, '', 'غير مختبر: لا Ground Truth (لقطة حقيقية)')
    return C

def persp_probe(R, tr, gt, W, H, probes, name, gate):
    if not gt: R.add(name, None, '', 'غير مختبر: لا GT'); return
    n = min(len(tr['frames']), len(gt['frames'])); Kt = Kof(W, H, tr['fov_deg']); errs = []
    for i in range(0, n, 3):
        ft, fg = tr['frames'][i], gt['frames'][i]; Kg = Kof(W, H, fg['fov'])
        for p in probes: errs.append(np.linalg.norm(pose_pt(ft, Kt, p) - pose_pt(fg, Kg, p)))
    R.add(name, np.mean(errs) / W * 100, '% of W', f'متوسط {np.mean(errs):.2f}px أقصى {np.max(errs):.2f}px', gate=gate)

def safe_check(R, aspect, W, H, boxes):
    x0, y0, x1, y1 = SAFE[aspect]; bad = 0
    for b in boxes:
        x, y, w, h = b; 
        if x < x0 * W - 1 or y < y0 * H - 1 or x + w > x1 * W + 1 or y + h > y1 * H + 1: bad += 1
    R.add('safe_zone_violations', bad, 'boxes', f'المنطقة الآمنة {aspect}: x {x0:.0%}-{x1:.0%}, y {y0:.0%}-{y1:.0%}')

# ───────────── A: STONE ─────────────
def qa_stone(proj, pd, tr, gt, meta, W, H, fps, R):
    P = proj['params']; beats = meta['beats']; fdir = os.path.join(pd, 'renders', 'frames'); plate = os.path.join(pd, proj['plate'])
    K = Kof(W, H, tr['fov_deg']); basis = meta['basis']; right = np.array(basis['right']); nrm = np.array(basis['nrm']); up = np.array([0, 0, 1.0])
    allowed_alpha = 0; tot_alpha = 0; worst_float = 0; sims = []; strokes = []; hts = []; boxes = []; shadow_ok = []
    def hull_pts(b):
        wp = np.array([*b['wp'], 0.0]); tw, th = b['width_units'], b['height_units']
        return [wp + right * sx * tw * .75 + nrm * sd * th * 2.0 + up * h * th * 2.2 for sx in (-1, 1) for sd in (-1, 1) for h in (0, 1)]
    i_lo = int(min(b['t0'] for b in beats) * fps); i_hi = int((max(b['end'] for b in beats) + 2.0) * fps)
    for i in range(i_lo, min(i_hi, len(tr['frames']) - 1) + 1, 2):   # اتحاد أحجام كل الـbeats لكل فريم
        p = os.path.join(fdir, f'{i:05d}.png')
        if not os.path.exists(p): continue
        ov = rgba(p); a = ov[:, :, 3].astype(np.float32) / 255; f = tr['frames'][i]; m = np.zeros(a.shape, np.uint8)
        for b in beats:
            pts = np.array([pose_pt(f, K, q) for q in hull_pts(b)]).astype(np.float32); cv2.fillConvexPoly(m, cv2.convexHull(pts).astype(np.int32), 1)
        tot = a.sum(); out = (a * (1 - m)).sum()
        if tot > 50: worst_float = max(worst_float, out / tot * 100)
    for b in beats:
        wp = np.array([*b['wp'], 0.0]); tw, th, dep = b['width_units'], b['height_units'], b['depth_units']
        hold_i = int(round((b['rise_end'] + b['hold_end']) / 2 * fps))
        # فريم الثبات
        hi = min(hold_i, len(tr['frames']) - 1); ov = rgba(os.path.join(fdir, f'{hi:05d}.png')); a = ov[:, :, 3]; f = tr['frames'][hi]
        # ارتفاع النص على الشاشة
        base = pose_pt(f, K, wp); top = pose_pt(f, K, wp + up * th); hts.append(np.linalg.norm(top - base) / H * 100)
        # مصفوفة القناع = بكسلات الحجر: ألفا ≥ .9
        mask = (a > 230).astype(np.uint8); nn, lab, stt, _ = cv2.connectedComponentsWithStats(mask); keep = np.zeros_like(mask)
        for q in range(1, nn):  # تجاهل الحطام الصغير (< 80 بكسل) عند قياس صندوق النص
            if stt[q, 4] >= 80: keep[lab == q] = 1
        mask = keep; ys, xs = np.where(mask > 0)
        if len(xs) < 100: R.add('stone_pixels_at_hold', len(xs), 'px', 'النص غير ظاهر وقت الثبات'); continue
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()); boxes.append((x0, y0, x1 - x0, y1 - y0)); print('   [stone bbox @hold]', boxes[-1], 'frame', hi)
        dt = cv2.distanceTransform(mask[y0:y1 + 1, x0:x1 + 1], cv2.DIST_L2, 3); strokes.append(2 * np.percentile(dt[dt > 0], 60) / W * 100)
        pl = plate_frame(plate, hi); comp = composite(pl, ov); pad = 12; crop = comp[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]
        # قناع الصورة الظلّية (الشكل كما يراه المشاهد) كنص أسود على أبيض
        sil = 255 - cv2.GaussianBlur(mask * 255, (0, 0), .8)[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad]
        expect = ''.join(b['lines']); s1, t1 = ocr_best(sil, expect); s2, t2 = ocr_best(crop, expect)
        # نسخة معدَّلة المنظور (Rectified) لقياس وضوح الخط نفسه بمعزل عن زاوية الكاميرا
        q = np.float32([pose_pt(f, K, wp + right * sx * tw / 2 + up * h * th) for sx, h in ((-1, 1), (1, 1), (1, 0), (-1, 0))]); Hm = cv2.getPerspectiveTransform(q, np.float32([[0, 0], [800, 0], [800, 800 * th / tw], [0, 800 * th / tw]]))
        rect = cv2.warpPerspective(255 - a, Hm, (800, int(800 * th / tw))); s3, t3 = ocr_best(rect, expect)
        sims.append((s1, s2, s3)); R.add(f'ocr_silhouette[{expect}]', s1, '', f'OCR «{t1}»', info=True); R.add(f'ocr_composite[{expect}]', s2, '', f'OCR «{t2}»', info=True); R.add(f'ocr_rectified[{expect}]', s3, '', f'OCR «{t3}» (الشكل بعد إزالة المنظور)', info=True)
        # الظل: بكسلات داكنة شبه شفافة قرب القاعدة
        dark = ((ov[:, :, 3] > 40) & (ov[:, :, 3] < 230) & (ov[:, :, :3].max(2) < 70)).sum(); shadow_ok.append(dark)
    R.add('ocr_similarity', min((max(s) for s in sims), default=0) if sims else None, '', 'أسوأ beat: أعلى تشابه OCR بين (ظلّية، مركّب، معدّل المنظور)', gate='ocr_similarity', mode='min')
    R.add('text_height_pct', min(hts) if hts else None, '% of H', 'ارتفاع النص على الشاشة وقت الثبات', mode='min'); R.add('stroke_rel_pct', min(strokes) if strokes else None, '% of W', 'سمك الخط التقديري', mode='min')
    R.add('floating_alpha_pct', worst_float, '%', 'أسوأ نسبة ألفا خارج الحجم المسموح (نص+غبار+حطام)')
    R.add('shadow_present', min(shadow_ok) if shadow_ok else 0, 'px', 'بكسلات الظل شبه الشفافة الداكنة', gate=None, info=True)
    persp_probe(R, tr, gt, W, H, [np.array([*b['wp'], h * b['height_units']]) for b in beats for h in (0, 1)], 'perspective_err_pct', 'perspective_err_pct')
    persp_probe(R, tr, gt, W, H, [np.array([*b['wp'], 0.0]) for b in beats], 'contact_err_pct', 'contact_err_pct')
    return boxes

# ───────────── B: HOLOGRAM ─────────────
def qa_holo(proj, pd, tr, gt, meta, W, H, fps, R, log):
    P = proj['params']; viol = 0; notes = []
    area_logged = any(l['kind'] == 'area' for l in log); badge_frames = {l['i'] for l in log if l['kind'] == 'badge'}
    if bool(P.get('area_m2')) != area_logged: viol += 1; notes.append('المساحة: ظهور لا يطابق بيانات المستخدم')
    if not P.get('area_m2') and area_logged: notes.append('ظهرت مساحة دون إدخال المستخدم')
    b = P.get('building')
    if b and not b.get('approved'):
        t0 = meta['timing']['build'][0]; need = range(int(t0 * fps) + 2, len(tr['frames']))
        miss = [i for i in need if i not in badge_frames]
        if miss: viol += 1; notes.append(f'شارة «تصور مبدئي» غائبة في {len(miss)} فريماً')
    if P.get('plan') and not P['plan'].get('approved'): viol += 1
    R.add('policy_violations', viol, '', '؛ '.join(notes) or 'قواعد الصدق: المساحة/المخطط/المبنى المعتمد — سليمة')
    boxes = [tuple(l['r']) for l in log if l['kind'] in ('area', 'badge')]
    # دقة الخط النهائية: زوايا الخط المرسومة (من pose) مقابل GT
    if gt:
        n = min(len(tr['frames']), len(gt['frames'])); Kt = Kof(W, H, tr['fov_deg']); pl = tr['plane']; e = []
        for i in range(0, n, 3):
            for (u, v) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p3 = [(u - .5) * pl['w'], (.5 - v) * pl['l'], 0]; e.append(np.linalg.norm(pose_pt(tr['frames'][i], Kt, p3) - pose_pt(gt['frames'][i], Kof(W, H, gt['frames'][i]['fov']), p3)))
        R.add('outline_to_gt_pct', np.mean(e) / W * 100, '% of W', f'الخط المرسوم مقابل حدود الأرض الحقيقية: {np.mean(e):.2f}px')
        hp = [[(u - .5) * tr['plane']['w'], (.5 - v) * tr['plane']['l'], h] for (u, v) in ((.35, .5), (.62, .5)) for h in (0, 4 * 3 * (1 if tr['plane']['units'] == 'meters' else .04))]
        persp_probe(R, tr, gt, W, H, hp, 'perspective_err_pct', 'perspective_err_pct')
    else: R.add('outline_to_gt_pct', None, '', 'غير مختبر: لا GT'); R.add('perspective_err_pct', None, '', 'غير مختبر: لا GT')
    # OCR للمساحة بعد إزالة المنظور
    if P.get('area_m2'):
        ai = max(l['i'] for l in log if l['kind'] == 'area'); fdir = os.path.join(pd, 'renders', 'frames'); ov = rgba(os.path.join(fdir, f'{ai:05d}.png')); pl_ = plate_frame(os.path.join(pd, proj['plate']), ai)
        C = np.float32(tr['frames'][ai]['corners']); Hm = cv2.getPerspectiveTransform(C, np.float32([[0, 0], [1000, 0], [1000, int(1000 * tr['plane']['l'] / tr['plane']['w'])], [0, int(1000 * tr['plane']['l'] / tr['plane']['w'])]]))
        rect = cv2.warpPerspective(composite(pl_, ov), Hm, (1000, int(1000 * tr['plane']['l'] / tr['plane']['w']))); h_ = rect.shape[0]; crop = rect[int(h_ * .38):int(h_ * .62), 150:850]
        s, t = ocr_best(crop, str(P['area_m2']), psms=(7, 6, 13)); R.add('ocr_similarity', s, '', f'قراءة المساحة بعد إزالة المنظور: «{t}» (المتوقع {P["area_m2"]})', mode='min')
    safe_check(R, proj['aspect'], W, H, boxes); return boxes

# ───────────── C: OUTLINE ─────────────
def qa_outline(proj, pd, tr, gt, meta, W, H, fps, R, log):
    edges = load_json(os.path.join(pd, 'edges.json'))['segments']; pl = tr['plane']
    if gt:
        n = min(len(tr['frames']), len(gt['frames'])); Kt = Kof(W, H, tr['fov_deg']); e = []
        for i in range(0, n, 3):
            for s in edges:
                for (u, v) in ((s['u0'], s['v0']), (s['u1'], s['v1'])):
                    p3 = [(u - .5) * pl['w'], (.5 - v) * pl['l'], 0]; e.append(np.linalg.norm(pose_pt(tr['frames'][i], Kt, p3) - pose_pt(gt['frames'][i], Kof(W, H, gt['frames'][i]['fov']), p3)))
        R.add('line_slip_pct', np.mean(e) / W * 100, '% of W', f'انزلاق الخطوط عن الواجهة الحقيقية: متوسط {np.mean(e):.2f}px أقصى {np.max(e):.2f}px')
        gh = [.05, .12, .40, .46, .49, .56, .60, .74, .82, .98]; dh = [s['v0'] for s in edges if s['kind'] != 'outline' and abs(s['v0'] - s['v1']) < 1e-6]
        rec = np.mean([any(abs(g - d) < .012 for d in dh) for g in gh]); prec = np.mean([any(abs(g - d) < .012 for g in gh) for d in dh]) if dh else 0
        R.add('edge_recall', rec, '', 'نسبة الحواف الأفقية الحقيقية المكتشفة', info=True); R.add('edge_precision', prec, '', 'نسبة الحواف المكتشفة التي تطابق حافة حقيقية', info=True)
    else: R.add('line_slip_pct', None, '', 'غير مختبر: لا GT')
    cards = {}
    for l in log:
        if l['kind'] == 'card': cards.setdefault(l['text'], []).append((l['i'], l['r']))
    jit = []; overlap = 0
    for tx, seq in cards.items():
        seq.sort(); full = [s for s in seq if s[0] >= seq[0][0] + 14]
        if len(full) > 6: c = np.array([[r[0] + r[2] / 2, r[1] + r[3] / 2] for _, r in full]); jit.append(np.std(np.diff(c, 2, axis=0)))
    byf = {}
    for l in log:
        if l['kind'] == 'card': byf.setdefault(l['i'], []).append(l['r'])
    for i, rs in byf.items():
        for a in range(len(rs)):
            for b in range(a + 1, len(rs)):
                A, B = rs[a], rs[b]
                if not (A[0] + A[2] < B[0] or B[0] + B[2] < A[0] or A[1] + A[3] < B[1] or B[1] + B[3] < A[1]): overlap += 1
    R.add('card_jitter_px', float(max(jit)) if jit else None, 'px', 'اهتزاز مواضع البطاقات (فرق ثانٍ)'); R.add('card_overlap', overlap, 'frames×pairs', 'تداخل البطاقات')
    # OCR البطاقات على فريم أخير
    last = max(byf) if byf else None; sims = []
    if last is not None:
        fdir = os.path.join(pd, 'renders', 'frames'); ov = rgba(os.path.join(fdir, f'{last:05d}.png')); comp = composite(plate_frame(os.path.join(pd, proj['plate']), last), ov)
        for l in [l for l in log if l['i'] == last and l['kind'] == 'card']:
            x, y, w, h = [int(round(v)) for v in l['r']]; hs = l.get('sub'); crop = comp[max(0, y + int(h * .1)):y + int(h * (.56 if hs else .92)), max(0, x + int(w * .06)):x + int(w * .86)]; s, t = ocr_best(crop, l['text'], psms=(7, 6, 8, 13)); sims.append(s); R.add(f'ocr[{l["text"]}]', s, '', f'«{t}»', info=True)
    R.add('ocr_similarity', float(np.mean(sims)) if sims else None, '', 'متوسط وضوح البطاقات (OCR عربي)', mode='min')
    safe_check(R, proj['aspect'], W, H, [tuple(l['r']) for l in log if l['kind'] == 'card'])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('proj'); ap.add_argument('--gt'); ap.add_argument('--out'); a = ap.parse_args()
    pd = os.path.abspath(a.proj); proj = load_json(os.path.join(pd, 'project.json')); tr = load_json(os.path.join(pd, 'track.json')); key = RECIPE2KEY[proj['recipe']]
    info = load_json(os.path.join(pd, 'renders', 'render-info.json')); W, H, fps = info['W'], info['H'], info['fps']; meta = load_json(os.path.join(pd, 'renders', 'meta.json')); log = load_json(os.path.join(pd, 'renders', 'frame-log.json')) or []
    gt = load_json(os.path.join(os.path.abspath(a.gt), 'renders', 'meta.json')) if a.gt else None
    R = Rep(key); asp = {'9:16': (9, 16), '4:5': (4, 5), '16:9': (16, 9)}[proj['aspect']]
    R.add('aspect_ok', 1 if abs(W / H - asp[0] / asp[1]) < .01 else 0, '', f'{W}×{H}', gate=None, info=True)
    track_checks(R, proj, tr, gt, W, H); boxes = []
    if proj['recipe'] == 'stone_text':
        boxes = qa_stone(proj, pd, tr, gt, meta, W, H, fps, R); safe_check(R, proj['aspect'], W, H, boxes)
    elif proj['recipe'] == 'land_hologram': qa_holo(proj, pd, tr, gt, meta, W, H, fps, R, log)
    elif proj['recipe'] == 'building_outline': qa_outline(proj, pd, tr, gt, meta, W, H, fps, R, log)
    v, why = R.verdict(); rep = {'project': os.path.basename(pd), 'effect': key, 'aspect': proj['aspect'], 'size': [W, H], 'verdict': v, 'reject_reasons': why, 'checks': R.checks}
    out = a.out or os.path.join(pd, 'qa_report.json'); json.dump(rep, open(out, 'w'), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    sym = {'pass': '✓', 'fail': '✗', 'info': '·', 'untested': '○'}
    print(f'── QA {rep["project"]}  [{key}] {proj["aspect"]} ──')
    for c in R.checks: print(f'  {sym[c["status"]]} {c["name"]:<28} {str(c["value"]):>10} {c["unit"]:<10} (عتبة {c["mode"]} {c["threshold"]}) {c["note"]}'[:230])
    print(f'  ⇒ الحكم: {v}' + (f' — {"، ".join(why)}' if why else ''))
if __name__ == '__main__': main()
