"""Generate matching roadside projection tables without changing live assets."""
from pathlib import Path
import json,hashlib,sys
from generate_route_candidate import curves,WORK,R
import generate_course as c
joined='--joined' in sys.argv
expressive='--expressive' in sys.argv
if joined or expressive:
 from join_route_shapes import joined_curves
 curves=lambda name:joined_curves(name,expressive=expressive)
 WORK=R/('work/expressive-route-shapes' if expressive else 'work/joined-route-shapes')
source=R.parents[3]/'public-road-cockpit/work/seamless-stage/tools/generate_road_markers.py'
code=source.read_text()
code=code.replace('R=Path(__file__).resolve().parents[1]','R=target')
code=code.replace('from coast_path import height,center','height,center=height_fn,center_fn')
reports=[]
names=('coast','canyon','forest','snow','city','night')
if '--stage' in sys.argv:names=(sys.argv[sys.argv.index('--stage')+1],)
for name in names:
 target=WORK/name;(target/'assets').mkdir(parents=True,exist_ok=True);(target/'outputs').mkdir(exist_ok=True)
 center,height=curves(name)
 exec(compile(code,str(source),'exec'),dict(target=target,height_fn=height,center_fn=center,__file__=str(source)))
 data=(target/'assets/road-markers.bin').read_bytes()
 if name=='coast':assert data==(R/'assets/road-markers.bin').read_bytes(),'Baseline projection mismatch'
 reports.append(dict(stage=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(WORK/'outputs').mkdir(exist_ok=True)
(WORK/'outputs'/('candidate-markers-'+names[0]+'.json' if len(names)==1 else 'candidate-markers.json')).write_text(json.dumps(dict(coast_exact='coast' in names,stages=reports,limitation='Offline projections only; native stage dispatch and visual inspection pending.'),indent=2)+'\n')
