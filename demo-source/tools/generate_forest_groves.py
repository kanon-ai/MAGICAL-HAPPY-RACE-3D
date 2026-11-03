"""Offline forest placement candidate; never overwrite playable assets."""
from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools'))
sys.path.insert(0,str(R/'work/route-shapes/tools'))
from join_route_shapes import joined_curves
from adaptive_road_rows import install
O=R/'work/forest-groves/forest'
for n in ('assets','outputs'):(O/n).mkdir(parents=True,exist_ok=True)
s=(R/'work/route-shapes/tools/extend_coast.py').read_text()
# Stable world-index groups, never a changing screen slot or frame counter.
s=s.replace('def footprint(index):',"def forest_setback(index):\n return (1600,1900,4200,5000,3200,1800,1600,3800)[(index%512)//64]\n\ndef footprint(index):")
s=s.replace('c.ROAD_WIDTH+2400-xx','c.ROAD_WIDTH+forest_setback(index)-xx')
s=s.replace('c.ROAD_WIDTH-2400-dx','c.ROAD_WIDTH-forest_setback(idx)-dx')
s=s.replace('clearance>=2399.99','clearance>=forest_setback(idx)-0.01')
s=s.replace('>=2399.99','>=forest_setback(idx)-0.01')
# Existing boundary trees already have dedicated safe two-sided positions.
ns={'__file__':str(R/'work/route-shapes/tools/extend_coast.py'),'__name__':'forest_groves_generator'}
exec(compile(s,'forest_groves_generator','exec'),ns)
ns['R']=O;ns['path_center'],ns['path_height']=joined_curves('forest',expressive=True)
install(ns['c'],stable=True,lane_grid=True);ns['ADAPTIVE_ROWS']=True
ns['main']()
base=R/'work/lined-route-shapes/forest/assets'
a=(base/'long-course.bin').read_bytes();b=(O/'assets/long-course.bin').read_bytes()
assert len(a)==len(b)==4096*256
# Road geometry and traffic anchors reside outside object records128..191.
for i in range(4096):
 aa=a[i*256:(i+1)*256];bb=b[i*256:(i+1)*256]
 assert aa[:128]==bb[:128] and aa[192:]==bb[192:],('non-scenery change',i)
assert (base/'rear-course.bin').read_bytes()==(O/'assets/rear-course.bin').read_bytes()
report={'scope':'Offline lateral forest placement only; not integrated or runtime verified','records':4096,'road_traffic_mirror_exact':True,'changed_object_records':sum(a[i*256+128:i*256+192]!=b[i*256+128:i*256+192] for i in range(4096)),'sha256':hashlib.sha256(b).hexdigest()}
(O/'outputs/scope-proof.json').write_text(json.dumps(report,indent=2));print(report)
