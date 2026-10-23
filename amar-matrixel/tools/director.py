#!/usr/bin/env python3
"""director.py — فحص إخراجي مسبق (Preflight) قبل الريندر، يقرأ direction/director.json.
  python3 director.py <project_dir>      ← يخرج برمز 1 لو وُجد خطأ مانع. لا يستهلك أي كريدت.
يفحص: نوع المشهد المناسب (يطلب تأكيداً)، المدد، FOV، دقة اللقطة، سلامة التتبع، قواعد الصدق، وجود الملفات."""
import sys, os, json
import cv2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = json.load(open(os.path.join(ROOT, 'direction', 'director.json')))
def main():
    pd = sys.argv[1]; pj = json.load(open(os.path.join(pd, 'project.json'))); rec = pj['recipe']; key = next((k for k, v in D.items() if isinstance(v, dict) and v.get('recipe') == rec), None)
    out = []; add = lambda lv, m: out.append((lv, m))
    if not key: print('✗ وصفة غير معروفة', rec); sys.exit(1)
    d = D[key]; dur = pj.get('duration', 4); lo, hi = d['duration_s']['total']
    add('ok' if lo <= dur <= hi else 'warn', f'المدة {dur}ث (الموصى {lo}–{hi}ث)')
    tp = os.path.join(pd, 'track.json'); tr = json.load(open(tp)) if os.path.exists(tp) else None
    if rec != 'camera_motion':
        if not tr: add('error', 'لا يوجد track.json — شغّل tools/track.py (النقاط الأربع قابلة للتعديل في project.json ▸ corners)')
        else:
            fo = d['camera']['fov_deg']; add('ok' if fo[0] <= tr['fov_deg'] <= fo[1] else 'warn', f'FOV المفترض {tr["fov_deg"]}° (الموصى {fo[0]}–{fo[1]}°) — خطأ FOV يزيح المنظور')
            fl = sum(1 for f in tr['frames'] if f['flag']); add('ok' if fl / len(tr['frames']) < .05 else 'error', f'فريمات التتبع المعلّمة: {fl}/{len(tr["frames"])}')
            if tr['plane']['units'] != 'meters': add('warn', 'أبعاد المستوى نسبية (لم تُدخل plane_w/plane_l): لن تظهر مساحة، وارتفاعات المبنى تقريبية')
        plate = os.path.join(pd, pj.get('plate', 'plate.mp4'))
        if os.path.exists(plate):
            c = cv2.VideoCapture(plate); w, h = int(c.get(3)), int(c.get(4)); add('ok' if min(w, h) >= 540 else 'warn', f'دقة اللقطة {w}×{h}')
        else: add('error', 'اللقطة غير موجودة: ' + plate)
    P = pj.get('params', {})
    if rec == 'stone_text':
        for b in P.get('beats', []):
            r = d['duration_s']; add('ok' if r['rise'][0] <= b.get('rise', 1.5) <= r['rise'][1] else 'warn', f'صعود {b.get("rise", 1.5)}ث (الموصى {r["rise"]})')
            if len(''.join(b['lines'])) > 24: add('warn', 'نص طويل (>24 حرفاً): قلّل أو قسّم على beats وإلا ينخفض الوضوح')
    if rec == 'land_hologram':
        if P.get('area_m2') and not P.get('area_source'): add('warn', 'area_m2 بلا area_source — يُنصح بإظهار مصدر المساحة')
        if not P.get('area_m2'): add('ok', 'لا مساحة: لن يُعرض رقم (سياسة الصدق)')
        b = P.get('building')
        if b is not None and not isinstance(b.get('approved'), bool): add('error', 'building.approved مطلوب صراحة')
        if b and not b['approved']: add('ok', 'المبنى غير معتمد ← ستظهر شارة «تصور مبدئي» تلقائياً')
    if rec == 'building_outline':
        ep = os.path.join(pd, 'edges.json'); add('ok' if os.path.exists(ep) else 'error', 'edges.json ' + ('موجود' if os.path.exists(ep) else 'غير موجود — شغّل tools/detect_edges.py'))
        cs = P.get('cards', []); add('ok' if len(cs) <= 4 else 'warn', f'{len(cs)} بطاقة (الموصى ≤ 4 بالعمودي)')
    print(f'── Preflight [{key}] ──'); bad = 0
    for lv, m in out: print({'ok': '  ✓', 'warn': '  ⚠', 'error': '  ✗'}[lv], m); bad += lv == 'error'
    print('  best_scenes:', ' | '.join(d['best_scenes'])); print('  avoid:', ' | '.join(d['avoid_scenes'])); sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
