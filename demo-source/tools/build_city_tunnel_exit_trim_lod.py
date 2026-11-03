from pathlib import Path
R=Path(__file__).resolve().parents[1]
t=(R/'src/drive_city_tunnel_exit_trim.c').read_text();t=t.replace('uint8_t distant=(gap>512','uint8_t distant=PIECE==40||(gap>512');needle='const uint8_t *back=halfdepth>24?tunnel_faces_back:arch_faces_back;';assert t.count(needle)==1;t=t.replace(needle,needle+'\n if(PIECE==40 && gap>512)return;')
(R/'src/drive_city_tunnel_exit_trim_lod.c').write_text(t)
p=Path(__file__).with_name('build_city_tunnel_trial.py');s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_exit_trim_lod.c').replace('city-tunnel-trial','city-tunnel-exit-trim-lod').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7ee0');exec(compile(s,str(p),'exec'))
p=Path(__file__).with_name('build_city_tunnel_depth_lod_tree.py');s=p.read_text().replace('six-route-city-tunnel-depth-lod','six-route-city-tunnel-exit-trim-lod');exec(compile(s,str(p),'exec'))
