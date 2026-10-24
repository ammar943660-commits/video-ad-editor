#!/usr/bin/env python3
"""qa_camera.py — اختبار D · CINEMATIC_CAMERA_MOTION كاملاً (يشغّل camera_motion.py ويقيس).
  python3 qa_camera.py [--out previews/camera] [--report reports/camera_qa.json]
الفحوص: نسبة الإخراج · صلاحية الحواف (Overscan) · تسارع/تباطؤ (سرعة البداية/النهاية) · نعومة (Jerk) ·
        تطابق الحركة المقاسة (Phase Correlation) مع المسار · رفض Parallax بلا depth · التثبيت (تحسّن الاهتزاز) · الفيديو الحقيقي مقابل الثابت."""
import os, sys, json, subprocess, argparse
import numpy as np, cv2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); CM = os.path.join(ROOT, 'tools', 'camera_motion.py'); DIRJ = json.load(open(os.path.join(ROOT, 'direction', 'director.json')))['CINEMATIC_CAMERA_MOTION']['quality_gates']
SZ = {'9:16': (1080, 1920), '4:5': (1080, 1350), '16:9': (1920, 1080)}
def run(args): r = subprocess.run(['python3', CM, *args], capture_output=True, text=True); return r.returncode, r.stdout.strip(), r.stderr.strip()
def frames_gray(p, step=1):
    cap = cv2.VideoCapture(p); out = []
    while True:
        ok, f = cap.read()
        if not ok: break
        out.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32))
    return out[::step]
def global_shift(frames):
    win = cv2.createHanningWindow(frames[0].shape[::-1], cv2.CV_32F); s = [(0.0, 0.0)]
    for a, b in zip(frames[:-1], frames[1:]):
        (dx, dy), _ = cv2.phaseCorrelate(a, b, win); s.append((dx, dy))
    return np.cumsum(np.array(s), 0)
def sp(vals): v = np.abs(np.diff(vals)); return v
def path_checks(pj, mode):
    P = pj['path']; k = {'tilt': 'pitch', 'rise': 'pitch', 'push': 'zoom', 'parallax': 'tx'}[mode]; x = np.array([p[k] for p in P]); v = np.abs(np.diff(x)); n = len(v); e = max(1, int(n * .05))
    se = max(v[:e].mean(), v[-e:].mean()) / (v.max() + 1e-12) * 100; j = np.abs(np.diff(x, 3)); jerk = j.max() / (v.max() + 1e-12)
    return se, jerk, x
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=os.path.join(ROOT, 'previews', 'camera')); ap.add_argument('--report', default=os.path.join(ROOT, 'reports', 'camera_qa.json')); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); os.makedirs(os.path.dirname(a.report), exist_ok=True)
    st = os.path.join(ROOT, 'stills'); res = []; G = DIRJ
    def case(name, src, mode, aspect, extra=(), hfov=60, scale=.5):
        out = os.path.join(a.out, name + '.mp4'); rc, so, se = run([src, out, '--mode', mode, '--aspect', aspect, '--duration', '4', '--scale', str(scale), '--hfov', str(hfov), *extra]); r = {'name': name, 'mode': mode, 'aspect': aspect, 'rc': rc, 'checks': []}
        def add(n, v, thr=None, m='max', note=''):
            ok = None if thr is None else ((v <= thr) if m == 'max' else (v >= thr)); r['checks'].append({'name': n, 'value': None if v is None else round(float(v), 3), 'threshold': thr, 'status': 'info' if ok is None else ('pass' if ok else 'fail'), 'note': note})
        if rc:
            r['rejected'] = (so + se)[:200]; res.append(r); return r
        pj = json.load(open(out.replace('.mp4', '.path.json'))); cap = cv2.VideoCapture(out); w, h = int(cap.get(3)), int(cap.get(4)); ew, eh = SZ[aspect]
        add('aspect_ok', 1 if abs(w / h - ew / eh) < .01 else 0, 1, 'min', f'{w}×{h}'); add('overscan_zoom', pj['info']['overscan_zoom'], G['overscan_zoom_max'], 'max', 'أقل تكبير يضمن بلا حواف فارغة')
        se_, jerk, x = path_checks(pj, mode); add('velocity_start_end_pct', se_, G['velocity_start_end_pct'], 'max', 'السرعة في أول/آخر 5٪ نسبة للقصوى'); add('jerk_ratio', jerk, .08, 'max', 'أقصى تغيّر تسارع نسبة للسرعة القصوى')
        if mode in ('tilt', 'rise', 'parallax'):
            fr = frames_gray(out, 1); s = global_shift(fr); ax = 1 if mode in ('tilt', 'rise') else 0; meas = s[:, ax]; pred = x[:len(meas)] - x[0]
            if np.ptp(meas) > .5 and np.ptp(pred) > 1e-9: add('measured_vs_path_corr', abs(np.corrcoef(meas, pred)[0, 1]), .95, 'min', f'مدى الإزاحة المقاسة {np.ptp(meas):.1f}px')
            else: add('measured_vs_path_corr', None, note=f'إزاحة صغيرة ({np.ptp(meas):.2f}px)')
        r['info'] = pj['info']; res.append(r); return r
    for asp, tag in (('9:16', '916'), ('4:5', '45'), ('16:9', '169')):
        for m in ('tilt', 'rise', 'push'):
            r = case(f'land_{tag}_{m}', f'{st}/land_{tag}.jpg', m, asp, hfov=60 if tag != '169' else 70)
            if tag == '169' and m == 'rise': r['expect_reject'] = True; r['pass_reject'] = r['rc'] == 4  # 16:9 لا يملك Overscan رأسياً كافياً: رفض صحيح
        if tag == '169': case('land_169_rise_gentle', f'{st}/land_169.jpg', 'rise', asp, ['--amount', '0.5'], hfov=70)
        case(f'facade_{tag}_push', f'{st}/facade_{tag}.jpg', 'push', asp, ['--focus', '0.5,0.55'], hfov=60)
    # depth-based
    for m in ('rise', 'push', 'parallax'): case(f'land_916_{m}_depth', f'{st}/land_916.jpg', m, '9:16', ['--depth', f'{st}/land_916_depth.jpg'])
    # رفض: parallax بلا depth
    r = case('land_916_parallax_nodepth', f'{st}/land_916.jpg', 'parallax', '9:16'); r['expect_reject'] = True; r['pass_reject'] = r['rc'] == 3
    # رفض: مصدر صغير جداً مع حركة كبيرة
    cv2.imwrite(os.path.join(a.out, '_small.jpg'), cv2.resize(cv2.imread(f'{st}/land_916.jpg'), (540, 960))); r = case('small_source_big_move', os.path.join(a.out, '_small.jpg'), 'rise', '9:16', ['--amount', '3.0', '--scale', '1.0'], scale=1.0); r['expect_reject'] = True; r['pass_reject'] = r['rc'] == 4
    # التثبيت: فيديو + اهتزاز يدوي صناعي
    plate = os.path.join(ROOT, 'projects', 'matrix', 'plate_land_916', 'plate.mp4')
    if not os.path.exists(plate): plate = os.path.join(ROOT, 'projects', 'plate_land_916', 'plate.mp4')
    fr = []; cap = cv2.VideoCapture(plate)
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    rng = np.random.default_rng(5); h0, w0 = fr[0].shape[:2]; sh = np.cumsum(rng.normal(0, 1.4, (len(fr), 2)), 0) * .35 + rng.normal(0, 1.6, (len(fr), 2)); sh -= np.convolve(np.ones(1), [1], 'same') * 0
    shaky = os.path.join(a.out, '_shaky.mp4'); vw = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w0}x{h0}', '-r', '30', '-i', '-', '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', shaky], stdin=subprocess.PIPE)
    for f, (dx, dy) in zip(fr, sh): vw.stdin.write(cv2.warpAffine(f, np.float32([[1, 0, dx], [0, 1, dy]]), (w0, h0), borderMode=cv2.BORDER_REFLECT).tobytes())
    vw.stdin.close(); vw.wait()
    base = global_shift(frames_gray(plate)); sj = global_shift(frames_gray(shaky))
    jit = lambda s: float(np.std(np.diff(s, 2, axis=0)))
    r = case('video_stabilized_push', shaky, 'push', '9:16', ['--stabilize', '--amount', '0.0', '--max-zoom', '1.5', '--scale', '1.0', '--duration', '2.6'], scale=1.0)
    if r['rc'] == 0:
        so = global_shift(frames_gray(os.path.join(a.out, 'video_stabilized_push.mp4'))); n = min(len(so), len(sj)); ratio = jit(sj[:n]) / (jit(so[:n]) + 1e-9)
        r['checks'].append({'name': 'stab_improvement_x', 'value': round(ratio, 2), 'threshold': G['stab_improvement_x'], 'status': 'pass' if ratio >= G['stab_improvement_x'] else 'fail', 'note': f'اهتزاز المدخل {jit(sj[:n]):.2f}px → بعد التثبيت {jit(so[:n]):.2f}px (مرجع المصدر النظيف {jit(base[:n]):.2f}px)'})
    # ملخص
    for r in res:
        if r.get('expect_reject'): r['verdict'] = 'pass' if r['pass_reject'] else 'fail'
        elif r.get('rejected'): r['verdict'] = 'reject'
        else: r['verdict'] = 'fail' if any(c['status'] == 'fail' for c in r['checks']) else 'pass'
    json.dump(res, open(a.report, 'w'), ensure_ascii=False, indent=1)
    for r in res:
        print(f"{'✓' if r['verdict'] == 'pass' else '✗'} {r['name']:<28} {r['verdict']:<7}" + (f" REJECT-EXPECTED→{'ok' if r['pass_reject'] else 'WRONG'}" if r.get('expect_reject') else '') + ' | ' + ' '.join(f"{c['name']}={c['value']}{'✗' if c['status'] == 'fail' else ''}" for c in r['checks']))
if __name__ == '__main__': main()
