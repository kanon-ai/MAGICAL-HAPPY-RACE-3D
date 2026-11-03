from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for suffix,name,expected in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom','5c8fa85fdfe816a2869d4b6a6f7d6d905e5fb055edfa5b2a475355ec824d77c2'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom','ef87843d2802b705ed5d273ff6b2651993ed5d4cebec13aa36731819109808a0')]:
 source=R/f'outputs/six-route-city-walk-continuity{suffix}';O=R/f'outputs/six-route-building-vertices{suffix}';O.mkdir(exist_ok=True)
 rom=bytearray((source/name).read_bytes());assert hashlib.sha256(rom).hexdigest()==expected
 asm=f"""org 09975h
 ld (ix-2),0
 pop bc
 push bc
loop:
 ld h,b
 ld l,c
 ld e,(hl)
 inc hl
 ld d,(hl)
 inc hl
 ld (ix-4),e
 ld (ix-3),d
 ld e,(hl)
 inc hl
 ld d,(hl)
 inc hl
 ld a,(hl)
 ld (ix-5),a
 ld a,({S['_camera_mode']})
 or a
 jr z,cockpit
 push bc
 push de
 ld a,(ix-5)
 push af
 inc sp
 ld l,(ix-4)
 ld h,(ix-3)
 call {S['_view_x']}
 ld (ix-4),e
 ld (ix-3),d
 pop hl
 ld a,(ix-5)
 push af
 inc sp
 call {S['_view_y']}
 push de
 ld a,(ix-5)
 call {S['_view_width']}
 pop de
 pop bc
 jr shifted_width
cockpit:
 ld a,(ix-5)
shifted_width:
 srl a
 push bc
 push de
 call {S['_camera_shift']}
 ex de,hl
 pop de
 pop bc
 ld a,(ix-4)
 sub l
 ld l,a
 ld a,(ix-3)
 sbc a,h
 ld h,a
 push bc
 call {S['_road_vertex']}
 pop bc
 inc bc
 inc bc
 inc bc
 inc bc
 inc bc
 inc (ix-2)
 ld a,(ix-2)
 cp 8
 jp c,loop
 jp 09a03h
"""
 (O/'vertices.asm').write_text(asm)
 subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'vertices.asm'),str(O/'vertices.bin')],check=True)
 code=(O/'vertices.bin').read_bytes();assert len(code)<=0x9a03-0x9975,len(code)
 at=16384+8192+0x1975;assert rom[at:at+6]==bytes.fromhex('dd36fe00c1c5')
 rom[at:at+0x8e]=code+bytes(0x8e-len(code));(O/name).write_bytes(rom)
 for asset in ('city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((source/asset).read_bytes())
 report=dict(source_sha256=expected,sha256=hashlib.sha256(rom).hexdigest(),code_bytes=len(code),free_rom_bytes=344064,scope='Building vertex fetch/camera path only; runtime validation pending.')
 (O/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
