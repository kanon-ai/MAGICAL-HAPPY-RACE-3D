from pathlib import Path
R=Path(__file__).resolve().parents[1]
text=(R/'src/drive_city_tunnel_far_lod.c').read_text()
text=text.replace('uint8_t distant=gap>512 && halfdepth<=24;', 'uint8_t distant=(gap>512 && halfdepth<=24)||(PIECE==39 && gap>1400);')
text=text.replace('stream_far_uv(arch_uv+64)','stream_far_uv(halfdepth>24?tunnel_uv+64:arch_uv+64)')
text=text.replace('if(entrance<=1400 && entrance>-(CAMERA?92:32))','if(entrance>-(CAMERA?92:32))')
(R/'src/drive_city_tunnel_portal_lod.c').write_text(text)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_portal_lod.c').replace('city-tunnel-trial','city-tunnel-portal-lod').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7ec0')
exec(compile(s,str(p),'exec'))
