from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 base=R/('outputs/six-route-city-walk-continuity'+suffix);src=R/('outputs/six-route-lean-top'+suffix);out=R/('outputs/six-route-forest-shade'+suffix);out.mkdir(exist_ok=True)
 asm=(base/'city-helper.asm').read_text()
 asm=asm.replace('left_color_ready:\n','left_color_ready:\n call forest_shade\n',1)
 asm=asm.replace('right_face:\n','right_face:\n call forest_left\n',1)
 asm+=f'''
forest_shade:
 ld a,({S['_route_piece']})
 sub 16
 cp 8
 ret nc
 ld a,c
 cp 43
 ret nz
 push hl
 ld a,(ix-1)
 ld hl,{S['_sea_crest']-74}
 ld e,a
 ld d,0
 add hl,de
 ld e,(hl)
 ld d,0
 ld hl,36549
 add hl,de
 ld a,(hl)
 add a,40
 ld c,a
 pop hl
 ret
forest_left:
 ld a,({S['_route_piece']})
 sub 16
 cp 8
 ret nc
 ld a,(ix-8)
 sub 40
 cp 8
 ret nc
 ld c,(ix-8)
 ld hl,left_land
 xor a
 jp face
'''
 (out/'helper.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(out/'helper.asm'),str(out/'helper.bin')],check=True)
 code=(out/'helper.bin').read_bytes();assert len(code)<=8192
 rom=bytearray((src/name).read_bytes());old=(base/'city-helper.bin').read_bytes();at=188*16384+8192;assert rom[at:at+len(old)]==old
 assert rom[at+len(old):at+8192]==bytes([255])*(8192-len(old))
 rom[at:at+8192]=code+bytes([255])*(8192-len(code));(out/name).write_bytes(rom)
 for asset in ['city-atlas.bin','night-atlas.bin']:(out/asset).write_bytes((src/asset).read_bytes())
 (out/'manifest.json').write_text(json.dumps(dict(bytes=len(rom),helper_bytes=len(code),sha256=hashlib.sha256(rom).hexdigest(),runtime_verified=False),indent=2))
 print(suffix,len(code))
