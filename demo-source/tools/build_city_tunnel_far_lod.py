from pathlib import Path
R=Path(__file__).resolve().parents[1]
text=(R/'src/drive_city_tunnel_early_portal.c').read_text()
a=text.index('static void draw_tunnel_embankment');b=text.index('static void draw_city_tunnel',a)
s=text[a:b]
s=s.replace('uint8_t i,j,k;', 'uint8_t i,j,k,step=(PIECE==39 && gap>1656)?4:1,faces=step==4?8:32;')
s=s.replace('i<5;++i','i<5;i+=step')
s=s.replace('i<32;++i','i<faces;++i')
s=s.replace('gd=45;gi=0x59;gd=32;', 'gd=step==4?18:45;gi=0x59;gd=faces;')
text=text[:a]+s+text[b:]
text=text.replace('if(entrance>-(CAMERA?92:32))draw_rock_shell(entrance,32);','if(entrance<=1400 && entrance>-(CAMERA?92:32))draw_rock_shell(entrance,32);')
(R/'src/drive_city_tunnel_far_lod.c').write_text(text)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_far_lod.c').replace('city-tunnel-trial','city-tunnel-far-lod').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7ea0')
exec(compile(s,str(p),'exec'))
