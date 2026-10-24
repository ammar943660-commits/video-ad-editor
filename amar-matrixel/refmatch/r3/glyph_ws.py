#!/usr/bin/env python3
"""glyph_ws.py — يحوّل هياكل الحروف التقريبية (strokes) إلى صورة ظلّية دقيقة بـWatershed على حواف صورة المرجع المعدَّلة.
   python3 glyph_ws.py <work> glyphs/x.json out_prefix [fg_scale bg_scale]  → out_mask.png + out_vis.jpg + out_shapes.json (بالمتر)"""
import sys,json,cv2,numpy as np
W,gj,outp=sys.argv[1:4]; fgs=float(sys.argv[4]) if len(sys.argv)>4 else 0.38; bgs=float(sys.argv[5]) if len(sys.argv)>5 else 1.7
G=json.load(open(gj)); im=cv2.imread(f"{W}/{G['image']}"); R=json.load(open(f"{W}/{G.get('rect','b1f')}_rect.json")); H,Wd=im.shape[:2]
def paint(scale,dilate=0,key=None):
    m=np.zeros((H,Wd),np.uint8)
    for s in G['strokes']:
        sc=s.get(key,scale) if key else scale
        if s['type']=='circle': cv2.circle(m,tuple(map(int,s['c'])),int(s['r']*max(sc,0.3)),255,-1)
        else:
            pts=np.array(s['pts'],np.int32); cv2.polylines(m,[pts],False,255,max(2,int(s['w']*sc)),cv2.LINE_AA)
            for p in pts: cv2.circle(m,tuple(p),max(1,int(s['w']*sc/2)),255,-1)
    return m
fg=paint(fgs,key='fg'); bgzone=paint(bgs,key='bg')
markers=np.zeros((H,Wd),np.int32); markers[bgzone==0]=1; markers[fg>0]=2
blur=cv2.GaussianBlur(im,(0,0),1.2); grad=cv2.Laplacian(cv2.cvtColor(blur,cv2.COLOR_BGR2GRAY),cv2.CV_32F); 
img8=cv2.cvtColor(cv2.convertScaleAbs(cv2.Sobel(cv2.cvtColor(blur,cv2.COLOR_BGR2GRAY),cv2.CV_32F,1,0)*0+cv2.magnitude(cv2.Sobel(cv2.cvtColor(blur,cv2.COLOR_BGR2GRAY),cv2.CV_32F,1,0),cv2.Sobel(cv2.cvtColor(blur,cv2.COLOR_BGR2GRAY),cv2.CV_32F,0,1))),cv2.COLOR_GRAY2BGR)
cv2.watershed(img8,markers); wsm=(markers==2).astype(np.uint8)*255
# مصنِّف لوني/ملمسي مدرَّب على البذور: يزيل تسرّب الغبار الأفتح/الأغمق من الحرف
import os
try:
    if os.environ.get('NO_RF'): raise RuntimeError('rf disabled')
    from sklearn.ensemble import RandomForestClassifier
    lab=cv2.cvtColor(blur,cv2.COLOR_BGR2LAB).astype(np.float32); feats=[lab]
    for sg in (3,9): feats.append(cv2.GaussianBlur(lab,(0,0),sg))
    gm=cv2.GaussianBlur(cv2.cvtColor(img8,cv2.COLOR_BGR2GRAY).astype(np.float32),(0,0),3)[:,:,None]; feats.append(gm)
    F=np.concatenate(feats,2).reshape(-1,10); fgm=(fg>0).reshape(-1); bgm=(bgzone==0).reshape(-1)
    idx_f=np.where(fgm)[0]; idx_b=np.where(bgm)[0]; rng=np.random.default_rng(1); idx_b=rng.choice(idx_b,min(len(idx_b),len(idx_f)*2),replace=False); idx_f=rng.choice(idx_f,min(len(idx_f),20000),replace=False)
    X=np.concatenate([F[idx_f],F[idx_b]]); y=np.concatenate([np.ones(len(idx_f)),np.zeros(len(idx_b))])
    rf=RandomForestClassifier(60,min_samples_leaf=15,n_jobs=4,random_state=0).fit(X,y); prob=rf.predict_proba(F)[:,1].reshape(H,Wd); cv2.imwrite(outp+'_prob.png',(prob*255).astype(np.uint8))
    mask=((wsm>0)&(prob>0.42)).astype(np.uint8)*255
except Exception as e:
    print('rf skipped',e); mask=wsm
mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((5,5),np.uint8)); mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8)); mask=cv2.GaussianBlur(mask,(0,0),2.5); mask=(mask>127).astype(np.uint8)*255
cv2.imwrite(outp+'_mask.png',mask)
vis=im.copy(); cs,hier=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE); cv2.drawContours(vis,cs,-1,(0,255,255),2); cv2.imwrite(outp+'_vis.jpg',vis)
def tom(p): return [(R['x0']+p[0]/R['wpx']*(R['x1']-R['x0']), R['z1']-p[1]/R['hpx']*(R['z1']-R['z0'])) for p in p]
shapes=[]
for i,c in enumerate(cs):
    if hier[0][i][3]!=-1 or cv2.contourArea(c)<300: continue
    ap=cv2.approxPolyDP(c,1.3,True)[:,0,:].astype(float); holes=[]
    ch=hier[0][i][2]
    while ch!=-1:
        if cv2.contourArea(cs[ch])>120: holes.append(tom(cv2.approxPolyDP(cs[ch],1.3,True)[:,0,:].astype(float)))
        ch=hier[0][ch][0]
    shapes.append({'outer':tom(ap),'holes':holes})
json.dump({'shapes':shapes,'width_m':R['width_m'],'height_m':R['height_m'],'x0':R['x0'],'z0':R['z0']},open(outp+'_shapes.json','w')); print('shapes',len(shapes))
