from pathlib import Path
R=Path(__file__).resolve().parents[1]
t=(R/'src/drive_city_tunnel_depth_lod.c').read_text();old='if(entrance>-(CAMERA?92:32))draw_rock_shell(entrance,32);';assert t.count(old)==1
t=t.replace(old,'if(PIECE==40)entrance=exitgap;\n if(entrance>-(CAMERA?92:32))draw_rock_shell(entrance,32);\n entrance=-progress;');(R/'src/drive_city_tunnel_exit_rim.c').write_text(t)
p=Path(__file__).with_name('build_city_tunnel_trial.py');s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_exit_rim.c').replace('city-tunnel-trial','city-tunnel-exit-rim').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7ee0');exec(compile(s,str(p),'exec'))
p=Path(__file__).with_name('build_city_tunnel_depth_lod_tree.py');s=p.read_text().replace('six-route-city-tunnel-depth-lod','six-route-city-tunnel-exit-rim');exec(compile(s,str(p),'exec'))
