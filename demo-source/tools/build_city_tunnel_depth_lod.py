from pathlib import Path
R=Path(__file__).resolve().parents[1]
t=(R/'src/drive_city_tunnel_portal_lod.c').read_text();a=t.index('static void draw_city_tunnel');b=t.index('void draw_late_tunnel',a);part=t[a:b]
assert part.count('farz=nearz+64;')==1
part=part.replace('farz=nearz+64;','farz=nearz+64;\n  if(n>=5){--n;nearz-=64;}')
t=t[:a]+part+t[b:];(R/'src/drive_city_tunnel_depth_lod.c').write_text(t)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_depth_lod.c').replace('city-tunnel-trial','city-tunnel-depth-lod').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7ed0')
exec(compile(s,str(p),'exec'))
