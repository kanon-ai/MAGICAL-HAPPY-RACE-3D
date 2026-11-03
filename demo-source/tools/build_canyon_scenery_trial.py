"""Use world-object piece to retain entrance trees and reveal inland rocks.

Only canyon pieces8..13 differ. Shared vegetation survives the coast entrance
and returns toward forest. No art, geometry, traffic or collision data changes.
"""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];O=R/'outputs/six-route-canyon-scenery';O.mkdir(exist_ok=True)
name='MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom'
source=R/'outputs/six-route-lined'/name;original=source.read_bytes();rom=bytearray(original)
S=json.loads((R/'outputs/symbols.json').read_text())
at=3*16384+8192+0x19a1
expected=b'\x18\x0c'+S['_route_piece'].to_bytes(2,'little')[1:]+bytes.fromhex('d6 08 38 07 3a')+S['_route_piece'].to_bytes(2,'little')+bytes.fromhex('d6 0e 38 18')
assert len(expected)==14 and rom[at:at+14]==expected
helper=0xdb84;start=3*16384+8192+0x1b84
assert rom[start:start+124]==b'\xff'*124
asm=f'''org {helper}
 ld a,({S['_route_piece']})
 cp 8
 jr c,shared_plants
 cp 14
 jr nc,shared_plants
 ; E is the sorted object slot, C is the architecture visibility mask.
 push bc
 ld a,e
 ld c,60
 db 0edh,0c9h
 ld bc,0100h+58
 add hl,bc
 ld a,({S['_route_piece']})
 add a,(hl)
 pop bc
 ; The object's piece is invariant as the camera crosses its boundary.
 cp 9
 jr c,shared_plants
 cp 14
 jr nc,shared_plants
 jp 0d9c7h
shared_plants:
 jp 0d9afh
'''
(O/'scenery.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'scenery.asm'),str(O/'scenery.bin'),str(O/'scenery.sym')],check=True)
code=(O/'scenery.bin').read_bytes();assert len(code)<=124
rom[start:start+len(code)]=code;rom[at:at+3]=b'\xc3'+helper.to_bytes(2,'little')
changes=[i for i,(a,b) in enumerate(zip(original,rom)) if a!=b]
assert all(i in range(at,at+3) or i in range(start,start+len(code)) for i in changes)
(O/name).write_bytes(rom)
report=dict(sha256=hashlib.sha256(rom).hexdigest(),source_sha256=hashlib.sha256(original).hexdigest(),helper_bytes=len(code),changed_bytes=len(changes),free_rules_padding=124-len(code),scope='Canyon world-object selection only. Visual, boundary stability and runtime validation pending.')
(O/'build-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
