#!/usr/bin/env python3
"""build_plate_proj.py — plate بإسقاط الكاميرا (Camera Projection Mapping): الفريم النظيف 0 يُسقَط على هندسة وسيطة
   (أرض + مستويات عمودية للمباني + خلفية بعيدة) ثم يُصوَّر بكاميرا المرجع الحقيقية الكاملة (camera_true.json) ← حركة المرجع بدل التخميد.
   python3 build_plate_proj.py <work> [n] [out_dir]   (يُتبع بتدريج لوني build_plate.py --grade-only)"""
import sys,json,math,numpy as np,cv2
W=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 292; OUT=sys.argv[3] if len(sys.argv)>3 else f'{W}/plate_proj'
import os; os.makedirs(OUT,exist_ok=True)
CAM=json.load(open(f'{W}/camera_true.json')); w,h=CAM['width'],CAM['height']; f=(w/2)/math.tan(math.radians(CAM['fov_deg'])/2)
f0=cv2.imread(f'{W}/frames/0001.png'); m=np.zeros(f0.shape[:2],np.uint8); m[585:625,995:1125]=255; f0=cv2.inpaint(f0,m,5,cv2.INPAINT_TELEA)
def cam(i):
    R=np.array(CAM['frames'][i]['R']).reshape(3,3); t=np.array(CAM['frames'][i]['t']); C=-R.T@t; return R,t,C
# إزالة أعمدة الإنارة (ستعود كأسطوانات ثلاثية الأبعاد): تتمدد بلا معنى عند إسقاطها على الأرض
for (px,y0,y1,wd) in ((161,296,470,7),(336,346,562,8),(919,352,480,7)):
    mk=np.zeros(f0.shape[:2],np.uint8); cv2.line(mk,(px,y0),(px+2,y1),255,wd*2); f0=cv2.inpaint(f0,mk,6,cv2.INPAINT_TELEA)
R0,t0,C0=cam(0)
def ray_dirs(R):
    u,v=np.meshgrid(np.arange(w)+0.5,np.arange(h)+0.5); d=np.stack([(u-w/2)/f,(v-h/2)/f,np.ones_like(u)],-1).reshape(-1,3)@R   # (R^T d) كصفوف
    return d/np.linalg.norm(d,axis=1,keepdims=True)
def proj0(X):  # نقاط عالم cv → بكسلات الفريم 0
    c=(X@R0.T)+t0; return np.stack([f*c[:,0]/c[:,2]+w/2,f*c[:,1]/c[:,2]+h/2],1),c[:,2]
def ground_pt(px,py):
    d=R0.T@np.array([(px-w/2)/f,(py-h/2)/f,1.0]); d/=np.linalg.norm(d); s=-C0[2]/d[2]; return C0+s*d
# مناطق الفريم 0: قاعدة المباني (polyline) وأفق الخلفية البعيدة
base=np.array([(0,332),(150,320),(350,292),(530,264),(700,272),(900,302),(1013,338),(1146,336)],float); xs=np.arange(w); yb=np.interp(xs,base[:,0],base[:,1])
YY=np.arange(h)[:,None]*np.ones((1,w)); XX=np.ones((h,1))*xs[None,:]
ground_mask=(YY>=yb[None,:]-2)
far_y=135.0; far_mask=(YY<far_y)&(~ground_mask)
bld_mask=(~ground_mask)&(~far_mask)
groups=[('G1',0,340),('G2',340,880),('G3',880,w)]   # مجموعات مباني: x-range في الفريم 0
planes=[]   # (point, normal, mask)
for name,xa,xb in groups:
    ya,yb_=float(yb[min(w-1,xa)]),float(yb[min(w-1,xb-1)])
    A=ground_pt(xa,ya+2); B=ground_pt(xb-1,yb_+2); e=B-A; e[2]=0; e/=np.linalg.norm(e); nrm=np.array([-e[1],e[0],0.0])
    msk=bld_mask&(XX>=xa)&(XX<xb); planes.append((A,nrm,msk,name))
# خلفية بعيدة: مستوى عمودي بعيد خلف قطعة الأرض (≈ 600م) بمحاذاة اتجاه النظر
fwd=R0.T@np.array([0,0,1.0]); fwd[2]=0; fwd/=np.linalg.norm(fwd); far_pt=C0+fwd*700
planes.append((far_pt,-fwd,far_mask|(YY<yb[None,:]-2)&(YY<far_y+30),'FAR'))
ground=(np.array([0,0,0.0]),np.array([0,0,1.0]),ground_mask,'GROUND')
cands=[ground]+planes
def render(i):
    R,t,C=cam(i); D=ray_dirs(R); best=np.full(len(D),np.inf); u_out=np.zeros((len(D),2),np.float32); ok=np.zeros(len(D),bool)
    for P0,N,M,name in cands:
        den=D@N; s=((P0-C)@N)/np.where(np.abs(den)<1e-9,1e-9,den); valid=(s>0.5)&(s<5000)
        X=C+s[:,None]*D; uv,z=proj0(X); xi=np.round(uv[:,0]).astype(int); yi=np.round(uv[:,1]).astype(int); inb=(xi>=0)&(xi<w)&(yi>=0)&(yi<h)&(z>0)&valid
        okm=np.zeros(len(D),bool); okm[inb]=M[yi[inb],xi[inb]]
        sel=okm&(s<best); best[sel]=s[sel]; u_out[sel]=uv[sel]; ok|=sel
    mx=u_out[:,0].reshape(h,w).astype(np.float32); my=u_out[:,1].reshape(h,w).astype(np.float32)
    img=cv2.remap(f0,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
    hole=(~ok.reshape(h,w)).astype(np.uint8)*255; hole=cv2.dilate(hole,np.ones((3,3),np.uint8))
    if hole.any(): img=cv2.inpaint(img,hole,3,cv2.INPAINT_TELEA)
    return img
frames=[int(x) for x in os.environ['FRAMES'].split(',')] if os.environ.get('FRAMES') else range(0,n)
for i in frames:
    cv2.imwrite(f'{OUT}/{i+1:04d}.png',render(i))
    if i%40==0: print('plate_proj',i,flush=True)
