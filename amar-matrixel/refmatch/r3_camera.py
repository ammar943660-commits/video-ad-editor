#!/usr/bin/env python3
"""r3_camera.py — من H(t) المتتبَّعة + رباعي الأرض في فريم مرجعي → كاميرا (R,t,fov) لكل فريم في إحداثيات مستوى الأرض (متر)."""
import numpy as np,cv2,json,sys,glob
W=sys.argv[1]; fov=float(sys.argv[2]) if len(sys.argv)>2 else 62.0; plot_w=float(sys.argv[3]) if len(sys.argv)>3 else 60.0
Hs=np.load(f'{W}/cam_H.npy'); n=len(Hs); ref_i=65
Q65=np.float32([[536,259],[1003,331],[800,580],[135,350]])           # TL(back),TR,BR,BL على الفريم 65 (من النيون)
Q0=cv2.perspectiveTransform(Q65[None],np.linalg.inv(Hs[ref_i]))[0]    # في إحداثيات الفريم 0
w,h=1146,644; f=(w/2)/np.tan(np.radians(fov)/2); K=np.array([[f,0,w/2],[0,f,h/2],[0,0,1]])
def pose(H):
    A=np.linalg.inv(K)@H; a1,a2,a3=A[:,0],A[:,1],A[:,2]; s=(np.linalg.norm(a1)+np.linalg.norm(a2))/2
    r1,r2,t=a1/s,a2/s,a3/s
    if t[2]<0: r1,r2,t=-r1,-r2,-t
    r3=np.cross(r1,r2); U,_,Vt=np.linalg.svd(np.stack([r1,r2,r3],1)); R=U@Vt
    if np.linalg.det(R)<0: R[:,2]*=-1
    return R,t
# أبعاد المستوى من نسبة الوحدة (على الفريم 0)
Hu=cv2.getPerspectiveTransform(np.float32([[0,0],[1,0],[1,1],[0,1]]),Q0.astype(np.float32)); A=np.linalg.inv(K)@Hu; asp=np.linalg.norm(A[:,0])/np.linalg.norm(A[:,1])
pw,pl=plot_w,plot_w/asp
Pw=np.float32([[-pw/2,-pl/2],[pw/2,-pl/2],[pw/2,pl/2],[-pw/2,pl/2]])   # (x, y_cv) ؛ TL ← y_cv=-l/2
out=[]
for i in range(n):
    Q=cv2.perspectiveTransform(Q0[None],Hs[i])[0].astype(np.float32); Hi=cv2.getPerspectiveTransform(Pw,Q).astype(np.float64); R,t=pose(Hi)
    out.append({'i':i,'R':R.flatten().tolist(),'t':t.tolist(),'quad':Q.tolist()})
json.dump({'width':w,'height':h,'fov_deg':fov,'plane':{'w':pw,'l':pl,'units':'meters(assumed)'},'frames':out,'Q0':Q0.tolist()},open(f'{W}/camera.json','w'))
print('plane',round(pw,1),'x',round(pl,1),'aspect',round(asp,3)); print('cam pos f0',np.round(-np.array(out[0]['R']).reshape(3,3).T@np.array(out[0]['t']),1),'f250',np.round(-np.array(out[250]['R']).reshape(3,3).T@np.array(out[250]['t']),1))
