#!/usr/bin/env python3
"""make_report.py — يجمّع qa_report.json لكل مشروع + camera_qa.json + فحوص التصدير في reports/TEST_REPORT.md
والمعاينات (mp4 + contact sheets) في previews/. التصنيف: ✅ مختبر وناجح · 🟡 منفذ ويحتاج تصحيحاً · ❌ غير منفذ."""
import os, sys, json, glob, shutil, subprocess, py_compile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); M = os.path.join(ROOT, 'projects', 'matrix'); PV = os.path.join(ROOT, 'previews'); os.makedirs(PV, exist_ok=True)
def J(p): return json.load(open(p)) if os.path.exists(p) else None
def sheet(pd, out, n=6):
    ri = J(os.path.join(pd, 'renders', 'render-info.json')); pv = os.path.join(pd, 'renders', 'preview.mp4')
    if not os.path.exists(pv): return
    shutil.copy(pv, os.path.join(PV, os.path.basename(pd) + '.mp4'))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pv, '-vf', f"select='not(mod(n\\,{max(1, (ri['last'] - ri['first'] + 1) // n)}))',scale=-1:{360 if ri['H'] > ri['W'] else 270},tile={n}x1", '-frames:v', '1', out], check=False)
def static_exports():
    res = {}; cand = sorted(glob.glob(os.path.join(M, 'stone_text_916'))) 
    if not cand: return res
    pd = cand[0]; subprocess.run(['python3', os.path.join(ROOT, 'tools', 'export.py'), pd], capture_output=True)
    ex = os.path.join(pd, 'export')
    try:
        import xml.dom.minidom as md; md.parse(os.path.join(ex, 'premiere.xml')); res['premiere.xml'] = 'XML سليم (parse OK) — غير مُستورد في Premiere'
    except Exception as e: res['premiere.xml'] = f'خطأ XML: {e}'
    r = subprocess.run(['node', '--check', os.path.join(ex, 'ae_build.jsx')], capture_output=True, text=True); res['ae_build.jsx'] = 'صياغة JS سليمة (node --check) — غير مُشغَّل في After Effects' if r.returncode == 0 else 'خطأ صياغة: ' + r.stderr[:200]
    try: py_compile.compile(os.path.join(ex, 'blender_build.py'), doraise=True); res['blender_build.py'] = 'صياغة Python سليمة — غير مُشغَّل في Blender'
    except Exception as e: res['blender_build.py'] = f'خطأ: {e}'
    for f in os.listdir(os.path.join(pd, 'renders')):
        pass
    return res
def main():
    rows = []; md = ['# تقرير الاختبار — AMAR Matrixel\n', f'> مولَّد تلقائياً بـ `tools/make_report.py` — {__import__("datetime").date.today()}\n']
    for tag in ('916', '45', '169'):
        for rec in ('stone_text', 'land_hologram', 'building_outline'):
            pd = os.path.join(M, f'{rec}_{tag}'); q = J(os.path.join(pd, 'qa_report.json'))
            if q: rows.append((rec, tag, q)); sheet(pd, os.path.join(PV, f'{rec}_{tag}_sheet.jpg'))
    md.append('## 1) نتائج QA الآلي لكل مؤثر × نسبة (مواد اختبار تركيبية بحقيقة أرضية)\n'); md.append('| المؤثر | النسبة | الحكم | فحوص فاشلة | ملاحظات |\n|---|---|---|---|---|')
    for rec, tag, q in rows:
        fails = [c for c in q['checks'] if c['status'] == 'fail']; md.append(f"| {q['effect']} | {q['aspect']} | **{q['verdict']}** | {', '.join(c['name'] for c in fails) or '—'} | {'؛ '.join(q['reject_reasons']) or ''} |")
    md.append('\n## 2) تفاصيل القياسات\n')
    for rec, tag, q in rows:
        md.append(f"\n### {q['project']} — {q['effect']} {q['aspect']} ({q['size'][0]}×{q['size'][1]})\n\n| الفحص | القيمة | العتبة | الحالة | ملاحظة |\n|---|---|---|---|---|")
        for c in q['checks']: md.append(f"| {c['name']} | {c['value']} {c['unit']} | {c['mode']} {c['threshold']} | {c['status']} | {c['note']} |")
    cq = J(os.path.join(ROOT, 'reports', 'camera_qa.json'))
    if cq:
        md.append('\n## 3) D · CINEMATIC_CAMERA_MOTION\n\n| الحالة | الحكم | القياسات |\n|---|---|---|')
        for r in cq: md.append(f"| {r['name']} | {r['verdict']}{' (رفض متوقع ✓)' if r.get('expect_reject') and r.get('pass_reject') else ''} | " + (', '.join(f"{c['name']}={c['value']}{'✗' if c['status']=='fail' else ''}" for c in r['checks']) or (r.get('rejected') or '')[:120]) + ' |')
    ex = static_exports()
    if ex: md.append('\n## 4) ملفات التصدير (فحص ثابت فقط)\n' + '\n'.join(f'- `{k}`: {v}' for k, v in ex.items()))
    open(os.path.join(ROOT, 'reports', 'TEST_REPORT.auto.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n'); print('✓ reports/TEST_REPORT.auto.md')
if __name__ == '__main__': main()
