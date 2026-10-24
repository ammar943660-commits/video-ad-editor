#!/usr/bin/env python3
"""grade_lot.py — تدريج إضافي للأرض فقط (الأرض الرملية تبقى أفتح من بقية المشهد في المرجع أثناء التعتيم).
   لكل فريم: ربح لوني لكل قناة = وسيط (المرجع/الـplate) في منطقة من الأرض (يمين-أمام الرباعي، بعيداً عن النص والغبار)، مُنعَّم زمنياً، ويُطبَّق على قناع الأرض (مضلع النيون الناعم).
   python3 grade_lot.py <work> <in_plate_dir> <out_dir> [n]"""
import numpy as np,cv2,json,sys,os
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d
W,IN,OUT=sys.argv[1:4]; n=int(sys.argv[4]) if len(sys.argv)>4 else 292; os.makedirs(OUT,exist_ok=True)
kf=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'keyframes.json')))['frames']; ks=sorted(int(k) for k in kf); Hs=np.load(f'{W}/cam_H.npy')
arr=np.array([kf[str(k)] for k in ks],float).reshape(len(ks),8)
Q=np.stack([PchipInterpolator(ks,arr[:,j])(np.arange(0,231)) for j in range(8)],1).reshape(-1,4,2); ext=[Q[230]]
for i in range(231,n): ext.append(cv2.perspectiveTransform(ext[-1][None].astype(np.float64),Hs[i]@np.linalg.inv(Hs[i-1]))[0])
Q=np.concatenate([Q,np.array(ext)],0)
def uv(q,u,v):  # TL,TR,BR,BL ; u نحو TR ، v نحو BL
    H=cv2.getPerspectiveTransform(np.float32([[0,0],[1,0],[1,1],[0,1]]),q.astype(np.float32)); return cv2.perspectiveTransform(np.float32([[[u,v]]]),H)[0,0]
gains=[]
for i in range(n):
    q=Q[i]; R=cv2.imread(f'{W}/frames/{i+1:04d}.png').astype(np.float32)+1; P=cv2.imread(f'{IN}/{i+1:04d}.png').astype(np.float32)+1
    m=np.zeros(R.shape[:2],np.uint8); cv2.fillPoly(m,[np.round(np.array([uv(q,.62,.55),uv(q,.9,.55),uv(q,.9,.9),uv(q,.62,.9)])).astype(np.int32)],255)
    gains.append([np.median(R[:,:,c][m>0])/np.median(P[:,:,c][m>0]) for c in range(3)])
G=np.clip(np.array(gains),0.7,3.2); G=gaussian_filter1d(G,5,axis=0,mode='nearest')
for i in range(n):
    q=Q[i]; P=cv2.imread(f'{IN}/{i+1:04d}.png').astype(np.float32); m=np.zeros(P.shape[:2],np.float32)
    cv2.fillPoly(m,[np.round(q).astype(np.int32)],1.0); m=cv2.GaussianBlur(m,(0,0),6)[:,:,None]
    o=P*(1+m*(G[i][None,None,:]-1))
    hp=f'{W}/plate_proj_hole/{i+1:04d}.png'
    if os.path.exists(hp):   # خارج تغطية الفريم المصدر: خذ بكسلات المرجع نفسها (حافة الطريق/السيارات غير متأثرة بالمؤثرات)
        hm=cv2.imread(hp,0).astype(np.float32)[:,:,None]/255; Rr=cv2.imread(f'{W}/frames/{i+1:04d}.png').astype(np.float32); o=o*(1-hm)+Rr*hm
    cv2.imwrite(f'{OUT}/{i+1:04d}.png',np.clip(o,0,255).astype(np.uint8))
print('gain sample',np.round(G[[0,15,30,60,130,200,260]],2).tolist())
