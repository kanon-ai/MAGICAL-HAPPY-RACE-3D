"""Separate concrete-portal variant; preserve the first tunnel trial."""
from pathlib import Path
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_concrete.c').replace('city-tunnel-trial','city-tunnel-concrete')
insertion='''source=R/'src/drive_city_tunnel_trial.c'
text=source.read_text()
needle='if(entrance>-(CAMERA?84:24))draw_rock_shell(entrance,24);'
assert text.count(needle)==1
text=text.replace(needle,'if(entrance>-(CAMERA?92:32))draw_rock_shell(entrance,32);')
(R/'src/drive_city_tunnel_concrete.c').write_text(text)
'''
s=s.replace('sd=Path(',insertion+'sd=Path(',1)
exec(compile(s,str(p),'exec'))
