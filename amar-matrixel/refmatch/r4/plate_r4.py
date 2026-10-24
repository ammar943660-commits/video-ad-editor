#!/usr/bin/env python3
"""plate_r4.py — plate لمرجع R4 من فريمات المرجع نفسها بعد إزالة الهولوغرام السماوي (قناع لوني متمدد + Inpaint).
   الكاميرا في R4 تنتقل لزوايا غير موجودة في أي فريم نظيف، فلا يوجد مصدر آخر للخلفية دون لقطة درون أو توليد AI (موثّق في TRACKER).
   الفريمات 0–20 و287+ بلا هولوغرام فتُنسخ كما هي. python3 plate_r4.py <work> <f0> <f1>"""
import cv2,numpy as np,sys,os
W=sys.argv[1]; a,b=int(sys.argv[2]),int(sys.argv[3]); O=f'{W}/plate'; os.makedirs(O,exist_ok=True)
for i in range(a,b+1):
    im=cv2.imread(f'{W}/frames/{i+1:04d}.png'); h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    bl=im[...,0].astype(int)-im[...,2].astype(int)
    m=(((h[...,0]>80)&(h[...,0]<115)&(h[...,1]>45)&(h[...,2]>70))|((bl>45)&(im[...,0]>110))).astype(np.uint8)*255
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((2,2),np.uint8)); m=cv2.dilate(m,np.ones((9,9),np.uint8))
    m[580:625,990:1130]=255   # شارة واجهة التسجيل
    if i<18 or i>=287: m[:]=0; m[580:625,990:1130]=255
    if m.mean()>0.5:
        sm=cv2.resize(im,None,fx=0.5,fy=0.5); mm=cv2.resize(m,None,fx=0.5,fy=0.5,interpolation=cv2.INTER_NEAREST)
        fill=cv2.resize(cv2.inpaint(sm,mm,6,cv2.INPAINT_TELEA),(im.shape[1],im.shape[0]),interpolation=cv2.INTER_CUBIC)
        a_=cv2.GaussianBlur(m.astype(np.float32)/255,(0,0),2)[...,None]; im=(im*(1-a_)+fill*a_).astype(np.uint8)
    cv2.imwrite(f'{O}/{i+1:04d}.png',im)
    if i%40==0: print('plate',i,flush=True)
