#!/usr/bin/env python3
"""build_plate.py — يبني plate المطابقة: الفريم 0 النظيف (بعد إزالة علامة واجهة التسجيل) ← طبقتان بحركة كاميرا المرجع
   (أرض: homography المستوى من الرباعي؛ مباني: homography SIFT) بدمج ناعم ← تدريج لوني يطابق المرجع لكل فريم (من مناطق بلا مؤثر).
   python3 build_plate.py <work> [n]"""
import numpy as np,cv2,json,sys,glob,os
from scipy.ndimage import gaussian_filter1d
W=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 292
CJ=json.load(open(f'{W}/camera.json')); cam=CJ['frames']; ALPHA=CJ.get('alpha',1.0); Hb=np.load(f'{W}/cam_H.npy'); Hb=np.eye(3)[None]+ALPHA*(Hb-np.eye(3)[None]); os.makedirs(f'{W}/plate',exist_ok=True)
f0=cv2.imread(f'{W}/frames/0001.png'); m=np.zeros(f0.shape[:2],np.uint8); m[585:625,995:1125]=255; f0=cv2.inpaint(f0,m,5,cv2.INPAINT_TELEA)
H0=np.array(cam[0]['H_plane'])
h,w=f0.shape[:2]
# منحنى فاصل مباني/أرض في الفريم 0
poly=np.array([(0,332),(150,320),(350,292),(530,264),(700,272),(900,302),(1013,338),(1146,336)],float)
yb=np.interp(np.arange(w),poly[:,0],poly[:,1])
yy=np.arange(h)[:,None]; wg0=np.clip((yy-(yb[None,:]-6))/12.0,0,1)  # 1 تحت الخط = أرض
def warp(im,H): return cv2.warpPerspective(im,H,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
gains=[]
raw=[]
for i in range(n):
    Hg=np.array(cam[i]['H_plane'])@np.linalg.inv(H0)
    G=warp(f0,Hg); B=warp(f0,Hb[i]); wg=warp((wg0*255).astype(np.uint8),Hg).astype(np.float32)[:,:,None]/255  # قناع الأرض يتبع الأرض
    P=(G.astype(np.float32)*wg+B.astype(np.float32)*(1-wg)).astype(np.uint8); raw.append(P)
# تدريج لوني: log R = log a + g log C على مناطق بلا مؤثر
sel=np.zeros((h,w),bool); sel[:35,:]=True; sel[40:330,:110]=True; sel[40:300,1030:]=True
params=[]
for i in range(n):
    R=cv2.imread(f'{W}/frames/{i+1:04d}.png').astype(np.float32)/255+1e-3; C=raw[i].astype(np.float32)/255+1e-3; p=[]
    for c in range(3):
        x=np.log(C[:,:,c][sel]);y=np.log(R[:,:,c][sel]);A=np.stack([np.ones_like(x),x],1)
        for _ in range(2):  # انحدار متين
            co,_,_,_=np.linalg.lstsq(A,y,rcond=None);res=np.abs(A@co-y);keep=res<np.percentile(res,80);A=A[keep];y=y[keep];x=x[keep]
        p.append(co)
    params.append(np.array(p).flatten())
P=np.array(params); P[200:]=P[200:].clip(P[:200].min(0),P[:200].max(0)); P=gaussian_filter1d(P,3,axis=0,mode='nearest')
for i in range(n):
    C=raw[i].astype(np.float32)/255+1e-3;out=np.zeros_like(C)
    for c in range(3): out[:,:,c]=np.exp(P[i,c*2]+P[i,c*2+1]*np.log(C[:,:,c]))
    im=(np.clip(out-1e-3,0,1)*255).astype(np.uint8); M=cv2.getRotationMatrix2D((w/2,h/2),0,1.07); im=cv2.warpAffine(im,M,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE); cv2.imwrite(f'{W}/plate/{i+1:04d}.png',im)
np.save(f'{W}/grade.npy',P);print('plate',n,'frames; grade sample',np.round(P[[0,30,65,140],:],2).tolist())
