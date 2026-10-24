#!/usr/bin/env python3
"""make_text_shapes.py — نص (أسطر متعددة، عربي/لاتيني مُشكَّل HarfBuzz) → shapes.json بإحداثيات مستوى النص بالمتر (x من 0 إلى العرض، y من 0 للأعلى)
   مضبوط على صندوق المرجع (width_m × height_m). كل سطر في المنتصف. /tmp/bpyenv/bin/python make_text_shapes.py "<سطر1>\\n<سطر2>" font.ttf W H out.json [line_gap=0.18] [wght]"""
import sys,os,json
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from glyphs import polygons
txt=sys.argv[1].replace('\\n','\n'); font=sys.argv[2]; Wm,Hm=float(sys.argv[3]),float(sys.argv[4]); out=sys.argv[5]; gap=float(sys.argv[6]) if len(sys.argv)>6 else 0.18; wght=int(sys.argv[7]) if len(sys.argv)>7 else 800
lines=txt.split('\n'); L=[polygons(l,font,wght) for l in lines]
hs=[yr[1]-yr[0] for _,_,yr in L]; ws=[xr[1]-xr[0] for _,xr,_ in L]; tot=sum(hs)+gap*(len(L)-1); sy=Hm/tot; sx=Wm/max(ws)
shapes=[]; ytop=Hm
for (polys,xr,yr),hh in zip(L,hs):
    y0=ytop-hh*sy; cx=(xr[0]+xr[1])/2
    T=lambda p:(Wm/2+(p[0]-cx)*sx, y0+(p[1]-yr[0])*sy)
    for ext,holes in polys: shapes.append({'outer':[T(p) for p in ext],'holes':[[T(p) for p in h] for h in holes]})
    ytop=y0-gap*sy
json.dump({'shapes':shapes,'width_m':Wm,'height_m':Hm,'sx_over_sy':sx/sy},open(out,'w')); print(out,len(shapes),'sx/sy',round(sx/sy,3))
