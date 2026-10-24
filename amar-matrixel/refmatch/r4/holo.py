#!/usr/bin/env python3
"""holo.py — طبقة هولوغرام R4 (RGB إضافي) لكل فريم: إطار نيون القطعة + جدران، نص المساحة كملصق أرضي مع انعكاس، مساقط المباني، مباني Wireframe بأدوار ونوافذ.
   الكاميرا لكل فريم من homography رباعي القطعة المتتبَّع (lot_track.json) + K من FOV. الإعداد: r4_cfg.json (قابل للتعديل بالكامل).
   python3 holo.py <work> <out_dir> <f0> <f1> [scale]"""
import cv2,numpy as np,json,sys,os,math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
W,OUT=sys.argv[1:3]; f0,f1=int(sys.argv[3]),int(sys.argv[4]); SC=float(sys.argv[5]) if len(sys.argv)>5 else 1.0; os.makedirs(OUT,exist_ok=True)
D=os.path.dirname(os.path.abspath(__file__)); C=json.load(open(os.environ.get('R4CFG',f'{D}/r4_cfg.json')))
TR=json.load(open(f'{W}/lot_track.json'))['snapped']; w,h=1146,644; LW,LH=C['lot_m']
f=(w/2)/math.tan(math.radians(C['fov_deg'])/2); K=np.array([[f,0,w/2],[0,f,h/2],[0,0,1]])
ease=lambda x:1-(1-min(max(x,0),1))**3
def ramp(fr,a,b): return min(max((fr-a)/max(b-a,1e-6),0),1)
def cam(fr):
    q=np.float32(TR[fr]); H=cv2.getPerspectiveTransform(np.float32([[0,0],[LW,0],[LW,LH],[0,LH]]),q); A=np.linalg.inv(K)@H
    s=(np.linalg.norm(A[:,0])+np.linalg.norm(A[:,1]))/2; r1,r2,t=A[:,0]/s,A[:,1]/s,A[:,2]/s
    if t[2]<0: r1,r2,t=-r1,-r2,-t
    r3=np.cross(r1,r2); U,_,Vt=np.linalg.svd(np.stack([r1,r2,r3],1)); R=U@Vt
    if -(R[:,2]@t)<0: R[:,2]*=-1          # محور Z يشير للأعلى نحو الكاميرا
    return H,R,t
def proj0(P,R,t):
    c=(P@R.T)+t; z=np.maximum(c[:,2],1e-3); return np.stack([f*c[:,0]/z+w/2,f*c[:,1]/z+h/2],1)
def proj(P,R,t):  # P: (n,3) بالمتر (X على u، Y على v، Z للأعلى)
    """منظور «ضعيف» للارتفاع (vert_straighten): مباني المرجع مرسومة بخطوط رأسية شبه متوازية لا تتبع منظور الكاميرا الحقيقي؛
    الارتفاع = مشتق محلي عند القاعدة، اتجاهه ممزوج نحو الرأسي في الصورة، وطوله ثابت مع z (بلا تقارب)."""
    P=np.asarray(P,float); a=C.get('vert_straighten',0.0)
    if a<=0 or not np.any(P[:,2]>0.01): return proj0(P,R,t)
    B=P.copy(); B[:,2]=0; b=proj0(B,R,t); B2=B.copy(); B2[:,2]=1.0; d=proj0(B2,R,t)-b
    L=np.linalg.norm(d,axis=1,keepdims=True)+1e-9
    if GS[0]: L=np.minimum(L,GS[0]*C.get('vert_ground_ratio',1.0))
    up=np.array([[0,-1.0]]); dirv=(1-a)*d/L+a*up; dirv/=np.linalg.norm(dirv,axis=1,keepdims=True)
    return b+dirv*L*P[:,2:3]
_txt=None
GS=[None]   # بكسل/متر للأرض في الفريم الحالي (حد أعلى لطول الارتفاع)
def text_contours():
    global _txt
    if _txt is None:
        from glyphs import outlines
        T=C['area_text']; cs,xr,yr=outlines(T['text'],os.path.join(D,T['font']),T['wght'],rtl=False,lang='en',script='Latn')
        s=T['width_u']*LW/(xr[1]-xr[0]); cu,cv=T['center_uv']; base=[]
        for c in cs:
            base.append([((cu*LW)+(x-(xr[0]+xr[1])/2)*s, (cv*LH)-(y-(yr[0]+yr[1])/2)*s, (y-yr[0])*s) for x,y in c])
        _txt=(base,(yr[1]-yr[0])*s)
    return _txt
def render(fr):
    src=fr-C['loop']['from'] if fr>=C['loop']['from'] else fr
    H,R,t=cam(min(src,len(TR)-1)); S=2; ss=S*16
    q_=np.float32(TR[min(src,len(TR)-1)]); GS[0]=math.sqrt(abs(cv2.contourArea(q_))/(LW*LH))
    core=np.zeros((h*S,w*S),np.float32); fill=np.zeros((h*S,w*S),np.float32)
    def line(P,a,th=2): 
        if a<=0.01: return
        uv=proj(np.asarray(P,float),R,t); cv2.polylines(core,[np.round(uv*ss).astype(np.int32)],False,float(a),max(1,int(th*S)),cv2.LINE_AA,4)
    def poly_fill(P,a):
        if a<=0.005: return
        uv=proj(np.asarray(P,float),R,t); cv2.fillPoly(fill,[np.round(uv*ss).astype(np.int32)],float(a),cv2.LINE_AA,4)
    O=C['outline']; g=[(0,0,0),(LW,0,0),(LW,LH,0),(0,LH,0)]
    p=ease(ramp(src,*O['draw']))
    if p>0:   # رسم تدريجي للمحيط
        L=4*p; pts=[g[0]]
        for k in range(4):
            if L<=k: break
            a_,b_=np.array(g[k]),np.array(g[(k+1)%4]); u=min(L-k,1); pts.append(tuple(a_+(b_-a_)*u))
        line(pts,1.0,2.2)
        wh=O['wall_h']*ease(ramp(src,*O['wall_rise']))*(1-ramp(src,*O.get('wall_fade',[1e9,1e9+1])))
        if wh>0.05:
            top=[(x,y,wh) for x,y,_ in g]; line(top+[top[0]],0.85,1.6)
            for k in range(4): line([g[k],top[k]],0.9,1.6)
            if O.get('posts'):
                for k in range(4):
                    a_,b_=np.array(g[k]),np.array(g[(k+1)%4]); L_=np.linalg.norm(b_-a_); n_=int(L_//O['posts'])
                    for j in range(1,n_): p_=a_+(b_-a_)*j/n_; line([tuple(p_),(p_[0],p_[1],wh)],0.7,1.2)
            for k in range(4): poly_fill([g[k],g[(k+1)%4],top[(k+1)%4],top[k]],O['wall_fill'])
    T=C['area_text']; ta=ease(ramp(src,*T['appear']))*(1-ramp(src,*T['fade']))
    if ta>0:
        base,th_=text_contours(); grow=0.6+0.4*ta
        cu,cv=T['center_uv'][0]*LW,T['center_uv'][1]*LH
        for c in base:
            P=[(cu+(x-cu)*grow,cv+(y-cv)*grow,0.05) for x,y,_ in c]; line(P+[P[0]],ta,1.8)
            dv=T['extrude_v']*LH; P2=[(x,y+dv,0.05) for x,y,_ in P]; line(P2+[P2[0]],ta*0.45,1.3)
            # انعكاس: مقلوب حول خط القاعدة، يخفت للأسفل
            yb=cv+th_/2*grow; R_=[(x,yb+(yb-y)*0.85,0.04) for x,y,_ in P]
            line(R_+[R_[0]],ta*T['reflection'],1.3)
    Fp=ease(ramp(src,*C['footprints']['draw'])); Dt=ease(ramp(src,*C['details']['appear']))
    if C.get('massing'): draw_massing(src,R,t,core,fill,ss,S,Fp,Dt,line)
    else:
      pass
      for bi,B in enumerate(C['buildings']):
          u0,u1,v0,v1=B['uv']; x0,x1,y0,y1=u0*LW,u1*LW,v0*LH,v1*LH; base=[(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)]
          if Fp>0:
              per=[base[0],base[1],base[2],base[3],base[0]]; L=4*Fp; pts=[per[0]]
              for k in range(4):
                  if L<=k: break
                  a_,b_=np.array(per[k]),np.array(per[k+1]); pts.append(tuple(a_+(b_-a_)*min(L-k,1)))
              line(pts,0.9,1.6)
          gh=B['h']*C.get('height_scale',1.0)*ease(ramp(src,*B['grow']))
          if gh<0.3: continue
          top=[(x,y,gh) for x,y,_ in base]
          line(top+[top[0]],1.0,1.6)
          for k in range(4): line([base[k],top[k]],1.0,1.6)
          for k in range(4): poly_fill([base[k],base[(k+1)%4],top[(k+1)%4],top[k]],C['details']['fill']*(0.5+Dt))
          poly_fill(top,C['details']['fill']*1.5)
          if Dt>0:
              nf=B['floors']; fh=B['h']*C.get('height_scale',1.0)/nf
              for k in range(1,nf):
                  z=k*fh
                  if z>gh: break
                  e=0.6*C.get('height_scale',1.0); ring=[(x0-e,y0-e,z),(x1+e,y0-e,z),(x1+e,y1+e,z),(x0-e,y1+e,z)]; line(ring+[ring[0]],0.45*Dt,1.0)
              nw=C['details']['windows_per_face']
              for k in range(4):
                  a_,b_=np.array(base[k][:2]),np.array(base[(k+1)%4][:2]); L=np.linalg.norm(b_-a_); dvec=(b_-a_)/L; n=max(2,int(nw*L/12))
                  for j in range(n):
                      s0=(j+0.35)/n*L; s1=(j+0.65)/n*L
                      for fl in range(1,nf):
                          z0=fl*fh+fh*0.3; z1=fl*fh+fh*0.75
                          if z1>gh: break
                          p0=a_+dvec*s0; p1=a_+dvec*s1
                          line([(p0[0],p0[1],z0),(p1[0],p1[1],z0),(p1[0],p1[1],z1),(p0[0],p0[1],z1),(p0[0],p0[1],z0)],0.5*Dt,0.9)
              for k in range(4):
                  a_,b_=np.array(base[k][:2]),np.array(base[(k+1)%4][:2])
                  for j in range(1,3):
                      p=a_+(b_-a_)*j/3; line([(p[0],p[1],0),(p[0],p[1],min(fh,gh))],0.8*Dt,1.3)
              # سطح: درابزين + غرفة درج
              cx,cy=(x0+x1)/2,(y0+y1)/2; sx,sy=(x1-x0)*0.22,(y1-y0)*0.22; zz=gh
              room=[(cx-sx,cy-sy,zz),(cx+sx,cy-sy,zz),(cx+sx,cy+sy,zz),(cx-sx,cy+sy,zz)]; hs_=C.get('height_scale',1.0); rt=[(x,y,zz+3*hs_) for x,y,_ in room]
              line(rt+[rt[0]],0.8*Dt,1.2); [line([room[k],rt[k]],0.8*Dt,1.2) for k in range(4)]
              if B.get('antenna'): line([(cx,cy,zz+3*hs_),(cx,cy,zz+10*hs_)],0.9*Dt,1.2)
    core=cv2.resize(core,(w,h),interpolation=cv2.INTER_AREA); fill=cv2.resize(fill,(w,h),interpolation=cv2.INTER_AREA)
    col=C['color']; I=C['intensity']
    g1=cv2.GaussianBlur(core,(0,0),2.2); g2=cv2.GaussianBlur(core,(0,0),7); g3=cv2.GaussianBlur(core,(0,0),20)
    L_=(core[...,None]*np.array(col['core'])/255*0.9+g1[...,None]*np.array(col['glow1'])/255*1.4+g2[...,None]*np.array(col['glow2'])/255*0.9+g3[...,None]*np.array(col['glow2'])/255*0.35+cv2.GaussianBlur(fill,(0,0),1.5)[...,None]*np.array(col['fill'])/255)*I
    return L_
def boxes_of(B,LW,LH,hs):
    """كتل المبنى: قاعدة/جسم رئيسي/تراجعات/غرفة سطح. كل كتلة (x0,x1,y0,y1,z0,z1,floors). الكتل من B['masses'] (إن وُجدت) أو تلقائياً."""
    u0,u1,v0,v1=B['uv']; X0,X1,Y0,Y1=u0*LW,u1*LW,v0*LH,v1*LH; fh=B.get('floor_h',3.2)*hs; n=B['floors']; out=[]
    if B.get('masses'):
        for M in B['masses']:
            a0,a1,b0,b1=M['uv']; f0,f1=M['floors']; out.append((a0*LW,a1*LW,b0*LH,b1*LH,f0*fh,f1*fh,f1-f0))
        return out
    ins=B.get('setback',0.12); top=B.get('setback_floors',1)
    out.append((X0,X1,Y0,Y1,0,(n-top)*fh,int(round(n-top))))
    if top>0 and n>1.5:
        dx=(X1-X0)*ins; dy=(Y1-Y0)*ins; sd=B.get('setback_side','both')
        out.append((X0+dx,X1-dx*(sd=='both'),Y0+dy*(sd=='both'),Y1-dy,(n-top)*fh,n*fh,int(top)))
    cx,cy=(X0+X1)/2,(Y0+Y1)/2; rx,ry=(X1-X0)*0.16,(Y1-Y0)*0.16
    if n>1.5: out.append((cx-rx+(X1-X0)*0.12,cx+rx+(X1-X0)*0.12,cy-ry,cy+ry,n*fh,n*fh+fh*0.8,0))   # غرفة درج صغيرة خارج المركز
    return out
def draw_massing(src,R,t,core,fill,ss,S,Fp,Dt,line):
    """رسم بإخفاء الخطوط: وجوه كل الكتل مرتبة من الأبعد للأقرب؛ كل وجه يمحو ما خلفه (occlude) ثم ترسم حوافه وأدواره ونوافذه."""
    hs=C.get('height_scale',1.0); HK=C.get('height_scale_keys')
    if HK: hs=float(np.interp(src,HK['f'],HK['v']))
    occ=C['massing'].get('occlude',0.88); faces=[]
    SK=C.get('shrink_keys'); shr=float(np.interp(src,SK['f'],SK['v'])) if SK else 1.0
    for bi,B in enumerate(C['buildings']):
        if B.get('floors_late'):   # المرجع يغيّر بعض الكتل بعد الانتقال (مثل الملحق ← مبنى): نمو ثانٍ
            B=dict(B,floors=B['floors']+(B['floors_late']-B['floors'])*ease(ramp(src,*B['grow_late'])))
            if B['floors']>1.5: B['setback_floors']=1; B['balconies']=True; B['pilotis']=True
        if shr!=1.0:
            u0,u1,v0,v1=B['uv']; cu,cv=(u0+u1)/2,(v0+v1)/2; B=dict(B,uv=[cu+(u0-cu)*shr,cu+(u1-cu)*shr,cv+(v0-cv)*shr,cv+(v1-cv)*shr])
        u0,u1,v0,v1=B['uv']; x0,x1,y0,y1=u0*LW,u1*LW,v0*LH,v1*LH
        if Fp>0:
            per=[(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0),(x0,y0,0)]; L=4*Fp; pts=[per[0]]
            for k in range(4):
                if L<=k: break
                a_,b_=np.array(per[k]),np.array(per[k+1]); pts.append(tuple(a_+(b_-a_)*min(L-k,1)))
            line(pts,0.9,1.5)
        g=ease(ramp(src,*B['grow']))
        if g<=0.01: continue
        for (a0,a1,b0,b1,z0,z1,nf) in boxes_of(B,LW,LH,hs):
            Htot=max(z for *_,z,_ in [(0,0,0,0,0,bb[5],0) for bb in boxes_of(B,LW,LH,hs)])
            zt=Htot*g
            if zt<=z0: continue
            z1c=min(z1,zt); Pb=[(a0,b0),(a1,b0),(a1,b1),(a0,b1)]
            for k in range(4):
                p,q=Pb[k],Pb[(k+1)%4]; quad=[(p[0],p[1],z0),(q[0],q[1],z0),(q[0],q[1],z1c),(p[0],p[1],z1c)]
                faces.append(('side',quad,nf,z0,z1,B,bi))
            faces.append(('top',[(a0,b0,z1c),(a1,b0,z1c),(a1,b1,z1c),(a0,b1,z1c)],0,z0,z1,B,bi))
    def depth(Q): c=(np.asarray(Q,float)@R.T)+t; return c[:,2].mean()
    faces.sort(key=lambda F:-depth(F[1]))
    H_,W_=core.shape
    for kind,Q,nf,z0,z1,B,bi in faces:
        uv=proj(np.asarray(Q,float),R,t); poly=np.round(uv*ss).astype(np.int32)
        m=np.zeros((H_//4,W_//4),np.uint8); cv2.fillPoly(m,[np.round(uv*ss/4/16).astype(np.int32)],1,cv2.LINE_8)   # قناع خشن سريع
        m=cv2.resize(m,(W_,H_),interpolation=cv2.INTER_NEAREST).astype(bool)
        core[m]*=(1-occ); fill[m]=fill[m]*(1-occ)+C['massing'].get('face_fill',0.06)*(1.6 if kind=='top' else 1.0)
        line(Q+[Q[0]],1.0,1.5)
        if kind=='side' and nf>0 and Dt>0:
            fh=(z1-z0)/nf; p,q=np.array(Q[0][:2]),np.array(Q[1][:2]); L=np.linalg.norm(q-p); d=(q-p)/max(L,1e-6); nrm=np.array([d[1],-d[0]])
            ztop=Q[2][2]
            for f_ in range(1,nf):
                z=z0+f_*fh
                if z>=ztop: break
                bo=C['massing'].get('balcony',0.7)*hs
                line([(p[0],p[1],z),(q[0],q[1],z)],0.55*Dt,1.0)
                if B.get('balconies',True) and L>8:   # شرفة بارزة: بلاطة للخارج
                    pa=p+d*L*0.2+nrm*bo; pb=p+d*L*0.8+nrm*bo
                    line([(p[0]+d[0]*L*0.2,p[1]+d[1]*L*0.2,z),(pa[0],pa[1],z),(pb[0],pb[1],z),(p[0]+d[0]*L*0.8,p[1]+d[1]*L*0.8,z)],0.6*Dt,1.0)
            nw=max(2,int(C['details']['windows_per_face']*L/12))
            for j in range(nw):
                s0=(j+0.35)/nw*L; s1=(j+0.65)/nw*L
                for fl in range(1 if z0==0 else 0,nf):
                    za=z0+fl*fh+fh*0.3; zb=z0+fl*fh+fh*0.75
                    if zb>ztop: break
                    a_=p+d*s0; b_=p+d*s1
                    line([(a_[0],a_[1],za),(b_[0],b_[1],za),(b_[0],b_[1],zb),(a_[0],a_[1],zb),(a_[0],a_[1],za)],0.42*Dt,0.8)
            if z0==0 and B.get('pilotis',True):
                for j in range(1,4):
                    c_=p+d*L*j/4; line([(c_[0],c_[1],0),(c_[0],c_[1],min(fh,ztop))],0.8*Dt,1.2)
        if kind=='top' and B.get('antenna') and Dt>0 and z1>=max(b[5] for b in boxes_of(B,LW,LH,hs))-0.01:
            cx=np.mean([q[0] for q in Q]); cy=np.mean([q[1] for q in Q]); zz=Q[0][2]; line([(cx,cy,zz),(cx,cy,zz+9*hs)],0.9*Dt,1.2)
if __name__=='__main__':
    for fr in range(f0,f1+1):
        L_=render(fr); cv2.imwrite(f'{OUT}/{fr+1:04d}.png',np.clip(L_*255,0,255).astype(np.uint8))
