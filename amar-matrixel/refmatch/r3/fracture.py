#!/usr/bin/env python3
"""fracture.py — يكسّر مضلعات حروف الجملة إلى شظايا حجرية (Voronoi ثنائي الأبعاد ∩ كنتور النص) ويكتب pieces JSON + نسخة موحَّدة (whole) بلا حاجة لـshapely على الماك.
   /tmp/bpyenv/bin/python fracture.py shapes.json out_prefix [cell_m=1.3] [seed=1]"""
import sys,json,random,numpy as np
from shapely.geometry import Polygon,MultiPoint,Point
from shapely.ops import unary_union,voronoi_diagram
sh,outp=sys.argv[1:3]; cell=float(sys.argv[3]) if len(sys.argv)>3 else 1.3; seed=int(sys.argv[4]) if len(sys.argv)>4 else 1
d=json.load(open(sh)); polys=[Polygon(s['outer'],[h for h in s['holes'] if len(h)>=3]).buffer(0) for s in d['shapes']]
U=unary_union(polys).buffer(0.03,join_style=1).buffer(-0.03,join_style=1).simplify(0.02)
x0,y0,x1,y1=U.bounds; rnd=random.Random(seed); pts=[]
for gx in np.arange(x0-cell,x1+cell,cell):
    for gy in np.arange(y0-cell,y1+cell,cell): pts.append((gx+rnd.uniform(-.45,.45)*cell,gy+rnd.uniform(-.45,.45)*cell))
vd=voronoi_diagram(MultiPoint(pts),envelope=U.buffer(cell*3).envelope)
pieces=[]
for c in vd.geoms:
    p=c.intersection(U)
    for g in (list(p.geoms) if hasattr(p,'geoms') else [p]):
        if g.geom_type!='Polygon' or g.area<0.12: continue
        cx,cy=g.centroid.x,g.centroid.y
        pieces.append({'cx':cx,'cy':cy,'area':g.area,'outer':[(x-cx,y-cy) for x,y in list(g.exterior.coords)[:-1]],'holes':[[(x-cx,y-cy) for x,y in list(i.coords)[:-1]] for i in g.interiors]})
gs=list(U.geoms) if hasattr(U,'geoms') else [U]
whole=[{'outer':list(g.exterior.coords)[:-1],'holes':[list(i.coords)[:-1] for i in g.interiors]} for g in gs]
json.dump({'pieces':pieces,'whole':whole,'bounds':U.bounds},open(outp+'_pieces.json','w'))
print(sh,'pieces',len(pieces),'whole parts',len(whole),'bounds',[round(v,1) for v in U.bounds])
