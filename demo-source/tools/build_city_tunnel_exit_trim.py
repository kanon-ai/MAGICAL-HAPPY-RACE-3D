from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
h=(R/'src/rock_arch_model.h').read_text();body=h.split('={',1)[1].split('};',1)[0];v=[list(map(int,x)) for x in re.findall(r'\{(-?\d+),(-?\d+),(-?\d+)\}',body)];assert len(v)==36 and [x[:2] for x in v[:18]]==[x[:2] for x in v[18:]]
base=[x[:2] for x in v[:18]];inner=base[9:];thin=[[round(x*1.08),round(y*1.08)] for x,y in inner]+inner
h='/* Front/back share XY; depth supplied by projected planes. */\n'
for name,data in [('rock_arch_vertices',base),('exit_trim_vertices',thin)]:h+='static const int16_t '+name+'[18][2]={'+','.join('{'+','.join(map(str,x))+'}' for x in data)+'};\n'
(R/'src/rock_arch_compact_exit.h').write_text(h)
t=(R/'src/drive_city_tunnel_exit_order.c').read_text().replace('#include "rock_arch_model.h"','#include "rock_arch_compact_exit.h"').replace('v=rock_arch_vertices[i];','v=(PIECE==40?exit_trim_vertices:rock_arch_vertices)[i<18?i:i-18];').replace('(_rock_arch_vertices+54)','(_rock_arch_vertices+36)')
a=t.index('static void lining_ring');b=t.index('static uint8_t draw_lining_slice',a);part=t[a:b];assert 'ld de,#6' in part;part=part.replace('ld de,#6','ld de,#4');t=t[:a]+part+t[b:]
(R/'src/drive_city_tunnel_exit_trim.c').write_text(t)
p=Path(__file__).with_name('build_city_tunnel_trial.py');s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_exit_trim.c').replace('city-tunnel-trial','city-tunnel-exit-trim').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7ee0');exec(compile(s,str(p),'exec'))
p=Path(__file__).with_name('build_city_tunnel_depth_lod_tree.py');s=p.read_text().replace('six-route-city-tunnel-depth-lod','six-route-city-tunnel-exit-trim');exec(compile(s,str(p),'exec'))
