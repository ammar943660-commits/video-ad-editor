#!/usr/bin/env python3
"""r3_track.py — يتتبع كاميرا المرجع R3 (من خلفية المباني/الطرق خارج منطقة المؤثر) ويقدّر رباعي حدود الأرض لكل فريم.
   الناتج: <work>/cam_H.npy (H: الفريم0→t) و quads.json. يُستخدم لإعادة بناء الكاميرا في Blender ولبناء الـplate."""
import cv2,numpy as np,glob,json,sys,os
W=sys.argv[1]; fs=sorted(glob.glob(f'{W}/frames/*.png')); n=int(sys.argv[2]) if len(sys.argv)>2 else len(fs)
exclude=json.loads(sys.argv[3]) if len(sys.argv)>3 else [[150,220,1000,644]]
g0=cv2.cvtColor(cv2.imread(fs[0]),cv2.COLOR_BGR2GRAY);eq=cv2.equalizeHist
mask=np.full(g0.shape,255,np.uint8)
for x0,y0,x1,y1 in exclude: mask[y0:y1,x0:x1]=0
mask[600:,900:]=0  # علامة واجهة التسجيل «١٠ ث»
sift=cv2.SIFT_create(5000);bf=cv2.BFMatcher();k0,d0=sift.detectAndCompute(eq(g0),mask)
Hs=[np.eye(3)]; prev=np.eye(3)
for i in range(1,n):
    g=cv2.cvtColor(cv2.imread(fs[i]),cv2.COLOR_BGR2GRAY);k1,d1=sift.detectAndCompute(eq(g),mask)
    ms=[m for m,nn in (p for p in bf.knnMatch(d0,d1,k=2) if len(p)==2) if m.distance<.78*nn.distance]
    H=None
    if len(ms)>=12:
        a=np.float32([k0[m.queryIdx].pt for m in ms]);b=np.float32([k1[m.trainIdx].pt for m in ms]);H,mk=cv2.findHomography(a,b,cv2.RANSAC,2.0)
        if H is not None and int(mk.sum())<15: H=None
    if H is None: H=prev
    # تلميس بيني: ECC لتحسين H داخل القناع
    try:
        a_=cv2.GaussianBlur(eq(g0),(0,0),1.5);b_=cv2.GaussianBlur(eq(g),(0,0),1.5)
        cc,H2=cv2.findTransformECC(a_,b_,H.astype(np.float32),cv2.MOTION_HOMOGRAPHY,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,60,1e-6),mask,5)
        if cc>.55 and np.abs(H2-H).max()<0.05+0.01*abs(H[0,2])/100: H=H2.astype(np.float64)
    except cv2.error: pass
    Hs.append(H); prev=H
    if i%30==0: print(i,np.round(H[:2,2],1),round(H[0,0],4),flush=True)
Hs=np.array(Hs)
# تنعيم زمني (غاوسي) على المعاملات
from scipy.ndimage import gaussian_filter1d
flat=Hs.reshape(n,9)/Hs[:,2,2].reshape(n,1,1).reshape(n,1);sm=gaussian_filter1d(flat,3,axis=0,mode='nearest').reshape(n,3,3)
np.save(f'{W}/cam_H.npy',sm);print('saved',sm.shape)
