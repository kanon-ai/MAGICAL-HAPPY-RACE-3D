"""Extend lining one world cell behind the car to cover the chase near plane."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
text=(R/'src/drive_city_tunnel_finish_trial.c').read_text()
needle='for(n=9;n;){\n  --n;z=((progress+32)&63);nearz=((int16_t)n<<6)-z;'
assert text.count(needle)==1
text=text.replace(needle,'for(n=10;n;){\n  --n;z=((progress+32)&63);nearz=(int16_t)n*64-64-z;')
(R/'src/drive_city_tunnel_nearfix.c').write_text(text)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_nearfix.c').replace('city-tunnel-trial','city-tunnel-nearfix').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7e00')
exec(compile(s,str(p),'exec'))
