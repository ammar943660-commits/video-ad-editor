#!/usr/bin/env python3
"""rectify.py — يعدّل منظور فريم المرجع إلى المستوى الأمامي للنص (مقابل الكاميرا) باستعمال موضع النص المضبوط.
   python3 rectify.py <work> <frame> <beat_idx> <out_prefix> [wpx]"""
import sys,json,numpy as np,cv2,math
W,fi,bi,outp=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]; wpx=int(sys.argv[5]) if len(sys.argv)>5 else 1400
import os
CAM=json.load(open(f"{W}/{os.environ.get('AMX_CAM','camera.json')}")); cfg=json.load(open('scene_cfg.json')); b=cfg['beats'][bi]
fr=CAM['frames'][fi]; R=np.array(fr['R']).reshape(3,3); t=np.array(fr['t']); w,h=CAM['width'],CAM['height']; f=(w/2)/math.tan(math.radians(CAM['fov_deg'])/2)
def to_img(Pb):  # Blender world (x,y,z) → pixel
    Pcv=np.array([Pb[0],-Pb[1],-Pb[2]]); c=R@Pcv+t; return np.array([f*c[0]/c[2]+w/2,f*c[1]/c[2]+h/2])
# مركز الكاميرا (Blender)
Rb=R; C=-R.T@t; cam=np.array([C[0],-C[1],-C[2]])
bx,by=b['xy']; yaw=math.atan2(cam[1]-by,cam[0]-bx); lean=math.radians(b.get('lean',0))
def Rz(a): return np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
def Rx(a): return np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
M=Rz(yaw+math.pi/2)@Rx(math.radians(90)-lean)
# أبعاد النص المحلية (م): العرض ≈ الارتفاع*extent؛ نأخذ مستطيلاً كبيراً حول النص: نستخدم bbox الهدف المخزّن
ext=json.load(open('text_extent.json')) if False else None
height=b['height']; half_w=float(b.get('plane_half_w',height*1.6)); top=height*1.2; bot=-height*0.45
corners_local=[(-half_w,top),(half_w,top),(half_w,bot),(-half_w,bot)]
pts=[]
for x,y in corners_local:
    p=M@np.array([x,y,0.0])+np.array([bx,by,0.0]); pts.append(to_img(p))
src=np.float32(pts); asp=(half_w*2)/(top-bot); H=int(wpx/asp)
dst=np.float32([[0,0],[wpx,0],[wpx,H],[0,H]]); Hm=cv2.getPerspectiveTransform(src,dst)
ref=cv2.imread(f'{W}/frames/{fi+1:04d}.png'); rect=cv2.warpPerspective(ref,Hm,(wpx,H),flags=cv2.INTER_CUBIC)
cv2.imwrite(outp+'_rect.png',rect); json.dump({'H':Hm.tolist(),'wpx':wpx,'hpx':H,'half_w':half_w,'top':top,'bot':bot,'corners_img':src.tolist()},open(outp+'_rect.json','w'))
print('rect',rect.shape,'corners',np.round(src).tolist())
