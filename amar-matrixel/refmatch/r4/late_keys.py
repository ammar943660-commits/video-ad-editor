#!/usr/bin/env python3
"""late_keys.py — كاميرا المرحلة الأخيرة في R4 (المباني تحجب القطعة): 3 زوايا مرئية لإطار القاعدة لكل فريم مفتاحي (قراءة يدوية)
   ← حل وضعية الكاميرا (least squares، دوران ≈ بلا ميلان أفقي) لمستطيل القطعة المعروف ← رباعي كامل؛ ثم PCHIP بين المفاتيح ومزج مع التتبع.
   الترتيب: TL,TR,BL مرئية (BR مخفية). python3 late_keys.py <work>"""
import numpy as np,json,sys,cv2,math
from scipy.optimize import least_squares
from scipy.interpolate import PchipInterpolator
W=sys.argv[1]; import os; C=json.load(open(os.environ.get('R4CFG','r4_cfg.json'))); LW,LH=C['lot_m']; w,h=1146,644; f=(w/2)/math.tan(math.radians(C['fov_deg'])/2)
K=np.array([[f,0,w/2],[0,f,h/2],[0,0,1]])
KEYS={238:{'TL':(411,600),'TR':(211,317),'BL':(989,411)},252:{'TL':(517,598),'TR':(178,339),'BL':(944,400)},
      266:{'TL':(550,600),'TR':(144,361),'BL':(944,361)},280:{'TL':(678,594),'TR':(133,372),'BL':(928,350)}}
Wp={'TL':(0,0,0),'TR':(LW,0,0),'BR':(LW,LH,0),'BL':(0,LH,0)}
T=json.load(open(f'{W}/lot_track.json')); S=T['snapped']
def project(x,P):
    rv,tv=x[:3],x[3:]; uv,_=cv2.projectPoints(np.float64(P),rv,tv,K,None); return uv.reshape(-1,2)
def init_from(q):
    ok,rv,tv=cv2.solvePnP(np.float64([Wp[k] for k in ('TL','TR','BR','BL')]),np.float64(q),K,None,flags=cv2.SOLVEPNP_IPPE); return np.concatenate([rv.ravel(),tv.ravel()])
x=init_from(S[190]); out={}
for fr in sorted(KEYS):
    xprev=x.copy(); kk=KEYS[fr]; P=[Wp[k] for k in kk]; Ob=np.float64([kk[k] for k in kk])
    def res(x):
        r=(project(x,P)-Ob).ravel()
        R,_=cv2.Rodrigues(x[:3]); up_img=R@np.array([0,0,-1.0])   # محور Z العالمي للأعلى يجب أن يكون رأسياً في الصورة (بلا ميلان)
        return np.concatenate([r,[40*up_img[0]/max(np.linalg.norm(up_img[:2]),1e-6)],(x-xprev)*np.array([30,30,30,0.5,0.5,0.5])*(1 if len(kk)<3 else 0.1)])
    best=None
    for s in range(12):
        x0=x.copy() if s==0 else x+np.random.RandomState(s).normal(0,[0.3,0.3,0.3,10,10,20])
        r=least_squares(res,x0,max_nfev=4000)
        uv=project(r.x,[Wp[k] for k in ('TL','TR','BR','BL')]); R,_=cv2.Rodrigues(r.x[:3]); cz=(-R.T@r.x[3:])[2]
        if (best is None or r.cost<best[0]) and cz<0 : best=(r.cost,r.x,uv)   # الكاميرا فوق الأرض (Z الكاميرا سالب في نظام opencv المختار)
    if best is None:
        for s in range(12):
            r=least_squares(res,x+np.random.RandomState(s).normal(0,[0.3,0.3,0.3,10,10,20]),max_nfev=4000); uv=project(r.x,[Wp[k] for k in ('TL','TR','BR','BL')])
            if best is None or r.cost<best[0]: best=(r.cost,r.x,uv)
    x=best[1]; out[fr]=best[2]; print(fr,'cost',round(best[0],1),np.round(best[2]).astype(int).tolist())
ks=[186,188,190]+sorted(out); Qk=np.array([S[k] for k in (186,188,190)]+[out[k] for k in sorted(out)]).reshape(len(ks),8)
fs=np.arange(186,287); Qi=np.stack([PchipInterpolator(ks,Qk[:,j],extrapolate=True)(fs) for j in range(8)],1).reshape(-1,4,2)
for i,fr in enumerate(fs): S[fr]=Qi[i].tolist()
T['snapped']=S; T['late_keys']={str(k):v.tolist() for k,v in out.items()}; json.dump(T,open(f'{W}/lot_track.json','w'))
