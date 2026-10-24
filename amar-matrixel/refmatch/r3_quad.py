#!/usr/bin/env python3
"""r3_quad.py — رباعي حدود الأرض لكل فريم من خط النيون نفسه: RANSAC متسلسل لأربعة خطوط ثم تقاطعها، مع تنعيم زمني."""
import cv2,numpy as np,glob,json,sys
from scipy.ndimage import gaussian_filter1d
W=sys.argv[1]; fs=sorted(glob.glob(f'{W}/frames/*.png')); n=int(sys.argv[2])
def cyan(im):
    h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV);m=((h[:,:,0]>82)&(h[:,:,0]<100)&(h[:,:,1]>110)&(h[:,:,2]>170)).astype(np.uint8);m[600:,900:]=0;return m
def ransac_lines(pts,k=4,thr=3.0,iters=400,rng=np.random.default_rng(0)):
    pts=pts.copy();L=[]
    for _ in range(k):
        if len(pts)<40: break
        best=None
        for _ in range(iters):
            a,b=pts[rng.integers(len(pts),size=2)]
            d=b-a;nrm=np.hypot(*d)
            if nrm<80: continue
            nvec=np.array([-d[1],d[0]])/nrm;dist=np.abs((pts-a)@nvec);inl=dist<thr
            if best is None or inl.sum()>best[0]: best=(inl.sum(),inl)
        if best is None or best[0]<40: break
        ip=pts[best[1]];[vx,vy,x0,y0]=cv2.fitLine(ip.astype(np.float32),cv2.DIST_L2,0,0.01,0.01).ravel();L.append((np.array([x0,y0]),np.array([vx,vy]),len(ip)));pts=pts[~best[1]]
    return L
def inter(l1,l2):
    p1,d1,_=l1;p2,d2,_=l2;A=np.array([d1,-d2]).T
    if abs(np.linalg.det(A))<1e-6: return None
    t=np.linalg.solve(A,p2-p1);return p1+t[0]*d1
res={}
for i in range(n):
    m=cyan(cv2.imread(fs[i]));ys,xs=np.where(m>0)
    if len(xs)<900: res[i]=None;continue
    L=ransac_lines(np.stack([xs,ys],1).astype(np.float64))
    if len(L)<3: res[i]=None;continue
    # تصنيف بالزاوية والموضع: BL-BR (ميل موجب متوسط)، BR-TR (شديد الميل صاعد)، TR-TL (شبه أفقي، أعلى)، TL-BL
    info=[]
    for p,d,c in L:
        ang=np.degrees(np.arctan2(d[1],d[0]))%180;info.append((ang,p,d,c))
    res[i]={'lines':[(float(a),list(map(float,p)),list(map(float,d)),int(c)) for a,p,d,c in info]}
json.dump(res,open(f'{W}/lines.json','w'))
print('ok',sum(1 for v in res.values() if v))
for i in (20,65,150,250):
    print(i,[ (round(a),c) for a,p,d,c in res[i]['lines']] if res[i] else None)
