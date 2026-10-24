#!/usr/bin/env python3
"""اختبار قابلية إعادة الاستخدام + إنفاذ قواعد الصدق: نفس المحرك، مدخلات JSON مختلفة، نسب مختلفة، بلا لمس الكود."""
import os, sys, json, subprocess, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'tools')); import amx
M = os.path.join(ROOT, 'projects', 'matrix'); OUT = os.path.join(ROOT, 'projects', 'reuse'); res = []
def mk(name, src, recipe, aspect, params, dur):
    d = os.path.join(OUT, name); shutil.rmtree(d, ignore_errors=True); amx.make_project(os.path.join(M, src), d, recipe, aspect, params, dur); return d
def neg(name, src, recipe, aspect, params, expect):
    d = mk(name, src, recipe, aspect, params, 3); r = subprocess.run(['node', amx.E, d, '--scale', '.25', '--frames', '0-1', '--no-encode'], capture_output=True, text=True)
    ok = r.returncode != 0 and expect in (r.stderr + r.stdout); res.append({'test': name, 'type': 'policy-negative', 'expect_error_contains': expect, 'passed': ok}); print(('✓' if ok else '✗'), name, '— رُفض كما يجب' if ok else (r.stderr[-200:]))
# إعادة استخدام: نص مختلف/beats متعددة/خامة مختلفة/نسبة مختلفة
d = mk('reuse_stone_2beats_169', 'plate_land_169', 'stone_text', '16:9', {'font': 'Tajawal Black', 'material': 'sandstone', 'beats': [
    {'lines': ['فيلا فاخرة'], 't0': .2, 'rise': 1.0, 'hold': .6, 'sink': .5, 'size': .7, 'anchor': [0, .1]}, {'lines': ['للبيع'], 't0': 2.2, 'rise': 1.0, 'hold': .6, 'sink': .5, 'size': .5, 'anchor': [0, .1]}]}, 4)
amx.render(d, .5); res.append({'test': 'reuse_stone_2beats_169', 'type': 'reuse', 'qa': amx.qa(d, os.path.join(M, 'plate_land_169'))})
d = mk('reuse_holo_noarea_45', 'plate_land_45', 'land_hologram', '4:5', {'building': {'approved': True, 'source': 'نموذج المهندس م. أحمد — v3', 'boxes': [{'u': .5, 'v': .5, 'du': .3, 'dv': .4, 'floors': 5}]}, 'timing': {'outline': [.15, .9], 'fill': [.6, 1.2], 'build': [1.4, 2.6], 'badge': [.3, .6]}}, 4)
amx.render(d, .5); res.append({'test': 'reuse_holo_noarea_45', 'type': 'reuse', 'qa': amx.qa(d, os.path.join(M, 'plate_land_45'))})
d = mk('reuse_outline_2cards_916', 'plate_facade_916', 'building_outline', '9:16', {'color': '#ffc14d', 'core': '#fff3d1', 'timing': {'outline': [.1, .8], 'major': [.6, 1.8], 'detail': [1.0, 2.4]}, 'cards': [{'text': 'للإيجار', 'u': .2, 'v': .12, 'dx': 3, 'dy': -14, 'at': 2.0, 'color': '#ffc14d'}, {'text': '٣ غرف نوم', 'sub': 'مساحة البناء ٣٠٠ م²', 'u': .8, 'v': .75, 'dx': -3, 'dy': 20, 'at': 2.4, 'color': '#ffc14d'}]}, 4)
amx.render(d, .5); res.append({'test': 'reuse_outline_2cards_916', 'type': 'reuse', 'qa': amx.qa(d, os.path.join(M, 'plate_facade_916'))})
# سياسات الصدق (يجب أن تفشل بوضوح)
neg('neg_building_without_approved', 'plate_land_916', 'land_hologram', '9:16', {'building': {'boxes': [{'u': .5, 'v': .5, 'du': .3, 'dv': .3, 'floors': 3}]}}, 'building.approved')
neg('neg_approved_without_source', 'plate_land_916', 'land_hologram', '9:16', {'building': {'approved': True, 'boxes': [{'u': .5, 'v': .5, 'du': .3, 'dv': .3, 'floors': 3}]}}, 'building.source')
neg('neg_area_not_number', 'plate_land_916', 'land_hologram', '9:16', {'area_m2': 'حوالي ألفين'}, 'area_m2')
neg('neg_unapproved_plan', 'plate_land_916', 'land_hologram', '9:16', {'plan': {'approved': False, 'footprints': []}}, 'plan.approved')
json.dump(res, open(os.path.join(ROOT, 'reports', 'reuse_policy.json'), 'w'), ensure_ascii=False, indent=1)
for r in res:
    if r['type'] == 'reuse': print(r['qa'][-420:])
