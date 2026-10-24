#!/usr/bin/env python3
"""detect_edges.py — اكتشاف حواف الواجهة مرة واحدة داخل «فضاء الواجهة المعدَّل» (Rectified) لا بكل فريم.
  python3 detect_edges.py <video|image> <project_dir> [--rect-w 1600] [--min-len 0.03] [--angle 3.0]
يقرأ track.json (corners_px0 + plane) ويكتب edges.json (إحداثيات u,v ∈ [0,1]، v من الأعلى) + edges_debug.png.
الإحداثيات النسبية تُتتبَّع بـ pose الواجهة، فلا تهتز ولا تنزلق (بدل اكتشاف الحواف على كل فريم).
المستخدم يستطيع تعديل edges.json يدوياً (حذف/إضافة خطوط) — الوصفة تقرأه كما هو."""
import sys, json, argparse, os
import numpy as np, cv2

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('proj'); ap.add_argument('--rect-w', type=int, default=1600)
    ap.add_argument('--min-len', type=float, default=.03); ap.add_argument('--angle', type=float, default=3.0); ap.add_argument('--merge', type=float, default=.006)
    a = ap.parse_args()
    tr = json.load(open(os.path.join(a.proj, 'track.json')))
    cap = cv2.VideoCapture(a.src); ok, img = cap.read(); assert ok, 'cannot read ' + a.src
    pw, pl = tr['plane']['w'], tr['plane']['l']; Wr = a.rect_w; Hr = int(round(Wr * pl / pw))
    C = np.float32(tr['corners_px0']); M = cv2.getPerspectiveTransform(C, np.float32([[0, 0], [Wr, 0], [Wr, Hr], [0, Hr]]))
    rect = cv2.warpPerspective(img, M, (Wr, Hr), flags=cv2.INTER_CUBIC)
    g = cv2.createCLAHE(2.0, (8, 8)).apply(cv2.cvtColor(rect, cv2.COLOR_BGR2GRAY)); g = cv2.GaussianBlur(g, (0, 0), 1.2)
    med = np.median(g); ed = cv2.Canny(g, int(max(0, .66 * med)), int(min(255, 1.33 * med + 30)))
    lines = cv2.HoughLinesP(ed, 1, np.pi / 360, threshold=int(Wr * .02), minLineLength=int(Wr * a.min_len), maxLineGap=int(Wr * .012))
    H_, V_ = [], []
    for l in (np.asarray(lines).reshape(-1, 4) if lines is not None else []):
        x0, y0, x1, y1 = map(float, l); ang = np.degrees(np.arctan2(y1 - y0, x1 - x0)) % 180
        if min(ang, 180 - ang) < a.angle: H_.append((np.mean([y0, y1]) / Hr, min(x0, x1) / Wr, max(x0, x1) / Wr))
        elif abs(ang - 90) < a.angle: V_.append((np.mean([x0, x1]) / Wr, min(y0, y1) / Hr, max(y0, y1) / Hr))
    def merge(items, tol):  # يدمج الخطوط المتوازية المتقاربة والمتداخلة
        items = sorted(items); out = []
        for p, s, e in items:
            for o in out:
                if abs(o['p'] - p) < tol and s <= o['e'] + .08 and e >= o['s'] - .08:
                    n = o['n']; o['p'] = (o['p'] * n + p) / (n + 1); o['s'] = min(o['s'], s); o['e'] = max(o['e'], e); o['n'] = n + 1; break
            else: out.append({'p': p, 's': s, 'e': e, 'n': 1})
        return [o for o in out if (o['e'] - o['s']) >= a.min_len]
    Hm, Vm = merge(H_, a.merge), merge(V_, a.merge * Hr / Wr)
    segs = []
    for o in Hm: segs.append({'u0': o['s'], 'v0': o['p'], 'u1': o['e'], 'v1': o['p'], 'n': o['n']})
    for o in Vm: segs.append({'u0': o['p'], 'v0': o['s'], 'u1': o['p'], 'v1': o['e'], 'n': o['n']})
    for s in segs:
        L = np.hypot((s['u1'] - s['u0']) * pw, (s['v1'] - s['v0']) * pl) / pl
        edge = min(s['u0'], s['v0'], 1 - s['u1'], 1 - s['v1']) if False else 0
        s['kind'] = 'major' if L > .35 else 'detail'
        s['score'] = round(min(1, s['n'] / 6), 2)
    # الإطار الخارجي (الواجهة كاملة)
    outline = [{'u0': 0, 'v0': 0, 'u1': 1, 'v1': 0, 'kind': 'outline', 'score': 1}, {'u0': 1, 'v0': 0, 'u1': 1, 'v1': 1, 'kind': 'outline', 'score': 1},
               {'u0': 1, 'v0': 1, 'u1': 0, 'v1': 1, 'kind': 'outline', 'score': 1}, {'u0': 0, 'v0': 1, 'u1': 0, 'v1': 0, 'kind': 'outline', 'score': 1}]
    # أزل ما التصق بالحدود (يُغطّى بالإطار)
    segs = [s for s in segs if not ((abs(s['v0']) < .012 and abs(s['v1']) < .012) or (abs(s['v0'] - 1) < .012 and abs(s['v1'] - 1) < .012) or (abs(s['u0']) < .008 and abs(s['u1']) < .008) or (abs(s['u0'] - 1) < .008 and abs(s['u1'] - 1) < .008))]
    allsegs = outline + segs
    for i, s in enumerate(allsegs): s['id'] = i; [s.__setitem__(k, round(float(s[k]), 5)) for k in ('u0', 'v0', 'u1', 'v1')]
    json.dump({'space': 'uv', 'v_origin': 'top', 'source': 'auto: Canny+HoughP in rectified plane', 'rect_size': [Wr, Hr], 'segments': allsegs}, open(os.path.join(a.proj, 'edges.json'), 'w'), ensure_ascii=False, indent=1)
    dbg = rect.copy()
    for s in allsegs: cv2.line(dbg, (int(s['u0'] * Wr), int(s['v0'] * Hr)), (int(s['u1'] * Wr), int(s['v1'] * Hr)), (255, 255, 0) if s['kind'] != 'detail' else (0, 255, 255), 2)
    cv2.imwrite(os.path.join(a.proj, 'edges_debug.png'), dbg)
    print(f"✓ edges.json — {len(allsegs)} segments ({len(Hm)} horizontal, {len(Vm)} vertical)")
if __name__ == '__main__': main()
