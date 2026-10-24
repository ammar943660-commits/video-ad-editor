#!/usr/bin/env python3
"""fit_text.py — يضبط موضع وحجم النص ثلاثي الأبعاد حتى يطابق صندوق النص في المرجع (بالبكسل) لفريم معيّن.
   /tmp/bpyenv/bin/python fit_text.py <work> <frame> x0 x1 y0 y1 [beat_index]"""
import sys,os,json,subprocess,numpy as np,cv2
W=sys.argv[1]; fi=int(sys.argv[2]); tx0,tx1,ty0,ty1=[float(v) for v in sys.argv[3:7]]; bi=int(sys.argv[7]) if len(sys.argv)>7 else 0
here=os.path.dirname(os.path.abspath(__file__)); cfgp=os.path.join(here,'scene_cfg.json')
for it in range(6):
    c=json.load(open(cfgp)); b=c['beats'][bi]
    subprocess.run(['/tmp/bpyenv/bin/python',os.path.join(here,'scene_r3.py'),W,str(fi),f'{W}/fit.png','4'],capture_output=True)
    a=cv2.imread(f'{W}/fit.png',-1)[:,:,3]; ys,xs=np.where(a>128)
    x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max(); print(it,'bbox',x0,x1,y0,y1,'target',tx0,tx1,ty0,ty1,'xy',b['xy'],'h',round(b['height'],2),'cond',round(b.get('condense',1),3))
    sx=(tx1-tx0)/max(1,x1-x0); sy=(ty1-ty0)/max(1,y1-y0)
    if abs(sx-1)<0.015 and abs(sy-1)<0.03 and abs((x0+x1)/2-(tx0+tx1)/2)<4 and abs(y1-ty1)<4: break
    b['height']*=sy**0.9; b['condense']=min(1.0,b.get('condense',1.0)*(sx/sy)**0.9)
    # إزاحة أرضية: الصورة→المستوى بالتقريب عبر jacobian عددي بسيط (خطوة صغيرة)
    dx=((tx0+tx1)/2-(x0+x1)/2); dy=(ty1-y1)
    b['xy'][0]+=dx*0.07; b['xy'][1]+=-dy*0.12
    json.dump(c,open(cfgp,'w'),indent=1)
