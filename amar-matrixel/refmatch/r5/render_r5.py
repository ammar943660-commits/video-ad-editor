#!/usr/bin/env python3
"""render_r5.py — R5 كامل (تركيب 2D لكاميرا ثابتة): plate نهار→ليل، نيون يُرسم على مسارات متتبَّعة من المرجع، بطاقات عربية بإطار/ذيل ونقطة متوهجة.
   نص عربي مُشكَّل HarfBuzz يُرسم كمضلعات (بلا خط نظام). python3 render_r5.py <work> <out_dir> <f0> <f1>  (يحتاج bpyenv لـuharfbuzz)"""
import cv2,numpy as np,json,sys,os,math
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(D,'..'))
from glyphs import outlines,outlines_mixed
W,O=sys.argv[1:3]; f0,f1=int(sys.argv[3]),int(sys.argv[4]); os.makedirs(O,exist_ok=True)
C=json.load(open(os.environ.get('R5CFG',f'{D}/r5_cfg.json'))); NP=json.load(open(f'{W}/'+C.get('neon_paths','neon_paths.json')))['paths']
if NP and isinstance(NP[0],dict): P=[p['pts'] for p in NP]; TIM=[(p['start'],p['dur']) for p in NP]
else:
    P=[p for p in NP if not (max(q[1] for q in p)<130 and max(q[0] for q in p)<260)]; TIM=None
day=cv2.imread(f'{W}/frames/0001.png').astype(np.float32); night=cv2.imread(f'{W}/night_plate.png').astype(np.float32)
mk=np.zeros(day.shape[:2],np.uint8); mk[575:625,985:1140]=255; day=cv2.inpaint(day.astype(np.uint8),mk,5,cv2.INPAINT_TELEA).astype(np.float32); night=cv2.inpaint(night.astype(np.uint8),mk,5,cv2.INPAINT_TELEA).astype(np.float32)
H,Wd=day.shape[:2]; SS=4
ease=lambda x:1-(1-min(max(x,0),1))**3
def rmp(f,a,b): return min(max((f-a)/max(b-a,1e-6),0),1)
rng=np.random.RandomState(4); starts=[t[0] for t in TIM] if TIM else [rng.uniform(C['neon_draw'][0],C['neon_draw'][1]-8) for _ in P]; durs=[max(t[1],2) for t in TIM] if TIM else [rng.uniform(5,10) for _ in P]
FONT=os.path.join(D,C['font']); _tc={}
def text_mask(txt,hpx):
    if (txt,hpx) in _tc: return _tc[(txt,hpx)]
    lines=txt.split('\n'); polys=[]; ws=[]; hs=[]
    for l in lines:
        cs,xr,yr=outlines_mixed(l,FONT,None); polys.append((cs,xr,yr)); ws.append(xr[1]-xr[0])
    s=hpx/ (polys[0][2][1]-polys[0][2][0]) if False else hpx/0.75
    gap=hpx*0.35; totw=int(max(ws)*s)+8; toth=int(len(lines)*hpx*1.25+gap*(len(lines)-1))+8
    m=np.zeros((toth*SS,totw*SS),np.uint8); y=4+hpx
    for cs,xr,yr in polys:
        x0=(totw-(xr[1]-xr[0])*s)/2-xr[0]*s
        pts=[np.round(np.array([((x*s+x0)*SS,(y-yy*s)*SS) for x,yy in c])).astype(np.int32) for c in cs]
        cv2.fillPoly(m,pts,255); y+=hpx*1.25+gap
    m=cv2.resize(m,(totw,toth),interpolation=cv2.INTER_AREA).astype(np.float32)/255; _tc[(txt,hpx)]=m; return m
def glow_layer(core):
    g1=cv2.GaussianBlur(core,(0,0),2); g2=cv2.GaussianBlur(core,(0,0),7); g3=cv2.GaussianBlur(core,(0,0),18)
    nc=np.array(C['neon']['glow'],np.float32)/255; cc=np.array(C['neon']['core'],np.float32)/255
    k=C['neon']; return (core[...,None]*cc*k.get('core_k',1.0)+g1[...,None]*nc*k.get('g1',1.3)+g2[...,None]*nc*k.get('g2',0.8)+g3[...,None]*nc*k.get('g3',0.35))*k['intensity']
def line_ss(img,pts,val,th): cv2.polylines(img,[np.round(np.array(pts)*SS*16).astype(np.int32)],False,float(val),max(1,int(th*SS)),cv2.LINE_AA,4)
for f in range(f0,f1+1):
    if f>=C['end_cut']: cv2.imwrite(f'{O}/{f+1:04d}.png',day.astype(np.uint8)); continue
    NC=C.get('night_curve')
    a=(float(np.interp(f,NC['f'],NC['a'])) if NC else ease(rmp(f,*C['day_to_night']))); base=day*(1-a)+night*a
    core=np.zeros((H*SS,Wd*SS),np.float32)
    for p,st,du in zip(P,starts,durs):
        u=rmp(f,st,st+du)
        if u<=0: continue
        pts=np.array(p,float); seg=np.linalg.norm(np.diff(pts,axis=0),axis=1); L=seg.sum()*ease(u); acc=0; out=[pts[0]]
        for k,sl in enumerate(seg):
            if acc+sl>=L: out.append(pts[k]+(pts[k+1]-pts[k])*(L-acc)/max(sl,1e-6)); break
            acc+=sl; out.append(pts[k+1])
        line_ss(core,out,1.0,C['neon']['width'])
    pan=np.zeros((H,Wd),np.float32); txt=np.zeros((H,Wd),np.float32)
    for cd in C['cards']:
        u=rmp(f,*cd['appear'])
        if u<=0: continue
        e=ease(u); x0,y0,x1,y1=cd['box']; xr=x0+(x1-x0)*min(1,e*1.4)   # مسح أفقي
        ch=8 if cd['style']=='tab' else 18
        poly=[(x0+ch,y0),(xr,y0),(xr,y1-ch),(xr-ch,y1),(x0,y1),(x0,y0+ch)] if cd['style']=='tab' else [(x0+ch,y0),(x1-ch,y0),(x1,y0+ch),(x1,y1-ch),(x1-ch,y1),(x0+ch,y1),(x0,y1-ch),(x0,y0+ch)]
        if cd['style']!='tab': poly=[(x0+(px-x0)*min(1,e*1.4),py) for px,py in poly]
        m=np.zeros((H*SS,Wd*SS),np.uint8); cv2.fillPoly(m,[np.round(np.array(poly)*SS).astype(np.int32)],255); pan=np.maximum(pan,cv2.resize(m,(Wd,H),interpolation=cv2.INTER_AREA).astype(np.float32)/255*e)
        line_ss(core,poly+[poly[0]],0.9*e,1.6)
        if cd.get('decor'):
            for dd in cd['decor']:
                if dd.get('rect'): rx,ry,rw,rh=dd['rect']; cv2.rectangle(core,(int(rx*SS*16),int(ry*SS*16)),(int((rx+rw)*SS*16),int((ry+rh)*SS*16)),float(dd.get('v',0.9)*e),-1,cv2.LINE_AA,4)
                else: line_ss(core,dd['pts'],dd.get('v',0.9)*e,dd.get('w',1.5))
        if cd.get('decor') is not None: pass
        else:
          # زخارف: شرطات علوية + شريط سفلي
          for k in range(3): line_ss(core,[(x0+10+k*9,y0-6),(x0+16+k*9,y0-12)],0.9*e,2.2)
          line_ss(core,[(x0+40,y0-9),(x0+(x1-x0)*0.55,y0-9)],0.6*e,2.5); line_ss(core,[(x0+(x1-x0)*0.6,y0-9),(x1-6,y0-9),(x1-6,y0+12)],0.5*e,1.2)
          line_ss(core,[(x0+30,y1+7),(x0+(x1-x0)*0.45,y1+7)],0.8*e,3.0)
        # ذيل + نقطة
        lu=rmp(f,cd['appear'][0]+4,cd['appear'][1]+4)
        if lu>0:
            lp=np.array(cd['leader'],float); seg=np.linalg.norm(np.diff(lp,axis=0),axis=1); L=seg.sum()*ease(lu); acc=0; out=[lp[0]]
            for k,sl in enumerate(seg):
                if acc+sl>=L: out.append(lp[k]+(lp[k+1]-lp[k])*(L-acc)/max(sl,1e-6)); break
                acc+=sl; out.append(lp[k+1])
            line_ss(core,out,0.9,1.5); cv2.circle(core,tuple(np.round(lp[0]*SS*16).astype(int)),int(4*SS*16),0.9,-1,cv2.LINE_AA,4)
            if lu>=1:
                c=tuple(np.round(lp[-1]*SS*16).astype(int)); cv2.circle(core,c,int(5*SS*16),1.0,-1,cv2.LINE_AA,4); cv2.circle(core,c,int((9+1.5*math.sin(f*0.3))*SS*16),0.6,max(1,int(1.2*SS)),cv2.LINE_AA,4)
        tu=rmp(f,cd['appear'][0]+cd.get('text_delay',5),cd['appear'][1]+cd.get('text_delay',5)-5)
        if tu>0:
            tm=text_mask(cd['text'],cd['text_h']); th_,tw_=tm.shape; cx=(x0+x1)//2-tw_//2; cy=(y0+y1)//2-th_//2+2
            ya,yb=max(cy,0),min(cy+th_,H); xa,xb=max(cx,0),min(cx+tw_,Wd); txt[ya:yb,xa:xb]=np.maximum(txt[ya:yb,xa:xb],tm[ya-cy:yb-cy,xa-cx:xb-cx]*tu)
    core=cv2.resize(core,(Wd,H),interpolation=cv2.INTER_AREA)
    pc=np.array(C['panel']['fill'],np.float32); al=pan[...,None]*C['panel']['alpha']
    o=base*(1-al)+pc*al; o=255-(255-o)*(1-np.clip(glow_layer(core),0,1)); tc=np.array(C['panel']['text'],np.float32); o=o*(1-txt[...,None])+tc*txt[...,None]
    cv2.imwrite(f'{O}/{f+1:04d}.png',np.clip(o,0,255).astype(np.uint8))
