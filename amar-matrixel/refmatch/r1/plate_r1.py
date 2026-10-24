#!/usr/bin/env python3
"""plate_r1.py — plate R1: الفريم 0 النظيف × homography الكاميرا لكل فريم + تدريج لوني (log-gamma لكل قناة) مقدَّر من مناطق بلا مؤثرات
   (السماء/الأطراف/أسفل الطريق)، مُنعَّم زمنياً. python3 plate_r1.py <work> <n>"""
import cv2,numpy as np,sys,os
from scipy.ndimage import gaussian_filter1d
W=sys.argv[1]; n=int(sys.argv[2]); H=np.load(f'{W}/H_r1.npy'); O=f'{W}/plate'; os.makedirs(O,exist_ok=True)
f0=cv2.imread(f'{W}/frames/0001.png'); mk=np.zeros(f0.shape[:2],np.uint8); mk[585:625,995:1125]=255; f0=cv2.inpaint(f0,mk,5,cv2.INPAINT_TELEA)
sel=np.zeros((644,1146),bool); sel[:60,:]=True; sel[60:330,:90]=True; sel[60:330,1060:]=True; sel[560:640,:900]=True; sel[100:250,:300]=True; sel[90:260,880:]=True   # مبانٍ جانبية بلا مؤثرات (لدفء اللون)
raw=[]; P=[]
for i in range(n):
    p=cv2.warpPerspective(f0,H[i],(1146,644),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE); raw.append(p)
    R=cv2.imread(f'{W}/frames/{i+1:04d}.png').astype(np.float32)/255+1e-3; C=p.astype(np.float32)/255+1e-3; co_=[]
    for c in range(3):
        x=np.log(C[:,:,c][sel]); y=np.log(R[:,:,c][sel]); A=np.stack([np.ones_like(x),x],1)
        for _ in range(2):
            co,*_=np.linalg.lstsq(A,y,rcond=None); r=np.abs(A@co-y); k=r<np.percentile(r,75); A,y=A[k],y[k]
        co_.append(co)
    P.append(np.array(co_).ravel())
P=np.array(P); P[262:298]=P[261]   # حلقة الختام تلوّث مناطق القياس: تثبيت التدريج
P=gaussian_filter1d(P,3,axis=0,mode='nearest')
for i in range(n):
    C=raw[i].astype(np.float32)/255+1e-3; o=np.stack([np.exp(P[i,2*c]+P[i,2*c+1]*np.log(C[:,:,c])) for c in range(3)],2)
    cv2.imwrite(f'{O}/{i+1:04d}.png',(np.clip(o-1e-3,0,1)*255).astype(np.uint8))
print('grade',np.round(P[::50],2).tolist())
