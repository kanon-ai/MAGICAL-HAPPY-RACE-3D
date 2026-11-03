"""Traffic-only balance candidate; keep road, hulls and arcade clock intact."""
from pathlib import Path
import sys
p=Path(__file__).with_name('build_front_gap_trial.py')
safe='--safe' in sys.argv
variant='traffic-balanced-safe' if safe else 'traffic-balanced'
s=p.read_text().replace('traffic-spaced',variant)
s=s.replace(' cp 1\n jr z,lane_allowed\n','')
s=s.replace(' and 127\n',' and 255\n')
s=s.replace(' and 7\n sub 2\n',' and 3\n sub 2\n')
s=s.replace('ld bc,2500','ld bc,4500').replace('ld bc,6000','ld bc,6000' if safe else 'ld bc,7000')
s=s.replace("bytes.fromhex('c608')","bytes.fromhex('c60c')")
s=s.replace("bytes.fromhex('dd36f50e')","bytes.fromhex('dd36f512')")
s=s.replace('pieces 2/3 within each stage','pieces 2/3/6/7 within each stage')
s=s.replace('staggered decisions for all five cars','8.53-second staggered decisions for all five cars')
s=s.replace('cruise steps8..10, passing14','cruise steps12..14, passing18')
s=s.replace('base2500 normally,6000','base4500 normally,'+('6000' if safe else '7000'))
if safe:
 # Four other cars can each push the spawn forward by 240. Keep the
 # worst-case slot below half the circular course, so it stays in front.
 assert 6000+4*240+4*240 < 8192
sys.argv=[str(p),'--'+variant]
exec(compile(s,str(p),'exec'))
