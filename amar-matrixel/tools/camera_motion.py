#!/usr/bin/env python3
"""camera_motion.py — D · CINEMATIC_CAMERA_MOTION
حركات كاميرا افتراضية فوق فيديو حقيقي أو صورة ثابتة، بلا اختلاق زوايا:
  tilt      Tilt Up: دوران كاميرا حول مركزها (تحويل منظوري دقيق فيزيائياً لصورة ثابتة).
  rise      Base-to-Top Rise: ميل للأعلى + إزاحة قص صاعدة. بلا depth = «محاكاة Rise» (دوران)، ومعها depth = ارتفاع حقيقي بمنظور.
  push      Smooth Architectural Push-In: تقريب هادئ نحو نقطة اهتمام (Zoom رقمي؛ مع depth = Dolly-in مع parallax).
  parallax  Controlled Parallax: إزاحة جانبية بعمق — يتطلب خريطة depth (من 3D أو توليد AI معتمد). بدونها: رفض صريح.
قواعد: لا اختلاق محتوى؛ فحص تغطية الحواف (Overscan) ورفض النتيجة لو احتاجت تكبيراً فوق الحد.
  python3 camera_motion.py <src> <out.mp4> --mode rise --aspect 9:16 [--duration 4] [--fps 30] [--hfov 65]
         [--depth depth.png] [--amount 1.0] [--ease inOutCubic|x1,y1,x2,y2] [--hold 0.25,0.25] [--max-zoom 1.35] [--stabilize]"""
import sys, json, argparse, os, subprocess
import numpy as np, cv2

SIZES = {'9:16': (1080, 1920), '4:5': (1080, 1350), '16:9': (1920, 1080)}

def bez(x1, y1, x2, y2):
    def f(x):
        x = min(1, max(0, x)); t = x
        for _ in range(12):
            cx, bx = 3 * x1, 3 * (x2 - x1) - 3 * x1; ax = 1 - cx - bx
            sx = ((ax * t + bx) * t + cx) * t - x; d = (3 * ax * t + 2 * bx) * t + cx
            if abs(sx) < 1e-7 or abs(d) < 1e-7: break
            t -= sx / d
        t = min(1, max(0, t)); cy = 3 * y1; by = 3 * (y2 - y1) - cy; ay = 1 - cy - by
        return ((ay * t + by) * t + cy) * t
    return f

EASE = {'linear': lambda t: t, 'inOutCubic': lambda t: 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2, 'outCubic': lambda t: 1 - (1 - t) ** 3, 'inOutSine': lambda t: -(np.cos(np.pi * t) - 1) / 2,
        'architect': bez(.42, 0, .18, 1)}  # بداية ناعمة ثم تباطؤ طويل — حركة معمارية هادئة

def rot_x(a):  # ميل (pitch) موجب = الكاميرا تنظر للأعلى
    c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, s], [0, -s, c]])

def load_src(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp'):
        im = cv2.imread(path); assert im is not None, 'cannot read image'; return [im], None, True
    cap = cv2.VideoCapture(path); fps = cap.get(5); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return fr, fps, False

def stabilize(frames, smooth=15):
    """تثبيت: تتبّع نقاط LK → حركة تراكمية (انتقال+دوران+مقياس) → تنعيم → تصحيح. يُرجع (إطارات, مسار خام, مسار منعّم)."""
    prev = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY); T = [np.zeros(3)]; tr = np.zeros(3)
    for f in frames[1:]:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY); p0 = cv2.goodFeaturesToTrack(prev, 400, .01, 12)
        if p0 is None: T.append(tr.copy()); prev = g; continue
        p1, st, _ = cv2.calcOpticalFlowPyrLK(prev, g, p0, None); ok = st.ravel() == 1
        M, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=2.0)
        if M is not None: tr = tr + np.array([M[0, 2], M[1, 2], np.arctan2(M[1, 0], M[0, 0])])
        T.append(tr.copy()); prev = g
    T = np.array(T); k = smooth | 1; pad = np.pad(T, ((k // 2, k // 2), (0, 0)), mode='edge'); ker = np.hanning(k + 2)[1:-1]; ker /= ker.sum()
    Ts = np.stack([np.convolve(pad[:, j], ker, mode='valid') for j in range(3)], 1)
    out = []
    for f, a, b in zip(frames, T, Ts):
        d = b - a; M = np.array([[np.cos(d[2]), -np.sin(d[2]), d[0]], [np.sin(d[2]), np.cos(d[2]), d[1]]]); out.append(cv2.warpAffine(f, M, (f.shape[1], f.shape[0]), borderMode=cv2.BORDER_REFLECT))
    return out, T, Ts

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--mode', required=True, choices=['tilt', 'rise', 'push', 'parallax'])
    ap.add_argument('--aspect', default='9:16'); ap.add_argument('--duration', type=float, default=4); ap.add_argument('--fps', type=float, default=30)
    ap.add_argument('--hfov', type=float, default=65, help='زاوية الرؤية الأفقية للمصدر (درجات)'); ap.add_argument('--depth'); ap.add_argument('--amount', type=float, default=1.0)
    ap.add_argument('--ease', default='architect'); ap.add_argument('--hold', default='0.25,0.25'); ap.add_argument('--max-zoom', type=float, default=1.35)
    ap.add_argument('--stabilize', action='store_true'); ap.add_argument('--focus', default='0.5,0.5', help='نقطة اهتمام u,v للـpush'); ap.add_argument('--scale', type=float, default=1.0, help='مقياس الإخراج (معاينة)')
    ap.add_argument('--allow-invented', action='store_true')
    a = ap.parse_args()
    frames, vfps, still = load_src(a.src); fps = a.fps; n = int(round(a.duration * fps)); sh, sw = frames[0].shape[:2]
    if not still and a.mode in ('tilt', 'rise', 'push') and len(frames) < n: n = len(frames)
    if a.mode == 'parallax' and not a.depth:
        print('✗ REJECT: parallax يتطلب خريطة depth (نموذج 3D أو توليد AI معتمد). لن أخترع زوايا جديدة من صورة ثابتة.'); sys.exit(3)
    if a.mode in ('rise', 'push') and a.depth is None: sim = True
    else: sim = False
    if still is False and a.depth: print('ℹ depth يُطبّق على أول فريم فقط للصور؛ للفيديو يُتجاهل'); a.depth = None
    ow, oh = SIZES[a.aspect]; ow, oh = 2 * int(round(ow * a.scale / 2)), 2 * int(round(oh * a.scale / 2))  # أبعاد زوجية (libx264)
    shake = None
    if a.stabilize and not still: frames, raw, sm = stabilize(frames); shake = {'raw_std_px': float(np.std(np.diff(raw[:, :2], axis=0))), 'stab_std_px': float(np.std(np.diff(sm[:, :2], axis=0)))}
    f = (sw / 2) / np.tan(np.radians(a.hfov) / 2); K = np.array([[f, 0, sw / 2], [0, f, sh / 2], [0, 0, 1.0]])
    # كاميرا الإخراج: تغطي أكبر قص بنفس نسبة الإخراج من المصدر (zoom=1 → أقصى قص)
    base = min(sw / ow, sh / oh) ; fo = f / base  # بكسل الإخراج لكل راديان بحيث الـcrop يملأ المصدر عند zoom 1
    Ko = np.array([[fo, 0, ow / 2], [0, fo, oh / 2], [0, 0, 1.0]])
    hold0, hold1 = [float(x) for x in a.hold.split(',')]; ez = EASE[a.ease] if a.ease in EASE else bez(*[float(x) for x in a.ease.split(',')])
    fx, fy = [float(x) for x in a.focus.split(',')]
    def params(u):  # u ∈ [0,1] بعد التهدئة → وضع الكاميرا
        e = ez(u); A = a.amount
        if a.mode == 'tilt': return dict(pitch=np.radians(-4 + 9 * e * A), zoom=1.0 + .03 * e, tx=0, ty=0)
        if a.mode == 'rise': return dict(pitch=np.radians(-5 + 11 * e * A), zoom=1.0 + .02 * e, tx=0, ty=-.9 * e * A)  # ty: ارتفاع بالمتر النسبي (يعمل مع depth)
        if a.mode == 'push': return dict(pitch=0, zoom=1.0 + .16 * e * A, tx=0, ty=0)
        if a.mode == 'parallax': return dict(pitch=0, zoom=1.04, tx=(-1.0 + 2 * e) * A, ty=0)
    depth = None
    if a.depth:
        d = cv2.imread(a.depth, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0; d = cv2.resize(d, (sw, sh)); depth = d  # 1=قريب، 0=بعيد (inverse depth نسبي)
    # فحص التغطية: لكل عينة نحسب زوايا الإخراج المسقطة على المصدر
    path = []; need_zoom = 1.0
    for k in range(n):
        t = k / fps; u = np.clip((t - hold0) / max(1e-6, a.duration - hold0 - hold1), 0, 1); p = params(u); path.append(p)
    def Hof(p, extra=1.0):
        R = rot_x(p['pitch']); Ko2 = Ko.copy(); Ko2[0, 0] *= p['zoom'] * extra; Ko2[1, 1] *= p['zoom'] * extra
        if a.mode == 'push':  # تقريب نحو نقطة الاهتمام بدل المركز
            c = np.array([[1, 0, (fx - .5) * ow * (p['zoom'] - 1) / p['zoom'] * -1], [0, 1, (fy - .5) * oh * (p['zoom'] - 1) / p['zoom'] * -1], [0, 0, 1]]); Ko2 = c @ Ko2
        return K @ R.T @ np.linalg.inv(Ko2)   # إخراج → مصدر
    def cover_ok(extra):
        crn = np.array([[0, 0, 1], [ow, 0, 1], [ow, oh, 1], [0, oh, 1]], np.float64).T
        for p in path[::max(1, n // 24)]:
            q = Hof(p, extra) @ crn; q = (q[:2] / q[2]).T
            if (q[:, 0].min() < 0) or (q[:, 1].min() < 0) or (q[:, 0].max() > sw - 1) or (q[:, 1].max() > sh - 1): return False
        return True
    extra = 1.0
    while not cover_ok(extra) and extra < a.max_zoom + .001: extra += .005
    if not cover_ok(extra) and not a.allow_invented:
        print(f'✗ REJECT: تغطية المصدر لا تكفي حتى بتكبير {a.max_zoom}× — المصدر صغير/الحركة كبيرة. قلّل --amount أو استخدم مصدراً أعلى دقة.'); sys.exit(4)
    info = {'mode': a.mode, 'simulated': sim, 'still': still, 'overscan_zoom': round(extra, 3), 'depth_used': bool(a.depth), 'shake': shake, 'aspect': a.aspect, 'fps': fps, 'frames': n, 'ease': a.ease,
            'note': 'rise/push بلا depth = محاكاة (دوران/Zoom رقمي)، وليس حركة كاميرا حقيقية' if sim else 'منظور حقيقي بالاعتماد على depth المقدَّم'}
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{ow}x{oh}', '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', a.out], stdin=subprocess.PIPE)
    yy, xx = np.mgrid[0:oh, 0:ow].astype(np.float32); rec = []
    for k in range(n):
        p = path[k]; src = frames[0] if still else frames[min(k, len(frames) - 1)]; H = Hof(p, extra); Hi = H
        if depth is None:
            out = cv2.warpPerspective(src, np.linalg.inv(np.linalg.inv(Hi)) if False else Hi, (ow, oh), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        else:  # إعادة إسقاط بالعمق: خريطة التحويل المنظوري + إزاحة تناسب inverse-depth (parallax)
            pts = np.stack([xx, yy, np.ones_like(xx)], -1).reshape(-1, 3) @ Hi.T; mx = (pts[:, 0] / pts[:, 2]).reshape(oh, ow).astype(np.float32); my = (pts[:, 1] / pts[:, 2]).reshape(oh, ow).astype(np.float32)
            for _ in range(2):
                dz = cv2.remap(depth, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                dxs = -p['tx'] * (dz - dz.mean()) * sw * .035 * 1.0 if a.mode == 'parallax' else 0
                dys = p['ty'] * (dz - dz.mean()) * sh * .05 if a.mode == 'rise' else 0
                if a.mode == 'push': s = (p['zoom'] - 1) * 1.6; dxs = (mx - sw / 2) * (dz - dz.mean()) * s * .5; dys = (my - sh / 2) * (dz - dz.mean()) * s * .5
                pts2x = (pts[:, 0] / pts[:, 2]).reshape(oh, ow).astype(np.float32) + dxs; pts2y = (pts[:, 1] / pts[:, 2]).reshape(oh, ow).astype(np.float32) + dys
                mx, my = np.asarray(pts2x, np.float32), np.asarray(pts2y, np.float32)
            out = cv2.remap(src, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        ff.stdin.write(np.ascontiguousarray(out).tobytes()); rec.append({'i': k, **{kk: float(v) for kk, v in p.items()}, 'H_out2src': H.flatten().tolist()})
    ff.stdin.close(); ff.wait()
    json.dump({'info': info, 'path': rec}, open(os.path.splitext(a.out)[0] + '.path.json', 'w'))
    print('✓', a.out, json.dumps(info, ensure_ascii=False))
if __name__ == '__main__': main()
