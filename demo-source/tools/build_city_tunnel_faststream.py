"""Exact byte-order face/UV port streams without C loop spills."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
t=(R/'src/drive_city_tunnel_fastcoord.c').read_text()
helpers='''static void lining_faces(uint16_t bases) __z88dk_fastcall __naked {
 bases;
 __asm
 ld b,#8
lining_faces_loop:
 ld a,l
 out (_gd),a
 inc a
 out (_gd),a
 ld a,h
 inc a
 out (_gd),a
 dec a
 out (_gd),a
 xor a
 out (_gd),a
 out (_gd),a
 out (_gd),a
 out (_gd),a
 out (_gd),a
 out (_gd),a
 ld a,#128
 out (_gd),a
 inc l
 inc h
 djnz lining_faces_loop
 ret
 __endasm;
}
static void lining_uv(uint8_t nearv) __z88dk_fastcall __naked {
 nearv;
 __asm
 ld b,#8
lining_uv_loop:
 ld a,#8
 out (_gd),a
 ld a,l
 out (_gd),a
 ld a,#55
 out (_gd),a
 ld a,l
 out (_gd),a
 ld a,#55
 out (_gd),a
 ld a,#9
 out (_gd),a
 ld a,#8
 out (_gd),a
 ld a,#9
 out (_gd),a
 djnz lining_uv_loop
 ret
 __endasm;
}
'''
needle='static uint8_t draw_lining_slice('
assert t.count(needle)==1;t=t.replace(needle,helpers+needle)
old='for(i=0;i<8;++i){gd=nearbase+i;gd=nearbase+1+i;gd=farbase+1+i;gd=farbase+i;\n  gd=0;gd=0;gd=0;gd=0;gd=0;gd=0;gd=128;}'
assert t.count(old)==1;t=t.replace(old,'lining_faces(nearbase|((uint16_t)farbase<<8));')
old='for(i=0;i<8;++i){gd=8;gd=vnear;gd=55;gd=vnear;gd=55;gd=9;gd=8;gd=9;}'
assert t.count(old)==1;t=t.replace(old,'lining_uv(vnear);')
(R/'src/drive_city_tunnel_faststream.c').write_text(t)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_faststream.c').replace('city-tunnel-trial','city-tunnel-faststream').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7e00')
exec(compile(s,str(p),'exec'))
