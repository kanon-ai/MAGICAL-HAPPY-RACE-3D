from pathlib import Path
R=Path(__file__).resolve().parents[1]
text=(R/'src/drive_city_tunnel_fastcoord.c').read_text()
old='if(entrance>1400 || exitgap<-(CAMERA?60:0))return;'
assert text.count(old)==1
text=text.replace(old,'if(entrance>4096 || exitgap<-(CAMERA?60:0))return;')
(R/'src/drive_city_tunnel_early_portal.c').write_text(text)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_early_portal.c').replace('city-tunnel-trial','city-tunnel-early-portal').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7e00')
exec(compile(s,str(p),'exec'))
