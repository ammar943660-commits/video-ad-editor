#!/usr/bin/env python3
"""build_camera.py — مفاتيح الرباعي → رباعي لكل فريم (PCHIP) → كاميرا (R,t) لكل فريم + plate للأرض/المباني.
   python3 build_camera.py <work> [fov] [plot_w_m]"""
import numpy as np,cv2,json,sys,glob
from scipy.interpolate import PchipInterpolator
W=sys.argv[1]; fov=float(sys.argv[2]) if len(sys.argv)>2 else 62.0; plot_w=float(sys.argv[3]) if len(sys.argv)>3 else 60.0; ALPHA=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
kf=json.load(open('keyframes.json'))['frames']; ks=sorted(int(k) for k in kf); Hs=np.load(f'{W}/cam_H.npy'); n=292
arr=np.array([kf[str(k)] for k in ks],float).reshape(len(ks),8)
Q=np.stack([PchipInterpolator(ks,arr[:,j])(np.arange(0,231)) for j in range(8)],1).reshape(-1,4,2)
# بعد الفريم 230: تمديد بحركة الكاميرا البنائية (SIFT) — تقدير فقط
ext=[Q[230]]
for i in range(231,n): ext.append(cv2.perspectiveTransform(ext[-1][None].astype(np.float64),Hs[i]@np.linalg.inv(Hs[i-1]))[0])
Q=np.concatenate([Q,np.array(ext)],0)
Qtrue=Q.copy(); Q=Q[0][None]+ALPHA*(Q-Q[0][None])   # تخميد حركة الكاميرا: plate من لقطة واحدة لا يدعم المسار الكامل
w,h=1146,644; f=(w/2)/np.tan(np.radians(fov)/2); K=np.array([[f,0,w/2],[0,f,h/2],[0,0,1]])
def pose(H):
    A=np.linalg.inv(K)@H; a1,a2,a3=A[:,0],A[:,1],A[:,2]; s=(np.linalg.norm(a1)+np.linalg.norm(a2))/2
    r1,r2,t=a1/s,a2/s,a3/s
    if t[2]<0: r1,r2,t=-r1,-r2,-t
    r3=np.cross(r1,r2);U,_,Vt=np.linalg.svd(np.stack([r1,r2,r3],1));R=U@Vt
    if np.linalg.det(R)<0: R[:,2]*=-1
    return R,t
Hu=cv2.getPerspectiveTransform(np.float32([[0,0],[1,0],[1,1],[0,1]]),Q[65].astype(np.float32)); A=np.linalg.inv(K)@Hu; asp=np.linalg.norm(A[:,0])/np.linalg.norm(A[:,1])
pw,pl=plot_w,plot_w/asp; Pw=np.float32([[-pw/2,-pl/2],[pw/2,-pl/2],[pw/2,pl/2],[-pw/2,pl/2]])
fr=[]
for i in range(n):
    Hi=cv2.getPerspectiveTransform(Pw,Q[i].astype(np.float32)).astype(np.float64); R,t=pose(Hi); fr.append({'i':i,'R':R.flatten().tolist(),'t':t.tolist(),'quad':Q[i].tolist(),'H_plane':Hi.tolist()})
json.dump({'width':w,'height':h,'fov_deg':fov,'alpha':ALPHA,'quad_true':Qtrue.tolist(),'plane':{'w':pw,'l':pl},'frames':fr},open(f'{W}/camera.json','w'))
print('plane',round(pw,1),round(pl,1)); C=lambda i:-np.array(fr[i]['R']).reshape(3,3).T@np.array(fr[i]['t'])
for i in (0,65,140,230,280): print(i,'cam pos',np.round(C(i),1))
