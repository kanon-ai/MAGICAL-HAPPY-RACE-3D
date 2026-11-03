from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];S=json.loads((R/'outputs/symbols.json').read_text())
for suffix,name,expected in [('', 'MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom','5c8fa85fdfe816a2869d4b6a6f7d6d905e5fb055edfa5b2a475355ec824d77c2'),('-external-88h','MAGICAL_HAPPY_RALLY_3D_EXTERNAL_88H_TRIAL.rom','ef87843d2802b705ed5d273ff6b2651993ed5d4cebec13aa36731819109808a0')]:
 source=R/f'outputs/six-route-city-walk-continuity{suffix}';O=R/f'outputs/six-route-city-trees{suffix}';O.mkdir(exist_ok=True)
 rom=bytearray((source/name).read_bytes());assert hashlib.sha256(rom).hexdigest()==expected
 asm=f"""org 0dbach
 ld b,0
 ld a,({S['_route_piece']})
 cp 40
 ld a,(ix-8)
 jr nc,night
 cp 1
 ld c,5
 ret z
 cp 3
 ret z
 jr building
night:
 cp 3
 ld c,1
 ret z
building:
 cp 2
 ld c,2
 ret z
 ld c,0
 ret
"""
 (O/'trees.asm').write_text(asm);subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'trees.asm'),str(O/'trees.bin')],check=True)
 code=(O/'trees.bin').read_bytes();assert len(code)<=84
 at=3*16384+8192+0x1bac;assert rom[at:at+len(code)]==bytes([255])*len(code);rom[at:at+len(code)]=code
 at=214*16384+8192+0x144c;assert rom[at:at+6]==bytes.fromhex('dd7ef8d60320');rom[at:at+6]=bytes.fromhex('cdacdbc39e38')
 (O/name).write_bytes(rom)
 for asset in ('city-atlas.bin','night-atlas.bin'):(O/asset).write_bytes((source/asset).read_bytes())
 (O/'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=expected,helper_bytes=len(code),free_bytes=344064,scope='City identity1 uses existing broadleaf sprite; night choices unchanged. Runtime validation pending.'),indent=2));print(O)
