#!/usr/bin/env python3
"""plane_from_image.py — يعرّف مستوى النص العمودي في العالم من نقاط على صورة المرجع:
   نقطتا القاعدة (يسار/يمين) على الأرض + نقطة قمة فوق اليمين. بعدها يُسقَط على أي فريم بكاميرته.
   python3 plane_from_image.py <work> <frame> blx bly brx bry trx try [cam.json]  → يطبع JSON للمستوى"""
import sys,json,math,numpy as np
W,fi=sys.argv[1],int(sys.argv[2]); blx,bly,brx,bry,trx,try_=[float(v) for v in sys.argv[3:9]]; camf=sys.argv[9] if len(sys.argv)>9 else 'camera_true.json'
CAM=json.load(open(f'{W}/{camf}')); w,h=CAM['width'],CAM['height']; f=(w/2)/math.tan(math.radians(CAM['fov_deg'])/2); fr=CAM['frames'][fi]
R=np.array(fr['R']).reshape(3,3); t=np.array(fr['t']); C=-R.T@t     # مركز الكاميرا في إحداثيات cv-plane (z سالب = فوق)
def ray(px,py): d=R.T@np.array([(px-w/2)/f,(py-h/2)/f,1.0]); return C,d/np.linalg.norm(d)
def to_blender(P): return np.array([P[0],-P[1],-P[2]])
def hit_ground(px,py):
    o,d=ray(px,py); s=-o[2]/d[2]; return o+s*d
BL=hit_ground(blx,bly); BR=hit_ground(brx,bry)
# مستوى عمودي يمر بـBL,BR : نقطة القمة = تقاطع شعاع (trx,try) مع المستوى
e=(BR-BL); e[2]=0; e/=np.linalg.norm(e); nrm=np.array([-e[1],e[0],0.0])
o,d=ray(trx,try_); s=np.dot(BR-o,nrm)/np.dot(d,nrm); TR=o+s*d
width=float(np.linalg.norm(BR-BL)); height=float(abs(TR[2]-BR[2]))
B=to_blender((BL+BR)/2); yaw=math.atan2(*(to_blender(BR)-to_blender(BL))[[1,0]])  # اتجاه محور x للنص في العالم (Blender)
out={'base_center':[float(B[0]),float(B[1])],'baseline_yaw':float(yaw),'width_m':width,'height_m':height,'BL':to_blender(BL).tolist(),'BR':to_blender(BR).tolist()}
print(json.dumps(out))
