"""Assemble optional adaptive-Y reader only; never patch a playable ROM.

Coast executes original byte-for-byte Y arithmetic. Inland reads the same
three-byte road records with Y in previously unused flag bits1..7.
"""
from pathlib import Path
import json,subprocess
R=Path(__file__).resolve().parents[1]
O=R/'work/adaptive-road-reader';O.mkdir(exist_ok=True)
rom=(R/'outputs/six-route-expressive/MAGICAL_HAPPY_RALLY_3D_DICT_COAST_TRIAL.rom').read_bytes()
S=json.loads((R/'outputs/symbols.json').read_text())
address=0x9024;at=1*16384+8192+0x1024
old=rom[at:at+32]
assert old[2:6]==bytes.fromhex('dd 86 f3 6f') and old[-2:]==bytes.fromhex('7b 81')
helper=0x3bab
asm=f'''org {helper}
 ld a,({S['_route_piece']})
 cp 8
 jr nc,adaptive
 db {','.join(str(v) for v in old)}
 jp {address+32}
adaptive:
 ld a,(ix-13)
 ld c,a
 add a,a
 add a,c
 add a,2
 ld l,a
 ld h,0
 ld de,{S['_profile']}
 add hl,de
 ld a,(hl)
 srl a
 add a,64
 jp {address+32}
'''
(O/'reader.asm').write_text(asm)
subprocess.run(['C:/Software/Pasmo/pasmo.exe','--bin',str(O/'reader.asm'),str(O/'reader.bin'),str(O/'reader.sym')],check=True)
code=(O/'reader.bin').read_bytes();assert len(code)<=85
assert rom[214*16384+8192+6059:214*16384+8192+6144]==b'\xff'*85
(O/'reader-proof.json').write_text(json.dumps(dict(bytes=len(code),helper_address=helper,patch_address=address,original_bytes=old.hex(),replacement_bytes=(b'\xc3'+helper.to_bytes(2,'little')+bytes(29)).hex(),scope='Assembled only. Matching adaptive assets, ROM integration and native verification required.'),indent=2)+'\n')
print('Adaptive reader assembled:',len(code),'of 85 spare VIEW bytes. No playable ROM changed.')
