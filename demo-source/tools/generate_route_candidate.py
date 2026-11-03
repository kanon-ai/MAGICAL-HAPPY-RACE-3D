"""Isolated complete geometry candidate; never changes playable ROM assets.

Road, traffic anchors, building grounding and mirror are generated together.
These candidates are not yet integrated or claimed to fit the cartridge.
"""
from pathlib import Path
import argparse, importlib.util, math, sys, json
R=Path(__file__).resolve().parents[1]
WORK=R/'work/route-shapes'
sys.path.insert(0,str(WORK/'tools'))
import extend_coast as generator
import coast_path

L=coast_path.LENGTH
def curves(name):
    if name=='coast': return coast_path.center,coast_path.height
    def center(z):
        t=z*math.tau/L
        if name=='canyon': return 12000*math.sin(t)+2400*math.sin(3*t)
        if name=='forest': return 7500*math.sin(t)+1200*math.sin(4*t)
        if name=='snow': return 11000*math.sin(2*t)+2000*math.sin(4*t)
        if name=='city': return 5000*math.sin(t)+300*math.sin(4*t)
        return 3500*math.sin(t)
    def height(z):
        t=z*math.tau/L
        if name=='canyon': return 600*math.sin(2*t)
        if name=='forest': return 8000*z/L+400*math.sin(t)
        if name=='snow': return 1600*math.sin(t)
        if name=='city': return -8000*z/L+250*math.sin(t)
        return 100*math.sin(t)
    return center,height

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['coast','canyon','forest','snow','city','night'])
    p.add_argument('--joined',action='store_true')
    p.add_argument('--expressive',action='store_true')
    p.add_argument('--adaptive',action='store_true')
    p.add_argument('--stable',action='store_true')
    p.add_argument('--lane-grid',action='store_true')
    args=p.parse_args();name=args.stage;out=(R/'work/joined-route-shapes' if args.joined else WORK)/name
    if args.expressive:out=R/'work/expressive-route-shapes'/name
    if args.adaptive:
        assert args.expressive and name!='coast'
        out=R/'work/adaptive-route-shapes'/name
    if args.stable:
        assert args.adaptive
        out=R/'work/stable-route-shapes'/name
    if args.lane_grid:
        assert args.stable
        out=R/'work/lined-route-shapes'/name
    (out/'assets').mkdir(parents=True,exist_ok=True)
    (out/'outputs').mkdir(exist_ok=True)
    center,height=curves(name)
    if args.joined or args.expressive:
        from join_route_shapes import joined_curves
        center,height=joined_curves(name,expressive=args.expressive)
    generator.R=out;generator.path_center=center;generator.path_height=height
    if args.adaptive:
        from adaptive_road_rows import install
        install(generator.c,stable=args.stable,lane_grid=args.lane_grid);generator.ADAPTIVE_ROWS=True
    generator.main()
    # Packing is an offline capacity measurement, not a runtime switch.
    spec=importlib.util.spec_from_file_location('candidate_pack',R/'tools/pack_runtime.py')
    pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
    pack.R=out;pack.main()
    samples=[]
    for i in range(513):
        z=i*L/512
        samples.append(dict(z=z,x=center(z),height=height(z),
                            grade=(height(z+1)-height(z-1))/2))
    report=dict(stage=name,integrated=False,world_length=L,
                net_height=height(L)-height(0),max_abs_grade=max(abs(s['grade']) for s in samples),
                samples=samples,
                joined_boundaries=args.joined or args.expressive,
                expressive=args.expressive,
                limitations=['Offline candidate; ROM placement and native driving validation pending'])
    (out/'outputs/path.json').write_text(json.dumps(report,indent=2))
    print(name, 'candidate generated; playable assets unchanged.')

if __name__=='__main__':main()
