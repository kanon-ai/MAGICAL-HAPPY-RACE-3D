"""Isolated portal embankment and checkpoint sign rendering."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
text=(R/'src/drive_city_tunnel_concrete.c').read_text()
text=text.replace('if(entrance>-(CAMERA?92:32))draw_rock_shell(entrance,32);',
 'if(entrance>16)draw_tunnel_embankment(entrance+256);\n if(entrance>-(CAMERA?92:32))draw_rock_shell(entrance,32);')
text=text.replace('if(top>=p.clip || p.y<0)return;',
 'if(PIECE==39){left=p.x-p.w*3/4;right=p.x+p.w*3/4;top=p.y-p.w*11/8;beam=p.y-p.w*9/8;}\n if(top>=p.clip || p.y<0)return;')
text=text.replace('gi=0x48;gd=7;while(gi&1)POLL();\n WORD(0x54,0);WORD(0x56,0);\n}',
 'if(PIECE==39){WORD(0x54,218);WORD(0x56,152);gi=0x42;gd=4;gi=0x59;gd=1;}\n gi=0x48;gd=7;while(gi&1)POLL();\n WORD(0x54,0);WORD(0x56,0);\n}',1)
city=text.index('static void draw_city_tunnel')
at=text.index(' for(n=0;n<5;++n){',city)
text=text[:at]+' if(PIECE==39)draw_drive_gate();\n'+text[at:]
(R/'src/drive_city_tunnel_finish_trial.c').write_text(text)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_finish_trial.c').replace('city-tunnel-trial','city-tunnel-finish-trial')
s=s.replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7e00')
exec(compile(s,str(p),'exec'))
