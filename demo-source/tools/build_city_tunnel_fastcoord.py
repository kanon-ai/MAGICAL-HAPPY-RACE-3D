"""Exact Q6 coordinate shift using two left shifts and a byte extraction."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
text=(R/'src/drive_city_tunnel_nearfix.c').read_text()
old='ld b,#6\narch_shift:\n srl e\n rr h\n rr l\n djnz arch_shift\n ex de,hl'
new='add hl,hl\n rl e\n add hl,hl\n rl e\n ld l,h\n ld h,e\n ex de,hl'
assert text.count(old)==1
text=text.replace(old,new)
(R/'src/drive_city_tunnel_fastcoord.c').write_text(text)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_fastcoord.c').replace('city-tunnel-trial','city-tunnel-fastcoord').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7e00')
exec(compile(s,str(p),'exec'))
