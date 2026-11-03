from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for suffix,name in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom')]:
 src=R/('outputs/six-route-sky-bridge-once'+suffix);O=R/('outputs/six-route-sky-bridge-top'+suffix);O.mkdir(exist_ok=True);rom=bytearray((src/name).read_bytes());old=bytes(rom)
 asm=f"""org 03947h
 ld a,({S['_scene_ready']})
 cp 1
 jr nz,original
 ld a,({S['_scene_target']})
 cp 5
 jr nz,original
 ld hl,({S['_scene_pan']})
 ld a,h
 or l
 jr nz,skip
original:
 ld a,({S['_route_piece']})
 sub 40
 jp 08b41h
skip:
 jp 08b60h
"""
 (O/'top.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'top.asm'),str(O/'top.bin')],check=True)
 code=(O/'top.bin').read_bytes();assert len(code)<=83
 at=214*16384+8192+0x1547;rom[at:at+len(code)]=code
 at=16384+8192+0xb3c;assert rom[at:at+3]==b'\x3a'+S['_route_piece'].to_bytes(2,'little');rom[at:at+3]=bytes.fromhex('c34739')
 assert rom[16384+8192+0xb73:16384+8192+0xb76]==bytes(3)
 (O/name).write_bytes(rom)
 for a in ['city-atlas.bin','night-atlas.bin']:(O/a).write_bytes((src/a).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(old).hexdigest(),free_bytes=303104,scope='Skip old initial topfill only when bridge emits its full topfill; repurpose unused draw_night_sky_top body.'),indent=2))
