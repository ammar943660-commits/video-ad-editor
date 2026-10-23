#!/usr/bin/env python3
"""neon.py — طبقة نيون حدود الأرض (RGBA، إضافية) لكل فريم من رباعي المفاتيح (نفس PCHIP الخاص بالكاميرا).
   رسم تدريجي TL→TR→BR→BL→TL في الفريمات 1–21، ثم محو تدريجي من البداية بعد ~240. python3 neon.py <work> <out_dir> [n]"""
import numpy as np,cv2,json,sys,os
from scipy.interpolate import PchipInterpolator
W,OUT=sys.argv[1:3]; n=int(sys.argv[3]) if len(sys.argv)>3 else 292; os.makedirs(OUT,exist_ok=True)
kf=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'keyframes.json')))['frames']; ks=sorted(int(k) for k in kf); Hs=np.load(f'{W}/cam_H.npy')
arr=np.array([kf[str(k)] for k in ks],float).reshape(len(ks),8)
Q=np.stack([PchipInterpolator(ks,arr[:,j])(np.arange(0,231)) for j in range(8)],1).reshape(-1,4,2)
ext=[Q[230]]
for i in range(231,n): ext.append(cv2.perspectiveTransform(ext[-1][None].astype(np.float64),Hs[i]@np.linalg.inv(Hs[i-1]))[0])
Q=np.concatenate([Q,np.array(ext)],0)
NB=400; SS=np.linspace(0,4,NB+1)
def mk(iv): return np.array([1.0 if any(a<=x<=b for a,b in iv) else 0.0 for x in SS])
# مفاتيح ظهور النيون (قُرئت من فريمات المرجع 150/175/190/230/285؛ أجزاء الإطفاء تقريبية)
MASK={150:mk([(0,4)]),162:mk([(0,4)]),168:mk([(1.0,2.4)]),174:mk([(1.4,2.3)]),180:mk([(0.4,2.0)]),186:mk([(0,2.0)]),192:mk([(0,2.0),(2.5,3.1)]),198:mk([(0.2,2.0),(2.2,3.4)]),204:mk([(0,4)]),210:mk([(0,4)]),258:mk([(0,4)]),270:mk([(1.0,3.9)]),276:mk([(1.2,2.1)]),282:mk([(1.3,2.1)]),288:mk([(1.8,2.1)]),292:mk([])}
MK=sorted(MASK)
def mask(f):
    if f<=26: p=np.clip((f-3)/23,0,1); return (SS<=p*4).astype(float)
    if f<=150: return np.ones(NB+1)
    for a,b in zip(MK[:-1],MK[1:]):
        if a<=f<=b: u=(f-a)/(b-a); return MASK[a]*(1-u)+MASK[b]*u
    return np.zeros(NB+1)
def pt(q,s):
    i=int(min(np.floor(s),3)); u=s-i; return q[i]+(q[(i+1)%4]-q[i])*u
for f in range(n):
    q=Q[f]; m=mask(f); L=np.zeros((644,1146,3),np.float32)
    if m.max()>0.01:
        sc=2; core=np.zeros((644*sc,1146*sc),np.float32)
        for k in range(NB):
            w=(m[k]+m[k+1])/2
            if w<0.02: continue
            P=np.array([pt(q,SS[k]),pt(q,SS[k+1])],np.float32)
            cv2.polylines(core,[np.round(P*sc*16).astype(np.int32)[None]],False,float(w),3*sc,cv2.LINE_AA,4)
        core=cv2.resize(core,(1146,644),interpolation=cv2.INTER_AREA)
        g1=cv2.GaussianBlur(core,(0,0),2.5); g2=cv2.GaussianBlur(core,(0,0),9); g3=cv2.GaussianBlur(core,(0,0),24)
        col=np.array([1.0,0.80,0.12])
        L=(core[...,None]*np.array([1.0,0.97,0.72])*0.7+g1[...,None]*col*1.3+g2[...,None]*np.array([1.0,0.65,0.05])*0.9+g3[...,None]*np.array([1.0,0.6,0.05])*0.3).astype(np.float32)
    cv2.imwrite(f'{OUT}/{f+1:04d}.png',np.clip(L*255,0,255).astype(np.uint8))
