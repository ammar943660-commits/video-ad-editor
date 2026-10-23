#!/usr/bin/env python3
"""rect_stack.py — يعدّل منظور عدة فريمات للمرجع إلى مستوى النص العمودي (من plane في scene_cfg) بكاميرا كل فريم، ثم وسيط زمني يزيل الغبار.
   python3 rect_stack.py <work> <beat> <f0> <f1> <step> <out_prefix> [wpx]
   الإحداثيات المعدَّلة: x∈[-mx,1+mx]·العرض ، z∈[-mb,1+mt]·الارتفاع ؛ الصورة تُحفظ مع json للتحويل إلى متر."""
import sys,os,json,numpy as np,cv2,math
os.environ.setdefault('AMX_CAM','camera_true.json')
W,bi,f0,f1,step,outp=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),sys.argv[6]; wpx=int(sys.argv[7]) if len(sys.argv)>7 else 1600
CAM=json.load(open(f"{W}/{os.environ['AMX_CAM']}")); cfg=json.load(open('scene_cfg.json')); P=cfg['beats'][bi]['plane']
w,h=CAM['width'],CAM['height']; f=(w/2)/math.tan(math.radians(CAM['fov_deg'])/2)
def to_img(fr,Pb):
    R=np.array(fr['R']).reshape(3,3); t=np.array(fr['t']); c=R@np.array([Pb[0],-Pb[1],-Pb[2]])+t; return np.array([f*c[0]/c[2]+w/2,f*c[1]/c[2]+h/2])
BL=np.array(P['BL']); BR=np.array(P['BR']); e=(BR-BL)/np.linalg.norm(BR-BL); Wm=P['width_m']; Hm=P['height_m']
mx,mb,mt=0.06,0.30,0.45; x0,x1,z0,z1=-mx*Wm,(1+mx)*Wm,-mb*Hm,(1+mt)*Hm
asp=(x1-x0)/(z1-z0); Hpx=int(wpx/asp); dst=np.float32([[0,0],[wpx,0],[wpx,Hpx],[0,Hpx]]); stack=[]
for i in range(f0,f1+1,step):
    fr=CAM['frames'][i]; pw=[BL+e*x+np.array([0,0,z]) for x,z in [(x0,z1),(x1,z1),(x1,z0),(x0,z0)]]
    M=cv2.getPerspectiveTransform(np.float32([to_img(fr,p) for p in pw]),dst); im=cv2.imread(f'{W}/frames/{i+1:04d}.png'); stack.append(cv2.warpPerspective(im,M,(wpx,Hpx),flags=cv2.INTER_CUBIC))
S=np.stack(stack).astype(np.float32); cv2.imwrite(outp+'_median.png',np.median(S,0).astype(np.uint8))
g=np.stack([cv2.cvtColor(s.astype(np.uint8),cv2.COLOR_BGR2GRAY) for s in S]).astype(np.float32); cv2.imwrite(outp+'_p30.png',np.percentile(g,30,axis=0).astype(np.uint8))
json.dump({'wpx':wpx,'hpx':Hpx,'x0':x0,'x1':x1,'z0':z0,'z1':z1,'width_m':Wm,'height_m':Hm,'frames':[f0,f1,step]},open(outp+'_rect.json','w')); print('stack',len(stack),(Hpx,wpx))
