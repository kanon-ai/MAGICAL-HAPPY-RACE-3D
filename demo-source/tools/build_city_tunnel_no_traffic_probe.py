"""Diagnostic only: isolate the city tunnel's extra traffic pass."""
from pathlib import Path
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text()
s=s.replace("src/drive_city_tunnel_trial.c", "src/drive_city_tunnel_no_traffic_probe.c")
s=s.replace("city-tunnel-trial", "city-tunnel-no-traffic-probe")
marker="sd=Path("
insertion='''source=R/'src/drive_city_tunnel_trial.c'
text=source.read_text()
start=text.index(' for(n=0;n<5;++n){',text.index('static void draw_city_tunnel'))
end=text.index('\\n}\\nvoid draw_late_tunnel',start)
text=text[:start]+text[end:]
(R/'src/drive_city_tunnel_no_traffic_probe.c').write_text(text)
'''
s=s.replace(marker,insertion+marker,1)
exec(compile(s,str(p),'exec'))
