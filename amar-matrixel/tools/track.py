#!/usr/bin/env python3
"""track.py — تتبع مستوي (Planar Track) لأرض أو واجهة، ثم حل الكاميرا (pose) لكل فريم.

  python3 track.py <video> <project_dir> [--corners "x,y;x,y;x,y;x,y"] [--fov 55] [--plane-w M --plane-l M]
                                          [--margin 0.10] [--smooth 7] [--max-w 960]

الزوايا بالترتيب: أعلى-يسار، أعلى-يمين، أسفل-يمين، أسفل-يسار (بكسل الفريم الأول).
تُقرأ من project.json → "corners" لو لم تُمرَّر. الناتج: <project_dir>/track.json
الطريقة: SIFT+RANSAC بين فريمين متتاليين (داخل قناع المستوى) ثم تنقيح ECC (Homography) مقابل الفريم الأول
لمنع الانجراف، ثم تنعيم زمني للزوايا، ثم تفكيك Homography إلى R,t بكاميرا معلومة FOV.
لا يخمّن المقاسات الحقيقية: بدون --plane-w/--plane-l تكون الوحدات «طبيعية» (طول=1) والمساحة لا تُحسب."""
import sys, json, argparse, os
import numpy as np, cv2

def pose_from_H(H, K):
    A = np.linalg.inv(K) @ H
    a1, a2, a3 = A[:, 0], A[:, 1], A[:, 2]
    s = (np.linalg.norm(a1) + np.linalg.norm(a2)) / 2
    r1, r2, t = a1 / s, a2 / s, a3 / s
    if t[2] < 0: r1, r2, t = -r1, -r2, -t
    r3 = np.cross(r1, r2)
    U, _, Vt = np.linalg.svd(np.stack([r1, r2, r3], 1)); R = U @ Vt
    if np.linalg.det(R) < 0: R[:, 2] *= -1
    return R, t

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('video'); ap.add_argument('proj')
    ap.add_argument('--corners'); ap.add_argument('--fov', type=float); ap.add_argument('--plane-w', type=float); ap.add_argument('--plane-l', type=float)
    ap.add_argument('--margin', type=float, default=.10); ap.add_argument('--smooth', type=int, default=7); ap.add_argument('--max-w', type=int, default=960)
    ap.add_argument('--no-ecc', action='store_true'); ap.add_argument('--limit', type=int, default=0); ap.add_argument('--drift-every', type=int, default=3); ap.add_argument('--out', default=None)
    a = ap.parse_args()
    pj = json.load(open(os.path.join(a.proj, 'project.json')))
    cap = cv2.VideoCapture(a.video); W0 = int(cap.get(3)); H0 = int(cap.get(4)); fps = cap.get(5) or pj.get('fps', 30)
    sc = min(1.0, a.max_w / W0)
    if a.corners: C0 = np.array([[float(v) for v in p.split(',')] for p in a.corners.split(';')], np.float64)
    else: C0 = np.array(pj['corners'], np.float64)
    fov = a.fov or pj.get('fov') or 55.0
    frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(f, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA) if sc < 1 else f, cv2.COLOR_BGR2GRAY)
        frames.append((g, f if len(frames) == 0 else None))
        if a.limit and len(frames) >= a.limit: break
    n = len(frames); assert n > 1, 'no frames'
    h, w = frames[0][0].shape
    C0s = C0 * sc
    def mask_for(C):
        m = np.zeros((h, w), np.uint8); cen = C.mean(0); P = (cen + (C - cen) * (1 + a.margin * 2)).astype(np.int32)
        cv2.fillConvexPoly(m, P, 255); return m
    sift = cv2.SIFT_create(nfeatures=3000); bf = cv2.BFMatcher()
    blur = lambda g: cv2.GaussianBlur(g, (0, 0), 1.2)
    Hs = [np.eye(3)]  # frame0 -> frame i  (بكسل مصغّر)
    conf = [1.0]; flags = ['']
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 1e-6); crit_fine = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 15, 1e-6)
    cshift = lambda Ha, Hb: float(np.abs(cv2.perspectiveTransform(C0s[None], Ha)[0] - cv2.perspectiveTransform(C0s[None], Hb)[0]).max())
    def ecc(tmpl, img, Hinit, msk, gate_px):
        """ECC متعدد المقاييس (½ ثم 1): Hinit يحوّل إحداثيات tmpl→img. يُرجع (H, cc) أو None لو رُفض."""
        try:
            Hh = Hinit.astype(np.float32).copy(); S = np.diag([.5, .5, 1.0]).astype(np.float32); Si = np.linalg.inv(S)
            small = lambda g: cv2.resize(blur(g), None, fx=.5, fy=.5, interpolation=cv2.INTER_AREA)
            _, Hs_ = cv2.findTransformECC(small(tmpl), small(img), (S @ Hh @ Si).astype(np.float32), cv2.MOTION_HOMOGRAPHY, crit, cv2.resize(msk, None, fx=.5, fy=.5, interpolation=cv2.INTER_NEAREST), 5)
            Hh = (Si @ Hs_ @ S).astype(np.float32)
            cc, Hh = cv2.findTransformECC(blur(tmpl), blur(img), Hh, cv2.MOTION_HOMOGRAPHY, crit_fine, msk, 5)
            Hh = Hh.astype(np.float64)
            return (Hh, float(cc)) if cc > .6 and cshift(Hh, Hinit) < gate_px else None
        except cv2.error: return None
    for i in range(1, n):
        Hprev = Hs[-1]; Cprev = cv2.perspectiveTransform(C0s[None].astype(np.float64), Hprev)[0]
        gp, gc = frames[i - 1][0], frames[i][0]; mprev = mask_for(Cprev)
        kp1, d1 = sift.detectAndCompute(gp, mprev); kp2, d2 = sift.detectAndCompute(gc, None)
        Hstep, inl = np.eye(3), 0
        if d1 is not None and d2 is not None and len(kp1) > 8 and len(kp2) > 8:
            ms = [m for m, nn in (p for p in bf.knnMatch(d1, d2, k=2) if len(p) == 2) if m.distance < .75 * nn.distance]
            if len(ms) >= 8:
                s1 = np.float32([kp1[m.queryIdx].pt for m in ms]); s2 = np.float32([kp2[m.trainIdx].pt for m in ms])
                Hc, mk = cv2.findHomography(s1, s2, cv2.RANSAC, 1.5)
                if Hc is not None and mk is not None and int(mk.sum()) >= 10: Hstep, inl = Hc, int(mk.sum())
        flag = '' if inl >= 10 else 'feature_lost'; cc = min(1.0, inl / 100.0)
        if not a.no_ecc:   # (ب) تنقيح تزايدي: ECC بين الفريمين المتتاليين (حركة صغيرة ← يتقارب دائماً)
            if inl < 40:
                r = ecc(gp, gc, Hstep, mprev, 8 + 4 * sc)
                if r: Hstep, cc = r; flag = ''
                elif flag: flag = 'step_unrefined'
        H = Hstep @ Hprev
        if not a.no_ecc and (i % a.drift_every == 0 or i == n - 1):   # (ج) تصحيح الانجراف مقابل الفريم الأول (يُقبل فقط لو تغيّر بسيط)
            r = ecc(frames[0][0], gc, H, mask_for(C0s), 3 + 2 * sc)
            if r: H, cc = r
        Hs.append(H); conf.append(float(min(1, max(0, cc)))); flags.append(flag)
        if i % 30 == 0: print(f'  track {i}/{n}', end='\r')
    # زوايا لكل فريم بالبكسل الأصلي
    C = np.stack([cv2.perspectiveTransform(C0s[None], H)[0] for H in Hs]) / sc
    raw = C.copy()
    if a.smooth > 2:  # تنعيم Savitzky-Golay بسيط (متعدد حدود درجة 2) — يقلّل الاهتزاز بلا تأخير
        k = a.smooth | 1; half = k // 2; xs = np.arange(-half, half + 1); V = np.vander(xs, 3); Pm = np.linalg.pinv(V)[2]
        pad = np.concatenate([C[:1].repeat(half, 0), C, C[-1:].repeat(half, 0)])
        C = np.stack([np.tensordot(Pm, pad[i:i + k], axes=(0, 0)) for i in range(n)])
    # أبعاد المستوى + K
    K = np.array([[(H0 / 2) / np.tan(np.radians(fov) / 2), 0, W0 / 2], [0, (H0 / 2) / np.tan(np.radians(fov) / 2), H0 / 2], [0, 0, 1]])
    if a.plane_w and a.plane_l: pw, pl, units = a.plane_w, a.plane_l, 'meters'
    else:
        Hu = cv2.getPerspectiveTransform(np.float32([[0, 0], [1, 0], [1, 1], [0, 1]]), C[0].astype(np.float32)); A = np.linalg.inv(K) @ Hu
        pw, pl, units = float(np.linalg.norm(A[:, 0]) / np.linalg.norm(A[:, 1])), 1.0, 'normalized'
    Pw = np.float32([[-pw / 2, -pl / 2], [pw / 2, -pl / 2], [pw / 2, pl / 2], [-pw / 2, pl / 2]])  # (x, y_cv) ; TL ← (x=-w/2, Y'=+l/2 ⇒ y_cv=-l/2)
    out = []
    for i in range(n):
        Hi = cv2.getPerspectiveTransform(Pw, C[i].astype(np.float32)).astype(np.float64)
        R, t = pose_from_H(Hi, K)
        out.append({'i': i, 'R': R.flatten().tolist(), 't': t.tolist(), 'corners': C[i].tolist(), 'raw_corners': raw[i].tolist(), 'conf': round(conf[i], 3), 'flag': flags[i]})
    f0 = frames[0][1]; m = np.zeros(f0.shape[:2], np.uint8); cv2.fillConvexPoly(m, C[0].astype(np.int32), 255); gc_ = cv2.mean(f0, m)[:3][::-1]
    res = {'version': 1, 'width': W0, 'height': H0, 'fps': fps, 'fov_deg': fov, 'plane': {'w': pw, 'l': pl, 'units': units, 'area_m2': (pw * pl if units == 'meters' else None)},
           'corners_px0': C0.tolist(), 'ground_color': [round(v) for v in gc_], 'frames': out}
    json.dump(res, open(a.out or os.path.join(a.proj, 'track.json'), 'w'))
    lowc = sum(1 for o in out if o['flag']); print(f'\n✓ track.json — {n} frames, plane {pw:.3f}×{pl:.3f} ({units}), flagged {lowc}')

if __name__ == '__main__': main()
