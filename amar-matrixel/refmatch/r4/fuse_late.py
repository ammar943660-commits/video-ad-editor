#!/usr/bin/env python3
"""fuse_late.py — يدمج تتبع المدينة (حركة دقيقة فريماً بفريم، lot_track.bak.json) مع مفاتيح الزوايا المحلولة (موضع مطلق صحيح):
   خطأ كل مفتاح = مفتاح − تتبع، ويُوزَّع خطياً بين المفاتيح (190 مرساة بخطأ صفر). python3 fuse_late.py <work>"""
import json,numpy as np,sys
W=sys.argv[1]; T=json.load(open(f'{W}/lot_track.json')); B=json.load(open(f'{W}/lot_track.bak.json'))['snapped']
K={int(k):np.array(v) for k,v in T['late_keys'].items()}; ks=[190]+sorted(K); err={190:np.zeros((4,2))}
for k in K: err[k]=K[k]-np.array(B[k])
S=T['snapped']
for f in range(190,287):
    if f>=ks[-1]: e=err[ks[-1]]
    else:
        a=max(k for k in ks if k<=f); b=min(k for k in ks if k>f); u=(f-a)/(b-a); e=err[a]*(1-u)+err[b]*u
    S[f]=(np.array(B[f])+e).tolist()
T['snapped']=S; json.dump(T,open(f'{W}/lot_track.json','w')); print({k:np.abs(v).max().round(1) for k,v in err.items()})
