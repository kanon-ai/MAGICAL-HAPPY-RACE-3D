"""Move invariant lining state setup outside each contiguous slice loop."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
t=(R/'src/drive_city_tunnel_fastcoord.c').read_text()
start=t.index('static uint8_t draw_lining_slice(')
end=t.index('\nvoid draw_drive_gate',start)
part=t[start:end]
old=''' TEX_WINDOW(192,754,255,767);
 WORD(24,1);WORD(26,0);WORD(28,0);WORD(30,1);WORD(34,a.clip);
 WORD(0x60,192);WORD(0x62,754);gi=0x64;gd=0;
 gi=0x68;gd=0;gi=0x6c;gd=0;gi=0x6e;gd=0;gi=0x6f;gd=0;'''
assert part.count(old)==1
common=old.replace('WORD(34,a.clip);','')
part=part.replace(old,' WORD(34,a.clip);')
t=t[:start]+'static void lining_setup(void){\n'+common+'\n}\n'+part+t[end:]
needle=' /* World anchored 64-unit cells; only the near road\'s sampled depth is used. */'
assert t.count(needle)==1;t=t.replace(needle,' lining_setup();\n'+needle)
needle='  draw_rock_shell(gap,256);\n  for(n=8;n;)'
assert t.count(needle)==1;t=t.replace(needle,'  draw_rock_shell(gap,256);\n  lining_setup();\n  for(n=8;n;)')
(R/'src/drive_city_tunnel_setup_once.c').write_text(t)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_setup_once.c').replace('city-tunnel-trial','city-tunnel-setup-once').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7e00')
exec(compile(s,str(p),'exec'))
