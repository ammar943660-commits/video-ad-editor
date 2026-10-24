#!/usr/bin/env python3
"""reuse_new_property.py — يجهّز مجلد عمل R5 لواجهة جديدة (صورة ثابتة أو أول فريم من لقطة ثابتة):
   1) الصورة → frames/0001.png (نهار).
   2) خطوط النيون: من edges.json (detect_edges.py في tools/، إحداثيات uv للواجهة) + رباعي الواجهة → قطع بالبكسل،
      وتوقيت رسم تلقائي (من الأسفل للأعلى ومن الوسط للأطراف) بدل توقيت المرجع.
   3) ليل: إن وُجدت صورة ليل حقيقية/مولّدة (--night) تُستخدم؛ وإلا تدريج ليلي محلي (تعتيم + زرقة + توهج نوافذ دافئ تقريبي) — موسوم «تقريب محلي».
   4) إعداد بطاقات افتراضي بمواضع نسبية من رباعي الواجهة (نصوص قابلة للتعديل).
   python3 reuse_new_property.py <image> <edges.json> '<quad TL,TR,BR,BL>' <work> [--night night.png] [--texts "فيلا للبيع|300 متر|في جدة|تواصل معنا\\n+966..."]"""
import sys,os,json,cv2,numpy as np,argparse
ap=argparse.ArgumentParser(); ap.add_argument('img'); ap.add_argument('edges'); ap.add_argument('quad'); ap.add_argument('work'); ap.add_argument('--night'); ap.add_argument('--texts',default="فيلا للبيع|300 متر|في جدة|تواصل معنا\n+966123456789")
a=ap.parse_args(); W=a.work; os.makedirs(f'{W}/frames',exist_ok=True)
day=cv2.imread(a.img); h,w=day.shape[:2]; cv2.imwrite(f'{W}/frames/0001.png',day)
Q=np.float32(json.loads(a.quad)); Hm=cv2.getPerspectiveTransform(np.float32([[0,0],[1,0],[1,1],[0,1]]),Q)
E=json.load(open(a.edges)); segs=[]
for s in E['segments']:
    if s.get('score',1)<0.12: continue
    p=cv2.perspectiveTransform(np.float32([[[s['u0'],s['v0']],[s['u1'],s['v1']]]]),Hm)[0]
    p[:,0]=p[:,0].clip(0,w-1); p[:,1]=p[:,1].clip(0,h-1)
    if np.linalg.norm(p[1]-p[0])<6: continue
    mid=(p[0]+p[1])/2; segs.append((p,mid))
cx=Q[:,0].mean(); ybot=Q[:,1].max(); ytop=Q[:,1].min()
out=[]
for p,mid in segs:
    order=0.65*(ybot-mid[1])/max(ybot-ytop,1)+0.35*abs(mid[0]-cx)/max(w/2,1)   # من الأسفل والوسط
    if p[0][1]<p[1][1]: p=p[::-1]   # يُرسم صاعداً
    out.append({'pts':[[round(float(x),1),round(float(y),1)] for x,y in p],'start':int(3+order*20),'dur':4})
json.dump({'_doc':'نيون R5 لعقار جديد: من edges.json + توقيت تلقائي','paths':out},open(f'{W}/neon_paths_v3.json','w'),ensure_ascii=False)
if a.night: night=cv2.imread(a.night); src='صورة ليل مقدَّمة'
else:
    f=day.astype(np.float32)/255; g=cv2.cvtColor(day,cv2.COLOR_BGR2GRAY).astype(np.float32)/255
    night=(f**1.9)*np.array([0.62,0.42,0.30])*0.55   # تعتيم + زرقة (BGR)
    win=((g>0.55)&(cv2.cvtColor(day,cv2.COLOR_BGR2HSV)[...,1]<90)).astype(np.float32)   # الأسطح الفاتحة/النوافذ ← توهج دافئ خفيف
    win=cv2.GaussianBlur(win,(0,0),2)*0.0   # معطّل افتراضياً: لا نخترع إضاءة نوافذ غير موجودة (دقة المواد الأصلية)
    sky=np.linspace(1,0,h)[:,None,None]**3*np.array([0.18,0.10,0.05]); night=night+sky*(g[...,None]>0.6)
    night=(np.clip(night,0,1)*255).astype(np.uint8); src='تقريب ليلي محلي (تدريج)'
cv2.imwrite(f'{W}/night_plate.png',night)
T=a.texts.split('|'); x0,x1=Q[:,0].min(),Q[:,0].max(); y0,y1=Q[:,1].min(),Q[:,1].max(); bw=(x1-x0)
def box(u,v,ww,hh): X=x0+u*bw; Y=y0+v*(y1-y0); return [int(X),int(Y),int(X+ww*bw),int(Y+hh*(y1-y0))]
B=[box(0.03,0.08,0.26,0.13),box(0.70,0.12,0.22,0.11),box(0.12,0.66,0.22,0.11),box(0.60,0.66,0.34,0.22)]
D=os.path.dirname(os.path.abspath(__file__)); C=json.load(open(f'{D}/r5_cfg.json'))
cards=[]
for k,(t,b) in enumerate(zip(T,B)):
    lx=b[2]+12 if k%2==0 else b[0]-12; ly=(b[1]+b[3])//2; tx=lx+(40 if k%2==0 else -40); ty=ly+50
    cards.append({"text":t.replace('\\n','\n'),"box":b,"text_h":int((b[3]-b[1])*(0.36 if '\n' in t else 0.5)),"appear":[24+k*55,36+k*55],"leader":[[lx,ly],[tx,ly],[tx,ty]],"style":"octagon" if k==3 else "tab"})
C.update({"_doc":"R5 لعقار جديد — مولَّد بـreuse_new_property.py؛ عدّل النصوص والمواضع هنا","cards":cards,"night_source":src})
C.pop('night_curve',None); C['day_to_night']=[2,20]
json.dump(C,open(f'{W}/r5_cfg_newprop.json','w'),indent=1,ensure_ascii=False); print('segments',len(out),'night:',src)
