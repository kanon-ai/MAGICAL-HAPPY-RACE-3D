"""Reuse four signed coordinate pairs on the stack for the mirrored half ring."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
t=(R/'src/drive_city_tunnel_fastcoord.c').read_text()
a=t.index('static void lining_ring(');b=t.index('static void terrain_ring(',a)
body='''static void lining_ring(Plane *p) __z88dk_fastcall __naked {
 p;
 __asm
 push ix
 push iy
 push hl
 pop ix
 ld iy,#(_rock_arch_vertices+54)
 ld b,#4
sym_left:
 push bc
 ld l,0(iy)
 ld h,1(iy)
 ld e,4(ix)
 ld d,5(ix)
 call _arch_coord
 pop bc
 push de
 ld l,0(ix)
 ld h,1(ix)
 add hl,de
 ld a,l
 out (_gd),a
 ld a,h
 out (_gd),a
 push bc
 ld l,2(iy)
 ld h,3(iy)
 ld e,4(ix)
 ld d,5(ix)
 call _arch_coord
 pop bc
 ld l,2(ix)
 ld h,3(ix)
 ex de,hl
 or a
 sbc hl,de
 push hl
 ld a,l
 out (_gd),a
 ld a,h
 out (_gd),a
 ld a,#1
 out (_gd),a
 xor a
 out (_gd),a
 ld de,#6
 add iy,de
 djnz sym_left
 ld a,0(ix)
 out (_gd),a
 ld a,1(ix)
 out (_gd),a
 ld hl,#100
 ld e,4(ix)
 ld d,5(ix)
 call _arch_coord
 ld l,2(ix)
 ld h,3(ix)
 ex de,hl
 or a
 sbc hl,de
 ld a,l
 out (_gd),a
 ld a,h
 out (_gd),a
 ld a,#1
 out (_gd),a
 xor a
 out (_gd),a
 ld b,#4
sym_right:
 pop iy
 pop de
 ld l,0(ix)
 ld h,1(ix)
 or a
 sbc hl,de
 ld a,l
 out (_gd),a
 ld a,h
 out (_gd),a
 push iy
 pop hl
 ld a,l
 out (_gd),a
 ld a,h
 out (_gd),a
 ld a,#1
 out (_gd),a
 xor a
 out (_gd),a
 djnz sym_right
 pop iy
 pop ix
 ret
 __endasm;
}
'''
t=t[:a]+body+t[b:]
(R/'src/drive_city_tunnel_symasm.c').write_text(t)
p=Path(__file__).with_name('build_city_tunnel_trial.py')
s=p.read_text().replace('src/drive_city_tunnel_trial.c','src/drive_city_tunnel_symasm.c').replace('city-tunnel-trial','city-tunnel-symasm').replace('-Wl-b_HOME=0x7d00','-Wl-b_HOME=0x7e00')
exec(compile(s,str(p),'exec'))
