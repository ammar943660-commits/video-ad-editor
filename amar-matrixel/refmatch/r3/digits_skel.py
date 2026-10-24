#!/usr/bin/env python3
"""digits_skel.py — أرقام لاتينية بسُمك موحّد وأطراف مدوّرة، تُبنى من هياكل (skeleton) مضبوطة على صناديق الأرقام المقيسة في صورة المرجع
   (x0,x1 لكل رقم + y المشترك). ليست تتبعاً بكسلياً للحواف؛ تُوسم كذلك في التقرير. يخرج مضلعات بنفس صيغة glyph_poly (pts/holes)."""
import numpy as np,json,sys
from shapely.geometry import LineString,Polygon,Point
from shapely.ops import unary_union
from shapely import affinity
def arc(cx,cy,rx,ry,a0,a1,n=40): a=np.radians(np.linspace(a0,a1,n)); return [(cx+rx*np.cos(t),cy+ry*np.sin(t)) for t in a]
def bez(p0,p1,p2,p3,n=30):
    t=np.linspace(0,1,n)[:,None]; P=[np.array(p) for p in (p0,p1,p2,p3)]; return [tuple(q) for q in ((1-t)**3*P[0]+3*(1-t)**2*t*P[1]+3*(1-t)*t**2*P[2]+t**3*P[3])]
def stroke(pts,t,cap=1): return LineString(pts).buffer(t/2,cap_style=cap,join_style=1,resolution=12)
def ring(cx,cy,rx,ry,t): return Point(cx,cy).buffer(1,resolution=32).__class__ and affinity.scale(Point(cx,cy).buffer(1,resolution=32),rx+t/2,ry+t/2).difference(affinity.scale(Point(cx,cy).buffer(1,resolution=32),max(rx-t/2,1),max(ry-t/2,1)))
def digit(ch,x0,x1,y0,y1,t):
    X0,X1,Y0,Y1=x0+t/2,x1-t/2,y0+t/2,y1-t/2; Wd=X1-X0; H=Y1-Y0; Xc=(X0+X1)/2
    if ch=='6':
        Yb=Y1-0.31*H; bowl=ring(Xc,Yb,Wd/2,0.31*H,t)
        up=stroke(bez((X0,Yb),(X0-0.02*Wd,Y0+0.45*H),(X0+0.2*Wd,Y0),(X1-0.02*Wd,Y0+0.04*H)),t); return unary_union([bowl,up])
    if ch=='9': g=digit('6',x0,x1,y0,y1,t); return affinity.rotate(g,180,origin=((x0+x1)/2,(y0+y1)/2))
    if ch=='8': return unary_union([ring(Xc,Y0+0.26*H,0.43*Wd/1.0,0.26*H,t),ring(Xc,Y1-0.30*H,Wd/2,0.30*H,t)])
    if ch=='1': return unary_union([stroke([(X0+0.62*Wd,Y0-t/2+0.1),(X0+0.62*Wd,Y1+t/2-0.1)],t*1.15,2),stroke([(X0+0.62*Wd,Y0),(X0+0.02*Wd,Y0+0.2*H)],t*0.9,1)])
    if ch=='2': return unary_union([stroke(arc(Xc,Y0+0.27*H,Wd/2,0.27*H,185,405),t),stroke([(X1-0.02*Wd,Y0+0.4*H),(X0+0.02*Wd,Y1-0.02*H)],t),stroke([(X0,Y1),(X1,Y1)],t,2)])
    if ch=='3': return unary_union([stroke(arc(Xc-0.02*Wd,Y0+0.25*H,0.46*Wd,0.25*H,205,450),t),stroke(arc(Xc,Y1-0.27*H,Wd/2,0.27*H,-90,150),t)])
    if ch=='4': return unary_union([stroke([(X0+0.62*Wd,Y0),(X0,Y0+0.66*H),(X1,Y0+0.66*H)],t,2),stroke([(X0+0.68*Wd,Y0-t/2+.1),(X0+0.68*Wd,Y1+t/2-.1)],t*1.1,2)])
    if ch=='5': return unary_union([stroke([(X1,Y0),(X0+0.12*Wd,Y0),(X0+0.06*Wd,Y0+0.44*H)],t,2),stroke(arc(Xc-0.02*Wd,Y0+0.68*H,0.5*Wd,0.32*H,-125,150),t)])
    if ch=='7': return stroke([(X0,Y0),(X1,Y0),(X0+0.32*Wd,Y1+t/2-.1)],t,2)
    if ch=='+': cx,cy=(x0+x1)/2,(y0+y1)/2; return unary_union([stroke([(x0,cy),(x1,cy)],t*0.8,2),stroke([(cx,y0+0.1*(y1-y0)),(cx,y1)],t*0.9,2)])
def to_json(g,pid):
    gs=list(g.geoms) if hasattr(g,'geoms') else [g]
    return [{"id":f"{pid}_{i}","pts":[list(p) for p in list(q.exterior.coords)[:-1]],"holes":[[list(p) for p in list(h.coords)[:-1]] for h in q.interiors]} for i,q in enumerate(gs)]
if __name__=='__main__':
    boxes={'+':(125,232),'9':(246,367),'6a':(379,496),'6b':(508,620),'1':(632,714),'2':(725,845),'3':(858,969),'4':(969,1093),'5':(1099,1216),'6c':(1222,1346),'7':(1319,1451),'8':(1448,1580),'9b':(1586,1698)}
    out=[]; y0,y1=425,598; t=40
    for k,(a,b) in boxes.items(): out+=to_json(digit(k[0],a,b,y0,y1,t),'d'+k)
    json.dump(out,open(sys.argv[1],'w')); print(len(out))
