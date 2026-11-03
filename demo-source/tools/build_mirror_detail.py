"""Near mirror silhouette: chamfered painted panels and a glass reflection.

Far rectangles and all projection/traffic rules remain unchanged. The original
clipping routine is relocated verbatim from compiler assembly into free ROM207.
"""
from pathlib import Path
import re,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
source=(R/'work/build/game.asm').read_text()
core=source.split('_mirror_rect:\n',1)[1].split('_rear_depth:',1)[0]
core='\n'.join(line.split(';',1)[0] for line in core.splitlines())
core=re.sub(r'(\d+)\$',r'core_\1',core).replace('#','')
core=re.sub(r'(-?\d+)\s*\(ix\)',lambda m:'(ix'+('+' if int(m[1])>=0 else '')+m[1]+')',core)
core=core.replace('_mirror_bottom',str(S['_mirror_bottom'])).replace('_gfx_fill',str(S['_gfx_fill']))
core=re.sub(r'\b(cp|sub|xor|or|and)\s+a,\s*',r'\1 ',core)
asm='''org 06000h
 push ix
 ld ix,0
 add ix,sp
 push hl
 push de
 push iy
 ; Preserve small/far shapes exactly. Width/height are signed 16-bit.
 ld a,(ix+5)
 or a
 jp nz,plain
 ld a,(ix+7)
 or a
 jp nz,plain
 ld a,(ix+4)
 cp 12
 jp c,plain
 ld a,(ix+6)
 cp 4
 jp c,plain
 ld a,(ix+8)
 cp 12
 jr z,glass
 cp 15
 jp z,plain
 ; Painted roof/bonnet: one-pixel bevel before clipping, not after it.
 call load_rect
 inc hl
 dec bc
 dec bc
 ld iy,1
 call panel
 call load_rect
 inc de
 ld iy,0
 push hl
 ld l,(ix+6)
 ld h,0
 dec hl
 dec hl
 push hl
 pop iy
 pop hl
 call panel
 call load_rect
 inc hl
 dec bc
 dec bc
 push hl
 ld l,(ix+6)
 ld h,0
 dec hl
 add hl,de
 ex de,hl
 pop hl
 ld iy,1
 call panel
 jp done
glass:
 call draw_plain
 call load_rect
 inc hl
 inc de
 dec bc
 dec bc
 ld iy,1
 ld a,36
 call fill_panel
 jp done
plain:
 call draw_plain
done:
 pop iy
 ld sp,ix
 pop ix
 pop hl
 pop af
 pop af
 inc sp
 jp 0a93dh
load_rect:
 ld l,(ix-2)
 ld h,(ix-1)
 ld e,(ix-4)
 ld d,(ix-3)
 ld c,(ix+4)
 ld b,(ix+5)
 ret
draw_plain:
 call load_rect
 push hl
 ld l,(ix+6)
 ld h,(ix+7)
 push hl
 pop iy
 pop hl
panel:
 ld a,(ix+8)
fill_panel:
 push af
 inc sp
 push iy
 push bc
 call clip_rect
 ret
clip_rect:
'''+core
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 O=R/('outputs/six-route-mirror-detail'+suffix);O.mkdir(exist_ok=True)
 (O/'detail.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'detail.asm'),str(O/'detail.bin')],check=True)
 code=(O/'detail.bin').read_bytes();assert len(code)<8192
 src=R/('outputs/six-route-traffic-balanced-safe'+suffix);rom=bytearray((src/name).read_bytes());old=bytes(rom)
 bank=207*16384+8192;assert rom[bank:bank+8192]==b'\xff'*8192
 at=2*16384+8192+0x935
 assert rom[at:at+8]==bytes.fromhex('dde5dd210000dd39')
 patch=bytes.fromhex('3ecf320060c300603efc320060e9')
 rom[at:at+len(patch)]=patch;rom[bank:bank+len(code)]=code
 assert len(rom)==4194304
 assert all(at<=i<at+len(patch) or bank<=i<bank+len(code) for i,(a,b) in enumerate(zip(old,rom)) if a!=b)
 (O/name).write_bytes(rom)
 for asset in ('night-sky.bin','snow-atlas.bin','city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((src/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),sha256=hashlib.sha256(rom).hexdigest(),helper_bytes=len(code),scope='Mirror rectangles only; near painted panel corners and glass reflection. Runtime verification pending.'),indent=2))
 print(O,len(code))
