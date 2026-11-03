"""Generate aligned road/props/mirror candidate into an isolated directory."""
from pathlib import Path
import sys,json,hashlib
from study_snow_city_turn import paired_curve
from adaptive_road_rows import install
R=Path(__file__).resolve().parents[1]
stage=sys.argv[1];assert stage in ('snow','city')
O=R/'work/snow-city-turn'/stage
for name in ('assets','outputs'):(O/name).mkdir(parents=True,exist_ok=True)
p=R/'work/route-shapes/tools/extend_coast.py'
ns=dict(__file__=str(p),__name__='snow_city_turn_generator')
exec(compile(p.read_text(),str(p),'exec'),ns)
if stage=='city':
 original=ns['building_shape']
 def shape(index):
  kind,w,d,h=original(index)
  if kind!=4:h*=(.75,1.,1.25,1.)[(index//3)%4]
  return kind,w,d,h
 ns['building_shape']=shape
ns['R']=O;ns['path_center'],ns['path_height']=paired_curve(stage,8000)
install(ns['c'],stable=True,lane_grid=True);ns['ADAPTIVE_ROWS']=True
ns['main']()
report=dict(stage=stage,amplitude=8000,integrated=False,scope='Aligned generated road, scenery and mirror; capacity and native rendering unverified',assets={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (O/'assets').glob('*.bin')})
(O/'outputs/candidate.json').write_text(json.dumps(report,indent=2));print(stage,'candidate generated')
