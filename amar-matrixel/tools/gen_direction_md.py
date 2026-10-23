#!/usr/bin/env python3
"""يولّد direction/DIRECTION.md من director.json (مصدر الحقيقة الوحيد)."""
import json, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = json.load(open(f'{R}/direction/director.json')); o = ['# دليل الإخراج — AMAR Matrixel\n', '> مولَّد تلقائياً من `director.json`. عدّل الـJSON ثم شغّل `python3 tools/gen_direction_md.py`.\n']
L = lambda xs: '\n'.join(f'- {x}' for x in xs)
for k, v in D.items():
    if not isinstance(v, dict): continue
    o += [f'\n## {k}  (`{v["recipe"]}`)\n', '### أفضل أنواع المشاهد\n' + L(v['best_scenes']), '\n### تجنّب\n' + L(v['avoid_scenes']), '\n### المدد (ثانية)\n' + L(f'{a}: {b[0]}–{b[1]}' for a, b in v['duration_s'].items()),
          '\n### الكاميرا والعدسة والمنظور\n' + L(f'{a}: {b}' for a, b in v['camera'].items()), '\n### الإضاءة والظلال\n' + L(f'{a}: {b}' for a, b in v['lighting'].items()), '\n### الحركة والتسارع والتباطؤ\n' + L(f'{a}: {b}' for a, b in v['motion'].items()),
          '\n### مؤثرات الصوت\n' + L(v['sfx']), '\n### الدمج مع اللقطات المجاورة\n' + L(f'{a}: {b}' for a, b in v['blend'].items())]
    if 'honesty' in v: o.append('\n### قواعد الصدق\n' + L(v['honesty']))
    o += ['\n### بوابات الجودة (قابلة للقياس)\n' + L(f'`{a}` {"≥" if a in ("ocr_similarity","text_height_pct","stroke_rel_pct","stab_improvement_x") else "≤"} {b}' for a, b in v['quality_gates'].items()),
          '\n### متى تُرفض النتيجة\n' + L(f'`{a}` — {v["reject_reasons"][a]}' for a in v['reject_if'])]
open(f'{R}/direction/DIRECTION.md', 'w', encoding='utf-8').write('\n'.join(o) + '\n'); print('✓ DIRECTION.md')
