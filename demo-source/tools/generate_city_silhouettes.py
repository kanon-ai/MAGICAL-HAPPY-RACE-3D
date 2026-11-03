"""Offline city silhouette variation; preserve footprint and driving geometry."""
from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'work/route-shapes/tools'))
from join_route_shapes import joined_curves
from adaptive_road_rows import install
O=R/'work/city-silhouettes/city'
for n in ('assets','outputs'):(O/n).mkdir(parents=True,exist_ok=True)
p=R/'work/route-shapes/tools/extend_coast.py'
ns={'__file__':str(p),'__name__':'city_silhouette_generator'}
exec(compile(p.read_text(),str(p),'exec'),ns)
original=ns['building_shape']
def shape(index):
 kind,w,d,h=original(index)
 if kind!=4:h*= (0.75,1.0,1.25,1.0)[(index//3)%4]
 return kind,w,d,h
ns['building_shape']=shape;ns['R']=O
ns['path_center'],ns['path_height']=joined_curves('city',expressive=True)
install(ns['c'],stable=True,lane_grid=True);ns['ADAPTIVE_ROWS']=True
ns['main']()
base=R/'work/lined-route-shapes/city/assets'
for name in ('long-course.bin','rear-course.bin'):
 assert (base/name).read_bytes()==(O/'assets'/name).read_bytes(),name
old=(base/'building-mesh.bin').read_bytes();new=(O/'assets/building-mesh.bin').read_bytes();assert len(old)==len(new)
report={'scope':'Offline candidate only, not integrated or native verified','course_mirror_exact':True,'mesh_changed_bytes':sum(a!=b for a,b in zip(old,new)),'sha256':hashlib.sha256(new).hexdigest(),'height_factors':[0.75,1.0,1.25,1.0],'footprint_preserved':all(original(i)[:3]==shape(i)[:3] for i in range(512))}
(O/'outputs/scope-proof.json').write_text(json.dumps(report,indent=2));print(report)
